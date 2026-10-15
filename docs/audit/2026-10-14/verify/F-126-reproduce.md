# F-126 reproduce: Duplicate and ambiguous 'Learn More' link in the timeline item

**Verdict:** CONFIRMED
**Confidence:** high
**Adjusted severity:** low

## Reasoning
- `django/main/templates/components/timeline_project_item.html:11-15`: if `project.blog and project.blog_url`, "Learn More" goes to `blog_detail` (same tab); `{% elif project.github_url %}` renders a second "Learn More" pointing to `project.github_url` with `target="_blank"`.
- `:16-18`: separate `{% if project.github_url %}` renders a "GitHub" button to the same URL. So any project without a blog post (or with `blog=True` but empty `blog_url`) and with `github_url` gets two buttons to the same URL.
- Reachable: included from `components/timeline_section.html:7`, rendered on the home page (`django/main/views.py:115-125`, `pages/home.html:15-16`). "Learn More" occurs only in this template, so the generic text repeats per project in the timeline.
- No test asserts on the button (`django/main/tests/test_views.py:56` only checks the context key), so removal breaks nothing.

## Proposal
As in the finding: delete lines 13-14 (`{% elif %}` branch). Optional `aria-label="Learn more about {{ project.title }}"` on the blog link. Effort S.
