# Architecture

This document describes the internal architecture of jarkdown, explaining how components work together to export Jira issues.

## Overview

jarkdown follows a modular async architecture with clear separation of concerns:

```
User Input → CLI (subcommand dispatch)
                   ↓
              ┌────┴────┐
              │ export   │ bulk    │ query   │ setup
              └────┬────┘
                   ↓
            async with JiraApiClient
                   ↓
         ┌─────────┼──────────┐
         ↓         ↓          ↓
    fetch_issue  fetch_fields  search_jql
         ↓         ↓
   AttachmentHandler  FieldMetadataCache
         ↓               ↓
   MarkdownConverter ← CustomFieldRenderer
         ↓
   File Output (.md + .json)
```

## Core Components

### CLI Layer (`jarkdown.py`)

The entry point and orchestrator of the application.

**Responsibilities:**
- Parse command-line arguments with subcommand dispatch (`export`, `bulk`, `query`, `setup`)
- Load environment configuration
- Coordinate workflow between components
- Handle all user-facing errors
- Control exit codes

**Key Functions:**
- `main()` - Entry point with backward-compatible shim (bare `PROJ-123` injects `export`)
- `export_issue()` - Async orchestrator for single-issue export
- `_handle_bulk()` / `_handle_query()` - Subcommand handlers
- `setup_configuration()` - Interactive `.env` wizard

**Design Decisions:**
- All `sys.exit()` calls happen here, not in component classes
- Components raise exceptions; CLI handles them
- `asyncio.run()` is called at the CLI boundary; all internal code is async
- Verbose output controlled at this layer

### API Client (`jira_api_client.py`)

Manages all communication with the Jira Cloud REST API v3.

**Class:** `JiraApiClient`

**Responsibilities:**
- Authenticate with Jira using Basic Auth via `aiohttp.BasicAuth`
- Fetch issue data via REST API v3
- Fetch field metadata for custom field resolution
- Search issues via JQL with `nextPageToken` pagination
- Stream attachment downloads
- Manage `aiohttp.ClientSession` lifecycle via async context manager

**Key Methods:**
- `__aenter__()` / `__aexit__()` - Session lifecycle with `TCPConnector` (limit 5 per host)
- `fetch_issue()` - Fetch complete issue data with `fields=*all` and `expand=renderedFields`
- `fetch_fields()` - Fetch all field definitions for custom field name resolution
- `search_jql()` - Paginated JQL search with retry support
- `download_attachment_stream()` - Stream download for attachments

**Design Decisions:**
- Returns raw JSON data without transformation
- Uses `aiohttp.ClientSession` with connection pooling via `TCPConnector`
- Raises specific exceptions for different failures (401 → `AuthenticationError`, 404 → `IssueNotFoundError`)
- JQL pagination uses `retry_with_backoff` for resilience

### Bulk Exporter (`bulk_exporter.py`)

Orchestrates concurrent export of multiple Jira issues.

**Class:** `BulkExporter`

**Responsibilities:**
- Manage concurrent issue exports with `asyncio.Semaphore`
- Collect results (successes and failures) using `asyncio.gather`
- Generate `index.md` summary table
- Continue-and-report on individual failures

**Key Methods:**
- `export_bulk()` - Export all issues concurrently, return (successes, failures) tuple
- `generate_index_md()` - Create Markdown summary table
- `write_index_md()` - Write index file to output directory

**Design Decisions:**
- Semaphore-based concurrency (configurable, default 3)
- Individual issue failures don't stop the batch
- Inlines `export_issue` logic to avoid circular imports
- Progress output via `\r` overwrite to stderr

### Retry Infrastructure (`retry.py`)

Provides exponential backoff with jitter for transient API errors.

**Key Components:**
- `RetryConfig` - Dataclass configuring max_retries (3), base_delay (1s), max_delay (60s), retryable status codes (429, 503, 504)
- `retry_with_backoff()` - Async retry decorator for coroutine functions
- `parse_retry_after()` - Parses `Retry-After` header (integer seconds or HTTP-date format)

**Design Decisions:**
- Jitter prevents thundering herd on concurrent retries
- `Retry-After` header honored on first retry attempt
- Non-retryable errors (401, 404) re-raised immediately

### Attachment Handler (`attachment_handler.py`)

Downloads and manages file attachments asynchronously.

**Class:** `AttachmentHandler`

**Responsibilities:**
- Download attachments from Jira via streaming
- Handle filename conflicts with numbered suffixes
- Track download progress (when verbose)
- Continue downloading remaining attachments on individual failure

**Key Methods:**
- `download_all_attachments()` - Sequential download of all attachments for an issue
- `download_attachment()` - Download a single attachment with conflict resolution

**Design Decisions:**
- Streaming downloads: buffers to memory then writes via `asyncio.to_thread`
- Preserves original filenames when possible
- Returns metadata about downloaded files (id, filename, mime_type, path)
- Continue-and-report: logs errors for failed downloads, continues with remaining

