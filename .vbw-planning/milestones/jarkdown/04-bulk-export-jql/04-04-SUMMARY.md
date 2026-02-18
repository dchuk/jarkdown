---
plan: "04-04"
title: "Bulk Export Engine, JQL Search & Full Wiring"
status: complete
commits:
  - hash: "86d211d"
    message: "feat(phase-04): add search_jql with nextPageToken pagination to JiraApiClient"
  - hash: "11cd43c"
    message: "feat(phase-04): add BulkExporter class with semaphore concurrency"
  - hash: "dc6482a"
    message: "feat(phase-04): wire bulk and query subcommands to BulkExporter"
  - hash: "8185c16"
    message: "test(phase-04): add comprehensive bulk exporter tests"
tests_passed: 230
tests_total: 230
deviations:
  - "Tasks 2 and 3 (BulkExporter class + generate_index_md) were implemented and committed together in a single commit. The plan called for two separate commits; all required functionality is present."
  - "test_semaphore_limits_concurrency: plan called for patching _export_one, but that bypasses the semaphore; fixed by patching _do_export instead so the real semaphore logic runs."
  - "test_missing_issues_data_shows_dashes: initial assertion used str.count('| - |') >= 3 which only yields 2 due to shared pipe separators; fixed to split on ' | ' and count dash-only columns."
---

## What Was Built

- `search_jql()` on `JiraApiClient`: paginates via `nextPageToken` using `retry_with_backoff`, stops at `max_results`
- `src/jarkdown/bulk_exporter.py`: `ExportResult` dataclass + `BulkExporter` with `asyncio.Semaphore` concurrency, `asyncio.gather(return_exceptions=True)` partial-failure handling, inline export logic (no circular import), progress to stderr, `generate_index_md()` Markdown table, `write_index_md()`
- `jarkdown.py`: extracted `_load_credentials()` and `_print_summary()` helpers; replaced `_handle_bulk`/`_handle_query` stubs with real async implementations
- `tests/test_bulk_exporter.py`: 22 new tests across 4 classes (init, export_bulk, search_jql, generate_index_md)
- `tests/test_cli.py`: updated stub routing tests to verify real handler dispatch

## Files Modified

- `src/jarkdown/jira_api_client.py` — added `search_jql()`
- `src/jarkdown/bulk_exporter.py` — new file
- `src/jarkdown/jarkdown.py` — wired bulk/query subcommands, extracted helpers
- `tests/test_bulk_exporter.py` — new file
- `tests/test_cli.py` — updated stub routing tests
