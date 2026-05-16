import bleach
import markdown
import shutil
from datetime import date, timedelta
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_GET, require_POST

from .heatmap import (
    fetch_heatmap_data,
    get_configured_github_token,
    get_or_create_snapshot,
    is_snapshot_stale,
    update_snapshot_error,
    update_snapshot_with_payload,
)
from .markdown_sync import build_readme_url, get_repo_path
from .models import Project, Tag, TaskExecutionLog, TaskExecutionStatus
from .tasks import (
    DISK_CRITICAL_GB,
    DISK_WARNING_GB,
    REFRESH_HEATMAP_TASK_NAME,
    SYNC_MARKDOWNS_TASK_NAME,
    refresh_portfolio_heatmap_cache_task,
    sync_project_markdowns_task,
)

ALLOWED_MARKDOWN_TAGS = [
    "a",
    "blockquote",
    "br",
    "code",
    "div",
    "em",
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
    "hr",
    "img",
    "li",
    "ol",
    "p",
    "pre",
    "strong",
    "table",
    "tbody",
    "td",
    "th",
    "thead",
    "tr",
    "ul",
    "span",
]
ALLOWED_MARKDOWN_ATTRIBUTES = {
    "a": ["href", "title"],
    "div": ["class"],
    "img": ["src", "alt", "title"],
    "span": ["class"],
}
ALLOWED_MARKDOWN_PROTOCOLS = ["http", "https", "mailto"]

_GITHUB_IMG_PREFIXES = (
    "https://github.com/",
    "https://raw.githubusercontent.com/",
    "https://camo.githubusercontent.com/",
)


def _clean_attributes(tag, name, value):
    # First check if the attribute is in the allowlist for this tag
    allowed_attrs = ALLOWED_MARKDOWN_ATTRIBUTES.get(tag, [])
    if name not in allowed_attrs:
        return False

    # Special handling for img src: only allow GitHub domains
    if tag == "img" and name == "src":
        return any(value.startswith(p) for p in _GITHUB_IMG_PREFIXES)

    return True


def handler404(request, exception):
    """Render custom 404 error page."""
    return render(request, "errors/404.html", status=404)


def handler500(request):
    """Render custom 500 error page."""
    return render(request, "errors/500.html", status=500)


def home(request):
    """Render home page with projects grouped by status timeline."""
    projects = Project.objects.prefetch_related("tags").order_by("-date")
    status_labels = {
        "planned": "Planned",
        "ongoing": "Ongoing",
        "finished": "Finished",
    }
    status_order = ["planned", "ongoing", "finished"]

    projects_by_status = {status: [] for status in status_order}
    for project in projects:
        if project.status in projects_by_status:
            projects_by_status[project.status].append(project)

    timeline_sections = [
        {
            "status": status,
            "title": status_labels[status],
            "checked": status == "finished",
            "projects": projects_by_status[status],
        }
        for status in status_order
    ]

    return render(request, "pages/home.html", {"timeline_sections": timeline_sections})


def about(request):
    """Render about page with heatmap flags and admin task panels."""
    has_portfolio_token = get_configured_github_token() is not None
    is_admin_user = request.user.is_authenticated and request.user.is_staff

    context = {
        "heatmap_component_visible": True,
        "heatmap_enabled": has_portfolio_token,
    }

    if is_admin_user:
        context["scheduled_jobs"] = _get_scheduled_jobs_overview()
        context["executed_tasks"] = _get_executed_tasks()
        context["disk_info"] = _get_disk_info()

    return render(request, "pages/about.html", context)


@require_GET
def about_heatmap_data(request):
    """Return cached heatmap payload JSON, refreshing when cache is stale."""
    if not get_configured_github_token():
        return JsonResponse(
            {"error": "Heatmap is not configured."},
            status=404,
        )

    snapshot = get_or_create_snapshot()

    if not snapshot.payload or is_snapshot_stale(snapshot):
        payload, error = fetch_heatmap_data()

        if error:
            update_snapshot_error(error)
            if snapshot.payload:
                return _build_heatmap_snapshot_response(snapshot)
            return JsonResponse({"error": error}, status=503)

        snapshot = update_snapshot_with_payload(payload)

    return _build_heatmap_snapshot_response(snapshot)


