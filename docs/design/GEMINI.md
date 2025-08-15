# GEMINI.md

## Project Overview

This project is a command-line tool named "Jira Download" that exports Jira Cloud issues to Markdown files. The tool fetches issue data from the Jira Cloud REST API, downloads all attachments, and converts the issue description from HTML to GitHub-flavored Markdown. The goal is to create a local, offline copy of a Jira issue with all its content and attachments preserved.

The project is written in Python and uses the following main technologies:

*   **`requests`**: For making HTTP requests to the Jira Cloud REST API.
*   **`markdownify`**: For converting HTML content to Markdown.
*   **`python-dotenv`**: For managing environment variables for Jira credentials.
*   **`pytest`**: For testing the application.

The application is structured around a `JiraDownloader` class, which encapsulates the logic for fetching, downloading, and converting Jira issues. The command-line interface is handled in the `main` function, which uses `argparse` to parse command-line arguments.

## Building and Running

### Prerequisites

*   Python 3.8+
*   Jira Cloud instance
*   Jira API token

### Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/chrisbyboston/jira-download.git
    cd jira-download
    ```

2.  **Set up a virtual environment:**
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Set up environment variables:**
    Create a `.env` file in the project root with your Jira credentials:
    ```
    JIRA_DOMAIN=your-company.atlassian.net
    JIRA_EMAIL=your-email@company.com
    JIRA_API_TOKEN=your-api-token
    ```

### Running the application

The application can be run directly from the command line:

```bash
./jira-download ISSUE-KEY
```

For example:

```bash
./jira-download PROJ-123
```

You can also specify an output directory:

```bash
./jira-download PROJ-123 --output ~/Documents/jira-exports
```

### Running tests

The project uses `pytest` for testing. To run the tests, first install the development dependencies:

```bash
pip install -r requirements.txt -e .[dev]
```

Then run the tests:

```bash
pytest
```

## Development Conventions

*   **Testing**: The project has a comprehensive test suite using `pytest`. Tests are located in the `tests` directory and are split into end-to-end CLI tests (`test_cli.py`) and unit tests for the `JiraDownloader` class (`test_jira_downloader.py`). The tests use mock data from the `tests/data` directory to simulate API responses.
*   **Code Style**: The code follows standard Python conventions (PEP 8).
*   **Dependencies**: Project dependencies are managed in `requirements.txt` and `pyproject.toml`.
*   **CI/CD**: The project has a CI workflow defined in `.github/workflows/ci.yml` that runs tests on every push and pull request.
