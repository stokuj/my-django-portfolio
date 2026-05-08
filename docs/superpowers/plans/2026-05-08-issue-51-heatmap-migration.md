# Issue 51 Heatmap Migration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Move GitHub heatmap fetching directly into Django, switch heatmap auth to a single `.env` token, and remove GitHub login via `django-allauth`.

**Architecture:** Add a small direct GitHub client for REST and GraphQL calls, keep `main/heatmap.py` as the orchestration and snapshot layer, then remove all `allauth`-driven routes, settings, and About-page UI. The frontend response contract and Celery snapshot flow stay intact while the dependency graph shrinks from `Django -> FastAPI -> GitHub` to `Django -> GitHub`.

**Tech Stack:** Django 5.1, Celery, requests, PostgreSQL, pytest-style Django test runner via `manage.py test`, uv.

---

## File Structure

- Create: `django/main/github_client.py`
  Responsibility: direct GitHub REST and GraphQL requests plus low-level response validation.
- Create: `django/main/tests/test_heatmap.py`
  Responsibility: unit coverage for GitHub client calls and heatmap payload shaping.
- Modify: `django/main/heatmap.py`
  Responsibility: replace `allauth`/FastAPI lookup with env-token orchestration and keep snapshot helpers.
- Modify: `django/main/tasks.py`
  Responsibility: keep the same task contract while consuming the new heatmap fetch path.
- Modify: `django/main/views.py`
  Responsibility: remove GitHub connect/disconnect behavior while keeping cached heatmap serving.
- Modify: `django/main/templates/pages/about.html`
  Responsibility: remove FastAPI/GitHub-connect wording and keep heatmap UI working from config-only state.
- Modify: `django/main/urls.py`
  Responsibility: remove heatmap disconnect route.
- Modify: `django/config/urls.py`
  Responsibility: remove `allauth` account routes and GitHub-login redirects.
- Modify: `django/main/context_processors.py`
  Responsibility: remove `github_connected` social-account context since it becomes dead code.
- Delete: `django/main/auth_adapters.py`
  Responsibility removed: GitHub social-login gatekeeping.
- Modify: `django/config/settings.py`
  Responsibility: remove `allauth` configuration, add `GITHUB_HEATMAP_TOKEN`, keep a simple auth backend list.
- Modify: `django/main/tests/test_views.py`
  Responsibility: replace social-auth-based tests with config-token-based behavior tests.
- Modify: `django/main/tests/test_urls.py`
  Responsibility: remove account-route assertions and assert removed routes are gone.
- Modify: `django/main/tests/test_tasks.py`
  Responsibility: add direct heatmap refresh task coverage.
- Modify: `README.md`
- Modify: `docs/architecture.md`
- Modify: `docs/implementation.md`
- Modify: `.env.example`
- Modify: `pyproject.toml`
- Modify: `uv.lock`

### Task 1: Add Direct GitHub Client And Unit Tests

**Files:**
- Create: `django/main/github_client.py`
- Create: `django/main/tests/test_heatmap.py`

- [ ] **Step 1: Write the failing GitHub client and heatmap unit tests**

