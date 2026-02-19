import logging
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from django.core.files.base import ContentFile

from .models import PortfolioProfile

logger = logging.getLogger(__name__)
MAX_MARKDOWN_SIZE_BYTES = 10 * 1024 * 1024

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


def get_repo_path(project):
    return BLOG_REPO_PATHS.get(project.blog_url, project.blog_url)


def _active_github_username():
    profile = PortfolioProfile.objects.filter(is_active=True).first() or PortfolioProfile()
    github_url = (profile.github_url or "").rstrip("/")
    if not github_url:
        return None

    path_parts = [part for part in urlparse(github_url).path.split("/") if part]
    if not path_parts:
        return None
    return path_parts[-1]


def _parse_github_owner_repo(github_url):
    if not github_url:
        return None, None

    parsed = urlparse(github_url.strip())
    if parsed.netloc not in {"github.com", "www.github.com"}:
        return None, None

    parts = [part for part in parsed.path.split("/") if part]
    if len(parts) < 2:
        return None, None
    return parts[0], parts[1]


def build_readme_url(project):
    repo_path = get_repo_path(project)
    if project.github_url:
        return f"{project.github_url.rstrip('/')}#readme"

    profile = PortfolioProfile.objects.filter(is_active=True).first() or PortfolioProfile()
    github_base = (profile.github_url or "https://github.com/your-username").rstrip("/")
    return f"{github_base}/{repo_path}#readme"


def build_markdown_candidate_urls(project):
    candidates = []

    owner, repo = _parse_github_owner_repo(project.github_url)
    if owner and repo:
        candidates.extend(
            [
                f"https://raw.githubusercontent.com/{owner}/{repo}/main/README.md",
                f"https://raw.githubusercontent.com/{owner}/{repo}/master/README.md",
            ]
        )

    repo_path = get_repo_path(project)
    active_username = _active_github_username()
    if active_username and repo_path:
        candidates.extend(
            [
                f"https://raw.githubusercontent.com/{active_username}/{repo_path}/main/README.md",
                f"https://raw.githubusercontent.com/{active_username}/{repo_path}/master/README.md",
            ]
        )

    deduped = []
    seen = set()
    for url in candidates:
        if url not in seen:
            deduped.append(url)
            seen.add(url)
    return deduped


def _download_markdown(url, timeout=20, opener=urlopen):
    request = Request(url, headers={"User-Agent": "my-django-portfolio-markdown-sync/1.0"})
    with opener(request, timeout=timeout) as response:
        status = getattr(response, "status", 200)
        if status != 200:
            raise HTTPError(url, status, "Non-200 response", None, None)
        content_length = None
        if hasattr(response, "getheader"):
            content_length = response.getheader("Content-Length")
        elif getattr(response, "headers", None) is not None:
            content_length = response.headers.get("Content-Length")

        if content_length is not None:
            try:
                parsed_length = int(content_length)
            except (TypeError, ValueError):
                parsed_length = None

            if parsed_length is not None and parsed_length > MAX_MARKDOWN_SIZE_BYTES:
                raise ValueError(f"Downloaded markdown exceeds size limit ({MAX_MARKDOWN_SIZE_BYTES} bytes)")

        chunks = []
        total_size = 0
        while True:
            chunk = response.read(64 * 1024)
            if not chunk:
                break
            total_size += len(chunk)
            if total_size > MAX_MARKDOWN_SIZE_BYTES:
                raise ValueError(f"Downloaded markdown exceeds size limit ({MAX_MARKDOWN_SIZE_BYTES} bytes)")
            chunks.append(chunk)
        raw_bytes = b"".join(chunks)

    text = raw_bytes.decode("utf-8-sig")
    if text.lstrip().lower().startswith("<!doctype html") or text.lstrip().lower().startswith("<html"):
        raise ValueError("Downloaded content is HTML, expected Markdown")
    return text


def sync_project_markdown(project, timeout=20, opener=urlopen):
    candidate_urls = build_markdown_candidate_urls(project)
    if not candidate_urls:
        return {
            "project_id": project.id,
            "slug": project.blog_url,
            "updated": False,
            "reason": "no_candidate_urls",
        }

    markdown_text = None
    source_url = None
    last_error = None

    for url in candidate_urls:
        try:
            markdown_text = _download_markdown(url, timeout=timeout, opener=opener)
            source_url = url
            break
        except (HTTPError, URLError, UnicodeDecodeError, ValueError, OSError) as exc:
            last_error = str(exc)
            logger.warning("Markdown sync failed for %s from %s: %s", project.blog_url, url, exc)

    if markdown_text is None:
        return {
            "project_id": project.id,
            "slug": project.blog_url,
            "updated": False,
            "reason": "download_failed",
            "error": last_error,
        }

    old_name = project.markdown_file.name if project.markdown_file else ""
    target_basename = Path(old_name).name if old_name else f"{project.blog_url or f'project-{project.id}'}.md"

    storage = project.markdown_file.storage
    project.markdown_file.save(target_basename, ContentFile(markdown_text.encode("utf-8")), save=False)
    project.save(update_fields=["markdown_file"])
    new_name = project.markdown_file.name

    if old_name and old_name != new_name and storage.exists(old_name):
        storage.delete(old_name)

    return {
        "project_id": project.id,
        "slug": project.blog_url,
        "updated": True,
        "source_url": source_url,
        "file": new_name,
    }
