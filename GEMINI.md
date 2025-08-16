# Project Overview

This project is a command-line tool named "Jira Download" that exports Jira Cloud issues to Markdown files. It fetches issue data from the Jira Cloud REST API, downloads all attachments, and converts the issue description and comments from HTML to GitHub-flavored Markdown. The tool is written in Python and uses the `requests` library for API communication, `markdownify` for HTML to Markdown conversion, and `python-dotenv` for managing environment variables.

The main entry point for the application is `src/jira_download/jira_download.py`, which contains the command-line interface logic. The project is structured into several modules:

- `jira_api_client.py`: Handles all communication with the Jira Cloud REST API.
- `attachment_handler.py`: Manages the downloading and saving of issue attachments.
- `markdown_converter.py`: Converts Jira issue data into Markdown format.
- `exceptions.py`: Defines custom exceptions for the application.

# Building and Running

## Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/chrisbyboston/jarkdown.git
    cd jarkdown
    ```

2.  **Create a virtual environment and install dependencies:**
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    pip install -e ".[dev]"
    ```

3.  **Set up environment variables:**
    Copy the `.env.example` file to `.env` and fill in your Jira credentials:
    ```bash
    cp .env.example .env
    ```
    You will need to provide your `JIRA_DOMAIN`, `JIRA_EMAIL`, and `JIRA_API_TOKEN`.

## Running the tool

To export a Jira issue, use the `jarkdown` command:

```bash
jarkdown ISSUE-KEY
```

For example:

```bash
jarkdown PROJ-123
```

You can also specify an output directory:

```bash
jarkdown PROJ-123 --output ~/Documents/jira-exports
```

## Running tests

The project uses `pytest` for testing. To run the test suite:

```bash
pytest
```

To run tests with coverage:

```bash
pytest --cov=src/jira_download --cov-report=term-missing
```

# Development Conventions

-   **Linting and Formatting:** The project uses `ruff` for linting and formatting.
-   **Pre-commit Hooks:** Pre-commit hooks are used to ensure code quality before committing. To install the hooks, run:
    ```bash
    pre-commit install
    ```
-   **Testing:** All new functionality should be accompanied by tests. The tests are located in the `tests` directory.
-   **Commit Messages:** Commit messages should be clear and descriptive.
-   **Documentation:** The project's documentation is located in the `docs` directory and is built using Sphinx.