### Markdown Converter (`markdown_converter.py`)

Converts Jira issue data to clean, comprehensive Markdown.

**Class:** `MarkdownConverter`

**Responsibilities:**
- Convert HTML to Markdown using markdownify
- Parse Atlassian Document Format (ADF) to Markdown
- Update attachment URLs to local references
- Compose full document with YAML frontmatter and all sections
- Render custom fields with type-aware formatting

**Key Methods:**
- `compose_markdown()` - Main conversion method producing the complete document
- `convert_html_to_markdown()` - HTML to Markdown via markdownify
- `_parse_adf_to_markdown()` - Recursive ADF node parser
- `replace_attachment_links()` - Replace Jira URLs with local paths
- `_generate_metadata_dict()` - Generate comprehensive YAML frontmatter
- `_compose_comments_section()` - Convert and format comments with ADF support
- `_compose_linked_issues_section()` - Group links by relationship type
- `_compose_subtasks_section()` - List subtasks with status
- `_compose_worklogs_section()` - Time tracking table
- `_compose_custom_fields_section()` - Custom fields with renderer

**ADF Node Support:**
Paragraph, text (with marks: bold, italic, code, link), heading, bulletList, orderedList, codeBlock, blockquote, table, mediaSingle, media, mediaGroup, mention, hardBreak, panel, expand, rule, emoji, status, date, inlineCard, taskList, taskItem, decisionList, decisionItem

**Design Decisions:**
- Uses markdownify for robust HTML conversion
- Handles multiple Jira URL patterns for attachment replacement
- ADF parser is recursive and handles all documented node types
- Creates readable, well-organized output with consistent structure

### Field Metadata Cache (`field_cache.py`)

XDG-compliant cache for Jira field definitions.

**Class:** `FieldMetadataCache`

**Responsibilities:**
- Cache field metadata with 24-hour TTL
- Resolve field IDs to display names (e.g., `customfield_10001` → `Story Points`)
- Retrieve field schema for type-aware rendering
- Store cache in platform-appropriate directory via `platformdirs`

**Design Decisions:**
- 24-hour TTL balances freshness with API call reduction
- Per-domain cache isolation
- Lazy-loaded field map for efficient lookups
- Graceful degradation: uses stale cache or raw IDs if refresh fails

### Config Manager (`config_manager.py`)

Manages field selection configuration from TOML file and CLI args.

**Class:** `ConfigManager`

**Responsibilities:**
- Load `.jarkdown.toml` configuration file
- Merge CLI flags with file-based settings (CLI overrides file)
- Provide `should_include_field()` predicate for filtering

**Design Decisions:**
- CLI args take full precedence over config file
- Uses `tomllib` (3.11+) or `tomli` fallback
- Graceful degradation if TOML parsing unavailable

### Custom Field Renderer (`custom_field_renderer.py`)

Renders custom field values with type-aware formatting.

**Class:** `CustomFieldRenderer`

**Responsibilities:**
- Schema-based rendering (string, number, date, option, user, array)
- Shape-based fallback rendering (dicts, lists, ADF documents)
- ADF rich text custom field support via injected parser

**Design Decisions:**
- Schema-first approach uses Jira field type metadata
- Shape inspection as fallback handles unknown schema types
- Supports nested ADF documents in custom fields

### Exception Hierarchy (`exceptions.py`)

Custom exceptions for clear error handling.

```
JarkdownError (base)
├── ConfigurationError     # Missing/invalid config
├── JiraApiError           # API communication issues
│   ├── AuthenticationError    # 401 responses
│   └── IssueNotFoundError     # 404 responses
└── AttachmentDownloadError    # Download failures
```

**Design Decisions:**
- Specific exceptions for different failures
- Inherit from common base class
- Include relevant context (status codes, filenames)
- Allow granular error handling at CLI layer

## Data Flow

### Single Issue Export

```python
# User runs: jarkdown export PROJ-123 --output /path

1. CLI validates arguments, backward-compat shim
2. Load .env file with python-dotenv
3. Verify required environment variables

# Async boundary (asyncio.run)
4. async with JiraApiClient(domain, email, token) as client:
5.     issue_data = await client.fetch_issue("PROJ-123")
6.     attachment_handler = AttachmentHandler(client)
7.     downloaded = await attachment_handler.download_all_attachments(...)
8.     field_cache = FieldMetadataCache(domain)
9.     if stale: fields = await client.fetch_fields(); cache.save(fields)
10.    config = ConfigManager().get_field_filter(include, exclude)
11.    markdown = MarkdownConverter.compose_markdown(issue_data, downloaded,
                                                     field_cache, field_filter)
12.    Write PROJ-123.json and PROJ-123.md
```

### Bulk Export

