---
phase: "01"
plan: "02"
title: "Linked Issues + Subtasks Body Sections"
status: complete
tasks_completed: 4
commits:
  - "2d57d80 test(phase-01): add linked issues and subtasks fixtures"
  - "f523bc7 feat(phase-01): add linked issues section renderer"
  - "7cb0da4 feat(phase-01): add subtasks section renderer"
  - "9b778e6 test(phase-01): add linked issues and subtasks section tests"
deviations: none
---

## What Was Built
- `_compose_linked_issues_section()` — groups links by title-cased directional label with `### Label` subheadings; each link as `- [KEY](url): Summary (Status)`; empty/missing returns "None"
- `_compose_subtasks_section()` — flat bullet list: `- [KEY](url): Summary (Status) — Type`; empty/missing returns "None"
- 2 JSON fixtures and 6 tests (all pass, 29 existing unaffected)

## Files Modified
- `tests/data/issue_with_links.json` — created (3 issuelinks: outward Blocks, inward Blocks, outward Relates)
- `tests/data/issue_with_subtasks.json` — created (2 subtasks)
- `src/jarkdown/markdown_converter.py` — 2 methods added after `replace_attachment_links()`, before `_parse_adf_to_markdown()`
- `tests/test_sections_links_subtasks.py` — created (6 tests across 2 test classes)
