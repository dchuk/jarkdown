---
phase: "02"
plan: "02"
title: "Dependencies, API & CLI Args"
status: complete
tasks_completed: 5
tests_passed: 59
tests_failed: 0
deviations: none
---

## What Was Built
- FieldMetadataCache: XDG-compliant cache with 24h TTL, per-domain storage, field name resolution, graceful degradation
- JiraApiClient.fetch_fields(): GET /rest/api/3/field endpoint with auth/error handling
- CLI args: --refresh-fields, --include-fields, --exclude-fields
- Dependencies: platformdirs>=4.0.0, tomli>=2.0.0 (Python <3.11)
- Task 1: 3e9322a — Task 2: d28d5a6 — Task 3: 78840b2 — Task 4: faf2dc5 — Task 5: 43e1e58

## Files Modified
- `pyproject.toml` — added platformdirs and tomli dependencies
- `src/jarkdown/jira_api_client.py` — added fetch_fields() method
- `src/jarkdown/field_cache.py` — new file, FieldMetadataCache class
- `src/jarkdown/jarkdown.py` — added --refresh-fields, --include-fields, --exclude-fields CLI args
- `tests/test_field_cache.py` — new file, 21 tests (storage, staleness, resolution, refresh, API)
