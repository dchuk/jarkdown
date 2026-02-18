---
phase: "04"
plan: "02"
title: "CLI Subcommand Restructuring"
status: complete
commits:
  - hash: "5946a62"
    message: "feat(phase-04): restructure CLI with subcommands and async export boundary"
    tasks: [1, 2, 3, 4]
  - hash: "a9e888c"
    message: "test(phase-04): update test_cli.py for subcommand structure"
    tasks: [5]
files_modified:
  - src/jarkdown/jarkdown.py
  - tests/test_cli.py
test_results: "14 passed in 0.30s"
deviations:
  - type: DEVN-01
    description: "Tasks 1-4 committed together (all modify jarkdown.py; incremental commits impractical for full-file restructure)"
  - type: DEVN-01
    description: "field_cache.refresh() bypassed in export_issue() — calls await api_client.fetch_fields() directly to avoid sync wrapper calling async method without await"
---

## What Was Built

Restructured `jarkdown.py` CLI from single flat argparse to proper subcommand architecture. Added `asyncio.run()` boundary with `async with JiraApiClient()` context manager. Updated `tests/test_cli.py` to use async mocking instead of deprecated `requests.Session` mocking.

## Files Modified

- `src/jarkdown/jarkdown.py` — full restructure: parent_parser, subparsers (export/bulk/query/setup), backward-compat shim (`^[A-Z]+-\d+$`), `async def export_issue()`, `async def _async_export()`, `_handle_export/bulk/query()` sync wrappers, stub handlers
- `tests/test_cli.py` — new async mocking strategy (AsyncMock JiraApiClient, AttachmentHandler patch, FieldMetadataCache patch), 5 new tests (backward-compat, bulk stub, query stub, setup, no-command), updated sys.argv to subcommand form
