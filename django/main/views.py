import bleach
import markdown
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from .markdown_sync import build_readme_url, get_repo_path
from .models import Project, Tag
from .tasks import sync_project_markdowns_task

ALLOWED_MARKDOWN_TAGS = [
    "a",
    "blockquote",
    "br",
    "code",
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
]
ALLOWED_MARKDOWN_ATTRIBUTES = {
    "a": ["href", "title"],
    "img": ["src", "alt", "title"],
}
ALLOWED_MARKDOWN_PROTOCOLS = ["http", "https", "mailto"]


def handler404(request, exception):
    return render(request, 'main/errors/404.html', status=404)


def handler500(request):
    return render(request, 'main/errors/500.html', status=500)


def home(request):
    projects = Project.objects.prefetch_related('tags').order_by('-date')
    status_labels = {
        'planned': 'Planned',
        'ongoing': 'Ongoing',
        'finished': 'Finished',
    }
    status_order = ['planned', 'ongoing', 'finished']

    projects_by_status = {status: [] for status in status_order}
    for project in projects:
        if project.status in projects_by_status:
            projects_by_status[project.status].append(project)

    timeline_sections = [
        {
            'status': status,
            'title': status_labels[status],
            'checked': status == 'finished',
            'projects': projects_by_status[status],
        }
        for status in status_order
    ]

    return render(request, "main/home.html", {'timeline_sections': timeline_sections})


def about(request):
    return render(request, "main/about.html", {})


def projects(request):
    projects = Project.objects.all().prefetch_related('tags')  # Faster tag loading

    # Pobieramy wszystkie unikalne tagi
    all_tags = Tag.objects.all().order_by('name')

    return render(request, 'main/projects.html', {
        'projects': projects,
        'all_tags': all_tags,
    })


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
        extensions=["fenced_code", "tables"],
    )
    return bleach.clean(
        markdown_html,
        tags=ALLOWED_MARKDOWN_TAGS,
        attributes=ALLOWED_MARKDOWN_ATTRIBUTES,
        protocols=ALLOWED_MARKDOWN_PROTOCOLS,
        strip=True,
    )


def _get_safe_redirect_url(request):
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
    project = get_object_or_404(Project, blog=True, blog_url=blog_slug)
    markdown_content = _load_project_markdown(project)
    markdown_html = _render_markdown_to_html(markdown_content)
    repo_path = get_repo_path(project)
    readme_url = build_readme_url(project)
    all_projects = Project.objects.order_by("-date")

    return render(
        request,
        "main/blog/detail.html",
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
