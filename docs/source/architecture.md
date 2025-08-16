# Architecture

This document describes the internal architecture of jira-download, explaining how components work together to export Jira issues.

## Overview

jira-download follows a modular architecture with clear separation of concerns:

```
User Input → CLI → API Client → Data Processing → File Output
                         ↓
                  Attachment Handler
                         ↓
                  Markdown Converter
```

## Core Components

### CLI Layer (`jira_download.py`)

The entry point and orchestrator of the application.

**Responsibilities:**
- Parse command-line arguments
- Load environment configuration
- Coordinate workflow between components
- Handle all user-facing errors
- Control exit codes

**Key Functions:**
- `main()` - Entry point, argument parsing
- `export_issue()` - Orchestrates the export workflow

**Design Decisions:**
- All `sys.exit()` calls happen here, not in component classes
- Components raise exceptions; CLI handles them
- Verbose output controlled at this layer

### API Client (`jira_api_client.py`)

Manages all communication with the Jira REST API.

**Class:** `JiraApiClient`

**Responsibilities:**
- Authenticate with Jira using Basic Auth
- Fetch issue data via REST API
- Handle API errors and rate limiting
- Manage HTTP session for connection pooling

**Key Methods:**
- `__init__()` - Initialize with credentials
- `get_issue()` - Fetch complete issue data
- `_make_request()` - Internal method for API calls

**Design Decisions:**
- Returns raw JSON data without transformation
- Uses requests.Session for connection reuse
- Raises specific exceptions for different failures
- No retry logic (kept simple)

### Attachment Handler (`attachment_handler.py`)

Downloads and manages file attachments.

**Class:** `AttachmentHandler`

**Responsibilities:**
- Download attachments from Jira
- Handle filename conflicts
- Use streaming for memory efficiency
- Track download progress (when verbose)

**Key Methods:**
- `__init__()` - Initialize with auth session
- `download_attachments()` - Main download orchestrator
- `_download_file()` - Stream download implementation
- `_get_unique_filename()` - Handle naming conflicts

**Design Decisions:**
- Streaming downloads for large files
- Automatic retry on failure (up to 3 times)
- Preserves original filenames when possible
- Returns metadata about downloaded files

### Markdown Converter (`markdown_converter.py`)

Converts Jira HTML content to clean Markdown.

**Class:** `MarkdownConverter`

**Responsibilities:**
- Convert HTML to Markdown using markdownify
- Update attachment URLs to local references
- Format issue metadata
- Structure the final document

**Key Methods:**
- `convert_issue()` - Main conversion method
- `_update_attachment_urls()` - Replace Jira URLs with local paths
- `_format_comments()` - Convert and format comments
- `_create_metadata_section()` - Generate issue header

**Design Decisions:**
- Uses markdownify for robust HTML conversion
- Handles multiple Jira URL patterns
- Preserves formatting and structure
- Creates readable, well-organized output

### Exception Hierarchy (`exceptions.py`)

Custom exceptions for clear error handling.

```python
JiraDownloadError (base)
├── ConfigurationError     # Missing/invalid config
├── JiraApiError           # API communication issues
│   ├── AuthenticationError    # 401 responses
│   └── IssueNotFoundError     # 404 responses
└── AttachmentDownloadError    # Download failures
```

**Design Decisions:**
- Specific exceptions for different failures
- Inherit from common base class
- Include relevant context in messages
- Allow graceful error handling

## Data Flow

### 1. Initialization

```python
# User runs: jira-download PROJ-123 --output /path

1. CLI validates arguments
2. Load .env file with python-dotenv
3. Verify required environment variables
4. Create output directory if needed
```

### 2. API Communication

```python
1. Create JiraApiClient with credentials
2. Build API URL: https://domain/rest/api/2/issue/PROJ-123
3. Make authenticated GET request
4. Receive JSON response with issue data
5. Extract attachments list from JSON
```

### 3. Attachment Processing

```python
1. Create AttachmentHandler with auth session
2. For each attachment in issue:
   a. Stream download from Jira
   b. Generate unique filename if conflict
   c. Save to output directory
   d. Track downloaded files
3. Return mapping of URLs to local paths
```

### 4. Markdown Generation

```python
1. Create MarkdownConverter
2. Extract issue fields (title, description, comments)
3. Convert HTML content to Markdown
4. Replace attachment URLs with local paths
5. Format metadata section
6. Combine into final document
```

### 5. File Output

```python
1. Create issue directory (e.g., PROJ-123/)
2. Write markdown file (PROJ-123.md)
3. Attachments already saved by handler
4. Report success to user
```

## Configuration Management

Environment variables are loaded using python-dotenv:

```python
# Automatic loading from .env file
from dotenv import load_dotenv
load_dotenv()

# Access via os.environ
domain = os.environ.get('JIRA_DOMAIN')
```

**Security:** Credentials never logged or included in error messages.

## Error Handling Strategy

Each layer handles errors appropriately:

1. **Components** - Raise specific exceptions
2. **CLI** - Catches and presents user-friendly messages
3. **Exit Codes** - Consistent codes for different failures

```python
# Example error flow
try:
    api_client.get_issue(issue_key)
except AuthenticationError:
    print("Error: Invalid credentials")
    sys.exit(1)
except IssueNotFoundError:
    print(f"Error: Issue {issue_key} not found")
    sys.exit(2)
```

## Performance Considerations

### Memory Efficiency

- **Streaming Downloads**: Attachments downloaded in chunks
- **Lazy Processing**: Data processed as needed
- **Session Reuse**: Single HTTP session for all requests

### Network Optimization

- **Connection Pooling**: Via requests.Session
- **Minimal API Calls**: Single call per issue
- **Parallel Downloads**: Could be added for multiple attachments

## Extension Points

The architecture supports future enhancements:

### Potential Extensions

1. **Bulk Export**: Process multiple issues
2. **Custom Templates**: Different output formats
3. **Plugin System**: Custom processors
4. **Caching**: Store frequently accessed data
5. **Resume Support**: Continue interrupted downloads

### Adding New Features

To add a new feature:

1. Create new module if needed
2. Raise specific exceptions
3. Integrate with CLI orchestrator
4. Update error handling
5. Add tests

## Testing Architecture

### Unit Tests

Each component tested in isolation:

```python
# Mock external dependencies
@patch('requests.Session')
def test_api_client(mock_session):
    # Test API client without network
```

### Integration Tests

CLI tested with mocked components:

```python
# Test full workflow with mocks
@patch('jira_download.JiraApiClient')
def test_export_workflow(mock_client):
    # Test complete export process
```

## Design Principles

1. **Single Responsibility**: Each class has one job
2. **Dependency Injection**: Components receive dependencies
3. **Fail Fast**: Validate early, fail with clear messages
4. **No Magic**: Explicit over implicit behavior
5. **Testability**: Easy to mock and test

## Security Considerations

- **No Credential Storage**: Only in environment
- **No Credential Logging**: Filtered from all output
- **HTTPS Only**: All API communication encrypted
- **Token Authentication**: No password storage

## Future Improvements

Potential architectural enhancements:

1. **Async Downloads**: Use asyncio for parallel downloads
2. **Progress Bars**: Rich terminal UI for long operations
3. **Incremental Updates**: Only download changed content
4. **Database Cache**: SQLite for metadata caching
5. **Plugin Architecture**: Allow custom processors

## Conclusion

The architecture prioritizes:
- **Simplicity**: Easy to understand and maintain
- **Modularity**: Components can be updated independently
- **Reliability**: Clear error handling and recovery
- **Extensibility**: Easy to add new features

This design makes jira-download both powerful and maintainable.