# Issue 51: GitHub Heatmap Migration Design

## Summary

This change removes the runtime dependency on the external `github-heatmap` FastAPI service and moves GitHub contribution fetching directly into the Django application. It also removes GitHub authentication through `django-allauth` and replaces the heatmap identity source with a single GitHub token stored in `.env`.

The migration keeps the current Django-side behavior where it already works well: `HeatmapSnapshot` remains the cache source, Celery continues to refresh data asynchronously, and the frontend continues to consume the same heatmap payload shape.

## Goals

- Remove the FastAPI heatmap service from the Django runtime flow.
- Fetch GitHub user and contribution data directly from GitHub REST and GraphQL APIs.
- Use a dedicated `.env` token as the only heatmap credential source.
- Remove GitHub login and connect/disconnect functionality from the Django app.
- Preserve the current frontend heatmap contract and cache-based behavior.
- Keep task logging, snapshot persistence, and stale-cache fallback behavior.

## Non-Goals

- Redesigning general admin authentication.
- Changing the visual heatmap component contract.
- Replacing GitHub auth with another SSO provider.
- Introducing multi-account heatmap selection.

## Current State

The current heatmap flow is:

1. Django reads a GitHub OAuth token from `django-allauth` models.
2. Django calls `{HEATMAP_API_BASE_URL}/heatmap/me`.
3. FastAPI calls GitHub APIs and returns a normalized payload.
4. Django stores the response in `HeatmapSnapshot`.
5. Views and Celery tasks serve or refresh that cached snapshot.

This design works, but it creates avoidable operational and maintenance cost:

- two codebases for one user-facing feature,
- an extra network hop,
- duplicated failure surfaces,
- coupling to `allauth` even though the final requirement is a single configured GitHub identity.

## Proposed Architecture

After the migration, the flow becomes:

1. Django reads `GITHUB_HEATMAP_TOKEN` from `.env`.
2. Django calls GitHub REST `/user` to resolve the token owner login.
3. Django calls GitHub GraphQL API to fetch the contribution calendar for that login.
4. Django normalizes GitHub data into the existing payload shape.
5. Django stores the normalized payload in `HeatmapSnapshot`.
6. Views and Celery tasks keep using the snapshot and stale-cache behavior already present in the project.

## Module Responsibilities

### `django/main/github_client.py`

New module dedicated to direct GitHub communication.

Responsibilities:

- fetch the authenticated user from `https://api.github.com/user`,
- fetch the contribution calendar from the GitHub GraphQL API,
- validate response structure,
- raise clear internal exceptions for auth failures vs temporary failures.

This module should stay transport-focused and should not know about Django models or snapshots.

### `django/main/heatmap.py`

This module remains the orchestration layer for portfolio heatmap behavior.

Responsibilities:

- read configured token from settings,
- call `github_client.py`,
- map GitHub responses into the existing `weeks/days` payload shape,
- calculate per-day `level` values,
- keep snapshot helpers and staleness checks,
- map low-level client failures into user-safe error messages.

This keeps the current Django integration entrypoint stable while improving separation of concerns.

### `django/main/tasks.py`

Celery task responsibilities remain unchanged at a high level:

- fetch or refresh heatmap data,
- update `TaskExecutionStatus`,
- append `TaskExecutionLog`,
- preserve delayed re-scheduling behavior.

The implementation changes only in where the data comes from.

### `django/main/views.py`

The heatmap view flow stays mostly intact:

- `/about/heatmap-data/` still serves cached data,
- cache miss or stale cache still triggers refresh logic,
- stale valid snapshot can still be served when refresh fails.

GitHub social-account-specific behavior is removed:

- GitHub connect redirect,
- disconnect endpoint,
- account-matching checks,
- UI state based on connected GitHub social accounts.

### `django/config/settings.py`

Configuration changes:

- add `GITHUB_HEATMAP_TOKEN`,
- optionally add `GITHUB_GRAPHQL_URL` only if needed for configurability, though defaulting to GitHub's public endpoint is preferred,
- remove `HEATMAP_API_BASE_URL`,
- remove `django-allauth` GitHub provider configuration and app registration.

## Data Contract

The frontend-facing heatmap payload should remain compatible with the current client code.

Expected normalized payload stored in `HeatmapSnapshot.payload`:

