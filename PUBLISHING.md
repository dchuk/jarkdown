# Publishing jarkdown to PyPI

This guide documents the process for publishing the `jarkdown` package to the Python Package Index (PyPI).

## Prerequisites

1. **PyPI Account**: Create an account at [pypi.org](https://pypi.org/)
2. **API Token**: Generate an API token from your PyPI account settings
3. **Configure Credentials**: Create a `~/.pypirc` file:

```ini
[pypi]
  username = __token__
  password = <your-pypi-api-token>
```

## Publishing Process

### 1. Update Version

Before publishing a new release:

1. Update the version in `pyproject.toml`
2. Update the `CHANGELOG.md` with release notes
3. Commit these changes

### 2. Build the Package

```bash
# Clean any previous builds
rm -rf dist/

# Build the distribution files
python -m build
```

This creates two files in the `dist/` directory:
- `jarkdown-X.Y.Z.tar.gz` (source distribution)
- `jarkdown-X.Y.Z-py3-none-any.whl` (wheel distribution)

### 3. Check the Distribution

Verify the package is ready for upload:

```bash
twine check dist/*
```

Both files should show "PASSED".

### 4. Upload to PyPI

```bash
twine upload dist/*
```

This will upload the package to PyPI using the credentials from `~/.pypirc`.

### 5. Verify the Release

1. Check the package page: https://pypi.org/project/jarkdown/
2. Test installation in a clean environment:

```bash
# Create a test environment
python3 -m venv test_env
source test_env/bin/activate

# Install from PyPI
pip install jarkdown

# Verify it works
jarkdown --version
```

## Development Installation

For local development, install in editable mode:

```bash
pip install -e ".[dev]"
```

## Troubleshooting

### Build Warnings

The build process may show deprecation warnings about the license format. These don't prevent publishing but should be addressed in future updates by using SPDX license expressions.

### Authentication Issues

If you encounter authentication errors:
1. Verify your API token is correct
2. Ensure the token has upload permissions
3. Check that `~/.pypirc` is properly formatted

## Version Management

Follow [Semantic Versioning](https://semver.org/):
- MAJOR version for incompatible API changes
- MINOR version for backwards-compatible functionality additions
- PATCH version for backwards-compatible bug fixes

## Release Checklist

- [ ] Update version in `pyproject.toml`
- [ ] Update `CHANGELOG.md` with release notes
- [ ] Run test suite: `pytest`
- [ ] Build package: `python -m build`
- [ ] Check package: `twine check dist/*`
- [ ] Upload to PyPI: `twine upload dist/*`
- [ ] Verify on PyPI website
- [ ] Test installation from PyPI
- [ ] Create git tag: `git tag v0.1.0`
- [ ] Push tag: `git push origin v0.1.0`
