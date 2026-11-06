# Staging Acceptance And Status Reconciliation — Implementation Plan

> **For agentic workers:** Execute this bounded documentation and acceptance slice inline using `executing-plans`. Use `docs/superpowers/templates/plan-template.md`; track observed results separately from open gates.

**Goal:** Reconcile current project documents with deployed behavior and record a fresh, bounded staging acceptance check.

**Architecture:** Inspect the existing public API, browser, GitHub configuration and one manual ingestion cycle. Store dated evidence in one acceptance record, then update the status register, completion plan, operating instructions and affected historical checkpoints to reference it.

**Tech Stack:** Markdown, GitHub CLI, existing HTTPS/WSS endpoints, browser inspection, Python structure verification.

## Global Constraints

- Follow `AGENTS.md`, `CODING_STANDARDS.md`, `docs/glossary.md` and `docs/git-workflow.md`.
- Use an isolated `docs/staging-acceptance-status` branch based on current `origin/main`.
- Do not expose connection secrets, change provider plans, release held profiles, import uncleared vectors, or invent device/scientific acceptance.
- Keep historical observations dated; update current summaries and add supersession notes to older plans.
- A manually dispatched ingestion cycle does not prove automatic scheduling, cold-start reconnection or durable event delivery.
- This slice changes documentation only. Verify structure, local Markdown targets and `git diff --check`; package behavior remains covered by the existing CI workflows.

### Task 1: Collect staging evidence

**Files:** Read existing workflows, deployment and acceptance records; create `docs/staging-acceptance-2026-11-06.md`.

**Interfaces:** Consumes public read endpoints, browser-visible states and GitHub run/configuration metadata. Produces dated observations with source/run identifiers and explicit limitations.

- [x] Inspect latest `main`, checks, worker image selection, schedule enable switch and staging secret names without reading secret values.
- [x] Check HTTPS health, both earthquake sources, faults, volcano bulletins, held clusters and allowed-origin CORS.
- [x] Observe browser map/activity rendering and ingestion-generated notifications during one bounded manual cycle; record WSS evidence and the final run outcome.
- [x] Record remaining automatic scheduling, device, backup/restore, usage and model-validation gates.

### Task 2: Reconcile current and historical documents

**Files:** Modify `PLAN.md`, `docs/project-status.md`, `docs/free-split-deployment.md`, `docs/runbook.md`, `docs/geohazard-project-overview.md`, `docs/geohazard-development-framework.md`, `docs/mobile-runtime-smoke-test.md` and directly superseded dated plans/acceptance notes. Modify `README.md` only for current navigation/operations guidance.

**Interfaces:** Consumes Task 1 evidence and existing release records. Produces consistent current summaries and an ordered acceptance backlog.

- [x] Update epic rows and the active staging milestone; distinguish event-count shading from held ML labels and browser inference from the mobile/server path.
- [x] Preserve earlier records as history; correct statements that now falsely describe active work or present availability.
- [x] Document observable acceptance procedures and external prerequisites without selecting scientific policy or implying permission clearance.

### Task 3: Verify and deliver

**Files:** All changed Markdown files.

- [x] Run `python scripts/verify_structure.py` from the worktree; all 140 required paths passed.
- [x] Check local Markdown file/fragment links and independently review the diff for stale claims, unsupported acceptance and secrets. All 159 local targets resolved; review findings on scope/cadence were reconciled.
- [x] Run `git diff --check`; exited 0.
- [ ] Commit only intended Markdown with a Conventional Commit, push the feature branch and open a PR using Summary / Testing / Notes.
- [ ] Inspect the resulting CI checks and report the delivered work plus unresolved gates.

## Notes for the executor

No new product behavior or endpoint is designed in this slice. Device, scientific-review and reuse-permission work requires its own evidence and must remain open when unavailable. Source outages or a failed acceptance probe must be recorded accurately rather than converted into a pass.
