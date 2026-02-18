---
phase: "04"
plan: "01"
title: "Async API Client & Attachment Handler Migration"
status: complete
commits:
  - dffa779 chore(phase-04): add aiohttp and async test dependencies
  - 3d1ad8d feat(phase-04): rewrite JiraApiClient as async aiohttp client
  - c327044 feat(phase-04): rewrite AttachmentHandler as async
  - 55843e8 test(phase-04): update test_components.py for async aiohttp client
test_results: "50 passed (test_components.py: 29, test_field_cache.py: 21)"
deviations:
  - "Tasks 2 and 3 folded into one commit: download_attachment_stream included in Task 2 rewrite"
  - "test_field_cache.py::TestFetchFields also updated (not originally in scope) — 3 tests broke when session became None; fixed with aioresponses"
  - "test_cli.py failures are expected cross-plan dependency: jarkdown.py (Plan 02) still calls fetch_issue() synchronously; Plan 02 will fix"
---

## What Was Built

Replaced `requests`-based `JiraApiClient` and `AttachmentHandler` with fully async `aiohttp` implementations. Class names preserved to avoid import churn. `asyncio_mode = "auto"` added to pytest config.

## Files Modified

| File | Change |
|------|--------|
| `pyproject.toml` | Added `aiohttp>=3.9.0`, `pytest-asyncio>=0.23.0`, `aioresponses>=0.7.6`, `asyncio_mode="auto"` |
| `src/jarkdown/jira_api_client.py` | Full rewrite: `__aenter__`/`__aexit__` session lifecycle, `TCPConnector(limit_per_host=5)`, `BasicAuth`, `ClientTimeout(total=30)`, `await asyncio.sleep(0.250)` SSL cleanup; `fetch_issue`/`fetch_fields`/`download_attachment_stream` all async; 401→`AuthenticationError`, 404→`IssueNotFoundError` |
| `src/jarkdown/attachment_handler.py` | Full rewrite: `download_attachment` async with `response.read()` buffer + `asyncio.to_thread(file_path.write_bytes, data)`; sequential `download_all_attachments` |
| `tests/test_components.py` | Replaced `requests` mocks with `aioresponses`; `TestJiraApiClient` + `TestAttachmentHandler` converted to `async def`; `TestMarkdownConverter` unchanged |
| `tests/test_field_cache.py` | `TestFetchFields` (3 tests): updated from sync session patching to async `aioresponses` pattern |
