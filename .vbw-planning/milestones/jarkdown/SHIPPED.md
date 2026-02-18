# jarkdown — Shipped

**Shipped:** 2026-02-18
**Started:** 2026-02-17

## Summary

Complete, offline-readable Jira issue archives in Markdown format. Built across 4 phases with 15 plans, 63 tasks, and 230 passing tests.

## Phases

| Phase | Name | Plans | Commits | Tests |
|-------|------|-------|---------|-------|
| 1 | Standard Field Coverage | 4 | 14 | 93 |
| 2 | Custom Fields & ADF | 4 | 18 | 187 |
| 3 | uv Migration & Tooling | 3 | 9 | 187 |
| 4 | Bulk Export & JQL | 4 | 17 | 230 |

## Requirements Satisfied

- REQ-01: Jira REST API v3 integration
- REQ-02: HTML to Markdown conversion
- REQ-03: Attachment download with local path replacement
- REQ-04: YAML frontmatter with issue metadata
- REQ-05: Comment export with ADF and rendered HTML
- REQ-06: Full standard field coverage
- REQ-07: Custom field mapping
- REQ-08: Complete ADF support
- REQ-09: Bulk export
- REQ-10: JQL query support
- REQ-11: uv package manager migration

## Key Decisions

| Decision | Rationale |
|----------|-----------|
| Time tracking in frontmatter | Keeps data queryable by frontmatter parsers |
| Issue links grouped by relationship type | Most scannable for issues with many links |
| All fields always present (complete schema) | YAML null / "None" — consistent, grep-able |
| Cached field metadata per domain | 24h TTL, XDG-compliant, graceful degradation |
| Best-effort ADF Markdown | Full node coverage, Markdown-only output |
| Subcommand CLI pattern | export/bulk/query subcommands with default-to-export compat |
| Full async rewrite (aiohttp) | One async code path, concurrent bulk with semaphore |
| Continue-and-report on partial failures | Retry transient, fail and record unrecoverable |
| Flat sibling output with optional batch dir | Reuses existing per-issue structure, index.md summary |

## Deferred to v2

- REQ-12: Parallel attachment downloads
- REQ-13: Incremental/delta export
- REQ-14: Alternative output formats (JSON, HTML)
