from collections.abc import Mapping
from datetime import date
from datetime import timedelta

import requests


class GitHubAuthError(Exception):
    """Raised when GitHub rejects the provided token."""


class GitHubUpstreamError(Exception):
    """Raised when GitHub requests fail for non-auth reasons."""


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

        if "resource not accessible" in message:
            return True
        if "forbidden" in message:
            return True
        if "unauthorized" in message:
            return True
        if "bad credentials" in message:
            return True

    return False


def _default_headers(token):
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "User-Agent": "my-django-portfolio",
    }


def fetch_authenticated_user(token):
    """Fetch basic profile data for the token owner from GitHub REST API."""
    try:
        response = requests.get(
            "https://api.github.com/user",
            headers=_default_headers(token),
            timeout=15,
        )
    except (requests.Timeout, requests.RequestException) as exc:
        raise GitHubUpstreamError from exc

    if response.status_code in {401, 403}:
        raise GitHubAuthError
    if response.status_code >= 400:
        raise GitHubUpstreamError

    try:
        payload = response.json()
    except ValueError as exc:
        raise GitHubUpstreamError("GitHub user response is invalid") from exc
    if not isinstance(payload, Mapping):
        raise GitHubUpstreamError("GitHub user response is invalid")

    raw_id = payload.get("id")
    raw_login = payload.get("login")
    if not isinstance(raw_id, int) or not isinstance(raw_login, str) or not raw_login:
        raise GitHubUpstreamError("GitHub user response is missing required fields")

    return {"id": raw_id, "login": raw_login}


def fetch_contribution_days(
    username,
    token,
    graphql_url="https://api.github.com/graphql",
):
    """Fetch one-year contribution days for a user from GitHub GraphQL API."""
    to_day = date.today()
    from_day = to_day - timedelta(days=364)

    query = """
    query($login: String!, $from: DateTime!, $to: DateTime!) {
      user(login: $login) {
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
            graphql_url,
            json={
                "query": query,
                "variables": {
                    "login": username,
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

    data = payload.get("data")
    if not isinstance(data, Mapping):
        raise GitHubUpstreamError("GitHub GraphQL data is missing")

    user = data.get("user")
    if not isinstance(user, Mapping):
        raise GitHubUpstreamError("GitHub user not found")

    collection = user.get("contributionsCollection")
    if not isinstance(collection, Mapping):
        raise GitHubUpstreamError("GitHub contributionsCollection is missing")

    calendar = collection.get("contributionCalendar")
    if not isinstance(calendar, Mapping):
        raise GitHubUpstreamError("GitHub contributionCalendar is missing")

    weeks = calendar.get("weeks")
    if not isinstance(weeks, list):
        raise GitHubUpstreamError("GitHub contribution weeks are missing")

    days = []
    for week in weeks:
        if not isinstance(week, Mapping):
            continue
        contribution_days = week.get("contributionDays")
        if not isinstance(contribution_days, list):
            continue
        for item in contribution_days:
            if not isinstance(item, Mapping):
                continue
            raw_date = item.get("date")
            raw_count = item.get("contributionCount")
            if isinstance(raw_date, str) and isinstance(raw_count, int):
                days.append({"date": raw_date, "count": raw_count})

    return days
