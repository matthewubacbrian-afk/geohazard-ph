# Kaggle `.env` Credential Loading — Design

**Date:** 2026-10-14

## Problem

The README instructs users to put `KAGGLE_USERNAME` and `KAGGLE_KEY` in the
repository-root `.env`, but the ML downloader checks only process environment
variables and `~/.kaggle/kaggle.json`. The supported setup described to users
therefore does not work unless another process loads `.env` first. This blocks
the versioned dataset refresh listed in `docs/project-status.md` when a user
has credentials only in the documented file.

## Goals

- Load only `KAGGLE_USERNAME` and `KAGGLE_KEY` from the repository-root `.env`
  during dataset download setup.
- Preserve non-empty process environment values as higher-priority credentials.
- Preserve support for Kaggle's user config file and existing credential errors.
- Parse the documented simple `KEY=value` form, optional matching surrounding
  single or double quotes, blank lines, and full-line comments; ignore unrelated
  keys. Do not perform interpolation or execute shell syntax.
- Keep credential values out of logs and error messages.
- Cover `.env` loading and precedence with temporary files and a fake downloader,
  with no network access.

## Non-goals

- Store or change any credential value, `.env` file, or Kaggle configuration.
- Download datasets or retrain profiles as part of this code change.
- Change dataset versions, parsing, regional assignment, model labels, or the
  held profile bundle.
- Add a general-purpose dotenv parser or new runtime dependency.
- Add scheduling or CI secret management for Kaggle downloads.

## Context And Constraints

- `ml/src/ml/ingest_kaggle.py::_has_credentials` currently checks process
  variables and `Path.home() / ".kaggle" / "kaggle.json"`.
- `download_datasets` calls the Kaggle downloader after this credential check;
  KaggleHub itself expects credentials in the process environment or user config.
- The root `.env` is ignored by Git and currently has empty Kaggle entries. Never
  read its values into tool output or commit it.
- The existing ML tests use `monkeypatch`, `tmp_path`, and fake downloaders; no
  network access is allowed by `docs/testing-standards.md`.
- Follow `CODING_STANDARDS.md`, `docs/glossary.md`,
  `docs/error-handling-and-logging.md`, and `docs/git-workflow.md`.
- Keep the held model bundle unchanged. The current local credential fields are
  empty, so this feature will not itself make a dataset refresh possible.

## Alternatives Considered

1. **Add `python-dotenv` and use its parser.** This provides broad dotenv syntax
   but adds a direct dependency for reading only two keys.
2. **Change the README to require shell variables or `kaggle.json`.** This avoids
   implementation work but removes a documented and useful setup path.
3. **Add a small stdlib parser scoped to the two Kaggle credential keys.** This
   supports the documented file setup, keeps shell variables and Kaggle config
   intact, and adds no dependency. This is the selected approach.

## Design

In `ml/src/ml/ingest_kaggle.py`, define a repository-root constant based on the
module's resolved file path so behavior does not depend on the current working
directory. Add a private `_load_dotenv_credentials(env_path: Path | None = None)
-> None` helper; when `env_path` is omitted it reads `<repository-root>/.env`.

The helper reads UTF-8 lines, ignores blank lines, full-line comments, malformed
lines, and keys other than `KAGGLE_USERNAME` and `KAGGLE_KEY`. For supported
keys it trims surrounding whitespace and removes a matching pair of single or
double quotes. It does not evaluate `export`, variable expansion, escapes, or
shell commands. Missing `.env` is allowed; an unreadable or invalid-UTF-8 file
raises a safe `KaggleCredentialError` without including its contents or values.

For each credential, a non-empty process environment value wins. Otherwise a
non-empty `.env` value is copied into the current Python process environment so
KaggleHub can consume it. Empty values are not credentials. `download_datasets`
loads `.env` values before applying the existing credential check. That check
continues to accept either a complete environment pair or the existing Kaggle
user config file. The missing-credentials message identifies the supported
locations but never includes any value.

Tests in `ml/tests/test_ingest_kaggle.py` will use a temporary `.env`, monkeypatch
the repository root or pass a temporary path to the helper, and a fake downloader
to assert loaded values and precedence. Additional tests will ensure blank
entries do not satisfy the credential check and unrelated variables are ignored.
README and data-source docs will clarify that the ML downloader reads the
repository-root `.env` at runtime.

## Rollout

One feature-branch change. Implement and verify the loader, tests, and setup
documentation, then open a PR. No secrets are added. No dataset download or
artifact update occurs. After merge, a future refresh can run only if valid Kaggle
credentials are supplied; it must use a new local artifact location and preserve
the existing held bundle.

## Files

- `ml/src/ml/ingest_kaggle.py` — read the two allowed credentials from root `.env`
  and keep existing credential sources.
- `ml/tests/test_ingest_kaggle.py` — verify dotenv loading, precedence, blanks,
  and safe missing-credential behavior without network access.
- `README.md` — explain which `.env` file the ML CLI reads.
- `docs/data-sources.md` — document root `.env` loading and credential precedence.
- `docs/superpowers/specs/2026-10-14-kaggle-dotenv-credentials-design.md` —
  this design.
- `docs/superpowers/plans/2026-10-14-kaggle-dotenv-credentials.md` — plan derived
  from this spec.

## Testing Strategy

Run focused `pytest` cases in `ml/tests/test_ingest_kaggle.py` for (1) loading
both values from a temporary `.env`, (2) process environment precedence, (3)
empty values not satisfying authentication, (4) unrelated keys ignored, (5)
missing `.env` and user config preserving existing failure/success behavior,
and (6) no real downloader invocation. Run the complete ML suite with `pytest
-v`, Ruff on the changed Python files, and `git diff --check`.

## Acceptance Criteria

- [ ] With process variables absent and a temporary `.env` containing both
  supported keys, `download_datasets` calls a fake downloader successfully.
- [ ] Non-empty process environment credentials are not replaced by `.env`.
- [ ] Blank or missing `.env` values do not authenticate; the existing
  `kaggle.json` fallback remains supported.
- [ ] Unrelated `.env` settings do not enter the process environment through this
  helper.
- [ ] No credential value appears in captured output or safe errors.
- [ ] README and data-source documentation describe the root `.env` behavior.
- [ ] Full ML tests, Ruff, and `git diff --check` pass; held artifacts and `.env`
  remain unchanged and untracked.

## Out Of Scope (backlog)

- Performing the actual Kaggle source refresh while credentials are absent.
- Scheduling dataset downloads or configuring remote CI secrets.
- Domain approval of the sparse-region policy or risk-profile export.

---

## Spec self-review

- No placeholders or unfinished requirements remain.
- Environment-variable precedence, `.env` syntax, and failure behavior are
  defined.
- Every goal is covered by the testing strategy and acceptance criteria.
- The change is limited to one ML credential path and its documentation.

## Related documents

- Implementation plan: `docs/superpowers/plans/2026-10-14-kaggle-dotenv-credentials.md`
- Terminology: `docs/glossary.md`
