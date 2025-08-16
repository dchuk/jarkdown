# Jira Download - Export Jira Issues to Markdown

[![Documentation Status](https://readthedocs.org/projects/jira-download/badge/?version=latest)](https://jira-download.readthedocs.io/en/latest/?badge=latest)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue)](https://www.python.org/downloads/)
[![Tests](https://img.shields.io/badge/tests-passing-brightgreen)](https://github.com/chrisbyboston/jira-download/actions)
[![Coverage](https://img.shields.io/badge/coverage-87%25-green)](https://github.com/chrisbyboston/jira-download/actions)

A command-line tool that exports Jira Cloud issues into markdown files with all attachments downloaded locally and referenced inline.

## Documentation

Full documentation is available at [jira-download.readthedocs.io](https://jira-download.readthedocs.io/), including:

- [Installation Guide](https://jira-download.readthedocs.io/en/latest/installation.html)
- [Usage Guide](https://jira-download.readthedocs.io/en/latest/usage.html)
- [Configuration](https://jira-download.readthedocs.io/en/latest/configuration.html)
- [API Reference](https://jira-download.readthedocs.io/en/latest/api_reference.html)
- [Contributing](https://jira-download.readthedocs.io/en/latest/contributing.html)

## Features

- Fetches Jira issues via the Jira Cloud REST API
- Downloads all attachments to a local folder
- Converts issue descriptions from HTML to GitHub-flavored Markdown
- Preserves formatting (headings, lists, code blocks, tables)
- Embeds images inline and links other file types
- Maintains the same visual structure as in Jira

## Installation

### Quick Install (Coming Soon)
```bash
pip install jira-download
```

### Install from Source

1. Clone the repository:
```bash
git clone https://github.com/chrisbyboston/jira-download.git
cd jira-download
```

2. Install dependencies:
```bash
python3 -m venv venv
source venv/bin/activate
pip install -e ".[dev]"
```

3. Set up environment variables:

Copy the example configuration and fill in your Jira credentials:
```bash
cp .env.example .env
# Edit .env with your actual values
```

To get a Jira API token:
1. Go to https://id.atlassian.com/manage-profile/security/api-tokens
2. Click "Create API token"
3. Give it a name and copy the token

## Usage

Basic usage:
```bash
jira-download ISSUE-KEY
```

Examples:
```bash
# Download an issue to the current directory
jira-download PROJ-123

# Download to a specific directory
jira-download PROJ-123 --output ~/Documents/jira-exports

# Enable verbose logging
jira-download PROJ-123 --verbose

# Show version
jira-download --version
```

## Output Structure

The tool creates a directory named after the issue key containing:
- A markdown file with the issue content
- All attachments downloaded from the issue

Example:
```
PROJ-123/
├── PROJ-123.md       # Issue content in markdown
├── diagram.png       # Downloaded attachments
├── report.pdf
└── ...
```

## Markdown Format

The generated markdown includes:
- Issue title with link to Jira
- Metadata (Type, Status, Priority, Assignee, Reporter)
- Description with preserved formatting
- Attachments section with all files

Images are embedded inline, other files are linked.

## Requirements

- Python 3.8+
- Jira Cloud instance
- Jira API token with read permissions

## Dependencies

- `requests` - HTTP client for API calls
- `markdownify` - HTML to Markdown conversion
- `python-dotenv` - Environment variable management

## Limitations

- Currently supports single issue export only
- Comments are not included (planned for future)
- Requires Jira Cloud (not Server/Data Center)

## Future Enhancements

- Export multiple issues with JQL queries
- Include issue comments
- Support for bulk export
- Hierarchical export (epics with stories)
- Better ADF format handling

## Contributing

We welcome contributions! Here's how to get started:

### Development Setup

1. **Fork and clone** the repository:
```bash
git clone https://github.com/YOUR-USERNAME/jira-download.git
cd jira-download
```

2. **Create a virtual environment** and install dependencies:
```bash
python3 -m venv venv
source venv/bin/activate
pip install -e ".[dev]"
```

3. **Install pre-commit hooks**:
```bash
pre-commit install
```

### Making Changes

1. **Create a feature branch**:
```bash
git checkout -b feature/your-feature-name
```

2. **Make your changes** and ensure tests pass:
```bash
pytest
pytest --cov=src/jira_download --cov-report=term-missing
```

3. **Commit your changes** (pre-commit hooks will run automatically):
```bash
git add .
git commit -m "feat: describe your change"
```

4. **Push and create a pull request**:
```bash
git push origin feature/your-feature-name
```

Then open a pull request on GitHub.

### Code Style

- We use `ruff` for linting and formatting
- Pre-commit hooks ensure code quality
- Write clear, descriptive commit messages
- Add tests for new functionality
- Update documentation as needed

### Testing

Run the test suite:
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src/jira_download --cov-report=term-missing

# Run specific test file
pytest tests/test_cli.py
```

### Reporting Issues

Please use the [GitHub issue tracker](https://github.com/chrisbyboston/jira-download/issues) to report bugs or request features.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