```python
from unittest.mock import Mock, patch

import requests
from django.test import SimpleTestCase, override_settings

from main.github_client import (
    GitHubAuthenticationError,
    GitHubUpstreamError,
    fetch_authenticated_user,
    fetch_contribution_days,
)
from main.heatmap import build_weeks_payload, contribution_level, fetch_heatmap_data


class GitHubClientTests(SimpleTestCase):
    @patch("main.github_client.requests.get")
    def test_fetch_authenticated_user_returns_login(self, get_mock):
        response = Mock()
        response.status_code = 200
        response.json.return_value = {"id": 1, "login": "OctoCat"}
        get_mock.return_value = response

        payload = fetch_authenticated_user("ghp_test_token")

        self.assertEqual(payload, {"id": 1, "login": "OctoCat"})

    @patch("main.github_client.requests.get")
    def test_fetch_authenticated_user_maps_auth_error(self, get_mock):
        response = Mock()
        response.status_code = 401
        response.raise_for_status.side_effect = requests.HTTPError(response=response)
        get_mock.return_value = response

        with self.assertRaises(GitHubAuthenticationError):
            fetch_authenticated_user("bad-token")

    @patch("main.github_client.requests.post")
    def test_fetch_contribution_days_returns_flat_days(self, post_mock):
        response = Mock()
        response.status_code = 200
        response.json.return_value = {
            "data": {
                "user": {
                    "contributionsCollection": {
                        "contributionCalendar": {
                            "weeks": [
                                {
                                    "contributionDays": [
                                        {"date": "2026-02-15", "contributionCount": 0},
                                        {"date": "2026-02-16", "contributionCount": 3},
                                    ]
                                }
                            ]
                        }
                    }
                }
            }
        }
        post_mock.return_value = response

        days = fetch_contribution_days("octocat", "ghp_test_token")

        self.assertEqual(
            days,
            [
                {"date": "2026-02-15", "count": 0},
                {"date": "2026-02-16", "count": 3},
            ],
        )

    @patch("main.github_client.requests.post")
    def test_fetch_contribution_days_maps_timeout(self, post_mock):
        post_mock.side_effect = requests.Timeout()

        with self.assertRaises(GitHubUpstreamError):
            fetch_contribution_days("octocat", "ghp_test_token")


class HeatmapPayloadTests(SimpleTestCase):
    def test_contribution_level_matches_existing_thresholds(self):
        self.assertEqual(contribution_level(0), 0)
        self.assertEqual(contribution_level(2), 1)
        self.assertEqual(contribution_level(5), 2)
        self.assertEqual(contribution_level(9), 3)
        self.assertEqual(contribution_level(10), 4)

    def test_build_weeks_payload_groups_days_and_computes_total(self):
        weeks, total = build_weeks_payload(
            [
                {"date": "2026-02-15", "count": 0},
                {"date": "2026-02-16", "count": 2},
                {"date": "2026-02-17", "count": 10},
            ]
        )

        self.assertEqual(total, 12)
        self.assertEqual(
            weeks,
            [
                {
                    "week_start": "2026-02-15",
                    "days": [
                        {"date": "2026-02-15", "weekday": 0, "count": 0, "level": 0},
                        {"date": "2026-02-16", "weekday": 1, "count": 2, "level": 1},
                        {"date": "2026-02-17", "weekday": 2, "count": 10, "level": 4},
                    ],
                }
            ],
        )

    @override_settings(GITHUB_HEATMAP_TOKEN="ghp_test_token")
    @patch("main.heatmap.fetch_contribution_days")
    @patch("main.heatmap.fetch_authenticated_user")
    def test_fetch_heatmap_data_returns_normalized_payload(
        self,
        user_mock,
        days_mock,
    ):
        user_mock.return_value = {"id": 1, "login": "OctoCat"}
        days_mock.return_value = [
            {"date": "2026-02-15", "count": 0},
            {"date": "2026-02-16", "count": 2},
        ]

        payload, error = fetch_heatmap_data()

        self.assertIsNone(error)
        self.assertEqual(payload["username"], "octocat")
        self.assertEqual(payload["total"], 2)
        self.assertEqual(payload["weeks"][0]["days"][1]["level"], 1)
```

- [ ] **Step 2: Run the new focused test file to verify it fails**

Run: `uv run python django/manage.py test main.tests.test_heatmap -v 2`
Expected: FAIL with import errors for `main.github_client` and missing `contribution_level` / `build_weeks_payload` / zero-arg `fetch_heatmap_data` behavior.

- [ ] **Step 3: Write the minimal GitHub client implementation**

