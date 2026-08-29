# Git Workflow

**Project**: GeoHazard PH
**Scope**: Branching, worktrees, commit messages, and PR/merge policy for human and agent work.

The baseline branching strategy and Conventional Commits rules live in `CODING_STANDARDS.md` → Git Workflow. This document adds what that section does not cover: how parallel agent work is isolated via worktrees, and the merge policy. Follow both together; if they conflict, the more specific rule here wins for the topics this document owns.

---

## Table Of Contents

1. Branching And Worktrees
2. Commit Convention
3. Commit Checklist For Agents
4. PR And Merge Policy
5. Naming Things
6. Known Deviations

---

## 1. Branching And Worktrees

- Keep `main` deployable and reviewable at all times. Non-trivial work happens on a feature branch.
- The `.worktrees/` directory exists for **parallel agent work**: each agentized feature stream runs in its own worktree checked out to its own feature branch, so multiple streams never share a dirty working tree.
- The mapping is strict: **one worktree ↔ one feature branch ↔ one plan or spec**. A worktree named for `epic1-*` never carries a `mobile-*` branch.
- Create a worktree from `main` for each feature stream:

```bash
git worktree add ../geohazard-ph-<feature> -b feat/<feature>
```

- Before starting, verify you are in the right worktree for the branch (run `git status` and `git branch --show-current`). A common failure mode is committing on `main` because the wrong worktree was selected.
- Rebase or merge `main` into your branch when it drifts; keep the diff against `main` reviewable in size.

## 2. Commit Convention

Conventional Commits, per `CODING_STANDARDS.md`:

```text
feat: add regional risk profile endpoint
fix: handle empty earthquake dataset
docs: add coding standards
ci: run web tests in ci
test: add parser regression coverage
refactor: split map layer controls
chore: update package metadata
```

Allowed types: `feat`, `fix`, `docs`, `ci`, `test`, `refactor`, `style`, `perf`, `chore`.

Rules: imperative mood, lowercase after the type, one logical change per commit, never mix generated artifacts or secrets into a commit.

## 3. Commit Checklist For Agents

Before every commit, verify:

- [ ] `git status --short` shows only files this change intends.
- [ ] `git diff --check` — no trailing whitespace or conflict markers.
- [ ] No `.env`, credentials, tokens, lockfile-plus-secret pairs, or large raw datasets staged.
- [ ] Message uses a valid Conventional Commit type and imperative lowercase after it.
- [ ] Package tests for every touched package pass (`docs/testing-standards.md`).
- [ ] `python scripts\verify_structure.py` passes when the file tree changed.
- [ ] Docs are updated in the same change when setup, commands, APIs, or workflows changed.

A skipped package test, a generated artifact, or a docs change without its commit message type being `docs` are review blockers.

## 4. PR And Merge Policy

- Open a PR per feature branch against `main`. Include the PR description skeleton from `CODING_STANDARDS.md` (Summary / Testing / Notes).
- Describe the tests actually run in the PR body; never claim untested behavior.
- Merges use a standard merge commit (observed history: `Merge pull request #N from <owner>/<branch>`). Squash is acceptable when the branch is a single logical change; rebase always when it avoids noise.
- Do not force-push shared branches; push a new fix commit instead.
- A PR that touches the API, DB schema, or environment must call out breaking changes explicitly.

## 5. Naming Things

| Kind | Convention | Example |
| --- | --- | --- |
| Feature branch | `feat/<topic>` | `feat/risk-profile-api` |
| Fix branch | `fix/<topic>` | `fix/usgs-parser-timezone` |
| Docs branch | `docs/<topic>` | `docs/coding-standards` |
| CI branch | `ci/<topic>` | `ci/web-build-check` |
| Worktree dir | `../geohazard-ph-<feature>` | `../geohazard-ph-risk-profile` |
| Plan/spec files | see `docs/superpowers/templates/` | `2026-08-29-<topic>.md` |

## 6. Known Deviations

- `.worktrees/` is empty as of writing; no worktree-based parallel streams are active yet. The convention above is the target for the first multi-stream epic.
- Some earlier commits use scoped styles such as `merge(web): ...` and `feat(mobile): ...`; scope prefixes are optional, not required.