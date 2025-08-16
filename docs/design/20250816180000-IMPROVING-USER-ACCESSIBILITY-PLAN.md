# Technical Plan: Improving Accessibility for Non-Technical Users

## 1. Overview

This document outlines the technical steps required to make the `jarkdown` command-line tool significantly more accessible to non-technical users. The primary goal is to eliminate complex, developer-centric setup procedures and provide clear, beginner-friendly documentation.

The core strategy involves two main initiatives:
1.  **Publishing the package to PyPI** to enable a simple, one-command installation.
2.  **Rewriting key documentation** to be explicit, cross-platform, and free of technical jargon.

## 2. Phase 1: Packaging and Publishing to PyPI

Publishing to the Python Package Index (PyPI) is the highest-impact change we can make. It simplifies the installation process from a multi-step, source-code-dependent procedure to a single command.

### 2.1. Update `pyproject.toml` for Distribution

The `pyproject.toml` file needs to be updated to include metadata for PyPI and define the command-line script entry point.

**Action Items:**
1.  **Add Project URLs:** Include links to the documentation and GitHub repository.
2.  **Define Classifiers:** Add PyPI classifiers to improve searchability and categorization.
3.  **Configure Entry Point:** Define the `jarkdown` command as a console script. This is critical for making the command available globally after a `pip install`.

**Example `pyproject.toml` additions:**

```toml
[project.urls]
"Homepage" = "https://github.com/chrisbyboston/jarkdown"
"Documentation" = "https://jarkdown.readthedocs.io/"
"Bug Tracker" = "https://github.com/chrisbyboston/jarkdown/issues"

[project.scripts]
jarkdown = "jarkdown.jarkdown:main"

[project]
# ... existing metadata ...
classifiers = [
    "Development Status :: 4 - Beta",
    "Intended Audience :: Developers",
    "Intended Audience :: End Users/Desktop",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.8",
    "Programming Language :: Python :: 3.9",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Operating System :: OS Independent",
    "Topic :: Utilities",
    "Topic :: Office/Business :: Groupware",
]
```

### 2.2. Build and Publish the Package

**Action Items:**
1.  **Install Build Tools:**
    ```bash
    pip install build twine
    ```
2.  **Build the Distribution:**
    ```bash
    python3 -m build
    ```
    This command will create a `dist/` directory containing the source archive (`.tar.gz`) and a wheel (`.whl`) file.
3.  **Register on PyPI:** Create an account on [PyPI](https://pypi.org/) if one does not already exist.
4.  **Upload to PyPI:**
    ```bash
    python3 -m twine upload dist/*
    ```
    This will prompt for PyPI credentials and upload the package. It is recommended to use an API token for this process in CI/CD environments.

## 3. Phase 2: Documentation Overhaul

With a simple installation path available, the documentation must be updated to guide users through it.

### 3.1. Update the Main `README.md`

The README is the first point of contact. It should prioritize the easy installation method.

**Action Items:**
1.  **Prominently feature the `pip install` method:** Move the `pip install jarkdown` command to the top of the "Installation" section and remove the "Coming Soon" note.
2.  **De-emphasize "Install from Source":** Move the source installation steps to a subsection titled "For Developers (Installing from Source)" or similar.
3.  **Simplify Configuration Instructions:**
    *   Rephrase the `.env` setup to be tool-agnostic. Instead of `cp .env.example .env`, instruct users to "Create a file named `.env` in the same directory where you will run the `jarkdown` command."
    *   Provide a clear, copy-pasteable template for the `.env` file's contents.
4.  **Add Cross-Platform Instructions:**
    *   For the developer setup, explicitly provide the Windows command for activating the virtual environment: `venv\Scripts\activate`.

### 3.2. Create a "Getting Started for Beginners" Guide

A dedicated guide in the Sphinx documentation will provide a safe, detailed walkthrough for users who are new to command-line tools.

**Action Items:**
1.  **Create a new file:** `docs/source/beginners_guide.rst` (or `.md`).
2.  **Add content covering:**
    *   **How to Install Python:** Link to the official Python downloads page and beginner-friendly guides for both Windows and macOS.
    *   **How to Open a Terminal:** Explain how to open Command Prompt/PowerShell on Windows and Terminal on macOS.
    *   **Installation:** Walk through the `pip install jarkdown` command.
    *   **Configuration:** A step-by-step guide on how to create the `.env` file using a simple text editor (like Notepad or TextEdit), with clear examples.
    *   **First Use:** Show the user how to run `jarkdown --version` to verify the installation and `jarkdown PROJ-123` as a first real command.
3.  **Link to the new guide:** Add a prominent link to this new guide in the main `README.md` and the documentation's index page.

## 4. Phase 3: Improving the CLI Experience (Optional but Recommended)

To further improve usability, the tool itself can be made more helpful.

### 4.1. Add a `--setup` Command

An interactive setup command would be the most user-friendly way to handle configuration.

**Action Items:**
1.  **Implement a `--setup` or `init` argument** in `jarkdown.py` using `argparse`.
2.  When run, this command should:
    *   Prompt the user for their Jira Domain, Email, and API Token.
    *   Provide a link to the Atlassian page for generating API tokens.
    *   Automatically create the `.env` file in the current directory with the provided values.

### 4.2. Enhance Error Handling

The tool should provide helpful, actionable error messages.

**Action Items:**
1.  **Check for `.env` file:** If the `.env` file is not found, catch the error and print a message like: "Configuration file `.env` not found. Please run `jarkdown --setup` or create it manually."
2.  **Validate Environment Variables:** On startup, check that the required variables (`JIRA_DOMAIN`, etc.) are present and not empty. If not, provide a clear error message indicating what is missing.
