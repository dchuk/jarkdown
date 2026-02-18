# jarkdown

Export Jira Cloud issues to Markdown with attachments. A Python CLI tool that fetches issue data from the Jira REST API, downloads all attachments locally, and produces rich Markdown files with YAML frontmatter, inline images, and full comment history.

**Core value:** Complete, offline-readable Jira issue archives in Markdown format.

## Requirements

### Validated
- Single issue export to Markdown with YAML frontmatter
- Attachment download with local path replacement
- Comment export (HTML + ADF support)

### Active
- [ ] Full Jira field coverage (issue links, subtasks, time tracking, progress, votes, etc.)
- [ ] Custom field mapping and rendering
- [ ] Better ADF parsing (tables, panels, expand blocks, emoji)
- [ ] Bulk export of multiple issues
- [ ] JQL query support for batch export
- [ ] Migration to uv package manager

### Out of Scope
- Real-time sync with Jira
- Jira write-back / import functionality

## Constraints
- **Python 3.8+**: Broad compatibility across environments
- **Minimal dependencies**: Only 4 runtime deps
- **Existing test suite**: All changes must maintain passing tests

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Pipeline architecture | Simple linear data flow | Easy to extend and test |
| Session-based auth | Reuse connections | Efficient API calls |
| Exception hierarchy | Clean error handling | Components stay decoupled from CLI |
