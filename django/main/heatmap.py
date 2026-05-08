import datetime

from django.conf import settings
from django.utils import timezone

from .github_client import GitHubAuthError
from .github_client import GitHubUpstreamError
from .github_client import fetch_authenticated_user
from .github_client import fetch_contribution_days
from .models import HeatmapSnapshot


def get_configured_github_token():
    """Return configured GitHub token for direct heatmap API requests."""
    github_token = (getattr(settings, "GITHUB_HEATMAP_TOKEN", "") or "").strip()
    return github_token or None


def contribution_level(count):
    """Map daily contribution count to a heatmap level in range 0..4."""
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
    """Group contribution days into week buckets and compute total count."""
    grouped_weeks = {}
    total = 0

    for item in contribution_days:
        raw_day = item.get("date")
        raw_count = item.get("count")
        if not isinstance(raw_day, str) or not isinstance(raw_count, int):
            continue

        try:
            parsed_day = datetime.date.fromisoformat(raw_day)
        except ValueError:
            continue

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
        days = sorted(grouped_weeks[week_start], key=lambda day: day["weekday"])
        weeks.append({"week_start": week_start.isoformat(), "days": days})

    return weeks, total


def fetch_heatmap_data(github_token=None):
    """Fetch normalized heatmap payload directly from GitHub APIs.

    Args:
        github_token (str | None): Optional GitHub bearer token override.

    Returns:
        tuple[dict | None, str | None]: `(payload, error_message)` pair.
    """
    token = github_token or get_configured_github_token()
    if not token:
        return None, "Heatmap is not configured."

    try:
        github_user = fetch_authenticated_user(token)
        raw_username = github_user.get("login")
        if not isinstance(raw_username, str) or not raw_username:
            raise GitHubUpstreamError("GitHub user response is invalid")
        username = raw_username

        contribution_days = fetch_contribution_days(username, token)
        weeks, total = build_weeks_payload(contribution_days)
    except GitHubAuthError:
        return None, "Configured GitHub token is invalid or expired."
    except GitHubUpstreamError:
        return None, "Heatmap service is temporarily unavailable."

    return {
        "username": username,
        "total": total,
        "weeks": weeks,
    }, None


def get_or_create_snapshot():
    """Return persistent portfolio heatmap snapshot row.

    Creates the row on first use with fixed key `portfolio`.
    """
    snapshot, _ = HeatmapSnapshot.objects.get_or_create(key="portfolio")
    return snapshot


def is_snapshot_stale(snapshot, ttl_minutes=None):
    """Check whether cached snapshot is stale against configured TTL.

    Args:
        snapshot (HeatmapSnapshot): Snapshot model instance.
        ttl_minutes (int | None): Optional TTL override in minutes.

    Returns:
        bool: True when snapshot should be refreshed.
    """
    ttl = ttl_minutes or int(getattr(settings, "HEATMAP_CACHE_TTL_MINUTES", 60))
    if not snapshot.fetched_at:
        return True

    threshold = timezone.now() - datetime.timedelta(minutes=ttl)
    return snapshot.fetched_at <= threshold


def update_snapshot_with_payload(payload):
    """Persist successful heatmap payload into snapshot fields.

    Args:
        payload (dict): Parsed response from heatmap service.

    Returns:
        HeatmapSnapshot: Updated snapshot instance.
    """
    weeks = payload.get("weeks") or []
    snapshot = get_or_create_snapshot()
    snapshot.payload = payload
    snapshot.username = payload.get("username") or ""
    snapshot.total = int(payload.get("total") or 0)
    snapshot.weeks_count = len(weeks)
    snapshot.fetched_at = timezone.now()
    snapshot.last_error = ""
    snapshot.save(
        update_fields=[
            "payload",
            "username",
            "total",
            "weeks_count",
            "fetched_at",
            "last_error",
        ]
    )
    return snapshot


def update_snapshot_error(error_message):
    """Persist latest heatmap sync error message on snapshot.

    Args:
        error_message (str): Human-readable error details.

    Returns:
        HeatmapSnapshot: Updated snapshot instance.
    """
    snapshot = get_or_create_snapshot()
    snapshot.last_error = error_message
    snapshot.save(update_fields=["last_error"])
    return snapshot
