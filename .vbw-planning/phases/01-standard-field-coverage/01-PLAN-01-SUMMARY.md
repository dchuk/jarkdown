---
phase: "01"
plan: "01"
title: "Frontmatter Field Extensions"
status: complete
---

## What Was Built
- Always-present frontmatter schema: all 29 fields output regardless of null/empty state
- 11 new fields: status_category, project, project_key, duedate, original_estimate, time_spent, remaining_estimate, progress, aggregate_progress, votes, watches
- Null scalars render as YAML `null`, zero-value integers as `0`, missing lists as `[]`
- 24 new tests covering populated values, empty defaults, and field ordering
- Tasks: fixture (f3c07d0), refactor (ff91382), new fields (e38bc7b), tests (cf3be7b)

## Files Modified
- `tests/data/issue_standard_fields.json` — new fixture with all standard fields
- `src/jarkdown/markdown_converter.py` — `_generate_metadata_dict()` refactored + extended
- `tests/test_frontmatter_fields.py` — new test file (3 classes, 24 tests)
