from django.conf import settings
from django.utils import timezone

from .github_client import (
    GitHubAuthError,
    GitHubUpstreamError,
    fetch_contribution_weeks,
)
from .models import HeatmapSnapshot


def get_configured_github_token():
    """Return configured GitHub token for direct heatmap API requests."""
    return settings.GITHUB_HEATMAP_TOKEN or None


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


def fetch_heatmap_data():
    """Fetch normalized heatmap payload directly from GitHub APIs.

    Returns:
        tuple[dict | None, str | None]: `(payload, error_message)` pair.
    """
    token = get_configured_github_token()
    if not token:
        return None, "Heatmap is not configured."

    try:
        username, raw_weeks = fetch_contribution_weeks(token)
    except GitHubAuthError:
        return None, "Configured GitHub token is invalid or expired."
    except GitHubUpstreamError:
        return None, "Heatmap service is temporarily unavailable."

    weeks = [
        {"days": [{**day, "level": contribution_level(day["count"])} for day in week]}
        for week in raw_weeks
    ]
    return {
        "username": username,
        "total": sum(day["count"] for week in raw_weeks for day in week),
        "weeks": weeks,
    }, None


def get_snapshot():
    """Return the single heatmap snapshot row, or None before the first refresh."""
    return HeatmapSnapshot.objects.first()


def update_snapshot_with_payload(payload):
    """Persist successful heatmap payload into the snapshot.

    Args:
        payload (dict): Normalized payload from `fetch_heatmap_data`.

    Returns:
        HeatmapSnapshot: Updated snapshot instance.
    """
    snapshot = get_snapshot() or HeatmapSnapshot()
    snapshot.payload = payload
    snapshot.fetched_at = timezone.now()
    snapshot.last_error = ""
    snapshot.save()
    return snapshot


def update_snapshot_error(error_message):
    """Persist latest heatmap sync error message on snapshot.

    Args:
        error_message (str): Human-readable error details.

    Returns:
        HeatmapSnapshot: Updated snapshot instance.
    """
    snapshot = get_snapshot() or HeatmapSnapshot()
    snapshot.last_error = error_message
    snapshot.save()
    return snapshot
