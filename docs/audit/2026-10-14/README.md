# Audit 2026-10-14: index

A read-only audit of `dev` at HEAD. **132 findings** were merged (F-001..F-107 from the lenses, F-108..F-132 from the gap passes). **129 were confirmed and 3 refuted** (F-006, F-058, F-095).
Confirmed severities: 0 critical, 3 high, 23 medium, 103 low.

| Path | What | Count |
|------|------|-------|
| [SYNTHESIS.md](SYNTHESIS.md) | Ranked backlog by category, with the chosen fix per finding and the refuted list | 129 items |
| [completeness.md](completeness.md) | Coverage review of the lens reports, which defined the 4 gap passes | 1 file |
| [find/](find/) | Raw findings | 25 files |
| find/01..20-*.md | One report per lens (mattpocock, ponytail, devkit, cr, sec, arch, libraries, frontend, perf, tests, ops) | 20 |
| find/gap-01..04-*.md | Gap passes: admin surface, SEO head, secondary templates, human docs drift | 4 |
| find/_merged.md | De-duplicated merged list F-001..F-107 | 1 |
| [verify/](verify/) | Per-finding verification | 200 files |
| verify/F-xxx-reproduce.md | Reproduction or code check (F-001..F-132) | 132 |
| verify/F-xxx-worth.md | Is it worth fixing, and is there a smaller fix | 57 |
| verify/F-xxx-risk.md | Risk of the proposed change (F-001..F-011 only) | 11 |

Confirmed findings by category: security 21, bug 16, simplification 18, frontend 18, ops 12, tests 11, docs 11, ci 6, library 6, performance 6, architecture 4.

The execution checklist is at [`PLAN.md`](PLAN.md) and has 12 phases. Owner decisions are in [`DECISIONS.md`](DECISIONS.md).
