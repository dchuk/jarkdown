
# Technical Design Document: Publishing `jarkdown` to PyPI

## 1. Introduction

This document outlines the technical steps and considerations for packaging the `jarkdown` command-line tool and publishing it to the Python Package Index (PyPI). The goal is to make `jarkdown` easily installable via `pip` for end-users.

## 2. Current State Analysis

The `jarkdown` project is a well-structured Python application. The current packaging and distribution configuration is managed through `pyproject.toml`, which is the modern standard for Python packaging.

### Key Files and their Status:

-   **`pyproject.toml`**: This file is comprehensive and correctly configured for `setuptools`. It includes:
    -   Project metadata (name, version, description, license, etc.).
    -   Dependencies and optional dependencies.
    -   Entry points for the command-line script.
    -   Package discovery settings.
    -   Pytest and coverage configurations.
-   **`MANIFEST.in`**: This file is correctly configured to include necessary non-Python files such as `README.md`, `LICENSE`, and `CHANGELOG.md` in the source distribution.
-   **`src/` layout**: The source code is located in a `src/` directory, which is a best practice for Python packaging.
-   **`README.md`**: The README is well-written and suitable for use as the long description on PyPI.
-   **`LICENSE`**: An MIT license is present.

The project is in a near-perfect state for publishing. The existing configuration adheres to modern Python packaging standards, and no major changes are required.

## 3. Proposed Changes and Additions

While the project is in great shape, the following minor additions and steps are required to ensure a smooth and professional publishing process.

### 3.1. Update `pyproject.toml` for Long Description Content Type

The `readme` key in `pyproject.toml` is correctly set to `README.md`. However, to ensure that PyPI renders the Markdown correctly, we should explicitly set the `long_description_content_type`.

**File to modify**: `pyproject.toml`

**Change**: Add the following line to the `[project]` section:

```toml
dynamic = ["long_description"]
```

And add this new section to the file:
```toml
[tool.setuptools.dynamic]
long_description = {file = "README.md", content-type = "text/markdown"}
```
This change tells `setuptools` to dynamically read the `README.md` file and set the content type to `text/markdown`, which PyPI will use to render the description.

### 3.2. Verify and Update Version Number

The current version in `pyproject.toml` is `1.1.0`. Before publishing, we should confirm that this is the correct version to be released. If any changes have been made since the last version, the version number should be incremented according to [Semantic Versioning](https://semver.org/).

**File to modify**: `pyproject.toml`

**Action**:
-   Review the `CHANGELOG.md` to determine if the version number needs to be updated.
-   If so, update the `version` field in the `[project]` section.

### 3.3. Create a `~/.pypirc` file

To publish to PyPI, you need to have an account and an API token. This information should be stored in a `~/.pypirc` file.

**Action**:
1.  Create an account on [PyPI](https://pypi.org/).
2.  Under your account settings, create an API token.
3.  Create a file at `~/.pypirc` with the following content:

```ini
[pypi]
  username = __token__
  password = <your-pypi-api-token>
```

This file will be used by the publishing tool (`twine`) to authenticate with PyPI.

## 4. Publishing Workflow

The following steps will be taken to build and publish the package to PyPI.

### 4.1. Install Publishing Tools

The `build` and `twine` packages are required for building and uploading the package.

**Command**:
```bash
pip install build twine
```

### 4.2. Clean Previous Builds

Before creating a new build, it's important to remove any old distribution files.

**Command**:
```bash
rm -rf dist/
```

### 4.3. Build the Package

The `build` tool will create the source distribution (`.tar.gz`) and the wheel (`.whl`) file in the `dist/` directory.

**Command**:
```bash
python -m build
```

### 4.4. Check the Distribution Files

Before uploading, it's a good practice to check the generated distribution files for any errors.

**Command**:
```bash
twine check dist/*
```

### 4.5. Publish to PyPI

Once the distribution files are verified, `twine` can be used to upload them to PyPI.

**Command**:
```bash
twine upload dist/*
```

This command will use the credentials from the `~/.pypirc` file to authenticate.

## 5. Post-Publishing Verification

After publishing, we should verify that the package is correctly listed on PyPI and can be installed.

1.  **Check the PyPI page**: Navigate to `https://pypi.org/project/jarkdown/` and verify that the project description, metadata, and version are correct.
2.  **Test installation**: Install the package from PyPI in a clean virtual environment.

**Commands**:
```bash
python3 -m venv test_env
source test_env/bin/activate
pip install jarkdown
jarkdown --version
```

This will confirm that the package was published successfully and is installable.

## 6. Summary of Actions

1.  **Modify `pyproject.toml`**: Add `dynamic = ["long_description"]` to the `[project]` section and a `[tool.setuptools.dynamic]` section to specify the long description content type.
2.  **Verify Version**: Check and update the version number in `pyproject.toml`.
3.  **Configure PyPI Credentials**: Create a `~/.pypirc` file with a PyPI API token.
4.  **Build**: Use `python -m build` to create the distribution files.
5.  **Publish**: Use `twine upload dist/*` to publish the package to PyPI.
6.  **Verify**: Check the PyPI page and test installation.
