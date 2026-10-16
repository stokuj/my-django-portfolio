import logging
from pathlib import Path
from urllib.parse import urlparse

import requests
from django.core.files.base import ContentFile

logger = logging.getLogger(__name__)
MAX_MARKDOWN_SIZE_BYTES = 10 * 1024 * 1024


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
    if project.github_url:
        return f"{project.github_url.rstrip('/')}#readme"
    return None


def build_markdown_candidate_urls(project):
    owner, repo = _parse_github_owner_repo(project.github_url)
    if not (owner and repo):
        return []
    return [
        f"https://raw.githubusercontent.com/{owner}/{repo}/main/README.md",
        f"https://raw.githubusercontent.com/{owner}/{repo}/master/README.md",
    ]


def _download_markdown(url):
    response = requests.get(
        url,
        headers={"User-Agent": "my-django-portfolio-markdown-sync/1.0"},
        timeout=20,
    )
    response.raise_for_status()

    raw_bytes = response.content
    if len(raw_bytes) > MAX_MARKDOWN_SIZE_BYTES:
        raise ValueError(
            f"Downloaded markdown exceeds size limit ({MAX_MARKDOWN_SIZE_BYTES} bytes)"
        )

    text = raw_bytes.decode("utf-8-sig")
    if text.lstrip().lower().startswith(("<!doctype html", "<html")):
        raise ValueError("Downloaded content is HTML, expected Markdown")
    return text


def sync_project_markdown(project):
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
            markdown_text = _download_markdown(url)
            source_url = url
            break
        # requests.RequestException is an OSError; UnicodeDecodeError is a ValueError.
        except (OSError, ValueError) as exc:
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

    data = markdown_text.encode("utf-8")
    old_name = project.markdown_file.name if project.markdown_file else ""
    storage = project.markdown_file.storage

    if old_name and storage.exists(old_name):
        # Overwrite in place: FileField.save would add a random suffix to the name.
        with storage.open(old_name, "rb") as fh:
            unchanged = fh.read() == data
        if not unchanged:
            with storage.open(old_name, "wb") as fh:
                fh.write(data)
    else:
        target_basename = (
            Path(old_name).name if old_name else f"{project.blog_url or f'project-{project.id}'}.md"
        )
        project.markdown_file.save(target_basename, ContentFile(data), save=False)
        project.save(update_fields=["markdown_file"])
    new_name = project.markdown_file.name

    return {
        "project_id": project.id,
        "slug": project.blog_url,
        "updated": True,
        "source_url": source_url,
        "file": new_name,
    }
