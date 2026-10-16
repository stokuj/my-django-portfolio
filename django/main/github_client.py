from collections.abc import Mapping
from datetime import date, timedelta

import requests


class GitHubAuthError(Exception):
    """Raised when GitHub rejects the provided token."""


class GitHubUpstreamError(Exception):
    """Raised when GitHub requests fail for non-auth reasons."""


_AUTH_ERROR_SUBSTRINGS = (
    "resource not accessible",
    "forbidden",
    "unauthorized",
    "bad credentials",
)


def _graphql_errors_indicate_auth_failure(errors):
    for error in errors:
        if not isinstance(error, Mapping):
            continue

        raw_type = error.get("type")
        error_type = raw_type.lower() if isinstance(raw_type, str) else ""
        raw_message = error.get("message")
        message = raw_message.lower() if isinstance(raw_message, str) else ""

        if error_type in {"forbidden", "unauthorized"}:
            return True
        if any(text in message for text in _AUTH_ERROR_SUBSTRINGS):
            return True

    return False


def _default_headers(token):
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "User-Agent": "my-django-portfolio",
    }


def _raise_if_rate_limited(response):
    # GitHub answers rate limits with 403 too; do not report them as a bad token.
    if response.status_code == 403 and (
        response.headers.get("X-RateLimit-Remaining") == "0" or "Retry-After" in response.headers
    ):
        raise GitHubUpstreamError("GitHub rate limit exceeded")


def fetch_contribution_days(token):
    """Fetch the token owner's login and one-year contribution days via GraphQL.

    Returns:
        tuple[str, list[dict]]: `(login, days)`, each day as `{"date", "count"}`.
    """
    to_day = date.today()
    from_day = to_day - timedelta(days=364)

    query = """
    query($from: DateTime!, $to: DateTime!) {
      viewer {
        login
        contributionsCollection(from: $from, to: $to) {
          contributionCalendar {
            weeks {
              contributionDays {
                date
                contributionCount
              }
            }
          }
        }
      }
    }
    """

    try:
        response = requests.post(
            "https://api.github.com/graphql",
            json={
                "query": query,
                "variables": {
                    "from": f"{from_day.isoformat()}T00:00:00Z",
                    "to": f"{to_day.isoformat()}T23:59:59Z",
                },
            },
            headers={
                **_default_headers(token),
                "Content-Type": "application/json",
            },
            timeout=20,
        )
    except (requests.Timeout, requests.RequestException) as exc:
        raise GitHubUpstreamError from exc

    _raise_if_rate_limited(response)
    if response.status_code in {401, 403}:
        raise GitHubAuthError
    if response.status_code >= 400:
        raise GitHubUpstreamError

    try:
        payload = response.json()
    except ValueError as exc:
        raise GitHubUpstreamError("GitHub GraphQL response is invalid") from exc
    if not isinstance(payload, Mapping):
        raise GitHubUpstreamError("GitHub GraphQL response is invalid")
    raw_errors = payload.get("errors")
    if isinstance(raw_errors, list) and raw_errors:
        if _graphql_errors_indicate_auth_failure(raw_errors):
            raise GitHubAuthError
        raise GitHubUpstreamError("GitHub GraphQL returned errors")

    try:
        viewer = payload["data"]["viewer"]
        weeks = viewer["contributionsCollection"]["contributionCalendar"]["weeks"]
        days = [
            {"date": day["date"], "count": day["contributionCount"]}
            for week in weeks
            for day in week["contributionDays"]
        ]
        return viewer["login"], days
    except (KeyError, TypeError) as exc:
        raise GitHubUpstreamError("GitHub GraphQL response is malformed") from exc
