# Local readiness and status reconciliation — Design

**Date:** 2026-10-30

## Problem

The primary checkout is 15 commits behind `origin/main` and contains an unrelated
uncommitted Figma capture script in `web/index.html`. The current `main` documents
still call the mobile app a starter shell, mark the merged PHIVOLCS UTF-8 fix's CI
as pending, and give Windows backend commands that point to `../.venv` after setup
created `backend/.venv`. These contradictions make local setup and release-readiness
decisions harder to trust. The user cannot provision Oracle staging now, and this
host currently has no connected Android device or running Docker daemon.

## Goals

1. Work on an isolated branch based on the current remote `main`, preserving the
   primary checkout's uncommitted edit.
2. Correct demonstrably stale project status and Windows setup statements using
   merged-commit, CI, and current file evidence.
3. Record local-readiness checks and their limits without treating simulator
   startup, an absent device, or unavailable services as completed runtime flows.
4. Give the next operator a short, ordered set of checks that can resume when
   Docker and Android or iOS hardware are available.

## Non-goals

- Create an Oracle account, staging host, DNS record, release bundle, or deployment.
- Publish the held regional risk-profile export or provision the scene model.
- Change application behavior, dependencies, API contracts, or source data.
- Mark mobile camera, offline, or iOS physical-device flows as passed without a
  recorded run on the matching app commit.

## Context And Constraints

- `docs/project-status.md` is the authoritative status register; `PLAN.md` is the
  completion queue, and `docs/mobile-runtime-smoke-test.md` holds device evidence.
- Remote `main` is `18b9a0ac` at design time. Backend, web, ML, and mobile CI
  completed successfully on that commit. PRs #77 and #78 merged the PHIVOLCS
  text and iOS safe-area fixes. PR #36 is open and reports merge conflicts.
- The existing `web/index.html` edit belongs to the primary checkout and is not
  copied into this worktree.
- `CODING_STANDARDS.md` and `docs/git-workflow.md` require a focused branch,
  Conventional Commits, package checks for touched packages, and a PR before merge.
- A local structure check reports all 140 expected scaffold paths. Docker Desktop
  is unavailable here; Android SDK `adb` sees no connected devices. These are
  environment observations, not product failures.

## Alternatives Considered

1. **Reconcile documentation and evidence now (chosen).** Gives a trustworthy
   local-readiness baseline without requiring an account or device. It cannot
   establish live behavior.
2. Wait for staging access before any work. Avoids a second review later but
   leaves known setup and status errors in place.
3. Start framework migration or scene training integration now. Advances a
   separate workstream but does not resolve the immediate status and setup drift.

## Design

### Architecture and data flow

Read the current remote commit and CI results, compare each claim against its
source, then update only the status register, completion queue, setup guide, and
runtime checklist where evidence warrants it. Preserve dated historical results
as dated results. Separate current code/CI state from local environment limits
and unrun device or deployment checks.

### Components and interfaces

- `PLAN.md`: refresh the review checkpoint, close the stale pending-CI wording,
  and identify the next local acceptance gates. No new tracking vocabulary.
- `docs/project-status.md`: add a concise current checkpoint for PRs #77/#78 and
  the four successful `main` CI runs; correct the older pending-CI statement.
- `README.md`: identify mobile by its implemented foreground scope and fix the
  Windows `backend/.venv` commands so they match the environment created above.
- `docs/mobile-runtime-smoke-test.md`: retain recorded device rows, clarify which
  flows remain unrun on current commits, and record any new *actual* check with
  app commit and runtime. No row is added for a device that is not connected.

No code interface, endpoint, schema, or environment variable changes.

### Configuration, error handling, and data considerations

No configuration, error-handling, database, or data-source behavior changes. If
the local API or device is unavailable, record the missing prerequisite and do
not infer pass or fail for the product flow.

## Rollout

This is a documentation and verification slice on `docs/local-readiness` in a
separate worktree. Review the focused diff, run structure and whitespace checks,
commit with a Conventional Commit message, open a PR, and merge only after review
and required CI. Keep the primary checkout's edit untouched. Staging stays held.

## Files

- `docs/superpowers/specs/2026-10-30-local-readiness-design.md` — this design.
- `docs/superpowers/plans/2026-10-30-local-readiness.md` — implementation steps
  after design approval.
- `PLAN.md` — current checkpoint and local acceptance queue.
- `docs/project-status.md` — authoritative status checkpoint.
- `README.md` — accurate product summary and Windows local setup.
- `docs/mobile-runtime-smoke-test.md` — evidence limits and future device checks.

## Testing Strategy

- Verify each changed status statement against a commit, CI run, existing source
  file, or actual runtime record.
- Run `python scripts/verify_structure.py` and `git diff --check` after edits.
- Run package checks only if package code changes, which are outside this slice.
- Confirm `git status --short` lists only intended documentation files and the
  primary checkout still has its original `web/index.html` edit.

## Acceptance Criteria

- [ ] No pending-CI claim remains for the merged PHIVOLCS fix.
- [ ] README's Windows backend commands resolve to `backend/.venv` as created.
- [ ] Current mobile and CI status is stated without overstating device evidence.
- [ ] The plan explicitly leaves Oracle staging on hold and lists the remaining
      local checks with their prerequisites.
- [ ] Structure verification and `git diff --check` pass.
- [ ] A reviewed PR contains only this focused documentation work before merge.

## Out Of Scope (backlog)

- Physical Android/iOS flows when devices are available.
- Local API and ingestion smoke when Docker is running.
- PR #36 scene-training conflict resolution and model validation.
- Regional risk-profile domain approval and PHIVOLCS geometry reuse clearance.
- Staging deployment when the user can provision a host and DNS.

## Related documents

- Implementation plan: `docs/superpowers/plans/2026-10-30-local-readiness.md`
  (to be written after review; see `docs/superpowers/templates/plan-template.md`).
- Terminology: `docs/glossary.md`.
