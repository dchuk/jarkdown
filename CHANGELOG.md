# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- **Enhanced Metadata Export:** All available issue metadata is now exported into a YAML frontmatter block at the top of the Markdown file. This includes labels, components, versions, parent issue links, resolution status, and all relevant dates.
- **Comment Export:** The tool now fetches and exports all issue comments, including the author, timestamp, and full body content.

### Changed
- The `fields` parameter in the Jira API call was changed from a predefined list to `*all` to fetch complete issue data.
- The Markdown output format was changed from simple key-value pairs to a structured YAML frontmatter block for metadata.

### Dependencies
- Added `PyYAML` for reliable YAML serialization.

## [0.1.0] - 2025-08-16

### Added
- Initial release of jarkdown
- Export single Jira Cloud issues to Markdown format
- Download and embed all attachments locally
- Convert HTML descriptions to clean Markdown
- Preserve formatting (headings, lists, code blocks, tables)
- Replace Jira attachment URLs with local file references
- Support for custom output directories
- Verbose logging mode
- Environment-based configuration (.env file)
- Comprehensive test suite with 87% code coverage
- Full documentation (README, Technical Design, Test Design)
- MIT License
- Contributing guidelines
- GitHub Actions CI/CD pipeline
- Modern Python packaging with pyproject.toml
- Support for Jira Cloud REST API v3
- Command-line interface

### Security
- API tokens stored in environment variables
- No credentials in code or logs
- Secure HTTPS connections to Jira Cloud

### Known Limitations
- Single issue export only (bulk export planned)
- Jira Cloud only (Server/Data Center support planned)

[Unreleased]: https://github.com/chrisbyboston/jarkdown/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/chrisbyboston/jarkdown/releases/tag/v0.1.0
