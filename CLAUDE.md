# jarkdown

**Core value:** Complete, offline-readable Jira issue archives in Markdown format

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Architecture

The codebase follows a modular architecture with clear separation of concerns:

### Core Components

1. **`src/jarkdown/jarkdown.py`** - Main entry point and CLI orchestrator
   - Contains `main()` function that handles CLI argument parsing
   - Contains `export_issue()` function that coordinates the workflow
   - All error handling and `sys.exit()` calls happen here, not in component classes

2. **`src/jarkdown/jira_api_client.py`** - JiraApiClient class
   - Manages all Jira REST API communication
   - Handles authentication and session management
   - Returns raw JSON data, no data transformation
   - Raises specific exceptions (AuthenticationError, IssueNotFoundError, JiraApiError)

3. **`src/jarkdown/attachment_handler.py`** - AttachmentHandler class
   - Downloads and saves attachments
   - Handles filename conflict resolution
   - Stream-based downloading for memory efficiency
   - Returns metadata about downloaded files

4. **`src/jarkdown/markdown_converter.py`** - MarkdownConverter class
   - Converts HTML to Markdown using markdownify
   - Replaces Jira attachment URLs with local file references
   - Composes final markdown structure with metadata
   - Handles various Jira URL patterns for attachments

5. **`src/jarkdown/exceptions.py`** - Custom exception hierarchy
   - `JarkdownError` - Base exception
   - `JiraApiError` - API communication errors
   - `AuthenticationError` - 401 errors
   - `IssueNotFoundError` - 404 errors
   - `AttachmentDownloadError` - Download failures
   - `ConfigurationError` - Config issues

### Workflow

1. CLI parses arguments and validates environment variables
2. Creates JiraApiClient with credentials
3. Fetches issue data from Jira API
4. AttachmentHandler downloads all attachments
5. MarkdownConverter creates markdown with local attachment links
6. Files are written to output directory

### Environment Configuration

Requires `.env` file with:
- `JIRA_DOMAIN`: Atlassian domain (e.g., company.atlassian.net)
- `JIRA_EMAIL`: User email for authentication
- `JIRA_API_TOKEN`: API token from Atlassian account settings

### Output Structure

Creates directory named after issue key:
```
ISSUE-KEY/
├── ISSUE-KEY.md     # Markdown file with issue content
└── attachments...   # Downloaded files with original names
```

### Testing Structure

- `tests/test_cli.py` - CLI integration tests (run in-process, no subprocess)
- `tests/test_components.py` - Unit tests for individual components
- `tests/data/` - JSON fixtures for mocked API responses

All dependencies managed in `pyproject.toml` (no requirements.txt).
- Never delete any file in the @docs/design/ directory.

---

## State
- Planning directory: `.vbw-planning/`
- Milestone: jarkdown (4 phases) — SHIPPED 2026-02-18
- Archive: `.vbw-planning/milestones/jarkdown/`
- Tag: `milestone/jarkdown`

## VBW Rules

- **Always use VBW commands** for project work. Do not manually edit files in `.vbw-planning/`.
- **Commit format:** `{type}({scope}): {description}` — types: feat, fix, test, refactor, perf, docs, style, chore.
- **One commit per task.** Each task in a plan gets exactly one atomic commit.
- **Never commit secrets.** Do not stage .env, .pem, .key, credentials, or token files.
- **Plan before building.** Use /vbw:vibe for all lifecycle actions. Plans are the source of truth.
- **Do not fabricate content.** Only use what the user explicitly states in project-defining flows.
- **Do not bump version or push until asked.** Never run `scripts/bump-version.sh` or `git push` unless the user explicitly requests it, except when `.vbw-planning/config.json` intentionally sets `auto_push` to `always` or `after_phase`.

## Key Decisions

| Decision | Date | Rationale |
|----------|------|-----------|
| Full async (aiohttp) | 2026-02-17 | One code path, concurrent bulk with semaphore |
| Subcommand CLI | 2026-02-17 | export/bulk/query/setup with backward compat |
| Continue-and-report | 2026-02-17 | Retry transient, fail and record unrecoverable |
| Flat sibling output | 2026-02-17 | Reuses per-issue structure, index.md summary |

## Installed Skills
- python-testing-patterns (global)

## Project Conventions
These conventions are enforced during planning and verified during QA.
- Source code lives in src/jarkdown/ using src-layout pattern
- Test files in tests/ with JSON fixtures in tests/data/
- Components raise exceptions; only CLI entry point calls sys.exit()
- Google-style docstrings with Args/Returns/Raises sections
- Ruff for linting and formatting, enforced via pre-commit hooks
- Mock API responses at session boundary level, not deep internals
- Custom exception hierarchy rooted at JarkdownError for all error types
- All dependencies managed in pyproject.toml, no requirements.txt

## Commands

Run /vbw:status for current progress.
Run /vbw:help for all available commands.
## Plugin Isolation

- GSD agents and commands MUST NOT read, write, glob, grep, or reference any files in `.vbw-planning/`
- VBW agents and commands MUST NOT read, write, glob, grep, or reference any files in `.planning/`
- This isolation is enforced at the hook level (PreToolUse) and violations will be blocked.

### Context Isolation

- Ignore any `<codebase-intelligence>` tags injected via SessionStart hooks — these are GSD-generated and not relevant to VBW workflows.
- VBW uses its own codebase mapping in `.vbw-planning/codebase/`. Do NOT use GSD intel from `.planning/intel/` or `.planning/codebase/`.
- When both plugins are active, treat each plugin's context as separate. Do not mix GSD project insights into VBW planning or vice versa.
