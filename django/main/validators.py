from urllib.parse import urlparse

from django.core.exceptions import ValidationError


def validate_github_repo_url(value):
    """Validate URL points to a GitHub repository root."""
    if not value:
        return

    parsed = urlparse(value.strip())

    if parsed.scheme != "https":
        raise ValidationError("GitHub repository URL must use HTTPS.")

    if parsed.netloc not in {"github.com", "www.github.com"}:
        raise ValidationError("GitHub repository URL must use github.com domain.")

    if parsed.params or parsed.query or parsed.fragment:
        raise ValidationError("GitHub repository URL must not include query parameters or fragments.")

    path_parts = [part for part in parsed.path.split("/") if part]
    if len(path_parts) != 2:
        raise ValidationError(
            "GitHub repository URL must point to repository root: https://github.com/<owner>/<repo>."
        )
