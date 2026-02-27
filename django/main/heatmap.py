import datetime

from django.conf import settings
from django.utils import timezone

import requests
from allauth.socialaccount.models import SocialAccount, SocialToken

from .models import HeatmapSnapshot


def get_portfolio_github_account():
    """Return the GitHub social account used for portfolio heatmap sync.

    Prefers the account matching `GITHUB_ALLOWED_LOGIN`; otherwise falls back
    to the first superuser-linked GitHub account.
    """
    github_accounts = SocialAccount.objects.select_related("user").filter(
        provider="github"
    )

    allowed_login = (
        (getattr(settings, "GITHUB_ALLOWED_LOGIN", "") or "").strip().lower()
    )

    if allowed_login:
        for account in github_accounts:
            account_login = (account.extra_data.get("login") or "").strip().lower()
            if account_login == allowed_login:
                return account

    return github_accounts.filter(user__is_superuser=True).order_by("id").first()


def get_portfolio_github_token():
    """Return OAuth token for the selected portfolio GitHub account.

    Returns:
        str | None: Non-empty token string if available, otherwise None.
    """
    selected_account = get_portfolio_github_account()
    if not selected_account:
        return None

    social_token = (
        SocialToken.objects.filter(account=selected_account)
        .exclude(token="")
        .order_by("id")
        .first()
    )
    if not social_token:
        return None
    return social_token.token


def fetch_heatmap_data(github_token):
    """Fetch heatmap payload from external service for authenticated user.

    Args:
        github_token (str): GitHub OAuth bearer token.

    Returns:
        tuple[dict | None, str | None]: `(payload, error_message)` pair.
    """
    heatmap_url = f"{settings.HEATMAP_API_BASE_URL.rstrip('/')}/heatmap/me"

    try:
        response = requests.get(
            heatmap_url,
            headers={"Authorization": f"Bearer {github_token}"},
            timeout=10,
        )
    except requests.Timeout:
        return None, "Heatmap service is temporarily unavailable."
    except requests.RequestException:
        return None, "Heatmap service is temporarily unavailable."

    if response.status_code == 401:
        return None, "GitHub session expired. Please sign in again."

    if response.status_code >= 400:
        return None, "Heatmap service is temporarily unavailable."

    try:
        payload = response.json()
    except ValueError:
        return None, "Heatmap service is temporarily unavailable."

    if not isinstance(payload, dict):
        return None, "Heatmap service is temporarily unavailable."

    return payload, None


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