```json
{
  "username": "example-user",
  "total": 123,
  "weeks": [
    {
      "week_start": "2026-01-04",
      "days": [
        {
          "date": "2026-01-04",
          "weekday": 0,
          "count": 3,
          "level": 2
        }
      ]
    }
  ]
}
```

The response returned by `/about/heatmap-data/` should keep the current wrapper fields:

- `username`
- `total`
- `last_30_days_total`
- `weeks_count`
- `raw`
- `fetched_at`

## Contribution Level Mapping

The existing FastAPI logic should be retained to avoid visual regressions:

- `0` contributions -> level `0`
- `1..2` contributions -> level `1`
- `3..5` contributions -> level `2`
- `6..9` contributions -> level `3`
- `10+` contributions -> level `4`

## Error Handling

The migration should preserve safe user-facing behavior while changing the underlying source.

### Missing Configuration

If `GITHUB_HEATMAP_TOKEN` is missing or blank:

- heatmap is treated as not configured,
- `/about/heatmap-data/` returns the same not-configured behavior used today,
- the About page does not depend on connected GitHub social accounts,
- admin task execution records a configuration failure when a refresh is attempted.

### GitHub Authentication Failure

If GitHub returns `401` or `403`:

- treat the configured token as invalid or expired,
- store a user-safe error message,
- keep serving the previous snapshot if one exists,
- mark task execution as failure.

### Temporary Failures

For timeouts, network failures, GitHub outages, or malformed upstream responses:

- return a generic temporary availability error,
- do not expose raw upstream details to the UI,
- preserve the last valid snapshot when available,
- record failure in snapshot and task status.

## Removal of GitHub Authentication

GitHub authentication should be removed from this Django project entirely.

Removal scope:

- remove `allauth` and GitHub provider apps from `INSTALLED_APPS`,
- remove `allauth` middleware,
- remove GitHub OAuth-related settings from `.env.example` and docs,
- remove heatmap connect/disconnect views and routes,
- remove any About-page text or controls related to connecting GitHub,
- remove logic that selects a portfolio GitHub account from social account records.

This issue assumes admin access will continue through Django's own authentication and user management.

## Testing Strategy

### Unit Tests

Add or update tests for:

- authenticated user fetch success,
- contribution GraphQL fetch success,
- invalid GitHub token handling,
- timeout and request-failure handling,
- invalid payload validation,
- contribution level mapping,
- week grouping and total calculation,
- staleness and snapshot update helpers.

### Integration Tests

Add or update Django tests for:

- `/about/heatmap-data/` when token is missing,
- `/about/heatmap-data/` when cache is missing and GitHub fetch succeeds,
- cached snapshot fallback when GitHub fetch fails,
- Celery heatmap refresh task success path,
- Celery heatmap refresh task failure path,
- About page behavior without social-account state,
- removed GitHub auth routes no longer being exposed.

## Documentation Changes

Update:

- `README.md`
- `docs/architecture.md`
- `docs/implementation.md`
- `.env.example`

Documentation should reflect:

- no FastAPI runtime dependency for heatmap,
- no GitHub login/auth integration,
- direct GitHub API usage from Django,
- new required environment variable for heatmap token.

## Risks

- GitHub API rate limiting when cache refreshes are too aggressive.
- Misconfigured or expired token causing silent operational confusion if error messages are unclear.
- Minor payload-shape drift during migration if normalization differs from the FastAPI implementation.
- Removing `allauth` may affect any untracked assumptions elsewhere in templates or tests.

## Rollout Notes

Implementation should proceed in small steps:

1. Introduce direct GitHub client code and tests.
2. Switch heatmap orchestration from FastAPI to direct GitHub calls.
3. Remove GitHub auth code and related UI/routes/settings.
4. Update docs and environment examples.
5. Verify the full Django heatmap flow without the FastAPI service.

## Acceptance Criteria

- `/about/heatmap-data/` works without the FastAPI service.
- `refresh_portfolio_heatmap_cache_task` refreshes snapshot data directly from GitHub.
- The About page no longer exposes GitHub connect/disconnect behavior.
- GitHub authentication through `allauth` is removed from the project.
- Existing frontend heatmap rendering continues to work with the normalized payload.
- Heatmap-related tests pass.
- Documentation and environment examples match the new architecture.