```python
from collections.abc import Mapping
from datetime import date, timedelta

import requests


class GitHubAuthenticationError(Exception):
    pass


class GitHubUpstreamError(Exception):
    pass


def _auth_headers(token: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "User-Agent": "my-django-portfolio",
    }


def fetch_authenticated_user(token: str) -> dict[str, str | int]:
    try:
        response = requests.get(
            "https://api.github.com/user",
            headers=_auth_headers(token),
            timeout=15,
        )
    except requests.Timeout as exc:
        raise GitHubUpstreamError from exc
    except requests.RequestException as exc:
        raise GitHubUpstreamError from exc

    if response.status_code in {401, 403}:
        raise GitHubAuthenticationError
    if response.status_code >= 400:
        raise GitHubUpstreamError

    payload = response.json()
    if not isinstance(payload, Mapping):
        raise GitHubUpstreamError

    raw_id = payload.get("id")
    raw_login = payload.get("login")
    if not isinstance(raw_id, int) or not isinstance(raw_login, str) or not raw_login:
        raise GitHubUpstreamError

    return {"id": raw_id, "login": raw_login}


def fetch_contribution_days(username: str, token: str) -> list[dict[str, str | int]]:
    from_day = date.today() - timedelta(days=364)
    to_day = date.today()
    query = """
    query($login: String!, $from: DateTime!, $to: DateTime!) {
      user(login: $login) {
        contributionsCollection(from: $from, to: $to) {
          contributionCalendar {
            weeks {
              contributionDays {
                date
                contributionCount
              }
            }
          }
        }
      }
    }
    """
    variables = {
        "login": username,
        "from": f"{from_day.isoformat()}T00:00:00Z",
        "to": f"{to_day.isoformat()}T23:59:59Z",
    }

    try:
        response = requests.post(
            "https://api.github.com/graphql",
            json={"query": query, "variables": variables},
            headers={**_auth_headers(token), "Content-Type": "application/json"},
            timeout=20,
        )
    except requests.Timeout as exc:
        raise GitHubUpstreamError from exc
    except requests.RequestException as exc:
        raise GitHubUpstreamError from exc

    if response.status_code in {401, 403}:
        raise GitHubAuthenticationError
    if response.status_code >= 400:
        raise GitHubUpstreamError

    payload = response.json()
    if not isinstance(payload, Mapping) or payload.get("errors"):
        raise GitHubUpstreamError

    data = payload.get("data")
    user = data.get("user") if isinstance(data, Mapping) else None
    collection = user.get("contributionsCollection") if isinstance(user, Mapping) else None
    calendar = collection.get("contributionCalendar") if isinstance(collection, Mapping) else None
    weeks = calendar.get("weeks") if isinstance(calendar, Mapping) else None
    if not isinstance(weeks, list):
        raise GitHubUpstreamError

    days = []
    for week in weeks:
        if not isinstance(week, Mapping):
            continue
        contribution_days = week.get("contributionDays")
        if not isinstance(contribution_days, list):
            continue
        for item in contribution_days:
            if not isinstance(item, Mapping):
                continue
            raw_date = item.get("date")
            raw_count = item.get("contributionCount")
            if isinstance(raw_date, str) and isinstance(raw_count, int):
                days.append({"date": raw_date, "count": raw_count})

    return days
```

- [ ] **Step 4: Refactor `main/heatmap.py` to orchestrate direct GitHub access**

```python
import datetime

from django.conf import settings
from django.utils import timezone

from .github_client import (
    GitHubAuthenticationError,
    GitHubUpstreamError,
    fetch_authenticated_user,
    fetch_contribution_days,
)
from .models import HeatmapSnapshot


def get_configured_github_token():
    return (getattr(settings, "GITHUB_HEATMAP_TOKEN", "") or "").strip() or None


def contribution_level(count: int) -> int:
    if count <= 0:
        return 0
    if count <= 2:
        return 1
    if count <= 5:
        return 2
    if count <= 9:
        return 3
    return 4


def build_weeks_payload(contribution_days):
    grouped_weeks = {}
    total = 0
    for item in contribution_days:
        raw_day = item.get("date")
        raw_count = item.get("count")
        if not isinstance(raw_day, str) or not isinstance(raw_count, int):
            continue
        parsed_day = datetime.date.fromisoformat(raw_day)
        weekday = (parsed_day.weekday() + 1) % 7
        week_start = parsed_day - datetime.timedelta(days=weekday)
        grouped_weeks.setdefault(week_start, []).append(
            {
                "date": parsed_day.isoformat(),
                "weekday": weekday,
                "count": raw_count,
                "level": contribution_level(raw_count),
            }
        )
        total += raw_count

    weeks = []
    for week_start in sorted(grouped_weeks):
        days = sorted(grouped_weeks[week_start], key=lambda day: int(day["weekday"]))
        weeks.append({"week_start": week_start.isoformat(), "days": days})
    return weeks, total


def fetch_heatmap_data(github_token=None):
    token = github_token or get_configured_github_token()
    if not token:
        return None, "Heatmap is not configured."
    try:
        github_user = fetch_authenticated_user(token)
        username = str(github_user["login"]).lower()
        contribution_days = fetch_contribution_days(username, token)
    except GitHubAuthenticationError:
        return None, "Configured GitHub token is invalid or expired."
    except GitHubUpstreamError:
        return None, "Heatmap service is temporarily unavailable."

    weeks, total = build_weeks_payload(contribution_days)
    return {"username": username, "total": total, "weeks": weeks}, None
```

