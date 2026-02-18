# Phase 4: Bulk Export & JQL — Context

Gathered: 2026-02-17
Calibration: architect

## Phase Boundary
Enable exporting multiple issues at once via key lists (REQ-09) or JQL queries (REQ-10). Includes CLI restructuring to subcommands and full async migration of the I/O pipeline.

## Decisions

### CLI Argument Design
- Subcommand pattern: `export`, `bulk`, `query`, `setup`
- `jarkdown export PROJ-123` is the canonical single-issue form
- `jarkdown PROJ-123` still works via default-to-export compat shim (auto-detect issue key pattern)
- `jarkdown bulk PROJ-123 PROJ-456 PROJ-789` for multiple keys
- `jarkdown query 'project = FOO AND status = Done'` for JQL
- `query` subcommand adds `--max-results` flag
- Parent-level shared flags: `--output`, `--include-fields`, `--exclude-fields`, `--verbose`, `--refresh-fields`
- Each subcommand inherits shared flags via parent parser

### Bulk Output Structure
- Flat siblings by default: each issue gets its own `KEY/KEY.md` directory under `--output`
- Optional `--batch-name` flag to create a named wrapper directory
- `index.md` summary file at the output root (or batch directory root)
- Index contains: Markdown table with key (linked to local .md), summary, status, type, assignee
- Header with export count and date

### Rate Limiting & Concurrency
- Full async rewrite: migrate JiraApiClient from `requests` to `aiohttp`
- All I/O is async — single export also uses `asyncio.run()` at CLI boundary
- `asyncio.Semaphore` with default 3 concurrent workers for bulk/query
- Respect `Retry-After` headers from Jira Cloud (429 responses)
- Exponential backoff on transient errors (rate limit, timeout)
- `AttachmentHandler` also migrated to async (aiohttp for downloads)
- No synchronous fallback — one code path for simplicity

### Partial Failure Semantics
- Continue-and-report: export all possible issues, collect failures
- Retry transient errors (rate limits, timeouts) with exponential backoff
- Fail immediately on unrecoverable errors (404, auth) — record and move to next issue
- Summary at end: completed count, failed count with per-issue error reasons
- Exit code 0 if all succeed, exit code 1 if any failures
- Failed issues listed in index.md with error column

### Open (Claude's discretion)
- Progress reporting: stderr counter (e.g., "Exporting 3/10...") — no heavy dependency like tqdm
- JQL pagination: use Jira's `startAt`/`maxResults` with configurable page size (default 50)
- Attachment concurrency: share the semaphore with issue fetching (simple) vs separate limit (complex) — use shared semaphore

## Deferred Ideas
None.

## Current State
- CLI: single positional `issue_key` with `nargs="?"`, argparse-based
- API client: synchronous `requests.Session` in `JiraApiClient`
- Attachment handler: synchronous `requests.get` with streaming
- Dependencies: requests, python-dotenv, markdownify, beautifulsoup4 (+ tomli for <3.11)
- New dependency needed: aiohttp (async HTTP client)