```python
# User runs: jarkdown bulk PROJ-1 PROJ-2 PROJ-3 --concurrency 3

1. async with JiraApiClient as client:
2.     exporter = BulkExporter(client, concurrency=3)
3.     semaphore = asyncio.Semaphore(3)
4.     tasks = [_export_one(key) for key in issue_keys]
5.     results = await asyncio.gather(*tasks)
6.     Each _export_one acquires semaphore, exports, releases
7.     Failures captured as ExportResult(success=False)
8.     Write index.md summary
9.     Print summary to stderr
```

### JQL Query Export

```python
# User runs: jarkdown query 'project = FOO AND status = Done' --max-results 100

1. async with JiraApiClient as client:
2.     issues = await client.search_jql(jql, max_results=100)
3.     # Automatic pagination via nextPageToken
4.     issue_keys = [i["key"] for i in issues]
5.     exporter = BulkExporter(client, concurrency=3)
6.     successes, failures = await exporter.export_bulk(issue_keys)
7.     Write index.md with JQL metadata
8.     Print summary
```

## Configuration Management

Environment variables are loaded using python-dotenv:

```python
from dotenv import load_dotenv
load_dotenv()
domain = os.getenv('JIRA_DOMAIN')
```

Field metadata is cached using platformdirs:

```python
from platformdirs import user_config_dir
cache_dir = Path(user_config_dir("jarkdown"))
# e.g., ~/.config/jarkdown/ on Linux, ~/Library/Application Support/jarkdown/ on macOS
```

**Security:** Credentials never logged or included in error messages.

## Error Handling Strategy

Each layer handles errors appropriately:

1. **Components** - Raise specific exceptions
2. **CLI** - Catches and presents user-friendly messages
3. **Bulk** - Continue-and-report for individual failures
4. **Retry** - Automatic retry for transient API errors
5. **Exit Codes** - 0 for success, 1 for failures

```python
# Example error flow
try:
    await api_client.fetch_issue(issue_key)
except AuthenticationError:
    print("Error: Invalid credentials", file=sys.stderr)
    sys.exit(1)
except IssueNotFoundError:
    print(f"Error: Issue {issue_key} not found", file=sys.stderr)
    sys.exit(1)
```

## Performance Considerations

### Async Architecture

- **aiohttp with connection pooling**: `TCPConnector(limit_per_host=5)` for efficient connection reuse
- **Semaphore concurrency**: Configurable concurrent exports (default 3) prevent overwhelming Jira API
- **Non-blocking I/O**: File writes delegated to thread pool via `asyncio.to_thread`

### Memory Efficiency

- **Streaming Downloads**: Attachments buffered then written via thread
- **Lazy Processing**: Field metadata loaded on demand
- **Session Reuse**: Single `aiohttp.ClientSession` for all requests within a context

### Resilience

- **Retry with backoff**: Exponential backoff (1s, 2s, 4s) with jitter for 429/503/504 errors
- **Retry-After**: Honors server-specified wait times
- **Continue-and-report**: Bulk/query exports continue past individual failures

## Testing Architecture

### Async Test Patterns

Tests use `pytest-asyncio` with `asyncio_mode = "auto"` and `aioresponses` for mocking:

```python
from aioresponses import aioresponses

async def test_fetch_issue(api_client):
    """Test that fetch_issue returns issue data."""
    with aioresponses() as m:
        m.get(
            "https://test.atlassian.net/rest/api/3/issue/TEST-1",
            payload={"key": "TEST-1", "fields": {...}}
        )
        result = await api_client.fetch_issue("TEST-1")
        assert result["key"] == "TEST-1"
```

### Unit Tests

Each component tested in isolation with mocked dependencies.

### Integration Tests

CLI tested with mocked async components (in-process, no subprocess).

## Design Principles

1. **Single Responsibility**: Each class has one job
2. **Dependency Injection**: Components receive dependencies
3. **Fail Fast**: Validate early, fail with clear messages
4. **No Magic**: Explicit over implicit behavior
5. **Testability**: Easy to mock and test
6. **Continue-and-Report**: Don't let one failure stop everything

## Security Considerations

- **No Credential Storage**: Only in environment
- **No Credential Logging**: Filtered from all output
- **HTTPS Only**: All API communication encrypted
- **Token Authentication**: No password storage
- **Hidden Input**: Setup wizard uses `getpass` for API token

## Future Improvements

Potential architectural enhancements:

1. **Parallel Attachment Downloads**: Concurrent downloads within a single issue
2. **Incremental Export**: Track last export time, only re-export changed issues
3. **Alternative Output Formats**: HTML, PDF via template system
4. **Plugin Architecture**: Allow custom processors and output formats
5. **Progress Bars**: Rich terminal UI for long operations

## Conclusion

The architecture prioritizes:
- **Simplicity**: Easy to understand and maintain
- **Modularity**: Components can be updated independently
- **Reliability**: Clear error handling, retry, and recovery
- **Performance**: Async I/O with concurrent exports
- **Extensibility**: Easy to add new features

This design makes jarkdown both powerful and maintainable.
