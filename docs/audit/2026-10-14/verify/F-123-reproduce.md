# F-123 - Inconsistent target on the shared social icon links

- Lens: reproduce
- Verdict: CONFIRMED
- Confidence: high
- Adjusted severity: low

## Reasoning

- `django/main/templates/base.html:63-69` (GitHub) and `:72-78` (LinkedIn): header icon links, `href="{{ profile_github_url }}"` / `{{ profile_linkedin_url }}`, no `target` or `rel`.
- `django/main/templates/base.html:127-135` and `:137-145`: footer icon links, same hrefs and same `aria-label`s, with `target="_blank" rel="noopener noreferrer"`.
- Same page, same URLs, different behaviour. The claim holds as described.
- The header pair is the odd one out. Every other external link in the templates opens in a new tab with `rel="noopener noreferrer"`: `components/hero/about_content.html:9` (same `profile_github_url`), `components/timeline_project_item.html:14,17`, `projects/components/project_card.html:57`, `projects/components/blog_projects_sidebar.html:12`, `projects/components/project_footer.html:6`, `projects/detail.html:15`.
- No security impact: the header links have no `target="_blank"`, so there is no opener exposure. It is a UX consistency issue only.

## Better proposal

Do not pick at random. Add `target="_blank" rel="noopener noreferrer"` to the two header links (`base.html:63`, `:72`), which matches the footer and every other external link in the codebase. Removing it from the footer would make the footer the new odd one out next to `about_content.html:9`.
