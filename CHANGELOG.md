# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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
- Comments not included (planned for v0.2.0)
- Jira Cloud only (Server/Data Center support planned)

[Unreleased]: https://github.com/chrisbyboston/jarkdown/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/chrisbyboston/jarkdown/releases/tag/v0.1.0
