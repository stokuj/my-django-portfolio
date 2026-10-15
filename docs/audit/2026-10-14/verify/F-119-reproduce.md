# F-119 reproduce: PageView counter registered raw in admin

- Verdict: CONFIRMED
- Confidence: high
- Adjusted severity: low

## Reasoning
- `django/main/admin.py:116` is `admin.site.register(PageView)`, with no ModelAdmin, so the default add, change and delete views are all enabled.
- The model is a singleton by convention only (`django/main/models.py:106-115`). `get_instance()` does `get_or_create(id=1)`, and nothing at the DB or model level stops other rows from existing.
- The only code that reads or writes the counter is hard-wired to id=1: `context_processors.py:15` (`filter(id=1).first()`), and `middleware.py:15-16` (`get_instance()`, then `update` on that id). A row added in admin gets an auto id other than 1, so neither path ever reads it.
- Deleting id=1 in admin makes `visitor_counter` return 0 (`context_processors.py:16`). The next first-session home visit then re-creates id=1 with `count=0` (`models.py:114`). The public count is reset silently, and there is no confirmation beyond Django's generic delete page.
- Scope: admin is restricted to staff and superusers, so no attacker can reach this. It is an operator footgun, not a security gap. Keeping `low` is right.

## Better proposal
Register it with a small ModelAdmin: `has_add_permission`/`has_delete_permission` return False, and `count` stays editable only if a manual reset is a wanted feature (otherwise use `readonly_fields=("count",)`). The other option is to drop the registration, since the count is already shown on the site.
