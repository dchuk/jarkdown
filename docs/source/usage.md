# Usage Guide

This guide covers all the ways to use jarkdown, from basic exports to advanced options.

## Quick Start

The simplest usage - export a single issue:

```bash
jarkdown export PROJ-123
```

For backward compatibility, you can also omit the `export` subcommand:

```bash
jarkdown PROJ-123
```

This creates a folder named `PROJ-123/` in your current directory containing:
- `PROJ-123.md` - The issue content in Markdown
- All attachments with their original filenames

Pass `--include-json` to also save the raw Jira API response as `PROJ-123.json`.

## Subcommands

jarkdown uses subcommands to organize its functionality:

| Command | Description |
|---------|-------------|
| `export` | Export a single Jira issue |
| `bulk` | Export multiple issues by key |
| `query` | Export issues matching a JQL query |
| `setup` | Interactive credential configuration |

## Export (Single Issue)

### Basic Syntax

```bash
jarkdown export ISSUE-KEY [OPTIONS]
```

### Options

#### `--output` / `-o`

Specify where to save the exported issue (default: current directory).

```bash
# Save to specific directory
jarkdown export PROJ-123 --output ~/Documents/jira-exports

# Use short form
jarkdown export PROJ-123 -o /tmp/exports
```

If no `--output` is given, the issue directory is created inside the current working directory. If the specified output directory doesn't exist, it will be created.

#### `--verbose` / `-v`

Enable detailed output to see what's happening (default: off).

```bash
jarkdown export PROJ-123 --verbose
```

This shows:
- API calls being made
- Attachments being downloaded
- File paths being created
- Any warnings or non-critical issues

#### `--include-fields`

Include only specific custom fields in the output (default: all custom fields with non-null values are included).

```bash
jarkdown export PROJ-123 --include-fields "Story Points,Sprint,Team"
```

When this flag is set, only the listed custom fields appear in the output. Overrides `.jarkdown.toml` include settings.

#### `--exclude-fields`

Exclude specific custom fields from the output (default: no fields excluded).

```bash
jarkdown export PROJ-123 --exclude-fields "Internal Notes,Dev Notes"
```

All custom fields except the listed ones are included. Overrides `.jarkdown.toml` exclude settings.

#### `--refresh-fields`

Force a refresh of the cached Jira field metadata (default: off; cache is refreshed automatically after 24 hours).

```bash
jarkdown export PROJ-123 --refresh-fields
```

#### `--include-json`

Save the raw Jira API response as `ISSUE-KEY.json` alongside the Markdown file (default: off).

```bash
jarkdown export PROJ-123 --include-json
```

#### `--help` / `-h`

Display help information:

```bash
jarkdown export --help
```

## Bulk Export

Export multiple issues concurrently using a semaphore-limited concurrency model.

### Basic Syntax

```bash
jarkdown bulk ISSUE-KEY1 ISSUE-KEY2 ... [OPTIONS]
```

### Examples

```bash
# Export three issues with default concurrency (3)
jarkdown bulk PROJ-1 PROJ-2 PROJ-3

# Export with higher concurrency
jarkdown bulk PROJ-1 PROJ-2 PROJ-3 PROJ-4 PROJ-5 --concurrency 5

# Export to a specific directory
jarkdown bulk PROJ-1 PROJ-2 --output ~/exports

# Group exports into a named batch directory
jarkdown bulk PROJ-1 PROJ-2 PROJ-3 --batch-name sprint-23
```

### Options

- `--concurrency N` - Maximum concurrent exports (default: 3)
- `--max-results N` - Limit the number of issue keys exported; by default all supplied keys are exported
- `--batch-name NAME` - Wrap all issue directories in a named subdirectory (default: none)
- `--output` / `-o` - Root output directory (default: current directory)
- `--include-json` - Save raw Jira API JSON alongside each Markdown file (default: off)
- `--verbose` / `-v` - Enable detailed logging (default: off)
- `--include-fields`, `--exclude-fields` - Comma-separated custom field filter (default: include all)
- `--refresh-fields` - Force refresh of cached field metadata (default: off)

### Output

Bulk export creates an `index.md` summary file alongside the issue directories:

```
output-dir/
├── index.md          # Summary table with status of each export
├── PROJ-1/
│   ├── PROJ-1.md
│   └── attachments...
├── PROJ-2/
│   ├── PROJ-2.md
│   └── attachments...
└── ...
```

The `index.md` contains a Markdown table with key, summary, status, type, assignee, and export result for each issue.

