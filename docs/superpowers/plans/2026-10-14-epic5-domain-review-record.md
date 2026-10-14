# Epic 5 Domain Review Decision Record — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Prepare a concise, evidence-linked stakeholder worksheet for Epic 5 domain review while preserving the held export and leaving all policy decisions open.

**Architecture:** Add one Markdown decision record that points to the existing quantitative quality review and source assumptions. Update the authoritative project-status row and next milestone to record completed PR #30 CI and link the worksheet; do not copy the entire analysis or alter model artifacts.

**Tech Stack:** Markdown, Git.

**Spec:** `docs/superpowers/specs/2026-10-14-epic5-domain-review-record-design.md`

## Global Constraints

- Follow `AGENTS.md`, `CODING_STANDARDS.md`, `docs/glossary.md`, and `docs/git-workflow.md`.
- Keep the Epic 5 export on quality hold; don't choose a cutoff, assignment rule, risk label, or release decision.
- Keep choices and reviewer fields blank by default; don't imply external review took place.
- Use Conventional Commits and do not add generated reports, local model artifacts, or raw datasets.
- Verify Markdown links/headings and run `git diff --check`; no package tests are needed for a documentation-only change.

---

### Task 1: Add the domain review decision worksheet

**Files:**
- Create: `docs/epic5-domain-review-decision-record.md`

**Interfaces:**
- Links to `docs/risk-profile-quality-review-2026-10-14.md`, `docs/project-status.md`, and `docs/data-sources.md`.
- Provides blank metadata fields for reviewer/role, review date, and evidence reviewed.
- Provides five decision sections: offshore assignment, sparse-region inclusion, source coverage/window, feature/category meaning, and validation criteria for lifting the hold.
- Each section has blank decision, rationale, limitations, and follow-up fields. The sparse-region section lists no preferred cutoff.
- Provides `not_reviewed`, `review_incomplete`, and `review_complete_hold_remains` closeout states; all remain unselected.

- [ ] **Step 1: Create the worksheet with evidence and decisions left unresolved.**

Include a short evidence summary that points to the detailed quality review for exact results. State that the worksheet is not a policy approval or a completed domain review. Keep the existing staging hold explicit.

- [ ] **Step 2: Check worksheet sections and links.**

Run:

```powershell
rg -n "^#|\[[^]]+\]\([^)]*\)|Decision:|Rationale:|Limitations:|Follow-up:" docs/epic5-domain-review-decision-record.md
```

Expected: the document has all five named review areas, each has decision/rationale/limitations/follow-up fields, and every relative link resolves to a tracked file.

- [ ] **Step 3: Commit the worksheet.**

```powershell
git add docs/epic5-domain-review-decision-record.md
git commit -m "docs: add epic 5 domain review worksheet"
```

---

### Task 2: Record completed CI and the next review step

**Files:**
- Modify: `docs/project-status.md`

**Interfaces:**
- Epic 5 evidence continues to cite the existing quality review and states the export remains held.
- Next integration milestone links the decision record and describes review as pending.
- CI evidence points to PR #30 and lists the completed backend, ML, web, mobile, and iOS simulator checks without implying product validation.

- [ ] **Step 1: Update the Epic 5 status and next milestone.**

Add that PR #30 merged on 2026-10-14 and its required CI checks passed. Link the decision worksheet from Epic 5 evidence and the next milestone. State that stakeholder decisions and policy remain pending; retain the no-export-to-staging language.

- [ ] **Step 2: Verify the status claims and hold language.**

Run:

```powershell
rg -n "PR #30|backend|ML|web|mobile|iOS|domain review|quality hold|hold|cutoff" docs/project-status.md
```

Expected: CI is described only as code/build verification, the decision record is linked, and the Epic 5 export is still explicitly held.

- [ ] **Step 3: Run documentation checks and commit.**

```powershell
git diff --check
git add docs/project-status.md
git commit -m "docs: record epic 5 review readiness"
```

Expected: `git diff --check` has no output.

---

## Notes for the executor

- Execute inline in this chat, consistent with the user's earlier choice.
- The source review, data report, and cutoff values are in `docs/risk-profile-quality-review-2026-10-14.md`; avoid maintaining duplicate detailed statistics in the worksheet.
- No domain stakeholder is currently available in this task. Do not fill out decision fields or claim the hold is resolved.
- After implementation, verify the documentation diff and use the normal project review/PR flow before merging.
