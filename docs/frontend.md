# Frontend Diagram

This diagram shows the current template composition around the shared layout, footer, and reusable components.

Related docs:

- [`README.md`](../README.md)
- [`architecture.md`](architecture.md)
- [`implementation.md`](implementation.md)

## Template structure

- `base.html` is the root layout for all pages. It contains the navbar, global scripts, and the global footer.
- Every page extends `base.html` and fills the main blocks (`content`, optional `sidebar`, optional `extra_scripts`).
- In practice there are 3 main page types inside this structure:
  1. static/content pages (`pages/home.html`, `pages/about.html`, error pages),
  2. projects listing (`projects/index.html`),
  3. project detail/blog page (`projects/detail.html`).
- `projects/detail.html` is rendered per project entry from the database (`Project`), resolved by slug (`/blog/<slug>/`).


```mermaid
flowchart TD
    Base["base.html\n(navbar + footer + global blocks)"]
    ThemeJS["static/js/theme-toggle.js"]
    MobileJS["static/js/mobile-menu.js"]
    ProjectsJS["static/js/projects-filters.js"]
    MathJax["MathJax scripts (detail page)"]

    Home["pages/home.html"]
    About["pages/about.html"]
    Errors["errors/404.html + errors/500.html"]
    ProjectsIndex["projects/index.html"]
    ProjectDetail["projects/detail.html"]
    ProjectDB["Project model (DB)"]

    Hero["components/hero_section.html"]
    TimelineSection["components/timeline_section.html"]
    TimelineItem["components/timeline_project_item.html"]
    ProjectCard["projects/components/project_card.html"]
    ProjectFooter["projects/components/project_footer.html"]
    Sidebar["projects/components/blog_*_sidebar.html"]
    GithubIcon["components/icons/github_icon.html"]
    LinkedinIcon["components/icons/linkedin_icon.html"]

    Home --> Base
    About --> Base
    Errors --> Base
    ProjectsIndex --> Base
    ProjectDetail --> Base

    Base --> ThemeJS
    Base --> MobileJS
    Base --> GithubIcon
    Base --> LinkedinIcon

    Home --> Hero
    Home --> TimelineSection
    TimelineSection --> TimelineItem

    About --> Hero

    ProjectsIndex --> Hero
    ProjectsIndex --> ProjectCard
    ProjectsIndex --> ProjectsJS

    ProjectDB --> ProjectsIndex
    ProjectDB --> ProjectDetail
    ProjectDetail --> Sidebar
    ProjectDetail --> ProjectFooter
    ProjectDetail --> MathJax
```