### Partial Failure Handling

If some issues fail to export, jarkdown continues exporting the remaining issues. A summary is printed at the end showing successes and failures, and the process exits with code 1 if any failures occurred.

## JQL Query Export

Search for issues using JQL and export the results.

### Basic Syntax

```bash
jarkdown query 'JQL_QUERY' [OPTIONS]
```

### Examples

```bash
# Export all done issues in a project
jarkdown query 'project = FOO AND status = Done'

# Export current sprint issues
jarkdown query 'project = FOO AND sprint in openSprints()'

# Limit results (both flags are equivalent)
jarkdown query 'assignee = currentUser() ORDER BY created DESC' --limit 25
jarkdown query 'assignee = currentUser() ORDER BY created DESC' --max-results 25

# Full options
jarkdown query 'project = FOO AND type = Bug' --limit 100 --concurrency 5 --output ~/exports
```

### Options

- `--limit N` / `--max-results N` - Maximum number of issues to export (default: 50). Both flags are equivalent; `--limit` is the shorter, more intuitive form. Results are paginated automatically.
- `--concurrency N` - Maximum concurrent exports (default: 3)
- `--batch-name NAME` - Wrap all issue directories in a named subdirectory (default: none)
- `--output` / `-o` - Root output directory (default: current directory)
- `--include-json` - Save raw Jira API JSON alongside each Markdown file (default: off)
- `--verbose` / `-v` - Enable detailed logging (default: off)
- `--include-fields`, `--exclude-fields` - Comma-separated custom field filter (default: include all)
- `--refresh-fields` - Force refresh of cached field metadata (default: off)

### Pagination

JQL queries are automatically paginated using Jira's `nextPageToken` mechanism. Pages of up to 50 issues are fetched until `--max-results` is reached or no more results exist.

## Setup Wizard

Interactive setup to create your `.env` configuration file:

```bash
jarkdown setup
```

The wizard prompts for:
1. Jira domain (e.g., `company.atlassian.net`)
2. Jira email address
3. Jira API token (input is hidden)

If a `.env` file already exists, you'll be asked to confirm before overwriting.

## Custom Field Filtering

Control which custom fields appear in your exported markdown.

### CLI Flags

```bash
# Only include these custom fields
jarkdown export PROJ-123 --include-fields "Story Points,Sprint"

# Exclude these custom fields
jarkdown export PROJ-123 --exclude-fields "Internal Notes,Dev Notes"
```

### Configuration File

Create a `.jarkdown.toml` file in your working directory:

```toml
[fields]
include = ["Story Points", "Sprint", "Team"]
```

Or to exclude specific fields:

```toml
[fields]
exclude = ["Internal Notes", "Dev Notes", "Epic Color"]
```

CLI flags override `.jarkdown.toml` settings. If both `--include-fields` is provided on the CLI, the config file's `include` setting is ignored entirely (and vice versa for exclude).

## Output Structure

Each exported issue creates this structure:

```
PROJ-123/
├── PROJ-123.md          # Main issue content
├── screenshot.png       # Attachments keep
├── design-doc.pdf       # their original names
└── meeting-notes.docx
```

Pass `--include-json` to also write `PROJ-123.json` with the raw Jira API response.

### The Markdown File

The generated Markdown file includes:

1. **YAML Frontmatter** - Comprehensive metadata block:

```yaml
---
key: PROJ-123
summary: Implement user authentication
type: Story
status: In Progress
status_category: In Progress
priority: High
resolution: null
project: My Project
project_key: PROJ
assignee: John Smith
reporter: Jane Doe
creator: Jane Doe
labels:
  - auth
  - frontend
components:
  - Web App
parent_key: EPIC-10
parent_summary: User Management Epic
affects_versions: []
fix_versions:
  - '2.0'
created_at: '2024-01-15T10:30:00.000+0000'
updated_at: '2024-01-20T15:45:00.000+0000'
resolved_at: null
duedate: '2024-02-15'
original_estimate: 3d
time_spent: 1d 2h
remaining_estimate: 1d 6h
progress: 40
aggregate_progress: 35
votes: 2
watches: 4
---
```

2. **Title** - The issue key and summary, linked to the original Jira issue.
3. **Description** - The main issue content, converted from Jira's HTML or ADF to Markdown.
4. **Environment** - Environment details if set on the issue.
5. **Linked Issues** - Grouped by relationship type (blocks, is blocked by, relates to, etc.).
6. **Subtasks** - Listed with status and issue type.
7. **Worklogs** - Table of time entries with author, time spent, date, and comment.
8. **Custom Fields** - Rendered with type-aware formatting (only if custom fields are present).
9. **Comments** - All comments with author, timestamp, and formatted content.
10. **Attachments** - Links to all downloaded files (images embedded inline).

