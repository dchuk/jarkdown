# Jarkdown - Export Jira Issues to Markdown

[![Documentation Status](https://readthedocs.org/projects/jarkdown/badge/?version=latest)](https://jarkdown.readthedocs.io/en/latest/?badge=latest)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue)](https://www.python.org/downloads/)
[![Tests](https://img.shields.io/badge/tests-230%20passing-brightgreen)](https://github.com/chrisbyboston/jarkdown/actions)
[![Coverage](https://img.shields.io/badge/coverage-230%20tests-green)](https://github.com/chrisbyboston/jarkdown/actions)

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
- **Bulk Export:** Export multiple issues concurrently with `jarkdown bulk KEY1 KEY2 --concurrency 5`.
- **JQL Query Export:** Export issues matching JQL queries with `jarkdown query 'project = FOO AND status = Done'`.
- **Rich Metadata:** Exports comprehensive YAML frontmatter including project, status category, time tracking, votes, watches, issue links, due dates, and more.
- **Custom Field Support:** Type-aware rendering of Jira custom fields with configurable include/exclude filtering.
- **ADF Parsing:** Full Atlassian Document Format support for descriptions and comments (paragraphs, headings, lists, code blocks, tables, media, mentions, panels, and more).
- **Async Processing:** Built on `aiohttp` for concurrent API calls and efficient bulk operations.
- **Retry & Rate Limiting:** Exponential backoff with jitter for transient errors (429, 503, 504) and `Retry-After` header support.
- **Preserves Formatting:** Converts Jira's HTML to GitHub-flavored Markdown, keeping headings, lists, code blocks, and tables intact.
- **Embeds Local Links:** Automatically references downloaded attachments with local links in the Markdown file.
- **Field Filtering:** Include or exclude custom fields via CLI flags or `.jarkdown.toml` config file.

## Installation

### Quick Install (Recommended)

Install as an isolated tool with [uv](https://docs.astral.sh/uv/):
```bash
uv tool install jarkdown
```

### Alternative: pipx

```bash
pipx install jarkdown
```

### Fallback: pip

```bash
pip install jarkdown
```

### Configuration

After installation, run the setup wizard to configure your Jira credentials:

```bash
jarkdown setup
```

Or create a `.env` file manually in the directory where you'll run jarkdown:

```
JIRA_DOMAIN=your-company.atlassian.net
JIRA_EMAIL=your-email@example.com
JIRA_API_TOKEN=your-api-token-here
```

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

2. Install dependencies (uv creates and manages the virtual environment automatically):
```bash
uv sync --dev
```

3. Set up your `.env` file as described above

## Usage

### Single Issue Export

```bash
# Export a single issue (subcommand form)
jarkdown export PROJ-123

# Backward-compatible shorthand
jarkdown PROJ-123

# Export to a specific directory
jarkdown export PROJ-123 --output ~/Documents/jira-exports

# Enable verbose logging
jarkdown export PROJ-123 --verbose
```

### Bulk Export

```bash
# Export multiple issues concurrently
jarkdown bulk PROJ-1 PROJ-2 PROJ-3

# Control concurrency and output location
jarkdown bulk PROJ-1 PROJ-2 PROJ-3 --concurrency 5 --output ~/exports

# Group into a named batch directory
jarkdown bulk PROJ-1 PROJ-2 --batch-name sprint-23
```

### JQL Query Export

```bash
# Export all issues matching a JQL query
jarkdown query 'project = FOO AND status = Done'

# Limit results (--limit and --max-results are equivalent)
jarkdown query 'project = FOO AND sprint in openSprints()' --limit 100
jarkdown query 'project = FOO AND sprint in openSprints()' --max-results 100

# With concurrency control
jarkdown query 'assignee = currentUser()' --concurrency 5
```

### Custom Field Filtering

```bash
# Include only specific custom fields
jarkdown export PROJ-123 --include-fields "Story Points,Sprint"

# Exclude specific custom fields
jarkdown export PROJ-123 --exclude-fields "Internal Notes,Dev Notes"
```

Or configure in `.jarkdown.toml`:
```toml
[fields]
exclude = ["Internal Notes", "Dev Notes"]
```

### Other Commands

```bash
# Interactive setup wizard
jarkdown setup

# Show version
jarkdown --version

# Show help
jarkdown --help
```

## Output Structure

The tool creates a directory named after the issue key containing:
- A markdown file with the issue content
- All attachments downloaded from the issue

Single issue example:
```
PROJ-123/
├── PROJ-123.md       # Issue content in markdown
├── diagram.png       # Downloaded attachments
├── report.pdf
└── ...
```

Pass `--include-json` to also save the raw Jira API response:
```
PROJ-123/
├── PROJ-123.md
├── PROJ-123.json     # Raw Jira API response (opt-in)
└── ...
```

Bulk/query export example:
```
output-dir/
├── index.md          # Summary table of all exported issues
├── PROJ-1/
│   ├── PROJ-1.md
│   └── ...
├── PROJ-2/
│   ├── PROJ-2.md
│   └── ...
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
status_category: In Progress
priority: High
resolution: null
project: My Project
project_key: PROJ
assignee: John Doe
reporter: Jane Smith
creator: Jane Smith
labels:
  - backend
  - performance
components:
  - API
  - Database
parent_key: PROJ-100
parent_summary: Parent epic title
affects_versions:
  - '1.0'
fix_versions:
  - '1.1'
created_at: '2025-01-15T10:30:00.000+0000'
updated_at: '2025-01-20T14:45:00.000+0000'
resolved_at: null
duedate: '2025-02-01'
original_estimate: 2d
time_spent: 1d 4h
remaining_estimate: 4h
progress: 60
aggregate_progress: 45
votes: 3
watches: 5
---
```

### Markdown Content
- Issue title with link to Jira
- Description with preserved formatting
- Environment section
- Linked Issues grouped by relationship type
- Subtasks with status
- Worklogs table with author, time, and comments
- Custom Fields section (when present)
- Comments section with all comments (author, date, and content)
- Attachments section with all files

Images are embedded inline, other files are linked.

## Requirements

- Python 3.8+
- Jira Cloud instance
- Jira API token with read permissions

## Dependencies

- `aiohttp` - Async HTTP client for API calls
- `markdownify` - HTML to Markdown conversion
- `python-dotenv` - Environment variable management
- `PyYAML` - YAML frontmatter generation
- `platformdirs` - XDG-compliant cache directory paths
- `tomli` - TOML config parsing (Python < 3.11; built-in `tomllib` on 3.11+)

## Limitations

- Requires Jira Cloud (not Server/Data Center)
- Attachment downloads are sequential per issue

## Future Enhancements

- Parallel attachment downloads within a single issue
- Incremental/delta export (only re-export changed issues)
- Alternative output formats (HTML, PDF)
- Hierarchical export (epics with all linked stories)

## Contributing

We welcome contributions! Here's how to get started:

### Development Setup

1. **Fork and clone** the repository:
```bash
git clone https://github.com/YOUR-USERNAME/jarkdown.git
cd jarkdown
```

2. **Install dependencies** (uv manages the virtual environment automatically):
```bash
uv sync --dev
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
uv run pytest
uv run pytest --cov=src/jarkdown --cov-report=term-missing
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
uv run pytest

# Run with coverage
uv run pytest --cov=src/jarkdown --cov-report=term-missing

# Run specific test file
uv run pytest tests/test_cli.py
```

### Reporting Issues

Please use the [GitHub issue tracker](https://github.com/chrisbyboston/jarkdown/issues) to report bugs or request features.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
