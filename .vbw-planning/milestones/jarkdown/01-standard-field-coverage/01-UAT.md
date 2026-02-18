---
phase: "01"
plan_count: 4
status: complete
started: "2026-02-17"
total_tests: 5
passed: 5
skipped: 0
issues: 0
---

## P01-T1: Verify frontmatter always-present schema

**Plan:** 01 — Frontmatter Field Extensions
**Scenario:** Run the converter on a minimal issue (no Phase 1 fields) and verify all 29 frontmatter fields appear with null/0/[] defaults.
**Command:**
```bash
python -c "
import json
from jarkdown.markdown_converter import MarkdownConverter
mc = MarkdownConverter('https://example.atlassian.net', 'example.atlassian.net')
data = {'key': 'MIN-1', 'fields': {'summary': 'Minimal', 'issuetype': {'name': 'Task'}, 'status': {'name': 'Open'}, 'created': '2025-01-01T00:00:00.000+0000', 'updated': '2025-01-01T00:00:00.000+0000'}, 'renderedFields': {'description': '<p>Test</p>'}}
output = mc.compose_markdown(data, [])
# Count frontmatter fields
lines = output.split('\n')
in_fm = False
fm_lines = []
for line in lines:
    if line == '---':
        if in_fm: break
        in_fm = True; continue
    if in_fm: fm_lines.append(line)
print(f'Frontmatter fields: {len(fm_lines)}')
for fl in fm_lines: print(f'  {fl}')
"
```
**Expected:** 29 frontmatter fields present. Missing scalars show `null`, integer fields show `0`, list fields show `[]`.
**Result:** PASS — 29 frontmatter fields present. Scalars show `null`, integer fields show `0`, list fields show `[]`.

## P02-T1: Verify linked issues grouping format

**Plan:** 02 — Linked Issues + Subtasks Body Sections
**Scenario:** Run the linked issues section method on the test fixture and verify grouping by title-cased directional labels.
**Command:**
```bash
python -c "
import json
from jarkdown.markdown_converter import MarkdownConverter
mc = MarkdownConverter('https://example.atlassian.net', 'example.atlassian.net')
with open('tests/data/issue_with_links.json') as f: data = json.load(f)
result = '\n'.join(mc._compose_linked_issues_section(data))
print(result)
"
```
**Expected:** Output shows `## Linked Issues` with `### Blocks`, `### Is Blocked By`, `### Relates To` subheadings. Each link formatted as `- [KEY](url): Summary (Status)`.
**Result:** PASS — `## Linked Issues` present with `### Blocks`, `### Is Blocked By`, `### Relates To` subheadings. Links formatted as `- [KEY](url): Summary (Status)`.

## P03-T1: Verify worklogs table output

**Plan:** 03 — Worklogs + Environment Body Sections
**Scenario:** Run the worklogs section on the test fixture and verify table format with total time summary.
**Command:**
```bash
python -c "
import json
from jarkdown.markdown_converter import MarkdownConverter
mc = MarkdownConverter('https://example.atlassian.net', 'example.atlassian.net')
with open('tests/data/issue_with_worklogs.json') as f: data = json.load(f)
result = '\n'.join(mc._compose_worklogs_section(data))
print(result)
"
```
**Expected:** Output shows `## Worklogs`, `**Total Time Logged:**` summary, table with Author/Time Spent/Date/Comment columns, ADF comment extracted as plain text.
**Result:** PASS — `## Worklogs` with `**Total Time Logged:** 4h 20m`, table with Author/Time Spent/Date/Comment columns, ADF comment `Implemented core API endpoints` extracted correctly.

## P04-T1: Verify section ordering in complete output

**Plan:** 04 — Integration Wiring + Section Ordering
**Scenario:** Run full converter on the comprehensive fixture and verify all sections appear in correct order.
**Command:**
```bash
python -c "
import json
from jarkdown.markdown_converter import MarkdownConverter
mc = MarkdownConverter('https://example.atlassian.net', 'example.atlassian.net')
with open('tests/data/issue_full_fields.json') as f: data = json.load(f)
output = mc.compose_markdown(data, [])
sections = [line for line in output.split('\n') if line.startswith('## ')]
for i, s in enumerate(sections): print(f'{i+1}. {s}')
"
```
**Expected:** Sections in order: Description, Environment, Linked Issues, Subtasks, Worklogs, Comments, Attachments.
**Result:** PASS — Sections in correct order: 1. Description, 2. Environment, 3. Linked Issues, 4. Subtasks, 5. Worklogs, 6. Comments.

## P04-T2: Verify empty sections show "None"

**Plan:** 04 — Integration Wiring + Section Ordering
**Scenario:** Run on minimal data and verify new sections all show "None" while Comments/Attachments are absent (conditional).
**Command:**
```bash
python -c "
import json
from jarkdown.markdown_converter import MarkdownConverter
mc = MarkdownConverter('https://example.atlassian.net', 'example.atlassian.net')
data = {'key': 'EMPTY-1', 'fields': {'summary': 'Empty Fields Test', 'issuetype': {'name': 'Task'}, 'status': {'name': 'Open'}, 'created': '2025-01-01T00:00:00.000+0000', 'updated': '2025-01-01T00:00:00.000+0000'}, 'renderedFields': {'description': '<p>Test</p>'}}
output = mc.compose_markdown(data, [])
for line in output.split('\n'):
    if '##' in line or 'None' in line: print(line)
"
```
**Expected:** Shows `## Environment` / `## Linked Issues` / `## Subtasks` / `## Worklogs` each followed by "None". No `## Comments` or `## Attachments`.
**Result:** PASS — All 4 sections present with "None" body. No `## Comments` or `## Attachments` in output.