- [ ] **Step 5: Run the focused test file to verify it passes**

Run: `uv run python django/manage.py test main.tests.test_heatmap -v 2`
Expected: PASS for all tests in `main.tests.test_heatmap`.

- [ ] **Step 6: Commit**

```bash
git add django/main/github_client.py django/main/heatmap.py django/main/tests/test_heatmap.py
git commit -m "feat: fetch heatmap data directly from github"
```

### Task 2: Switch Django Views And Celery To The New Heatmap Source

**Files:**
- Modify: `django/main/views.py`
- Modify: `django/main/tasks.py`
- Modify: `django/main/tests/test_views.py`
- Modify: `django/main/tests/test_tasks.py`

- [ ] **Step 1: Write failing integration tests for config-token heatmap behavior**

```python
from unittest.mock import patch

from django.test import TestCase, override_settings
from django.urls import reverse

from main.models import HeatmapSnapshot, TaskExecutionStatus
from main.tasks import REFRESH_HEATMAP_TASK_NAME, refresh_portfolio_heatmap_cache_task


class HeatmapViewBehaviorTests(TestCase):
    @override_settings(GITHUB_HEATMAP_TOKEN="ghp_live_token")
    @patch("main.views.refresh_portfolio_heatmap_cache_task.apply_async")
    @patch("main.views.fetch_heatmap_data")
    def test_about_heatmap_data_fetches_sync_when_cache_missing(
        self,
        fetch_mock,
        apply_async_mock,
    ):
        fetch_mock.return_value = (
            {
                "username": "portfolio-admin",
                "total": 21,
                "weeks": [
                    {
                        "days": [
                            {"date": "2026-05-08", "count": 3, "weekday": 5, "level": 2}
                        ]
                    }
                ],
            },
            None,
        )

        response = self.client.get(reverse("about_heatmap_data"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["username"], "portfolio-admin")
        fetch_mock.assert_called_once_with()
        apply_async_mock.assert_called_once_with(kwargs={"schedule_next": True}, countdown=3600)


class HeatmapTaskBehaviorTests(TestCase):
    @override_settings(GITHUB_HEATMAP_TOKEN="ghp_live_token")
    @patch("main.tasks.fetch_heatmap_data")
    def test_refresh_task_updates_status_on_success(self, fetch_mock):
        fetch_mock.return_value = (
            {"username": "octocat", "total": 12, "weeks": [{"days": []}]},
            None,
        )

        result = refresh_portfolio_heatmap_cache_task()

        status = TaskExecutionStatus.objects.get(task_name=REFRESH_HEATMAP_TASK_NAME)
        self.assertTrue(result["ok"])
        self.assertEqual(status.last_status, TaskExecutionStatus.STATUS_SUCCESS)

    @override_settings(GITHUB_HEATMAP_TOKEN="")
    def test_refresh_task_fails_when_token_missing(self):
        result = refresh_portfolio_heatmap_cache_task()

        status = TaskExecutionStatus.objects.get(task_name=REFRESH_HEATMAP_TASK_NAME)
        self.assertFalse(result["ok"])
        self.assertEqual(result["error"], "Heatmap is not configured.")
        self.assertEqual(status.last_status, TaskExecutionStatus.STATUS_FAILURE)
```

- [ ] **Step 2: Run the targeted view and task tests to verify they fail**

Run: `uv run python django/manage.py test main.tests.test_views main.tests.test_tasks -v 2`
Expected: FAIL because current code still patches `get_portfolio_github_token`, still calls `fetch_heatmap_data(github_token)`, and does not yet reflect the new missing-token error path.

- [ ] **Step 3: Update views and tasks to consume config-only heatmap fetching**

