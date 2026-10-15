# F-065 — Active-profile lookup repeated 3x; processor flattens model into 15 keys

**Lens:** reproduce
**Verdict:** CONFIRMED (facts accurate; proposal partly overreaches)
**Confidence:** high
**Adjusted severity:** low

## Reasoning
- The identical expression `PortfolioProfile.objects.filter(is_active=True).first() or PortfolioProfile()` is at
  `django/main/context_processors.py:28-30`, `django/main/markdown_sync.py:33` and `django/main/markdown_sync.py:63`. 3 copies, as claimed.
- `portfolio_profile()` returns 15 keys (`context_processors.py:36-52`): `site_name` + 14 `profile_*`. Count matches.
- Not every key is a plain field copy. Three are derived and `|default` cannot replace them:
  - `profile_email_href` (`:44`) builds `mailto:` and falls back to `#`. Used 4x (`base.html:159,165,177`, `components/hero/about_content.html:8`).
  - `profile_github_base` (`:34,46`) strips the trailing `/`. Used in `projects/components/project_footer.html:6`.
  - The `#` fallbacks for github/linkedin (`:31-32`).
- Templates have about 22 `profile_*` references across several files. No test asserts on these context keys; `test_models.py` only matches by test name.
- Nothing is broken. This is only duplication and naming.

## Better proposal
1. (S, worth doing) Add one classmethod, `PortfolioProfile.get_active()`, that returns `cls.objects.filter(is_active=True).first() or cls()`, and use it at the 3 call sites.
2. (Optional, skip unless templates are touched anyway) Do not flatten the profile in the processor. If you do change it, expose `{"profile": source}` and move the derived values to model properties (`email_href`, `github_base`). `|default` alone is not enough. This rewrites ~22 template references for no behaviour gain, so effort M is right for this part only.
