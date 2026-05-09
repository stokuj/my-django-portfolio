# Analysis of Options for Dev/Prod Compose and Makefile Workflow

## Context

The repository currently uses one production-leaning `docker-compose.yml`, no top-level `Makefile`, manual `.env` preparation, and scattered verification commands. The goal is to introduce a more deliberate operational workflow without overengineering the project.

## Options Considered

### Option 1: Thin Makefile + Separate Dev and Prod Compose Files

This option adds a small Makefile as the main user interface, renames the current compose file to `docker-compose.prod.yml`, and introduces a dedicated `docker-compose.dev.yml`.

Characteristics:

- simple mental model,
- explicit separation between environments,
- minimal refactoring of existing container behavior,
- easy to align with current documentation and CI.

Advantages:

- low implementation risk,
- low cognitive load,
- preserves existing production behavior,
- easy to review and maintain.

Disadvantages:

- some duplication between dev and prod compose files,
- local verification still depends on host tools such as `uv` and `npm`.

### Option 2: Base Compose File with Dev and Prod Overrides

This option introduces a shared base compose file and two environment-specific overlays.

Characteristics:

- less duplication in compose definitions,
- more compositional structure,
- stronger long-term reuse if the topology grows.

Advantages:

- cleaner DRY story,
- flexible extension for future environments.

Disadvantages:

- more moving parts,
- harder for a small project to reason about quickly,
- higher chance of configuration coupling and override mistakes.

### Option 3: Makefile Interface with Verification Executed Entirely in Docker

This option still adds a Makefile, but runs the verification workflow through containers instead of the host environment.

Characteristics:

- stronger environment reproducibility,
- fewer assumptions about host Python tooling,
- more orchestration overhead.

Advantages:

- consistent execution surface,
- potentially easier onboarding on machines with minimal local setup.

Disadvantages:

- slower feedback loop,
- more complex implementation,
- unnecessary weight for the current repository size and workflow.

## Recommendation

Option 1 is the recommended path.

It provides the biggest usability gain for the smallest structural change:

- clear environment split,
- simple Makefile entrypoints,
- direct support for the requested `.env` behavior,
- straightforward addition of `make verify`,
- minimal disruption to the existing production stack.

## Key Decisions Captured from Discussion

- The current root compose file should be renamed to `docker-compose.prod.yml`.
- Local development should run the full app stack in Docker.
- Local development does not need Caddy.
- `make dev-up` should create `.env` from `.env.example` when needed and continue startup.
- `make prod-up` should never create `.env` and must fail without it.
- `make dev-status` and `make prod-status` should present a readable table rather than raw `docker compose ps` output.
- `make verify` should mean the full local quality gate, including Ruff.

## Why This Recommendation Fits the Repository

The project already has a straightforward runtime structure and does not need a more abstract compose system yet. The chosen design keeps operations explicit, aligns with the current stack, and addresses the exact friction points raised in the issue:

- setup friction,
- unclear environment boundaries,
- missing verification entrypoint,
- inconsistent `.env` handling.

This keeps the implementation small enough to review confidently while still improving the day-to-day development experience in a meaningful way.