```python
from .heatmap import (
    fetch_heatmap_data,
    get_configured_github_token,
    get_or_create_snapshot,
    is_snapshot_stale,
    update_snapshot_error,
    update_snapshot_with_payload,
)


def about(request):
    has_heatmap_token = get_configured_github_token() is not None
    is_admin_user = request.user.is_authenticated and request.user.is_staff
    context = {
        "heatmap_component_visible": has_heatmap_token or is_admin_user,
        "heatmap_enabled": has_heatmap_token,
    }
    if is_admin_user:
        context["scheduled_jobs"] = _get_scheduled_jobs_overview()
        context["executed_tasks"] = _get_executed_tasks()
    return render(request, "pages/about.html", context)


@require_GET
def about_heatmap_data(request):
    if not get_configured_github_token():
        return JsonResponse({"error": "Heatmap is not configured."}, status=404)

    snapshot = get_or_create_snapshot()
    if not snapshot.payload or is_snapshot_stale(snapshot):
        payload, error = fetch_heatmap_data()
        if error:
            update_snapshot_error(error)
            if snapshot.payload:
                return _build_heatmap_snapshot_response(snapshot)
            return JsonResponse({"error": error}, status=503)
        snapshot = update_snapshot_with_payload(payload)
        _schedule_next_heatmap_refresh()

    return _build_heatmap_snapshot_response(snapshot)
```

```python
from .heatmap import (
    fetch_heatmap_data,
    get_configured_github_token,
    update_snapshot_error,
    update_snapshot_with_payload,
)


@shared_task
def refresh_portfolio_heatmap_cache_task(schedule_next=False):
    status, _ = TaskExecutionStatus.objects.get_or_create(
        task_name=REFRESH_HEATMAP_TASK_NAME
    )
    status.last_run_at = timezone.now()

    if not get_configured_github_token():
        message = "Heatmap is not configured."
        update_snapshot_error(message)
        status.last_status = TaskExecutionStatus.STATUS_FAILURE
        status.last_failure_at = timezone.now()
        status.last_total = 1
        status.last_updated = 0
        status.last_failed = 1
        status.last_error = message
        status.save(update_fields=[
            "last_status",
            "last_run_at",
            "last_failure_at",
            "last_total",
            "last_updated",
            "last_failed",
            "last_error",
        ])
        _log_task_execution(status)
        _maybe_schedule_next_refresh(schedule_next)
        return {"ok": False, "error": message}

    payload, error = fetch_heatmap_data()
    if error:
        update_snapshot_error(error)
        status.last_status = TaskExecutionStatus.STATUS_FAILURE
        status.last_failure_at = timezone.now()
        status.last_total = 1
        status.last_updated = 0
        status.last_failed = 1
        status.last_error = error
        status.save(update_fields=[
            "last_status",
            "last_run_at",
            "last_failure_at",
            "last_total",
            "last_updated",
            "last_failed",
            "last_error",
        ])
        _log_task_execution(status)
        _maybe_schedule_next_refresh(schedule_next)
        return {"ok": False, "error": error}

    snapshot = update_snapshot_with_payload(payload)
    status.last_status = TaskExecutionStatus.STATUS_SUCCESS
    status.last_success_at = timezone.now()
    status.last_total = 1
    status.last_updated = 1
    status.last_failed = 0
    status.last_error = ""
    status.save(update_fields=[
        "last_status",
        "last_run_at",
        "last_success_at",
        "last_total",
        "last_updated",
        "last_failed",
        "last_error",
    ])
    _log_task_execution(status)
    _maybe_schedule_next_refresh(schedule_next)
    return {
        "ok": True,
        "username": snapshot.username,
        "total": snapshot.total,
        "weeks_count": snapshot.weeks_count,
    }
```

- [ ] **Step 4: Update existing view/task tests to stop depending on social auth**

```python
@override_settings(GITHUB_HEATMAP_TOKEN="")
def test_about_shows_heatmap_for_admin_when_not_configured(self):
    admin_user = User.objects.create_user(
        username="admin-no-token",
        email="admin-no-token@example.com",
        password="secret",
        is_superuser=True,
        is_staff=True,
    )
    self.client.force_login(admin_user)

    response = self.client.get(reverse("about"))

    self.assertEqual(response.status_code, 200)
    self.assertContains(response, "GitHub Contributions")
    self.assertContains(response, "Heatmap is not configured.")
    self.assertNotContains(response, "Login with GitHub")
    self.assertNotContains(response, "Disconnect GitHub")


@override_settings(GITHUB_HEATMAP_TOKEN="ghp_live_token")
def test_about_shows_heatmap_for_anonymous_when_configured(self):
    response = self.client.get(reverse("about"))
    self.assertEqual(response.status_code, 200)
    self.assertContains(response, "GitHub Contributions")
```

