# F-080 — Nav and footer semantics (aria-current, role=status, duplicate links)

**Lens:** reproduce
**Verdict:** CONFIRMED
**Confidence:** high
**Adjusted severity:** low

## Reasoning (HEAD, `django/main/templates/base.html`)

- **No aria-current:** desktop nav (55-57) and mobile menu (44-46) render Home/My Projects/About with no `aria-current` or active-state logic. No `aria-current` exists anywhere in `django/main/templates/`.
- **Messages without role:** the message loop (91-98, alert div at 94) has no `role`/`aria-live`. Messages are only emitted by admin-tool endpoints (`django/main/views.py:431-456`) and shown on a full page load after a redirect. A live region present at initial load is often not announced, so `role="status"` helps little here. `role="alert"` on errors, or moving focus to the message, would do more.
- **Duplicate footer links:** `{% url 'projects' %}` appears twice: "My projects" (154) and "Projects" (158).
- **3 mailto links:** `profile_email_href` is used at 159 ("Contact me"), 165 ("Get In Touch" button) and 177 (Email: address).
- **SVG without aria-hidden:** the arrow SVG at 167-169 has no `aria-hidden`, unlike the other icons (34, `components/icons/*_icon.html:1`). It has no title and the link already has the text "Get In Touch", so the real impact is small.

Every sub-claim matches the code. The overall impact is cosmetic/a11y polish, so the severity stays low.

## Better proposal

- Add `aria-current="page"` using `request.resolver_match.url_name` on the 6 nav links (44-46, 55-57).
- Add `aria-hidden="true"` on the SVG at 167.
- Remove footer link 158 (a duplicate of 154). Optionally drop "Contact me" (159), since the button and the email address already cover it.
- For messages, use `role="alert"` for `error` and `role="status"` otherwise. Since messages only appear on page load in the admin tools, this is optional.

Effort: S.
