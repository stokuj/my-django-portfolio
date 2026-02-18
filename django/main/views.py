import markdown
from django.conf import settings
from django.shortcuts import get_object_or_404, render

from .models import Project, Tag


BLOG_REPO_PATHS = {
    "activity-tracker": "activity_tracker",
    "analiza-makro-konkurs": "analiza-makro-konkurs",
    "cartoon-filter": "cartoon-filter",
    "currency-price-prediction": "CryptoCurrencyPP",
    "github-heatmap": "github-heatmap",
    "granular-data-grouping": "granular_data_grouping",
    "multidimensional-dashboard": "multidimensional-dashboard",
    "my-django-portfolio": "my_django_portfolio",
    "NTwI-obliczenia-ziarniste": "NTwI-obliczenia-ziarniste",
    "weather-web-scraping": "WeatherWebScraping",
    "web-scraping-lubimyczytac": "web_scraping_lubimyczytac",
}


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
    """Load markdown content stored directly in the database."""
    return project.markdown_content or None


def _render_markdown_to_html(markdown_content):
    """Render markdown content to HTML for trusted local blog files."""
    if not markdown_content:
        return None
    markdown_content = markdown_content.lstrip("\ufeff")
    return markdown.markdown(
        markdown_content,
        extensions=["fenced_code", "tables"],
    )


def _build_readme_url(project, repo_path):
    """Build a branch-agnostic README URL for a project repository."""
    if project.github_url:
        return f"{project.github_url.rstrip('/')}#readme"

    github_base = settings.PORTFOLIO_PROFILE.get(
        "github_base",
        "https://github.com/your-username",
    ).rstrip("/")
    return f"{github_base}/{repo_path}#readme"


def blog_detail(request, blog_slug):
    project = get_object_or_404(Project, blog=True, blog_url=blog_slug)
    markdown_content = _load_project_markdown(project)
    markdown_html = _render_markdown_to_html(markdown_content)
    repo_path = BLOG_REPO_PATHS.get(project.blog_url, project.blog_url)
    readme_url = _build_readme_url(project, repo_path)
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
