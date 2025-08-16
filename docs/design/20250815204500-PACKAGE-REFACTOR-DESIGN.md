# Technical Design: Python Packaging Refactor

## 1. Introduction

This document outlines the technical design for refactoring the `jarkdown` tool into a standard, installable Python package. During attempts to install the tool for global access using `pipx`, a `ModuleNotFoundError` was encountered. This error prevents the tool from running outside of its root development directory and indicates a fundamental issue with the project's structure.

The goal of this refactor is to adopt a standard Python packaging layout that enables robust, reliable installation and allows the `jarkdown` command to be executed from any directory on the user's system.

## 2. Problem Analysis

The current project structure is a "flat layout" where all Python source files (`jarkdown.py`, `jira_api_client.py`, etc.) reside in the project's root directory. The `pyproject.toml` file uses the `py-modules` directive in `[tool.setuptools]` to list these files as individual top-level modules.

When a tool like `pip` or `pipx` installs the project, it creates an executable script for `jarkdown` and places it on the system's `PATH`. However, the source modules are installed into a `site-packages` directory. When the `jarkdown` script runs, it can no longer find its sibling modules (like `jira_api_client`) because they are not in the same directory, leading to the `ModuleNotFoundError`.

## 3. Solution Overview

The solution is to restructure the project from a flat layout to a standard "src layout" or "package layout". All Python source code will be moved into a dedicated package directory. This allows setuptools to correctly discover, install, and manage the code as a single, cohesive package.

The high-level steps are:
1.  **Create a new package directory** (e.g., `jarkdown_pkg`) to house all source code.
2.  **Move all `.py` source files** into this new directory.
3.  **Create an `__init__.py` file** within the package directory to mark it as a Python package.
4.  **Update `pyproject.toml`** to discover the new package and correctly configure the command-line script entry point.
5.  **Update imports** within the source code to be relative to the new package structure.
6.  **Verify the fix** by performing a clean installation with `pipx`.

## 4. Detailed Implementation Plan

### Step 4.1: Restructure the File System

A new directory will be created, and all Python source files will be moved.

-   **Action:**
    1.  Create a new directory: `mkdir jarkdown_pkg`
    2.  Move the relevant Python files:
        ```bash
        mv jarkdown.py jira_api_client.py attachment_handler.py markdown_converter.py exceptions.py jarkdown_pkg/
        ```
    3.  Create an empty initializer file: `touch jarkdown_pkg/__init__.py`

### Step 4.2: Update `pyproject.toml`

The `pyproject.toml` file needs to be modified to recognize the new package structure and update the script's entry point.

-   **Action:** Modify the `[project.scripts]` and `[tool.setuptools]` sections.

-   **Current `pyproject.toml` sections:**
    ```toml
    [project.scripts]
    jarkdown = "jarkdown:main"

    [tool.setuptools]
    py-modules = ["jarkdown", "jira_api_client", "attachment_handler", "markdown_converter", "exceptions"]
    ```

-   **New `pyproject.toml` sections:**
    ```toml
    [project.scripts]
    jarkdown = "jarkdown_pkg.jarkdown:main"

    [tool.setuptools]
    packages = ["jarkdown_pkg"]
    ```
    *   The `[project.scripts]` entry point is updated to point to the `main` function within the `jarkdown.py` module inside the `jarkdown_pkg` package.
    *   The `py-modules` directive is replaced with `packages = ["jarkdown_pkg"]`, which tells setuptools to find and include the specified package directory.

### Step 4.3: Update Source Code Imports

The main script needs to be updated to use relative imports to find its sibling modules within the package.

-   **Action:** Modify the import statements in `jarkdown_pkg/jarkdown.py`.

-   **Current Imports in `jarkdown.py`:**
    ```python
    from jira_api_client import JiraApiClient
    from attachment_handler import AttachmentHandler
    from markdown_converter import MarkdownConverter
    from exceptions import JarkdownError
    ```

-   **New Imports in `jarkdown_pkg/jarkdown.py`:**
    ```python
    from .jira_api_client import JiraApiClient
    from .attachment_handler import AttachmentHandler
    from .markdown_converter import MarkdownConverter
    from .exceptions import JarkdownError
    ```
    *   The leading dot (`.`) makes the imports relative, ensuring that Python looks for the modules within the same package (`jarkdown_pkg`).

## 5. Verification Strategy

The success of the refactor will be verified by installing and running the tool in an isolated environment.

1.  **Uninstall any previous versions:**
    ```bash
    pipx uninstall jarkdown
    ```
2.  **Perform a fresh installation** from the project's root directory using `pipx`:
    ```bash
    pipx install .
    ```
3.  **Verify the command runs** from a different directory (e.g., the user's home directory):
    ```bash
    cd ~
    jarkdown --help
    ```
    *   The command should execute successfully and display the help message without any `ModuleNotFoundError`.

## 6. Expected Outcome

After this refactor, the `jarkdown` project will be structured as a standard, distributable Python package. It will be installable via `pip` and `pipx`, and the `jarkdown` command will be globally available to the user, running correctly from any directory in the filesystem.
