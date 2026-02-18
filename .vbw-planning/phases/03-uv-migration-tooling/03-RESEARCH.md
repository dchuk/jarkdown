# Phase 3 Research: uv Migration & Tooling

## Findings

### pyproject.toml Migration (setuptools → hatchling)
- Change `[build-system]` to `requires = ["hatchling"]`, `build-backend = "hatchling.build"`
- Move version to `[project]` table or use `dynamic = ["version"]` with `tool.hatch.version.path`
- Hatchling automatically includes source files via `.gitignore` patterns — no MANIFEST.in needed
- Conditional `tomli` dependency with markers fully supported in `[project]` table

### GitHub Actions CI with uv
- Use official `astral-sh/setup-uv@v7` action with `enable-cache: true`
- Standard pattern: `uv sync --locked --all-extras --dev` then `uv run pytest`
- Matrix testing uses setup-uv's `python-version` input per job
- Run `uv cache prune --ci` after installation to optimize CI cache size

### `uv build` for PyPI Publishing
- `uv build` creates wheel + sdist in `dist/`
- Trusted publishing (OIDC) supported: `permissions: { id-token: write }` + configured trusted publisher on PyPI
- `uv.lock` ensures build environment consistency but is NOT distributed with package
- `uv publish` handles upload; works with OIDC tokens automatically in GitHub Actions

### Python 3.8 Compatibility
- uv itself supports Python 3.8+; jarkdown's `requires-python = ">=3.8"` remains valid
- GitHub Actions runners have Python 3.8 available natively
- Some Docker base images dropped 3.8 (Alpine, Debian Trixie) but this doesn't affect GitHub Actions CI

### uv.lock Behavior
- Cross-platform, reproducible snapshot of all dependencies; single file works across OS + Python versions
- Generated/updated by `uv sync`; never manually edit
- Commit to version control for reproducible CI
- Does not affect wheel/sdist artifacts directly

## Relevant Patterns

### pyproject.toml Changes
- Replace `[build-system]` with hatchling
- Version can be static in `[project]` or dynamic via `tool.hatch.version`
- All setuptools-specific sections (`[tool.setuptools]`, `[tool.setuptools.packages.find]`) removed
- No `setup.py`, `setup.cfg`, or `MANIFEST.in` needed for pure Python

### GitHub Actions Workflow Pattern
```yaml
- uses: astral-sh/setup-uv@v7
  with:
    python-version: ${{ matrix.python-version }}
    enable-cache: true
- run: uv sync --locked --all-extras --dev
- run: uv run pytest
```

### Publishing Workflow Pattern
```yaml
permissions:
  id-token: write
steps:
  - uses: astral-sh/setup-uv@v7
  - run: uv build
  - uses: pypa/gh-action-pypi-publish@release/v1
```

## Risks

| Risk | Severity | Mitigation |
|------|----------|------------|
| Hatchling version handling differs from setuptools | Medium | Use static version or `tool.hatch.version.path`; validate |
| uv.lock format stability across uv versions | Low | Pin uv version in setup-uv action and via `required-version` in pyproject.toml |
| Conditional tomli dep may break with new build backend | Low | Test on 3.8-3.10 (needs tomli) and 3.11+ (stdlib tomllib) |
| Trusted publishing OIDC permission changes | Low | One-time PyPI configuration + `id-token: write` permission |

## Recommendations

### Migration Order
1. Update pyproject.toml build system (setuptools → hatchling)
2. Remove setup.py/setup.cfg/MANIFEST.in if present
3. Run `uv sync` to generate/update uv.lock
4. Update CI workflows (ci.yml, publish-to-pypi.yml)
5. Update README with install instructions
6. Verify all 187 tests pass with `uv run pytest`

### Files to Change
| File | Action |
|------|--------|
| `pyproject.toml` | Update build-system, remove setuptools config |
| `uv.lock` | Commit (already exists locally) |
| `.github/workflows/ci.yml` | Replace pip with uv, add setup-uv action |
| `.github/workflows/publish-to-pypi.yml` | Replace `python -m build` with `uv build` |
| `README.md` | Update install instructions |
| `setup.py` | DELETE if exists |
| `setup.cfg` | DELETE if exists |

### Testing Strategy
1. Pre-migration: verify current build works
2. Post-migration: `uv build` produces valid artifacts
3. CI matrix: all Python 3.8-3.12 pass with uv
4. Publishing: inspect wheel contents, test install paths
