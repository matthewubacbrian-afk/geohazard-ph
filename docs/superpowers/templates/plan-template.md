# Implementation Plan Template

Use this skeleton for every implementation plan saved to `docs/superpowers/plans/YYYY-MM-DD-<topic>.md`. This codifies the format already used by existing plans (`2026-08-27-kaggle-risk-profile-pipeline.md`, `2026-08-28-epic1-mvp-live-slice.md`, `2026-08-29-epic1-polish.md`) — a new plan should look identical to those, because an agent executing it must be able to pick it up without a format lesson.

A plan is derived from a spec (`docs/superpowers/templates/spec-template.md`) and references it by path. If a plan exists without a spec (small, bounded change), keep the same skeleton and omit the Spec line.

---

# <Topic> — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** One-sentence outcome statement.

**Architecture:** How the change is decomposed and in which order the layers depend on one another.

**Tech Stack:** The languages, frameworks, and test tools involved in this plan only.

**Spec:** `docs/superpowers/specs/YYYY-MM-DD-<topic>-design.md`

## Global Constraints

Short list every task must honor — conventions, verification commands, and invariants. Copy relevant rules from `CODING_STANDARDS.md` and the stack docs (for example: `BACKEND_STANDARDS.md`, `docs/testing-standards.md`) rather than re-deriving them:

- Follow `CODING_STANDARDS.md`, `AGENTS.md`, and the applicable stack doc.
- Conventional Commits; imperative, lowercase after type.
- Python line length 100; type hints on public functions.
- Backend imports resolve from `backend/`; `pytest` runs from `backend/`.
- Do not commit credentials, generated artifacts, or large datasets.
- Route ordering: static segments before `/{param}` routes.
- Verification: package tests, `npm run build` where applicable, `python scripts\verify_structure.py`, `git diff --check`.
- Note which integration tests require provisioned services and how to run them.

---

### Task N: <Task name>

**Files:**
- Modify: `path`
- Create: `path`
- Test: `path`

**Interfaces:**
- Consumes: what this task reads from earlier tasks or libraries.
- Produces: exact signatures, schema fields, endpoint shapes, exports — precise enough that the agent never guesses.

- [ ] **Step 1: Write the failing test**
- [ ] **Step 2: Run the test, verify it fails for the expected reason**
- [ ] **Step 3: Implement** (include the code or a precise description)
- [ ] **Step 4: Run the test, verify it passes**
- [ ] **Step 5: Commit**

```bash
git add <files>
git commit -m "feat: <imperative, lowercase>"
```

---

## Notes for the executor

- Ordering constraints between tasks (which can run in parallel, which cannot).
- Environment requirements: docker services, credentials, databases.
- Anything a reviewer will double-check.