```python
from main.tasks import (
    REFRESH_HEATMAP_TASK_NAME,
    SYNC_MARKDOWNS_TASK_NAME,
    refresh_portfolio_heatmap_cache_task,
    sync_project_markdowns_task,
)
```

- [ ] **Step 5: Run the targeted integration tests to verify they pass**

Run: `uv run python django/manage.py test main.tests.test_views main.tests.test_tasks -v 2`
Expected: PASS for updated heatmap view and task coverage.

- [ ] **Step 6: Commit**

```bash
git add django/main/views.py django/main/tasks.py django/main/tests/test_views.py django/main/tests/test_tasks.py
git commit -m "refactor: route heatmap flow through django github client"
```

### Task 3: Remove GitHub Login And Allauth Integration

**Files:**
- Modify: `django/config/settings.py`
- Modify: `django/config/urls.py`
- Modify: `django/main/urls.py`
- Modify: `django/main/context_processors.py`
- Modify: `django/main/templates/pages/about.html`
- Modify: `django/main/tests/test_views.py`
- Modify: `django/main/tests/test_urls.py`
- Delete: `django/main/auth_adapters.py`

- [ ] **Step 1: Write failing tests for removed routes and UI**

```python
def test_about_url_does_not_offer_github_login(self):
    response = self.client.get("/about/")
    self.assertEqual(response.status_code, 200)
    self.assertNotContains(response, "Login with GitHub")
    self.assertNotContains(response, "Live from FastAPI")


def test_about_heatmap_disconnect_route_is_removed(self):
    response = self.client.post("/about/heatmap-disconnect/")
    self.assertEqual(response.status_code, 404)


def test_accounts_login_route_is_removed(self):
    response = self.client.get("/accounts/login/")
    self.assertEqual(response.status_code, 404)


def test_accounts_3rdparty_route_is_removed(self):
    response = self.client.get("/accounts/3rdparty/")
    self.assertEqual(response.status_code, 404)
```

- [ ] **Step 2: Run the URL and view tests to verify they fail**

Run: `uv run python django/manage.py test main.tests.test_urls main.tests.test_views -v 2`
Expected: FAIL because the routes still exist, the template still contains GitHub-login strings, and `allauth` code paths still render connect/disconnect behavior.

- [ ] **Step 3: Remove allauth configuration, routes, context, and template behavior**

```python
INSTALLED_APPS = [
    "main.apps.MainConfig",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "main.middleware.VisitorCountMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
]

GITHUB_HEATMAP_TOKEN = env("GITHUB_HEATMAP_TOKEN", default="").strip()
HEATMAP_CACHE_TTL_MINUTES = env.int("HEATMAP_CACHE_TTL_MINUTES", default=60)
```

```python
urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("main.urls")),
]
```

```python
urlpatterns = [
    path("", views.home, name="home"),
    path("home/", views.home, name="home"),
    path("about/", views.about, name="about"),
    path("about/heatmap-data/", views.about_heatmap_data, name="about_heatmap_data"),
    path("projects/", views.projects, name="projects"),
    path("blog/<slug:blog_slug>/", views.blog_detail, name="blog_detail"),
    path("admin-tools/run-markdown-sync/", views.run_markdown_sync_task, name="run_markdown_sync_task"),
    path("admin-tools/run-heatmap-refresh/", views.run_heatmap_refresh_task, name="run_heatmap_refresh_task"),
]
```

```python
def auth_state(request):
    return {}
```

```html
<div class="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
    <div>
        <h2 class="text-xl font-semibold text-primary">GitHub Contributions</h2>
        <p id="heatmap-minimal-status" class="mt-1 text-sm text-base-content/70">Loading heatmap data...</p>
    </div>
    <div class="badge badge-outline badge-sm">Live from GitHub API</div>
</div>

<div id="heatmap-minimal-error" class="alert alert-error mt-4 hidden">
    <span id="heatmap-minimal-error-text"></span>
</div>

<div id="heatmap-minimal-content" class="mt-4 hidden">
```

```javascript
if (!heatmapEnabled) {
    variants.forEach(function (variant) {
        variant.statusEl.textContent = "Heatmap is not configured.";
    });
    return;
}
```

- [ ] **Step 4: Delete the obsolete social-auth adapter and remove old tests/helpers**

