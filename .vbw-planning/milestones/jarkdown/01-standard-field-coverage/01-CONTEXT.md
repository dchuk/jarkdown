# Phase 1: Standard Field Coverage — Context

Gathered: 2026-02-17
Calibration: architect

## Phase Boundary
Expand markdown output to cover all standard Jira fields returned by the API, closing the gap identified from PSOP-419. Adds project, issuelinks, subtasks, time tracking, progress, votes/watches, worklogs, duedate, environment, and statusCategory to the output.

## Decisions

### Frontmatter vs Body Boundary
- **Frontmatter (scalar) fields:** project name/key, statusCategory, duedate, votes, watches, original_estimate, time_spent, remaining_estimate, progress
- **Body sections:** environment (always rendered as `## Environment`, even for short values), issuelinks (`## Linked Issues`), subtasks (`## Subtasks`), worklogs (`## Worklogs`)
- Time tracking uses Jira's human-readable format (e.g., "2d", "4h", "1d 4h")

### Issue Link Rendering
- Grouped by relationship type using `###` sub-headings (e.g., `### Blocks`, `### Is Blocked By`)
- Each link rendered as: `- [KEY](jira_url): Summary (Status)`
- Use the inward/outward name from the link type (the directional label, not the generic type name)

### Subtask Rendering
- Flat bullet list under `## Subtasks`
- Each subtask: `- [KEY](jira_url): Summary (Status) — Type`

### Worklog Rendering
- Full markdown table with columns: Author, Time Spent, Date, Comment
- Total time logged summary line above the table: `**Total Time Logged:** Xd Xh`
- ADF/HTML comments in worklogs stripped to plain text for table cells
- Date column uses YYYY-MM-DD format

### Empty Field Handling
- **All fields always present** — complete schema approach
- Frontmatter: null values use YAML `null` keyword, zero counts show `0`
- Body sections: empty sections show "None" (e.g., `## Subtasks\n\nNone`)
- This ensures every field is grep-able and downstream tools can rely on consistent schema

### Open (Claude's discretion)
- Section ordering in body: Description → Environment → Linked Issues → Subtasks → Worklogs → Comments → Attachments
- Frontmatter field ordering: key, summary, type, status, status_category, priority, resolution, project, project_key → people → labels/components → parent → versions → dates → time tracking → votes/watches

## Deferred Ideas
None.
