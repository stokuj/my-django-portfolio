# F-061 (reproduce): Dead/default settings: STATICFILES_STORAGE, Env(DEBUG), result backend, Polish comments

- Verdict: CONFIRMED
- Confidence: high
- Adjusted severity: low

## Reasoning
- `django/config/settings.py:181` sets `STATICFILES_STORAGE`. `pyproject.toml:10` pins `django==5.1.15`; the setting was removed in 5.1 (replaced by `STORAGES`), so Django ignores it. Its value matches the default anyway.
- `settings.py:24-27` declares `environ.Env(DEBUG=(bool, False))`, but nothing reads `env("DEBUG")`. `DEBUG` comes from `env.bool("DJANGO_DEBUG")` at `settings.py:40`. The scheme is dead. Note: `DEBUG=` in `.env` would be ignored even without the scheme, so the "silently does nothing" wording describes the env var naming, not something the scheme causes.
- Result backend: every task uses `@shared_task(ignore_result=True)` (`django/main/tasks.py:24,29,112,201`), and the global setting `CELERY_TASK_IGNORE_RESULT = True` is at `settings.py:213`. Callers only read `async_result.id` (`views.py:436,441,458`), which needs no backend. No `AsyncResult`/`.get()`/chord/group anywhere. `CELERY_RESULT_BACKEND` (`settings.py:207`) and `CELERY_RESULT_SERIALIZER` (`settings.py:210`, not 207) are unused. The env lines also appear in `infra/docker-compose.dev.yml:51,85,118`, `infra/docker-compose.prod.yml:64,103,141` and `.env.example:44`.
- Commented-out prints: `settings.py:119-121`, confirmed.
- Polish comments: `settings.py:25,28` and `views.py:327` ("Pobieramy wszystkie unikalne tagi"), confirmed.
- `AUTHENTICATION_BACKENDS` (`settings.py:168-170`) only lists `ModelBackend`, which is the default.
- `DEFAULT_AUTO_FIELD` is set at `settings.py:163` and again at `django/main/apps.py:8`, with the same value.
- `TEMPLATES.DIRS` (`settings.py:74`) points to `django/templates/`, and that directory does not exist. Templates load through `APP_DIRS=True`.
- `STATICFILES_DIRS` (`settings.py:156`) points to `django/main/static`, the `main` app's own static dir, which `AppDirectoriesFinder` already finds.

## Better proposal
- Remove one `DEFAULT_AUTO_FIELD`, not both. Keep the one in settings and drop `apps.py:8`, or keep apps.py and drop settings. All contrib apps set their own field, so either choice is safe.
- Also drop `CELERY_ACCEPT_CONTENT` and `CELERY_TASK_SERIALIZER` (`settings.py:208-209`). They restate Celery's json defaults.
- Also remove `CELERY_RESULT_BACKEND` from `.env.example:44`.
- Removing `STATICFILES_DIRS` stops the duplicate lookup of the same files and gives the same collectstatic output. Run `make verify` and `collectstatic --dry-run` to check.
