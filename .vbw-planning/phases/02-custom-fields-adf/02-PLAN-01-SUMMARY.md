---
phase: "02"
plan: "01"
title: "ADF Parser Extensions"
status: complete
tasks:
  - name: "Add ADF table support"
    commit: 7966c70
  - name: "Add panel, expand, and rule support"
    commit: 236e24f
  - name: "Add inline node support"
    commit: 47b2dc9
  - name: "Add taskList, decisionList, mediaGroup support"
    commit: 32e2cba
  - name: "Write comprehensive ADF node tests"
    commit: 2ec2ad7
tests:
  test_adf_nodes: "24 passed"
  test_components: "29 passed"
deviations: none
---

## What Was Built
- 12 new ADF node types in `_parse_adf_to_markdown()`: table, tableRow, tableHeader, tableCell, panel, expand, rule, emoji, status, date, inlineCard, taskList, taskItem, decisionList, decisionItem, mediaGroup
- Tables render as pipe-delimited Markdown with header separator
- Panels render as blockquotes with bold type prefix
- Expand blocks render as bold title + indented content
- Inline nodes (emoji, status, date, inlineCard) render correctly inline
- Task/decision lists render with checkbox/blockquote syntax
- 24 new tests across 7 test classes, all passing

## Files Modified
- `src/jarkdown/markdown_converter.py` — added 12 elif branches to `_parse_adf_to_markdown()`
- `tests/test_adf_nodes.py` — new, 24 tests across 7 test classes
- `tests/data/adf_table.json` — new fixture
- `tests/data/adf_panel_expand_rule.json` — new fixture
- `tests/data/adf_inline_nodes.json` — new fixture
- `tests/data/adf_task_decision.json` — new fixture
