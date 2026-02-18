# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.2.0] - 2026-02-18

### Added
- **Subcommand CLI:** Restructured CLI with `export`, `bulk`, `query`, and `setup` subcommands (backward-compatible `jarkdown PROJ-123` still works)
- **Bulk Export:** Export multiple issues concurrently with `jarkdown bulk KEY1 KEY2 KEY3 --concurrency 5` and semaphore-limited parallelism
- **JQL Query Export:** Export issues matching JQL queries with `jarkdown query 'project = FOO AND status = Done' --max-results 100` and automatic pagination via `nextPageToken`
- **Setup Wizard:** Interactive `jarkdown setup` command to create `.env` file with guided prompts
- **Full Standard Field Coverage:** Exported metadata now includes project, status category, resolution, creator, affects/fix versions, due date, time tracking, progress, votes, watches, and all dates
- **Custom Field Support:** Type-aware rendering of Jira custom fields with schema-based formatting (options, users, arrays, dates, etc.)
- **ADF Parsing:** Full Atlassian Document Format parser supporting paragraphs, headings, lists, code blocks, blockquotes, tables, media, mentions, panels, expand sections, task lists, decision items, inline cards, emojis, and more
- **Field Metadata Caching:** XDG-compliant cache (`platformdirs`) for Jira field definitions with 24-hour TTL and `--refresh-fields` flag
- **Field Filtering:** Include/exclude custom fields via `--include-fields`, `--exclude-fields` CLI flags or `.jarkdown.toml` config file
- **Retry Infrastructure:** Exponential backoff with jitter for transient errors (429, 503, 504), `Retry-After` header parsing, configurable via `RetryConfig`
- **Linked Issues Section:** Grouped by relationship type (blocks, is blocked by, relates to, etc.)
- **Subtasks Section:** Listed with status and issue type
- **Worklogs Section:** Time tracking table with author, time spent, date, and comment
- **Environment Section:** Rendered from HTML or ADF
- **Index File:** `index.md` summary table generated for bulk and query exports
- **JSON Output:** Raw API response saved as `ISSUE-KEY.json` alongside the markdown file

### Changed
- **Async Rewrite:** Migrated from synchronous `requests` to fully async `aiohttp` with `asyncio.run()` at CLI boundary
- **API Version:** Updated from Jira REST API v2 to v3
- **CLI Structure:** Restructured from single positional argument to subcommand-based interface
- **Connection Management:** `JiraApiClient` now uses async context manager (`async with`) for session lifecycle with connection pooling (`TCPConnector`)
- **Attachment Downloads:** Async streaming downloads with continue-and-report error handling
- **Markdown Converter:** Enhanced with ADF parsing, custom field rendering, and full field sections (Environment, Linked Issues, Subtasks, Worklogs, Custom Fields)

### Dependencies
- Added `aiohttp>=3.9.0` as primary HTTP client
- Added `platformdirs>=4.0.0` for XDG-compliant cache directory
- Added `tomli>=2.0.0` (Python < 3.11) for `.jarkdown.toml` config parsing
- Added `pytest-asyncio>=0.23.0` and `aioresponses>=0.7.6` for async test support
- Retained `requests>=2.28.0` for backward compatibility

### Known Limitations
- Jira Cloud only (Server/Data Center not supported)
- Attachment downloads are sequential per issue (parallel planned for v3)

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

[Unreleased]: https://github.com/chrisbyboston/jarkdown/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/chrisbyboston/jarkdown/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/chrisbyboston/jarkdown/releases/tag/v0.1.0
