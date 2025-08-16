# Usage Guide

This guide covers all the ways to use jira-download, from basic exports to advanced options.

## Quick Start

The simplest usage - export a single issue:

```bash
jira-download PROJ-123
```

This creates a folder named `PROJ-123/` in your current directory containing:
- `PROJ-123.md` - The issue content in Markdown
- All attachments with their original filenames

## Command-Line Options

### Basic Syntax

```bash
jira-download ISSUE-KEY [OPTIONS]
```

### Available Options

#### `--output` / `-o`

Specify where to save the exported issue:

```bash
# Save to specific directory
jira-download PROJ-123 --output ~/Documents/jira-exports

# Use short form
jira-download PROJ-123 -o /tmp/exports
```

If the output directory doesn't exist, it will be created.

#### `--verbose` / `-v`

Enable detailed output to see what's happening:

```bash
jira-download PROJ-123 --verbose
```

This shows:
- API calls being made
- Attachments being downloaded
- File paths being created
- Any warnings or non-critical issues

#### `--help` / `-h`

Display help information:

```bash
jira-download --help
```

## Output Structure

Each exported issue creates this structure:

```
PROJ-123/
├── PROJ-123.md          # Main issue content
├── screenshot.png       # Attachments keep
├── design-doc.pdf       # their original names
└── meeting-notes.docx
```

### The Markdown File

The generated Markdown file includes:

1. **Header metadata** - Issue key, type, status, priority
2. **Issue details** - Reporter, assignee, dates
3. **Description** - Main issue content converted from Jira's HTML
4. **Comments** - All comments with author and timestamp
5. **Attachment links** - Updated to reference local files

Example structure:

```markdown
# PROJ-123: Implement user authentication

**Type:** Story  
**Status:** In Progress  
**Priority:** High  

## Details
- **Reporter:** Jane Doe
- **Assignee:** John Smith
- **Created:** 2024-01-15 10:30:00
- **Updated:** 2024-01-20 15:45:00

## Description
As a user, I want to be able to log in...

![Screenshot](screenshot.png)

## Comments

### Jane Doe - 2024-01-16 09:00:00
Here's the updated design: [design-doc.pdf](design-doc.pdf)
```

## Common Use Cases

### Archiving Completed Sprints

Export all completed issues from a sprint:

```bash
for issue in PROJ-101 PROJ-102 PROJ-103; do
    jira-download $issue --output ~/sprints/sprint-23
done
```

### Creating Documentation

Export issues to include in project documentation:

```bash
jira-download EPIC-1 --output docs/requirements
```

### Backup Before Migration

Export critical issues before system changes:

```bash
# Create timestamped backup
OUTPUT_DIR="backup-$(date +%Y%m%d)"
jira-download CRITICAL-1 --output $OUTPUT_DIR --verbose
```

### Offline Access

Download issues for offline work:

```bash
# Export to synced folder
jira-download TASK-456 --output ~/Dropbox/jira-offline
```

## Working with Attachments

### Attachment Handling

- **Automatic download**: All attachments are downloaded by default
- **Original names**: Files keep their original names from Jira
- **Conflict resolution**: Duplicate names get numbered suffixes (e.g., `file-1.pdf`, `file-2.pdf`)
- **Link updates**: All references in the Markdown are updated to local paths

### Large Attachments

For issues with many or large attachments:

```bash
# Use verbose to monitor progress
jira-download PROJ-789 --verbose
```

The tool uses streaming downloads to handle large files efficiently.

## Error Handling

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
**Solution**: Check your API token and email in the `.env` file

#### Network Issues
```
Error: Connection timeout
```
**Solution**: Check your internet connection and Jira availability

### Retry Failed Downloads

If a download fails partway through:

```bash
# Remove partial download
rm -rf PROJ-123/

# Retry with verbose output
jira-download PROJ-123 --verbose
```

## Advanced Usage

### Scripting and Automation

Use jira-download in scripts:

```python
#!/usr/bin/env python3
import subprocess
import os

issues = ['PROJ-1', 'PROJ-2', 'PROJ-3']
output_base = '/path/to/exports'

for issue in issues:
    result = subprocess.run(
        ['jira-download', issue, '--output', output_base],
        capture_output=True,
        text=True
    )
    if result.returncode == 0:
        print(f"✓ Exported {issue}")
    else:
        print(f"✗ Failed to export {issue}: {result.stderr}")
```

### Integration with Other Tools

Process exported Markdown with other tools:

```bash
# Export and convert to HTML
jira-download PROJ-123
pandoc PROJ-123/PROJ-123.md -o PROJ-123.html

# Export and create PDF
jira-download PROJ-456
pandoc PROJ-456/PROJ-456.md -o PROJ-456.pdf --pdf-engine=xelatex
```

## Tips and Best Practices

1. **Regular Backups**: Schedule regular exports of important issues
2. **Organize by Project**: Use `--output` to organize exports by project or sprint
3. **Version Control**: Consider committing exported issues to Git for history
4. **Clean URLs**: The tool handles various Jira URL formats for attachments
5. **Batch Operations**: Use shell scripts for bulk exports

## Next Steps

- Learn about [Configuration](configuration.md) options
- Understand the [Architecture](architecture.md)
- Contribute to the project - see [Contributing](contributing.md)