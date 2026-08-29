# Specification Template

Use this skeleton for every new design spec saved to `docs/superpowers/specs/YYYY-MM-DD-<topic>-design.md`. Fill in every section; mark a section `N/A` only when a heading genuinely does not apply, and say why in one line. Existing specs (`2026-08-27-kaggle-risk-profile-pipeline-design.md`, `2026-08-28-epic1-mvp-live-slice-design.md`) are worked examples of this structure.

Implementation plans derived from this spec must reference `docs/superpowers/templates/plan-template.md`.

---

# <Topic> — Design

**Date:** YYYY-MM-DD

## Problem

What problem does this change solve, for whom, and why now? Name the concrete pain or missing capability in the current repo, with the specific files or flows affected.

## Goals

The outcomes this change must achieve. Each goal must be independently verifiable (a test, a command, a doc statement).

## Non-goals

What this change explicitly will not do. Non-goals are as important as goals — they prevent scope creep and keep reviewers honest. Mirror the "Out of scope" sections in existing specs.

## Context And Constraints

Relevant current state: existing modules this depends on, standing conventions (`CODING_STANDARDS.md`, `BACKEND_STANDARDS.md`, stack docs), data-source assumptions (`docs/data-sources.md`), and any limits on the surface area.

## Alternatives Considered

2–3 reasonable alternatives to the chosen approach, each with trade-offs and a one-line reason for rejection. If no real alternatives exist, say so and why. Do not invent strawmen.

## Design

The chosen approach. Use diagrams or flow blocks when helpful. Cover:

- **Architecture and data flow** — how components fit together and how data moves between them.
- **Components** — each new or changed module, file, or package with its responsibility.
- **Interfaces** — function signatures, schema fields, endpoint shapes, type exports. Exact enough that an implementer never guesses.
- **Configuration** — new env vars, settings fields, defaults.
- **Error handling** — expected failures and their mapping (see `docs/error-handling-and-logging.md`).
- **Data considerations** — schema/migration notes, coordinates, datetimes, deduplication keys.

## Rollout

How the change lands: order of packages, migration sequence, flag gating, or feature-branch plan. For docs/specs-only work, say so directly.

## Files

Tree of files to create and modify, one line each, grouped by package. Use each path with its purpose.

## Testing Strategy

Per package, what tests will prove the goals (see `docs/testing-standards.md`). List the behaviors each test file covers.

## Acceptance Criteria

Checklist that, when all boxes are true, means the spec is implemented. Prefer concrete commands and states over adjectives.

## Out Of Scope (backlog)

Anything deferred that this spec revealed but will not build — list it here so it is not lost, and reference future work where relevant.

---

## Spec self-review

Before handing off, verify:

- No `TBD`, `TODO`, or unfinished sections remain.
- No two sections contradict each other.
- Every goal maps to at least one acceptance criterion.
- Every interface is exact enough to implement without guessing.
- The scope fits a single implementation plan; if not, split.

## Related documents

- Implementation plan: to be created as `docs/superpowers/plans/YYYY-MM-DD-<topic>.md` (see plan template).
- Terminology: `docs/glossary.md`.