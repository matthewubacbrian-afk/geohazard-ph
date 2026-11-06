# Kaggle `.env` Credential Loading — Implementation Plan

> **For agentic workers:** Execute this plan task-by-task in the current chat. Use the test-driven development skill before implementation.

**Goal:** Make the ML dataset downloader read the two documented Kaggle credentials from repository-root `.env`, preserving current credential precedence and fallback behavior.

**Architecture:** Add tests first around a private standard-library `.env` loader and fake downloader, implement loading before the existing credential check, then update the setup documentation. Verification remains within the ML package and does not use Kaggle network access.

**Tech Stack:** Python 3.11+, pytest, Ruff, Markdown.

**Spec:** `docs/superpowers/specs/2026-10-14-kaggle-dotenv-credentials-design.md`

## Global Constraints

- Follow `AGENTS.md`, `CODING_STANDARDS.md`, `docs/glossary.md`, `docs/testing-standards.md`, `docs/error-handling-and-logging.md`, and `docs/git-workflow.md`.
- Keep the parser limited to `KAGGLE_USERNAME` and `KAGGLE_KEY`; do not add dependencies, shell evaluation, interpolation, or logging of credential contents.
- A non-empty process environment value takes precedence; missing `.env` is allowed; unreadable or invalid UTF-8 raises `KaggleCredentialError` with safe text.
- Preserve `~/.kaggle/kaggle.json` fallback and the held risk-profile bundle. Do not download data, retrain, or change `.env`.
- Tests must use temporary files and fake downloaders only; no network calls.
- Python line length is 100. Use Conventional Commits with imperative lowercase subjects.
- Verify with the focused pytest file, full ML `pytest -v`, Ruff on changed Python files, and `git diff --check`.

---

### Task 1: Implement and test root `.env` credential loading

**Files:**
- Modify: `ml/src/ml/ingest_kaggle.py`
- Modify: `ml/tests/test_ingest_kaggle.py`

**Interfaces:**
- Add private `_load_dotenv_credentials(env_path: Path | None = None) -> None`; default path is repository-root `.env` derived from the module path.
- Read only `KAGGLE_USERNAME` and `KAGGLE_KEY`; trim values and matching surrounding single/double quotes; skip blanks, full-line comments, malformed lines, and unrelated keys.
- Ignore missing `.env`; raise safe `KaggleCredentialError` for unreadable/invalid UTF-8. For each key, preserve a non-empty existing environment value and otherwise populate only a non-empty parsed value.
- Invoke the loader from `download_datasets` before its credential check. Keep the Kaggle JSON fallback and generic safe error message.

- [ ] **Step 1: Write failing tests** for temporary `.env` loading through `download_datasets` and a fake downloader; environment precedence; blank and unrelated values; missing file; unreadable/invalid UTF-8; and existing Kaggle JSON fallback.
- [ ] **Step 2: Run focused tests and confirm the expected failures** are due to missing `.env` loading / safe file handling, not fixture errors:

```powershell
pytest -q tests/test_ingest_kaggle.py
```

Expected before implementation: new `.env` cases fail while unrelated existing downloader tests remain meaningful; no network request occurs.

- [ ] **Step 3: Implement** the path constant and narrowly scoped parser, then call it before `_has_credentials()` in `download_datasets`. Do not echo exception details that could contain file contents.
- [ ] **Step 4: Run focused tests and confirm they pass**:

```powershell
pytest -q tests/test_ingest_kaggle.py
```

- [ ] **Step 5: Commit** the test and implementation changes:

```powershell
git add ml/src/ml/ingest_kaggle.py ml/tests/test_ingest_kaggle.py
git commit -m "feat: load kaggle credentials from dotenv"
```

---

### Task 2: Document the credential setup behavior

**Files:**
- Modify: `README.md`
- Modify: `docs/data-sources.md`

**Interfaces:**
- State that the ML downloader reads `KAGGLE_USERNAME` and `KAGGLE_KEY` from the repository-root `.env` when process values are not set.
- State that non-empty process variables take precedence and `~/.kaggle/kaggle.json` remains supported. Do not include actual credential values.

- [ ] **Step 1: Update both docs** to match the implemented supported behavior and identify `.env` as repository-root.
- [ ] **Step 2: Run complete ML verification** from `ml/`:

```powershell
pytest -v
ruff check src/ml/ingest_kaggle.py tests/test_ingest_kaggle.py
```

Expected: all ML tests pass and Ruff reports no issues.

- [ ] **Step 3: Check the complete branch diff** from the repository root:

```powershell
git diff --check
git status --short
```

Expected: no whitespace errors; only the two docs, implementation, tests, and this plan/spec are tracked changes. `.env` and generated artifacts remain untouched.

- [ ] **Step 4: Commit** documentation and plan:

```powershell
git add README.md docs/data-sources.md docs/superpowers/plans/2026-10-14-kaggle-dotenv-credentials.md
git commit -m "docs: explain kaggle dotenv credential setup"
```

---

## Notes for the executor

- Task 1 must be completed before Task 2 verification because the docs describe implemented behavior.
- Run pytest from `ml/`; use repository root for Git operations.
- No external service or credentials are required. The local `.env` entries are empty; do not inspect or print their contents and do not attempt a Kaggle refresh.
- The plan and spec are already on `fix/kaggle-dotenv-loader`; keep all work on that branch. A later merge/release is separate from this implementation plan.
- Review that no credential values can appear in errors, and that the user-config fallback test remains intact.
