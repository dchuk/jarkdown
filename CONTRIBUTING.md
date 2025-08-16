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

3. **Create a virtual environment**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

4. **Install dependencies**:
   ```bash
   pip install -e ".[dev]"  # Install package in editable mode with dev dependencies
   ```

5. **Install pre-commit hooks**:
   ```bash
   pre-commit install
   ```

6. **Create a branch** for your feature or fix:
   ```bash
   git checkout -b feature/your-feature-name
   ```

## Running Tests

Before submitting a pull request, make sure all tests pass:

```bash
# Run all tests
pytest

# Run with coverage report
pytest --cov=src/jarkdown --cov-report=term-missing

# Run specific test file
pytest tests/test_cli.py

# Run with verbose output
pytest -v
```

Our CI pipeline requires:
- All tests must pass
- Code coverage should not decrease
- No linting errors (if linter is configured)

## Pull Request Process

1. **Ensure your code follows the existing style** in the project

2. **Update the README.md** with details of changes to the interface, if applicable

3. **Add tests** for any new functionality

4. **Update documentation** as needed (see Documentation section below)

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

## Documentation

The project documentation is built with Sphinx and hosted on [ReadTheDocs](https://jarkdown.readthedocs.io/).

### Building Documentation Locally

1. **Install documentation dependencies**:
   ```bash
   pip install -r docs/requirements.txt
   ```

2. **Build the documentation**:
   ```bash
   cd docs
   make clean
   make html
   ```

3. **View the documentation**:
   Open `docs/build/html/index.html` in your browser.

### Documentation Guidelines

- Update docstrings for any new or modified functions/classes
- Use Google-style docstrings for consistency
- Update relevant `.md` or `.rst` files in `docs/source/`
- Add examples for new features
- Ensure all links work correctly
- Update the API reference if you add new public APIs

### Documentation Structure

- `docs/source/` - Source files for documentation
- `docs/source/conf.py` - Sphinx configuration
- `docs/source/index.rst` - Main documentation index
- `docs/source/api_reference.rst` - Auto-generated API docs
- `docs/requirements.txt` - Documentation dependencies

## Style Guide

### Python Style

- Follow [PEP 8](https://www.python.org/dev/peps/pep-0008/)
- Use meaningful variable names
- Add docstrings to all functions and classes
- Keep functions small and focused
- Maximum line length: 100 characters

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

Thank you for contributing! 🎉
