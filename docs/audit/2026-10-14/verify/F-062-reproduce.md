# F-062 — No Celery task time limit (reproduce lens)

- Verdict: CONFIRMED
- Confidence: high
- Adjusted severity: low

## Reasoning
- `django/config/settings.py:203-228`: Celery config block sets broker, serializers, timezone, ignore_result and beat schedule. No `CELERY_TASK_TIME_LIMIT` / `CELERY_TASK_SOFT_TIME_LIMIT`. The cited line 214 is `CELERY_BEAT_SCHEDULE`, i.e. the end of that block; the gap is the block as a whole.
- `django/config/celery.py`: no time-limit config (grep empty).
- `django/main/tasks.py:24,29,112,201`: all tasks are `@shared_task(ignore_result=True)`, no `time_limit`/`soft_time_limit` kwargs.
- Worker command `infra/docker-compose.prod.yml:88` / `infra/docker-compose.dev.yml:70`: `celery -A config worker --loglevel=info`, no `--time-limit`.
- HTTP calls do set timeouts: `django/main/github_client.py:55` (15s), `:121` (20s), `django/main/markdown_sync.py:104` (20s). `requests` timeouts are per connect/read, not total, so a slow-drip response or a DB stall can still exceed them. Real risk is small; low severity is right.
- "No lock needed because tasks are idempotent overwrites": consistent with code — tasks `get_or_create` a `TaskExecutionStatus` row and overwrite it (`tasks.py:30-33,113-116,203-204`).

## Better proposal
Set both limits so the task can log failure before being killed:
`CELERY_TASK_SOFT_TIME_LIMIT = 540` and `CELERY_TASK_TIME_LIMIT = 600` in `django/config/settings.py` next to the other `CELERY_*` settings. The soft limit raises `SoftTimeLimitExceeded`; it is caught only where the task already catches broad exceptions, so a hard limit alone leaves `TaskExecutionStatus` stale. Effort S.
