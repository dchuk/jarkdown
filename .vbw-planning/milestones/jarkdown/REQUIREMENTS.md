# jarkdown Requirements

Defined: 2026-02-17 | Core value: Complete, offline-readable Jira issue archives in Markdown

## v1 Requirements

### Core (Validated)
- [x] **REQ-01**: Jira REST API v3 integration with authentication (domain standard)
- [x] **REQ-02**: HTML to Markdown conversion via markdownify (domain standard)
- [x] **REQ-03**: Attachment download with local path replacement (domain standard)
- [x] **REQ-04**: YAML frontmatter with issue metadata (domain standard)
- [x] **REQ-05**: Comment export with ADF and rendered HTML support

### Field Coverage
- [x] **REQ-06**: Full standard field coverage — project, issuelinks, subtasks, time tracking, progress, worklogs, votes, watches, duedate, environment, statusCategory
- [x] **REQ-07**: Custom field mapping — configurable rendering of customfield_* entries in markdown output

### ADF Parsing
- [x] **REQ-08**: Complete ADF support — tables, panels, expand blocks, emoji, inline cards, decision items, task lists

### Bulk Operations
- [x] **REQ-09**: Bulk export — export multiple issues from a list of keys
- [x] **REQ-10**: JQL query support — accept JQL queries to find and export matching issues

### Tooling
- [x] **REQ-11**: Migrate to uv package manager — replace pip with uv for cleaner install and usage

## v2 Requirements
- [ ] **REQ-12**: Parallel attachment downloads for performance
- [ ] **REQ-13**: Incremental/delta export (only re-export changed issues)
- [ ] **REQ-14**: Alternative output formats (JSON, HTML)

## Out of Scope

- Real-time sync with Jira (deliberately excluded — tool is for point-in-time export)
- Jira write-back / import functionality (deliberately excluded — read-only tool)
- Jira Server/Data Center support (Cloud-only for now)
