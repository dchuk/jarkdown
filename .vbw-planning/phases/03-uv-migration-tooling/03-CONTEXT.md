# Phase 3 Context: uv Migration & Tooling

## Discussion Summary

Discussed 4 gray areas for the uv migration. User is highly technical (Architect calibration).

## Decisions

### 1. uv Adoption Depth: Full uv
- Replace setuptools build backend with uv/hatchling
- Use uv in all CI workflows
- Use uv build for PyPI publishing
- Drop pip entirely from project tooling

### 2. End-user Install Story: All Three Paths
- Document `uv tool install jarkdown` as primary
- Document `pipx install jarkdown` as alternative
- Document `pip install jarkdown` as fallback
- README features uv first, pip last

### 3. Lock File Strategy: Commit uv.lock
- Commit uv.lock to repository
- Guarantees reproducible dev and CI environments
- CI resolves from lock file for identical deps across runs

### 4. CI/CD Changes: Full Replacement
- Replace pip install with uv in all CI jobs (test matrix, lint, docs, security)
- Use `uv build` for publishing instead of `python -m build`
- Use `uv run` for test/lint commands
- Drop pip-based caching in favor of uv cache

## Current State (Pre-Migration)

- **Build backend:** setuptools>=61.0 + wheel
- **pyproject.toml:** setuptools-based, requires-python >=3.8
- **CI test matrix:** Python 3.8-3.12 via pip
- **CI lint:** ruff via pip
- **CI publish:** `python -m build` + pypa/gh-action-pypi-publish (trusted publishing)
- **Local:** uv.lock exists (216KB, untracked), venv managed by uv already
- **Conditional deps:** tomli;python_version<"3.11"

## Constraints

- Python >=3.8 minimum stays (no version bump in this phase)
- tomli conditional dependency remains for 3.8-3.10 support
- Trusted PyPI publishing (OIDC) must continue working
- Pre-commit hooks remain (ruff, etc.)
- All 187 existing tests must pass after migration
