# Changelog

All notable changes to jarkdown will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Comprehensive Sphinx documentation
- Read the Docs integration
- API reference documentation with autodoc
- Architecture documentation
- Detailed usage guides
- Configuration documentation

### Changed
- Restructured codebase into proper Python package
- Updated development setup to use `pip install .[dev]`
- Improved error handling and exceptions
- Enhanced markdown formatting for comments

### Fixed
- CI workflow updated to use pyproject.toml

## [1.0.0] - 2024-01-15

### Added
- Initial release
- Core functionality to export Jira issues to Markdown
- Attachment downloading and organization
- HTML to Markdown conversion
- Command-line interface
- Support for environment-based configuration
- Comprehensive test suite
- GitHub Actions CI/CD pipeline

### Features
- Export single Jira issues with `jarkdown ISSUE-KEY`
- Download all attachments automatically
- Convert Jira HTML to clean Markdown
- Update attachment links to local references
- Verbose mode for detailed output
- Custom output directory support

## Version History

### Pre-release Development

- Initial prototype and proof of concept
- Basic API integration
- Attachment handling implementation
- Markdown conversion development
- Test suite creation
- Documentation writing