## Common Use Cases

### Archiving Completed Sprints

Export all issues from a sprint using JQL:

```bash
jarkdown query 'project = PROJ AND sprint = "Sprint 23" AND status = Done' \
  --output ~/sprints/sprint-23
```

Or export specific issues by key:

```bash
jarkdown bulk PROJ-101 PROJ-102 PROJ-103 --output ~/sprints/sprint-23
```

### Creating Documentation

Export issues to include in project documentation:

```bash
jarkdown export EPIC-1 --output docs/requirements
```

### Backup Before Migration

Export critical issues before system changes:

```bash
jarkdown query 'project = CRITICAL AND priority in (Highest, High)' \
  --output "backup-$(date +%Y%m%d)" --max-results 200
```

### Offline Access

Download issues for offline work:

```bash
jarkdown bulk TASK-456 TASK-457 TASK-458 --output ~/Dropbox/jira-offline
```

## Working with Attachments

### Attachment Handling

- **Automatic download**: All attachments are downloaded by default
- **Original names**: Files keep their original names from Jira
- **Conflict resolution**: Duplicate names get numbered suffixes (e.g., `file_1.pdf`, `file_2.pdf`)
- **Link updates**: All references in the Markdown are updated to local paths

### Large Attachments

For issues with many or large attachments:

```bash
# Use verbose to monitor progress
jarkdown export PROJ-789 --verbose
```

The tool uses async streaming downloads to handle large files efficiently.

## Error Handling

### Retry and Rate Limiting

jarkdown automatically retries transient API errors with exponential backoff:

- **Retryable errors**: HTTP 429 (rate limited), 503 (service unavailable), 504 (gateway timeout)
- **Retry-After**: Honors the `Retry-After` header from Jira when rate limited
- **Backoff**: Exponential backoff with jitter (1s, 2s, 4s base delays, up to 60s max)
- **Max retries**: 3 attempts before raising an error

### Common Errors and Solutions

#### Issue Not Found
```
Error: Issue PROJ-999 not found
```
**Solution**: Verify the issue key and your access permissions

#### Authentication Failed
```
Error: Authentication failed (401)
```
**Solution**: Check your API token and email in the `.env` file, or run `jarkdown setup`

#### Network Issues
```
Error: Connection timeout
```
**Solution**: Check your internet connection and Jira availability. Transient errors are retried automatically.

### Bulk Export Failures

When using `bulk` or `query`, individual issue failures don't stop the entire batch. Failed issues are reported in the summary and marked in `index.md`:

```
Export complete: 8/10 succeeded, 2 failed.

Failed issues:
  PROJ-404: Issue PROJ-404 not found or not accessible.
  PROJ-500: HTTP error occurred: 500 Server Error
```

## Advanced Usage

### Scripting and Automation

Use jarkdown in scripts:

```python
#!/usr/bin/env python3
import subprocess

# Export issues from a JQL query
result = subprocess.run(
    ['jarkdown', 'query', 'project = PROJ AND status = Done',
     '--max-results', '50', '--output', '/path/to/exports'],
    capture_output=True,
    text=True
)
if result.returncode == 0:
    print("Export complete")
else:
    print(f"Export failed: {result.stderr}")
```

### Integration with Other Tools

Process exported Markdown with other tools:

```bash
# Export and convert to HTML
jarkdown export PROJ-123
pandoc PROJ-123/PROJ-123.md -o PROJ-123.html

# Export and create PDF
jarkdown export PROJ-456
pandoc PROJ-456/PROJ-456.md -o PROJ-456.pdf --pdf-engine=xelatex
```

## Tips and Best Practices

1. **Use bulk/query for multiple issues**: Prefer `jarkdown bulk` or `jarkdown query` over shell loops for better concurrency and error handling
2. **Organize by project**: Use `--output` to organize exports by project or sprint
3. **Version control**: Consider committing exported issues to Git for history
4. **Field filtering**: Use `.jarkdown.toml` to permanently exclude noisy custom fields
5. **Batch naming**: Use `--batch-name` to group related exports together

## Next Steps

- Learn about [Configuration](configuration.md) options
- Understand the [Architecture](architecture.md)
- Contribute to the project - see [Contributing](contributing.md)
