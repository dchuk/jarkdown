# Repository Cleanup and Stabilization Plan

## 1. Introduction

This document outlines the action plan to address the issues identified during the codebase review of August 15, 2025. The previous refactoring effort (`TECHNICAL-DESIGN-V2.md`) successfully restructured the application into modular components but failed to correctly implement the top-level error handling and integration testing strategy.

The result is a codebase that is structurally sound at the unit level but fails its own integration tests, indicating a critical disconnect between the application's behavior and its tests.

This plan provides a clear path to fix the failing tests, align the application's error handling with the design, and ensure the repository is in a stable, maintainable state.

## 2. Root Cause Analysis

The investigation surfaced two primary categories of issues:

1.  **Incorrect CLI Test Assertions:** The tests for successful CLI execution incorrectly assert that the `main()` function should raise a `SystemExit` exception. The function is designed to exit cleanly (with an implicit exit code of 0) on success, which is standard practice. The tests are fundamentally flawed in their expectation.
2.  **Flawed Error Handling Logic:** The `main()` function's `try...except` block does not consistently call `sys.exit(1)` on all error paths as intended by the technical design. This leads to unexpected behavior in error scenarios, such as the one identified in `test_missing_environment_variables`.
3.  **Minor Test Data Mismatch:** A single component test is failing due to a simple inconsistency between the mock data and the test's assertion.

## 3. Action Plan

The following steps will be executed to resolve these issues.

### Step 1: Fix the Component Test (`test_components.py`)

-   **Task:** Correct the data mismatch in `test_complete_markdown_structure`.
-   **Action:**
    1.  Open `tests/data/issue_with_attachments.json`.
    2.  Locate the `priority` field and change its `name` from `"High"` to `"Medium"`.
    3.  This will align the test fixture with the test's expectation and resolve the failure.

### Step 2: Correct the CLI Tests (`test_cli.py`)

-   **Task:** Align the CLI tests with the actual behavior of the `main()` function for successful execution.
-   **Action:**
    1.  For all tests that verify **successful** outcomes (e.g., `test_successful_download_with_attachments`, `test_markdown_content_correct`, etc.), remove the `with pytest.raises(SystemExit)` block.
    2.  Instead, directly call `main()`. Since a successful run does not raise an exception, the absence of one will constitute a pass for that part of the test.
    3.  The existing assertions that check for file creation and content remain correct and will be kept.

### Step 3: Fix the `main()` Function's Error Handling (`jarkdown.py`)

-   **Task:** Ensure the `main()` function reliably exits with a non-zero status code on any captured exception.
-   **Action:**
    1.  Review the main `try...except` block in the `main()` function.
    2.  Ensure that every `except` block (e.g., for `JarkdownError`, `Exception`, etc.) concludes with `sys.exit(1)`.
    3.  Modify the logic for the environment variable check. It should be inside the `try` block and raise a `ConfigurationError` if variables are missing, allowing the main `except` block to handle the exit uniformly.

### Step 4: Validate All Fixes

-   **Task:** Run the entire test suite to confirm that all tests now pass.
-   **Action:**
    1.  Execute `pytest` from the project root.
    2.  Verify that the output shows "32 passed".

## 4. Expected Outcome

Upon completion of this plan, the following will be true:

-   The project's test suite will be stable and reliable ("green").
-   The application's error handling will be robust and predictable.
-   The codebase will accurately reflect the goals of the `TECHNICAL-DESIGN-V2.md` document.
-   The repository will be in a clean, maintainable state, ready for future development.
