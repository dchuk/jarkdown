# Plan: Pre-commit Hooks for Automated Quality Checks

**Date:** 2025-08-15
**Author:** Gemini

## 1. Summary

To improve code quality and ensure that tests and linters are run before code is committed, this plan outlines the implementation of automated pre-commit hooks using the `pre-commit` framework.

This framework will automatically run `ruff` for linting and `pytest` for testing every time a developer attempts to make a commit. If either the linter or the test suite fails, the commit will be aborted, preventing broken or non-compliant code from entering the version history.

## 2. Rationale

-   **Early Bug Detection:** Catching errors on a developer's local machine is faster and cheaper than catching them in a CI pipeline.
-   **Enforce Code Style:** Automatically enforces a consistent code style across all contributions.
-   **Improve CI Efficiency:** Reduces the number of CI pipeline failures caused by simple linting or testing errors.
-   **Standardized Workflow:** Provides a sharable, version-controlled configuration that ensures all contributors run the same checks.

## 3. Implementation Steps

### Step 1: Add `pre-commit` as a Development Dependency

The `pre-commit` tool needs to be added to the project's development dependencies.

1.  **Modify `pyproject.toml`:**
    *   Locate the `[project.optional-dependencies]` section.
    *   Add `"pre-commit>=2.0.0"` to the `dev` list.

### Step 2: Create the Configuration File

The `pre-commit` framework is configured using a YAML file in the project root.

1.  **Create `.pre-commit-config.yaml`:**
    *   This file will define the hooks that the framework will manage and run.

2.  **Configure the Hooks:**
    *   The configuration will include two main hooks:
        1.  A hook for the `ruff` linter to check for style and quality issues.
        2.  A local hook that runs `pytest` to execute the entire test suite.

    *   **Proposed `.pre-commit-config.yaml` content:**
        ```yaml
        # .pre-commit-config.yaml
        repos:
          # Hook for Ruff Linter
          - repo: https://github.com/astral-sh/ruff-pre-commit
            rev: v0.5.0 # Use a recent, stable version
            hooks:
              - id: ruff
                args: [--fix, --exit-non-zero-on-fix]
              - id: ruff-format

          # Hook for running the test suite
          - repo: local
            hooks:
              - id: pytest
                name: Run Pytest
                entry: poetry run pytest # Or `pytest` if not using Poetry
                language: system
                types: [python]
                pass_filenames: false # Run against the whole suite, not just changed files
                always_run: true      # Ensure it runs on every commit
        ```
    *Note: The `entry` for the pytest hook will need to be adjusted based on the project's specific environment runner (e.g., `venv/bin/pytest` or just `pytest` if the virtual environment is expected to be active).*

### Step 3: Document the Setup for Developers

To make this useful, developers need to know how to activate it. This information will be added to the new Sphinx documentation.

1.  **Update `contributing.md` (in `docs/source`):**
    *   Add a new section titled "Setting Up Pre-commit Hooks".
    *   This section will instruct contributors to run the following command **once** after cloning the repository and setting up their environment:
        ```bash
        pre-commit install
        ```
    *   Explain that after this one-time setup, the checks will run automatically on every `git commit`.

## 4. Expected Outcome

-   When a developer runs `git commit`, `ruff` will first lint the staged files, automatically fixing issues where possible.
-   If linting succeeds, `pytest` will then run the entire test suite.
-   If both hooks pass, the commit will be created successfully.
-   If either hook fails, the commit will be aborted, and the developer will see the error output in their terminal, prompting them to fix the issue before they can commit.
-   This will lead to a cleaner commit history and a more stable `main` branch.