```python
# Delete file entirely:
# django/main/auth_adapters.py
```

```python
# Remove from test_views.py:
from allauth.socialaccount.models import SocialAccount, SocialApp, SocialToken
from django.contrib.sites.models import Site


def _create_github_token(self, user, token_value="gho_test_token"):
    ...


def test_about_disconnect_github_removes_admin_social_account(self):
    ...


def test_accounts_3rdparty_redirects_staff_to_github_connect(self):
    ...
```

- [ ] **Step 5: Run the URL and view tests again to verify they pass**

Run: `uv run python django/manage.py test main.tests.test_urls main.tests.test_views -v 2`
Expected: PASS with no remaining assertions about `/accounts/*`, social accounts, or GitHub connect/disconnect UI.

- [ ] **Step 6: Commit**

```bash
git add django/config/settings.py django/config/urls.py django/main/urls.py django/main/context_processors.py django/main/templates/pages/about.html django/main/tests/test_views.py django/main/tests/test_urls.py
git rm django/main/auth_adapters.py
git commit -m "refactor: remove github social login integration"
```

### Task 4: Update Dependencies, Docs, And Full Verification

**Files:**
- Modify: `pyproject.toml`
- Modify: `uv.lock`
- Modify: `.env.example`
- Modify: `README.md`
- Modify: `docs/architecture.md`
- Modify: `docs/implementation.md`

- [ ] **Step 1: Write failing documentation/config expectations as a checklist in the working branch**

```text
- `.env.example` must expose `GITHUB_HEATMAP_TOKEN` and no longer mention GitHub OAuth or `HEATMAP_API_BASE_URL`.
- README and docs must describe direct GitHub API fetching from Django.
- Python dependency list must no longer include `django-allauth`.
```

- [ ] **Step 2: Update dependency and environment files**

```toml
dependencies = [
    "asgiref==3.8.1",
    "bleach==6.2.0",
    "celery[redis]==5.4.0",
    "django==5.1.15",
    "django-environ==0.12.0",
    "gunicorn==23.0.0",
    "markdown==3.8.2",
    "packaging==25.0",
    "pillow==12.1.1",
    "psycopg2-binary==2.9.10",
    "pymdown-extensions==10.16.1",
    "requests==2.32.5",
    "sqlparse==0.5.4",
    "tzdata==2025.2",
]
```

```env
# Heatmap integration
GITHUB_HEATMAP_TOKEN=your_github_token_with_read_access
HEATMAP_CACHE_TTL_MINUTES=60
```

Run: `uv lock`
Expected: `uv.lock` updates to remove `django-allauth` and its transitive packages.

- [ ] **Step 3: Update the product and architecture docs**

```markdown
- GitHub contribution heatmap is fetched directly by Django from GitHub REST and GraphQL APIs.
- No external FastAPI heatmap service is required at runtime.
- GitHub login/auth integration has been removed; heatmap identity comes from `GITHUB_HEATMAP_TOKEN`.
```

```markdown
## Heatmap Integration

The project reads `GITHUB_HEATMAP_TOKEN` from `.env`, fetches the token owner via GitHub REST `/user`, then fetches the contribution calendar via GitHub GraphQL. Normalized heatmap payloads are cached in `HeatmapSnapshot` and refreshed by Celery.
```

- [ ] **Step 4: Run the full verification suite**

Run: `uv run python django/manage.py check`
Expected: PASS.

Run: `uv run python django/manage.py makemigrations --check --dry-run`
Expected: PASS with `No changes detected`.

Run: `uv run python django/manage.py test main -v 2`
Expected: PASS for the full `main` app test suite.

- [ ] **Step 5: Commit**

```bash
git add pyproject.toml uv.lock .env.example README.md docs/architecture.md docs/implementation.md
git commit -m "docs: update heatmap architecture and configuration"
```

## Self-Review

- Spec coverage check:
  - direct GitHub client: Task 1
  - heatmap orchestration and snapshot contract: Tasks 1-2
  - remove GitHub auth and UI/routes/settings: Task 3
  - docs and env updates: Task 4
- Placeholder scan: no `TODO`, `TBD`, or deferred implementation markers remain.
- Type consistency check: the plan consistently uses `get_configured_github_token()`, `fetch_heatmap_data()`, `contribution_level()`, and `build_weeks_payload()` across tasks.