def _build_heatmap_snapshot_response(snapshot):
    """Serialize snapshot model into heatmap API response payload."""
    last_30_days_total = _calculate_last_30_days_total(snapshot.payload)

    return JsonResponse(
        {
            "username": snapshot.username,
            "total": snapshot.total,
            "last_30_days_total": last_30_days_total,
            "weeks_count": snapshot.weeks_count,
            "raw": snapshot.payload,
            "fetched_at": snapshot.fetched_at.isoformat()
            if snapshot.fetched_at
            else None,
        }
    )


def _schedule_next_heatmap_refresh():
    """Best-effort enqueue of next asynchronous heatmap refresh task."""
    try:
        refresh_portfolio_heatmap_cache_task.apply_async(
            kwargs={"schedule_next": False},
            countdown=3600,
        )
    except Exception:
        return


def _calculate_last_30_days_total(payload):
    """Sum contribution counts from payload days within last 30 days."""
    weeks = payload.get("weeks") if isinstance(payload, dict) else None
    if not isinstance(weeks, list):
        return 0

    today = date.today()
    start_date = today - timedelta(days=29)
    total = 0

    for week in weeks:
        days = week.get("days") if isinstance(week, dict) else None
        if not isinstance(days, list):
            continue

        for day in days:
            if not isinstance(day, dict):
                continue

            day_date = day.get("date")
            if not day_date:
                continue

            try:
                parsed_date = date.fromisoformat(str(day_date).split("T", 1)[0])
            except ValueError:
                continue

            if not (start_date <= parsed_date <= today):
                continue

            count = day.get("count", day.get("contribution_count", 0))
            try:
                total += int(count or 0)
            except (TypeError, ValueError):
                continue

    return total


def _get_disk_info():
    usage = shutil.disk_usage("/")
    free_raw_gb = usage.free / (1024 ** 3)
    free_gb = round(free_raw_gb, 1)
    used_gb = round(usage.used / (1024 ** 3), 1)
    total_gb = round(usage.total / (1024 ** 3), 1)
    free_pct = round((usage.free / usage.total) * 100, 1)

    if free_raw_gb < DISK_CRITICAL_GB:
        level = "critical"
    elif free_raw_gb < DISK_WARNING_GB:
        level = "warning"
    else:
        level = "ok"

    return {
        "free_gb": free_gb,
        "used_gb": used_gb,
        "total_gb": total_gb,
        "free_pct": free_pct,
        "level": level,
    }


def _get_scheduled_jobs_overview():
    """Build admin-facing summary for periodic markdown/heatmap tasks."""
    task_statuses = {
        item.task_name: item
        for item in TaskExecutionStatus.objects.filter(
            task_name__in=[REFRESH_HEATMAP_TASK_NAME, SYNC_MARKDOWNS_TASK_NAME]
        )
    }

    jobs_config = [
        {
            "task_name": REFRESH_HEATMAP_TASK_NAME,
            "label": "Heatmap Refresh",
            "schedule_label": "Every 60 minutes",
            "interval_minutes": 60,
        },
        {
            "task_name": SYNC_MARKDOWNS_TASK_NAME,
            "label": "Markdown Sync (.md)",
            "schedule_label": "Every 2 hours",
            "interval_minutes": 120,
        },
    ]

    jobs = []
    for item in jobs_config:
        status = task_statuses.get(item["task_name"])
        last_run_at = status.last_run_at if status else None
        next_run_at = (
            last_run_at + timedelta(minutes=item["interval_minutes"])
            if last_run_at
            else timezone.now() + timedelta(minutes=item["interval_minutes"])
        )

        jobs.append(
            {
                "label": item["label"],
                "task_name": item["task_name"],
                "schedule_label": item["schedule_label"],
                "status": status.last_status
                if status and status.last_status
                else "never",
                "last_run_at": last_run_at,
                "next_run_at": next_run_at,
                "last_error": status.last_error if status else "",
                "last_total": status.last_total if status else 0,
                "last_updated": status.last_updated if status else 0,
                "last_failed": status.last_failed if status else 0,
            }
        )

    return jobs


