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
        raise ValidationError(
            "GitHub repository URL must not include query parameters or fragments."
        )

    path_parts = [part for part in parsed.path.split("/") if part]
    if len(path_parts) != 2:
        raise ValidationError(
            "GitHub repository URL must point to repository root: https://github.com/<owner>/<repo>."
        )


def validate_utf8_file(value):
    """Reject a newly uploaded file that is not UTF-8 text."""
    if getattr(value, "_committed", True):
        return  # Already stored: checked on upload or written by the markdown sync.
    data = value.read()
    value.seek(0)
    try:
        data.decode("utf-8")
    except UnicodeDecodeError:
        raise ValidationError("File must be UTF-8 encoded text.") from None


def validate_str_list(value):
    """Require a JSON list of strings."""
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise ValidationError('Enter a JSON list of strings, e.g. ["Python", "Django"].')
