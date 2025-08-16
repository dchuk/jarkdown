# Technical Design v2: Refactoring for Maintainability

## Introduction

This document outlines the technical design for the next version of `jarkdown`. It directly addresses the issues raised in the `CODEBASE_REVIEW.md` document and provides a clear path forward for improving the project's architecture, maintainability, and testing strategy.

## 1. Dependency Management Strategy

- **Decision:** `pyproject.toml` will be the single source of truth for all project dependencies.
- **Action Items:**
    - The `requirements.txt` file will be deleted to eliminate redundancy and version conflicts.
    - All development and production dependencies will be managed within the `pyproject.toml` file.

## 2. Application Architecture Refactor

The current monolithic `Jarkdowner` class will be decomposed into smaller, more focused components, each with a single responsibility.

### Proposed Architecture

The application logic will be split across three new, distinct classes:

1.  **`JiraApiClient`**:
    - **Responsibility:** All communication with the Jira Cloud REST API.
    - **Tasks:** Manages the `requests` session, authentication, and API endpoints. Methods like `fetch_issue()` will return raw JSON data. It will not perform any data transformation or file I/O.

2.  **`AttachmentHandler`**:
    - **Responsibility:** Manages the downloading and saving of issue attachments.
    - **Tasks:** Takes attachment metadata from the `JiraApiClient`, downloads the files, and handles any potential filename conflicts in the output directory.

3.  **`MarkdownConverter`**:
    - **Responsibility:** Converts the Jira issue data into a final Markdown file.
    - **Tasks:** Takes the raw issue data and the list of downloaded attachments, converts the description from HTML to Markdown, replaces attachment links, and composes the final `.md` file structure.

The main `jarkdown.py` script will be simplified to act as an orchestrator, coordinating the work between these components.

## 3. Error Handling Framework

- **Problem:** The current use of `sys.exit(1)` within the core logic makes the code difficult to reuse or test.
- **Solution:** A robust exception-based error handling framework will be implemented.
    - **Custom Exceptions:** A new `exceptions.py` module will define custom exceptions (e.g., `JiraApiError`, `AttachmentDownloadError`, `ConfigurationError`).
    - **Raising Exceptions:** The refactored classes (`JiraApiClient`, etc.) will `raise` these specific exceptions when an error occurs.
    - **Handling Exceptions:** The top-level `main()` function will be the *only* place that catches these exceptions. It will contain a `try...except` block to provide user-friendly error messages to the console and call `sys.exit(1)`.

## 4. Testing Strategy Enhancements

### CLI Testing

- **Decision:** The CLI tests will be refactored to run in-process, which is faster, more reliable, and resolves the current CI failures.
- **Action Items:**
    - Remove the use of `subprocess` in `test_cli.py`.
    - Modify the tests to call the `main()` function directly.
    - Use `unittest.mock.patch` to mock `sys.argv` and other global objects.
    - Capture `stdout` and `stderr` to assert the correctness of the console output.

### Development Environment

- **Decision:** The standard development setup will use an editable install.
- **Action Items:**
    - The `CONTRIBUTING.md` and `README.md` files will be updated to specify `pip install -e .[dev]` as the required installation command for developers.
    - All manual `sys.path` manipulations will be removed from the `tests/` directory.

## 5. Documentation Policy

- **Decision:** We will consolidate formal design documentation while explicitly preserving the logs of our AI-assisted development sessions.
- **Action Items:**
    - This document, `TECHNICAL_DESIGN_V2.md`, officially supersedes the original `TECHNICAL-DESIGN-DOCUMENT.md`. The old file will be removed.
    - The files `GEMINI.md` and `CLAUDE.md` will be kept in the repository's root. Their stated purpose is to serve as a historical record and artifact of the AI-driven development and brainstorming sessions that have shaped this project. They are not to be treated as formal design documents.

## 6. Code Style and Conventions

- **Test Naming and Comments:** Test function names will be made more descriptive (e.g., `test_fetch_issue_handles_404_error`). Redundant docstrings and comments that merely repeat the function name (e.g., `"""Test Case 5.8.1: ..."""`) will be removed to improve readability. Docstrings will only be used to explain *why* a complex test is necessary, not *what* it is doing.
