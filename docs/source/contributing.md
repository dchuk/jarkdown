# Contributing to Jarkdown

First off, thank you for considering contributing to Jarkdown! It's people like you that make this tool better for everyone.

## How Can I Contribute?

### Reporting Bugs

Before creating bug reports, please check existing issues as you might find out that you don't need to create one. When you are creating a bug report, please include as many details as possible:

* **Use a clear and descriptive title** for the issue to identify the problem
* **Describe the exact steps which reproduce the problem** in as much detail as possible
* **Provide specific examples to demonstrate the steps**
* **Describe the behavior you observed after following the steps** and point out what exactly is the problem with that behavior
* **Explain which behavior you expected to see instead and why**
* **Include your environment details** (Python version, OS, Jira Cloud version if relevant)

### Suggesting Enhancements

Enhancement suggestions are tracked as GitHub issues. When creating an enhancement suggestion, please include:

* **Use a clear and descriptive title** for the issue to identify the suggestion
* **Provide a step-by-step description of the suggested enhancement** in as much detail as possible
* **Provide specific examples to demonstrate the steps** or mock-ups if applicable
* **Describe the current behavior** and **explain which behavior you expected to see instead** and why
* **Explain why this enhancement would be useful** to most users

### Your First Code Contribution

Unsure where to begin contributing? You can start by looking through these `beginner` and `help-wanted` issues:

* [Beginner issues](https://github.com/chrisbyboston/jarkdown/labels/beginner) - issues which should only require a few lines of code
* [Help wanted issues](https://github.com/chrisbyboston/jarkdown/labels/help%20wanted) - issues which need extra attention

## Development Setup

1. **Fork the repository** on GitHub

2. **Clone your fork locally**:
   ```bash
   git clone https://github.com/YOUR-USERNAME/jarkdown.git
   cd jarkdown
   ```

3. **Install dependencies** (uv creates and manages the virtual environment automatically):
   ```bash
   uv sync --dev
   ```

4. **Set up pre-commit hooks** (one-time setup):
   ```bash
   pre-commit install
   ```
   This will automatically run linting and tests before each commit to ensure code quality.

5. **Create a branch** for your feature or fix:
   ```bash
   git checkout -b feature/your-feature-name
   ```

## Setting Up Pre-commit Hooks

After setting up your development environment, run the following command **once** to install the pre-commit hooks:

```bash
pre-commit install
```

This installs Git hooks that will automatically run before each commit to:
- Run `ruff` to check and fix code style issues
- Run `pytest` to ensure all tests pass

If either check fails, the commit will be aborted, and you'll see the error output in your terminal. Fix the issues and try committing again.

You can also manually run the hooks on all files at any time:
```bash
pre-commit run --all-files
```

## Running Tests

Before submitting a pull request, make sure all tests pass:

```bash
# Run all tests
uv run pytest

# Run with coverage report
uv run pytest --cov=src/jarkdown --cov-report=term-missing

# Run specific test file
uv run pytest tests/test_cli.py
uv run pytest tests/test_components.py

# Run with verbose output
uv run pytest -v
```

Our CI pipeline requires:
- All tests must pass
- Code coverage should not decrease
- No linting errors

## Pull Request Process

1. **Ensure your code follows the existing style** in the project

2. **Update the README.md** with details of changes to the interface, if applicable

3. **Add tests** for any new functionality

4. **Update documentation** as needed

5. **Ensure all tests pass** locally

6. **Write a good commit message**:
   - Use the present tense ("Add feature" not "Added feature")
   - Use the imperative mood ("Move cursor to..." not "Moves cursor to...")
   - Limit the first line to 72 characters or less
   - Reference issues and pull requests liberally after the first line

7. **Create the Pull Request**:
   - Fill in the PR template
   - Link to the issue being addressed
   - Include screenshots for UI changes
   - Request review from maintainers

8. **Address review feedback** promptly

## Style Guide

### Python Style

- Follow [PEP 8](https://www.python.org/dev/peps/pep-0008/)
- Use meaningful variable names
- Add docstrings to all functions and classes
- Keep functions small and focused
- Maximum line length: 100 characters

### Docstring Format

We use Google-style docstrings:

```python
def function_name(param1: str, param2: int) -> bool:
    """Brief description of function.

    More detailed explanation if needed.

    Args:
        param1: Description of first parameter.
        param2: Description of second parameter.

    Returns:
        Description of return value.

    Raises:
        ValueError: When invalid input provided.
    """
```

### Commit Messages

We follow conventional commits format:

```
type(scope): subject

body

footer
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Test additions or changes
- `chore`: Maintenance tasks

Example:
```
feat(export): add support for exporting comments

- Fetch comments from Jira API
- Include comments in markdown output
- Add --include-comments flag

Closes #123
```

## Project Structure

Understanding the codebase:

```
src/jarkdown/
├── jarkdown.py              # Main CLI entry point (subcommand dispatch)
├── jira_api_client.py       # Async Jira API interaction (aiohttp)
├── attachment_handler.py    # Async attachment downloading
├── markdown_converter.py    # HTML/ADF to Markdown conversion
├── bulk_exporter.py         # Concurrent multi-issue export
├── retry.py                 # Exponential backoff retry infrastructure
├── config_manager.py        # .jarkdown.toml configuration
├── custom_field_renderer.py # Type-aware custom field rendering
├── field_cache.py           # XDG-compliant field metadata cache
├── exceptions.py            # Custom exception hierarchy
tests/
├── test_cli.py              # CLI integration tests
├── test_components.py       # Unit tests for components
└── data/                    # JSON fixtures for mocked API responses
docs/
└── source/                  # Sphinx documentation
pyproject.toml               # Project configuration and dependencies
```

## Testing Guidelines

### Writing Tests

- Write tests for all new functionality
- Use descriptive test names that explain what's being tested
- Use pytest fixtures for common setup
- Mock external dependencies (API calls, file I/O)
- Use `pytest-asyncio` for async test functions and `aioresponses` for mocking HTTP calls

Example async test:

```python
from aioresponses import aioresponses

async def test_fetch_issue_returns_data(api_client):
    """Test that fetch_issue returns issue data."""
    with aioresponses() as m:
        m.get(
            "https://test.atlassian.net/rest/api/3/issue/TEST-1",
            payload={"key": "TEST-1", "fields": {"summary": "Test"}}
        )
        result = await api_client.fetch_issue("TEST-1")
        assert result["key"] == "TEST-1"
```

### Test Coverage

Aim for high test coverage:
- New features should have >90% coverage
- Bug fixes should include regression tests
- Edge cases should be tested

## Additional Notes

### Issue and Pull Request Labels

* `bug` - Something isn't working
* `enhancement` - New feature or request
* `documentation` - Improvements or additions to documentation
* `duplicate` - This issue or pull request already exists
* `good first issue` - Good for newcomers
* `help wanted` - Extra attention is needed
* `invalid` - This doesn't seem right
* `question` - Further information is requested
* `wontfix` - This will not be worked on

## Recognition

Contributors will be recognized in our README.md file. Thank you for your contributions!

## Questions?

Feel free to open an issue with your question or reach out to the maintainers directly.

Thank you for contributing!
