# CI Workflow Fix Plan

**Date:** 2025-08-15
**Author:** Gemini

## 1. Problem Statement

The `test` job in the current CI workflow (`.github/workflows/ci.yml`) is configured to install Python dependencies using the command `pip install -r requirements.txt`.

This project does not use a `requirements.txt` file. Instead, dependencies are managed in `pyproject.toml` in accordance with modern Python packaging standards (PEP 621).

As a result, the `test` job will fail with a "file not found" error for `requirements.txt`, preventing the test suite from running in the CI pipeline.

## 2. Proposed Solution

The `Install dependencies` step within the `test` job will be modified to correctly install dependencies from `pyproject.toml`.

The incorrect commands:
```yaml
run: |
  python -m pip install --upgrade pip
  pip install -r requirements.txt
  pip install pytest pytest-mock pytest-cov
```

Will be replaced with a single, correct command:
```yaml
run: |
  python -m pip install --upgrade pip
  pip install .[dev]
```

This command instructs `pip` to install the project in the current directory (`.`) along with the optional dependencies defined under the `[dev]` key in `pyproject.toml`. This is the standard and correct way to install a package and its test dependencies for this project structure.

## 3. Implementation Steps

1.  Read the content of `.github/workflows/ci.yml`.
2.  Locate the `Install dependencies` step within the `test` job.
3.  Replace the existing `run` block with the corrected one.
4.  Commit the change.

## 4. Expected Outcome

- The `test` job will successfully install all required project and development dependencies from `pyproject.toml`.
- The CI pipeline will proceed to the "Run tests with coverage" step and execute the test suite across all specified Python versions.
- The overall CI workflow will function as intended, providing automated testing, linting, and security scanning.