def _get_executed_tasks():
    """Return latest task execution log entries for admin panel."""
    return TaskExecutionLog.objects.order_by("-last_run_at", "-id")[:30]


def projects(request):
    """Render projects listing page with tag filters metadata."""
    projects = Project.objects.order_by("-date", "-id").prefetch_related("tags")

    # Pobieramy wszystkie unikalne tagi
    all_tags = Tag.objects.all().order_by("name")

    return render(
        request,
        "projects/index.html",
        {
            "projects": projects,
            "all_tags": all_tags,
        },
    )


def _load_project_markdown(project):
    """Load markdown content from uploaded markdown file."""
    if not project.markdown_file:
        return None

    try:
        project.markdown_file.open("rb")
        return project.markdown_file.read().decode("utf-8")
    except (OSError, UnicodeDecodeError):
        return None
    finally:
        try:
            project.markdown_file.close()
        except OSError:
            pass


def _render_markdown_to_html(markdown_content):
    """Render markdown to safe HTML using an explicit allowlist."""
    if not markdown_content:
        return None
    markdown_content = markdown_content.lstrip("\ufeff")
    markdown_html = markdown.markdown(
        markdown_content,
        extensions=["fenced_code", "tables", "pymdownx.arithmatex"],
        extension_configs={
            "pymdownx.arithmatex": {
                "generic": True,
            }
        },
    )
    return bleach.clean(
        markdown_html,
        tags=ALLOWED_MARKDOWN_TAGS,
        attributes=_clean_attributes,
        protocols=ALLOWED_MARKDOWN_PROTOCOLS,
        strip=True,
    )


def _get_safe_redirect_url(request):
    """Resolve safe local redirect target from POST `next` or referrer."""
    allowed_hosts = {request.get_host()}
    candidates = [
        request.POST.get("next"),
        request.META.get("HTTP_REFERER"),
    ]

    for candidate in candidates:
        if candidate and url_has_allowed_host_and_scheme(
            url=candidate,
            allowed_hosts=allowed_hosts,
            require_https=request.is_secure(),
        ):
            return candidate

    return reverse("home")


def blog_detail(request, blog_slug):
    """Render single blog project with markdown content and navigation."""
    project = get_object_or_404(Project, blog=True, blog_url=blog_slug)
    markdown_content = _load_project_markdown(project)
    markdown_html = _render_markdown_to_html(markdown_content)
    repo_path = get_repo_path(project)
    readme_url = build_readme_url(project)
    all_projects = Project.objects.order_by("-date")

    return render(
        request,
        "projects/detail.html",
        {
            "project": project,
            "all_projects": all_projects,
            "blog_markdown_content": markdown_content,
            "blog_markdown_html": markdown_html,
            "repo_path": repo_path,
            "readme_url": readme_url,
        },
    )


@staff_member_required
@require_POST
def run_markdown_sync_task(request):
    """Enqueue markdown sync Celery task for one slug or all projects."""
    blog_slug = (request.POST.get("blog_slug") or "").strip() or None

    try:
        async_result = sync_project_markdowns_task.delay(blog_slug=blog_slug)
    except Exception:
        messages.error(request, "Failed to enqueue markdown sync task.")
    else:
        if blog_slug:
            messages.success(
                request,
                f"Markdown sync task queued for slug '{blog_slug}' (task id: {async_result.id}).",
            )
        else:
            messages.success(
                request,
                f"Markdown sync task queued for all blog projects (task id: {async_result.id}).",
            )

    return redirect(_get_safe_redirect_url(request))


@staff_member_required
@require_POST
def run_heatmap_refresh_task(request):
    """Enqueue immediate heatmap refresh task from admin tools."""
    try:
        async_result = refresh_portfolio_heatmap_cache_task.delay(schedule_next=False)
    except Exception:
        messages.error(request, "Failed to enqueue heatmap refresh task.")
    else:
        messages.success(
            request,
            f"Heatmap refresh task queued (task id: {async_result.id}).",
        )

    return redirect(_get_safe_redirect_url(request))
