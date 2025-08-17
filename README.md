# Jarkdown - Export Jira Issues to Markdown

[![Documentation Status](https://readthedocs.org/projects/jarkdown/badge/?version=latest)](https://jarkdown.readthedocs.io/en/latest/?badge=latest)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue)](https://www.python.org/downloads/)
[![Tests](https://img.shields.io/badge/tests-passing-brightgreen)](https://github.com/chrisbyboston/jarkdown/actions)
[![Coverage](https://img.shields.io/badge/coverage-87%25-green)](https://github.com/chrisbyboston/jarkdown/actions)

A command-line tool that exports Jira Cloud issues into clean, portable Markdown files with all attachments.

Jarkdown bridges the gap between Jira and your local development environment. It makes it easy to archive tickets, share them with others, or work with issues offline.

## Documentation

Full documentation is available at [jarkdown.readthedocs.io](https://jarkdown.readthedocs.io/), including:

- [Getting Started for Beginners](https://jarkdown.readthedocs.io/en/latest/beginners_guide.html) - Step-by-step guide for new users
- [Installation Guide](https://jarkdown.readthedocs.io/en/latest/installation.html)
- [Usage Guide](https://jarkdown.readthedocs.io/en/latest/usage.html)
- [Configuration](https://jarkdown.readthedocs.io/en/latest/configuration.html)
- [Contributing](https://jarkdown.readthedocs.io/en/latest/contributing.html)

## Key Features

- **Complete Export:** Fetches all issue metadata, descriptions, comments, and downloads all attachments locally.
- **Rich Metadata:** Exports comprehensive metadata in YAML frontmatter including labels, components, versions, parent issues, and more.
- **Comment Support:** Exports all issue comments with author, date, and formatted content, including support for Atlassian Document Format (ADF).
- **Preserves Formatting:** Converts Jira's HTML to GitHub-flavored Markdown, keeping headings, lists, code blocks, and tables intact.
- **Embeds Local Links:** Automatically references downloaded attachments with local links in the Markdown file.
- **Simple and Fast:** A command-line tool that is easy to script and integrate into your workflow.

## Installation

### Quick Install (Recommended)

Install directly from PyPI with a single command:
```bash
pip install jarkdown
```

### Configuration

After installation, you need to set up your Jira credentials. Create a file named `.env` in the directory where you'll run the `jarkdown` command:

1. Create the `.env` file with the following content:
```
JIRA_DOMAIN=your-company.atlassian.net
JIRA_EMAIL=your-email@example.com
JIRA_API_TOKEN=your-api-token-here
```

2. Replace the values with your actual Jira information:
   - `JIRA_DOMAIN`: Your Atlassian domain (e.g., company.atlassian.net)
   - `JIRA_EMAIL`: The email address you use to log into Jira
   - `JIRA_API_TOKEN`: Your personal API token (see below)

### Getting Your Jira API Token

1. Go to https://id.atlassian.com/manage-profile/security/api-tokens
2. Click "Create API token"
3. Give it a name (e.g., "jarkdown")
4. Copy the token and paste it into your `.env` file

### For Developers (Installing from Source)

If you want to contribute to the project or need the latest development version:

1. Clone the repository:
```bash
git clone https://github.com/chrisbyboston/jarkdown.git
cd jarkdown
```

2. Create a virtual environment and install dependencies:

**On macOS/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
pip install -e ".[dev]"
```

**On Windows:**
```bash
python -m venv venv
venv\Scripts\activate
pip install -e ".[dev]"
```

3. Set up your `.env` file as described above

## Usage

Basic usage:
```bash
jarkdown ISSUE-KEY
```

Examples:
```bash
# Download an issue to the current directory
jarkdown PROJ-123

# Download to a specific directory
jarkdown PROJ-123 --output ~/Documents/jira-exports

# Enable verbose logging
jarkdown PROJ-123 --verbose

# Show version
jarkdown --version
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

### YAML Frontmatter with Complete Metadata
```yaml
---
key: PROJ-123
summary: Issue title
type: Bug
status: In Progress
priority: High
assignee: John Doe
reporter: Jane Smith
labels:
  - backend
  - performance
components:
  - API
  - Database
parent_key: PROJ-100
created_at: 2025-01-15T10:30:00.000+0000
updated_at: 2025-01-20T14:45:00.000+0000
---
```

### Markdown Content
- Issue title with link to Jira
- Description with preserved formatting
- Comments section with all comments (author, date, and content)
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
- `PyYAML` - YAML frontmatter generation

## Limitations

- Currently supports single issue export only
- Requires Jira Cloud (not Server/Data Center)

## Future Enhancements

- Export multiple issues with JQL queries
- Support for bulk export
- Hierarchical export (epics with stories)
- Better ADF format handling
- Custom field support

## Contributing

We welcome contributions! Here's how to get started:

### Development Setup

1. **Fork and clone** the repository:
```bash
git clone https://github.com/YOUR-USERNAME/jarkdown.git
cd jarkdown
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
pytest --cov=src/jarkdown --cov-report=term-missing
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
pytest --cov=src/jarkdown --cov-report=term-missing

# Run specific test file
pytest tests/test_cli.py
```

### Reporting Issues

Please use the [GitHub issue tracker](https://github.com/chrisbyboston/jarkdown/issues) to report bugs or request features.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
