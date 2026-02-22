# Frontend Diagram

This diagram shows how the template layer is composed around the shared base layout and reusable UI components.

Related docs:

- [`README.md`](../README.md)
- [`architecture.md`](architecture.md)
- [`implementation.md`](implementation.md)

```mermaid
flowchart TD
    Base["base.html"]
    ThemeJS["static/js/theme-toggle.js"]
    ProjectsJS["static/js/projects-filters.js"]

    Home["main/home.html"]
    Projects["main/projects.html"]
    ProjectDetail["main/project_detail.html"]
    About["main/about.html"]
    NotFound["main/404.html"]
    ServerError["main/500.html"]
    Blog["main/blog/* (9 templates)"]

    TimelineSection["components/timeline_section.html"]
    TimelineItem["components/timeline_project_item.html"]
    ProjectCard["components/project_card.html"]
    GithubIcon["components/icons/github_icon.html"]
    LinkedinIcon["components/icons/linkedin_icon.html"]

    Base --> ThemeJS
    Base --> GithubIcon
    Base --> LinkedinIcon

    Home --> Base
    Home --> TimelineSection
    TimelineSection --> TimelineItem

    Projects --> Base
    Projects --> ProjectsJS
    Projects --> ProjectCard

    ProjectDetail --> Base
    About --> Base
    NotFound --> Base
    ServerError --> Base
    Blog --> Base
```
