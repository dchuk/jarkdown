# Technical Design: Automated PyPI Publishing with GitHub Actions

## 1. Introduction

This document outlines the design and implementation of a GitHub Actions workflow to automate the process of building and publishing the `jarkdown` package to the Python Package Index (PyPI).

The goal is to create a secure, reliable, and automated pipeline that triggers upon the creation of a new release in the GitHub repository.

## 2. Workflow Design

The workflow will be defined in a new YAML file located at `.github/workflows/publish-to-pypi.yml`.

### 2.1. Triggering Event

The workflow will be configured to run only when a new release is **published** on GitHub. This provides a deliberate, manual gate for releases while automating the repetitive and error-prone steps of building and uploading.

```yaml
on:
  release:
    types: [published]
```

### 2.2. Security and Authentication

To ensure a high level of security, the workflow will use **Trusted Publishing**. This is the most secure method for publishing to PyPI from GitHub Actions and is recommended by the Python Packaging Authority (PyPA).

-   **Permissions:** The job will be granted the `id-token: write` permission. This allows the workflow to request a short-lived OpenID Connect (OIDC) token from GitHub.
-   **Authentication:** The `pypa/gh-action-pypi-publish` action will use this OIDC token to authenticate with PyPI. PyPI will be configured to trust tokens coming from this specific repository and workflow, eliminating the need to store long-lived API tokens as GitHub Secrets.

### 2.3. Job Steps

The workflow will consist of a single job named `publish` that performs the following steps:

1.  **Checkout Code:** Check out the repository's source code.
2.  **Set up Python:** Install a specific, stable version of Python (e.g., 3.11).
3.  **Install Dependencies:** Install the necessary build tools (`build`).
4.  **Build Package:** Run `python -m build` to create the source distribution (`.tar.gz`) and wheel (`.whl`) files.
5.  **Publish to PyPI:** Use the `pypa/gh-action-pypi-publish` action to upload the built packages to PyPI.

### 2.4. Complete Workflow File

```yaml
# .github/workflows/publish-to-pypi.yml
name: Publish to PyPI

on:
  release:
    types: [published]

jobs:
  publish:
    runs-on: ubuntu-latest
    permissions:
      # This permission is mandatory for trusted publishing
      id-token: write
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: "3.11"

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install build

      - name: Build package
        run: python -m build

      - name: Publish package to PyPI
        uses: pypa/gh-action-pypi-publish@release/v1
```

## 3. PyPI Configuration

To enable trusted publishing, the following configuration must be applied on the PyPI project settings page:

1.  Navigate to the project's "Publishing" settings on PyPI (`https://pypi.org/manage/project/jarkdown/settings/publishing/`).
2.  Add a new "Trusted publisher" with the following details:
    *   **Owner:** `chrisbyboston`
    *   **Repository name:** `jarkdown`
    *   **Workflow name:** `publish-to-pypi.yml`

This one-time setup establishes the trust relationship between PyPI and the GitHub Actions workflow.
