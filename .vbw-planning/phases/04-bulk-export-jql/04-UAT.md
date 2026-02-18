---
phase: "04"
plan_count: 4
status: complete
completed: 2026-02-18
started: 2026-02-18
total_tests: 8
passed: 8
skipped: 0
issues: 0
---

## P01-T1: Full test suite passes
**Plan:** 01 — Async API Client & Attachment Handler Migration
**Scenario:** Run `uv run pytest tests/ -v` and confirm all 230 tests pass with no errors or warnings.
**Expected:** 230 passed, 0 failed, 0 errors.
**Result:** PASS — 230 passed in 3.97s

## P01-T2: Async API client structure
**Plan:** 01 — Async API Client & Attachment Handler Migration
**Scenario:** Run `uv run python -c "from jarkdown.jira_api_client import JiraApiClient; print('async:', hasattr(JiraApiClient, '__aenter__'))"` and verify it prints `async: True`.
**Expected:** Output shows `async: True` confirming the client is an async context manager.
**Result:** PASS — Output: `async: True`

## P02-T1: CLI subcommand help
**Plan:** 02 — CLI Subcommand Restructuring
**Scenario:** Run `uv run python -m jarkdown.jarkdown --help` and verify the output lists subcommands: export, bulk, query, setup.
**Expected:** Help text shows `{export,bulk,query,setup}` in the subcommand list.
**Result:** PASS — Shows `{export,bulk,query,setup}` with descriptions and examples

## P02-T2: Backward compatibility
**Plan:** 02 — CLI Subcommand Restructuring
**Scenario:** Run `uv run python -m jarkdown.jarkdown export --help` and verify shared flags (--output, --verbose, --include-fields, --exclude-fields, --refresh-fields) are listed.
**Expected:** All 5 shared flags appear in export subcommand help.
**Result:** PASS — All 5 shared flags present: --output/-o, --verbose/-v, --refresh-fields, --include-fields, --exclude-fields

## P03-T1: Retry module importable with correct defaults
**Plan:** 03 — Retry & Rate Limiting Infrastructure
**Scenario:** Run `uv run python -c "from jarkdown.retry import RetryConfig, DEFAULT_RETRY; print(f'retries={DEFAULT_RETRY.max_retries}, delay={DEFAULT_RETRY.base_delay}, max={DEFAULT_RETRY.max_delay}')"` and verify defaults.
**Expected:** Output: `retries=3, delay=1.0, max=60.0`
**Result:** PASS — Output: `retries=3, delay=1.0, max=60.0`

## P04-T1: Bulk subcommand help
**Plan:** 04 — Bulk Export Engine, JQL Search & Full Wiring
**Scenario:** Run `uv run python -m jarkdown.jarkdown bulk --help` and verify it shows positional `issue_keys` argument and `--concurrency` flag.
**Expected:** Help lists `issue_keys` positional arg and `--concurrency` option (default 3).
**Result:** PASS — Shows `issue_keys` nargs='+', `--concurrency` (default: 3), `--batch-name`, all shared flags inherited

## P04-T2: Query subcommand help
**Plan:** 04 — Bulk Export Engine, JQL Search & Full Wiring
**Scenario:** Run `uv run python -m jarkdown.jarkdown query --help` and verify it shows `jql` positional argument, `--max-results`, and `--batch-name` flags.
**Expected:** Help lists `jql` positional arg, `--max-results` option, and `--batch-name` option.
**Result:** PASS — Shows `jql` positional, `--max-results` (default: 50), `--batch-name`, `--concurrency`, all shared flags

## P04-T3: Real single-issue export
**Plan:** 04 — Bulk Export Engine, JQL Search & Full Wiring
**Scenario:** With your `.env` configured, run `uv run python -m jarkdown.jarkdown export <YOUR-ISSUE-KEY> -o /tmp/jarkdown-uat` on a real Jira issue. Verify the output directory contains `<KEY>/<KEY>.md` with YAML frontmatter and markdown content.
**Expected:** Directory created with `.md` file containing frontmatter (title, status, type, priority) and issue body content.
**Result:** PASS — User confirmed real single-issue export produces correct output
