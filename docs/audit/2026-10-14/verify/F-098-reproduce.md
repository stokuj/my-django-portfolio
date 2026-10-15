# F-098 — Task docs out of sync (healthcheck_task unused, disk task undocumented)

**Lens:** reproduce
**Verdict:** CONFIRMED
**Confidence:** high
**Adjusted severity:** low (docs)

## Reasoning

- `docs/implementation.md:36` lists `healthcheck_task` as "worker health check". The task (`django/main/tasks.py:24-26`) just returns `"ok"`.
- Its only references outside docs and plans are the import and test at `django/main/tests/test_tasks.py:14,337-338`. Nothing in `infra/` (compose files, Dockerfile) or `django/config/settings.py` calls it. No compose healthcheck exists for worker or beat.
- `check_disk_usage_task` is defined at `django/main/tasks.py:202` and scheduled daily at 06:00 at `django/config/settings.py:224-227`.
  - It is missing from the task list in `docs/implementation.md:34-38`.
  - It is missing from `docs/architecture.md:146`, which names only the markdown sync job as the notable periodic job.
  - It is missing from the CLAUDE.md "Celery beat schedule" section, which lists only the heatmap and markdown jobs. CLAUDE.md "Key modules" also says tasks.py has "two main Celery tasks".
- Extra detail: `healthcheck_task` uses `ignore_result=True` (tasks.py:24), and `CELERY_TASK_IGNORE_RESULT = True` is set at settings.py:213. So even a caller using `.delay().get()` could not use the task for a round-trip check, because no result is stored. As written it cannot work as a health check.

## Better proposal

- Delete `healthcheck_task`, its test (`test_tasks.py:337-338`, plus the import at line 14) and the doc line at `implementation.md:36`.
- If F-048 adds a worker healthcheck, use `celery -A config inspect ping -d celery@$HOSTNAME`. It needs no custom task.
- Add `check_disk_usage_task` (daily 06:00) to `implementation.md`, `architecture.md` and the CLAUDE.md beat schedule.
- Effort: S.
