## Findings

### 1. `issuelinks`

Array of link objects. Each entry has exactly one of `inwardIssue` or `outwardIssue` — never both.

```json
"issuelinks": [
  {
    "id": "10001",
    "type": {
      "id": "10000",
      "name": "Blocks",
      "inward": "is blocked by",
      "outward": "blocks"
    },
    "inwardIssue": {
      "id": "10200",
      "key": "FEAT-1",
      "fields": {
        "summary": "Build login page",
        "status": {
          "name": "In Progress",
          "statusCategory": { "key": "indeterminate", "name": "In Progress" }
        },
        "priority": { "name": "High" },
        "issuetype": { "name": "Story", "subtask": false }
      }
    }
  }
]
```

Direction model: `inwardIssue` present → use `type.inward` as label. `outwardIssue` present → use `type.outward`.

### 2. `subtasks`

Lightweight array — only `id`, `key`, `self`, and `fields.{summary, status, priority, issuetype}`.

```json
"subtasks": [
  {
    "id": "10300",
    "key": "PROJ-124",
    "fields": {
      "summary": "Write unit tests",
      "status": { "name": "To Do", "statusCategory": { "key": "new", "name": "To Do" } },
      "priority": { "name": "Medium" },
      "issuetype": { "name": "Sub-task", "subtask": true }
    }
  }
]
```

### 3. `timetracking`

```json
"timetracking": {
  "originalEstimate": "1d 2h",
  "originalEstimateSeconds": 36000,
  "remainingEstimate": "3h 25m",
  "remainingEstimateSeconds": 12300,
  "timeSpent": "6h",
  "timeSpentSeconds": 21600
}
```

Entire object is `null` if time tracking disabled globally. Individual sub-keys are **absent** (not null) when no value is set.

### 4. `worklog`

Paginated wrapper, hard-capped at 20 entries embedded:

```json
"worklog": {
  "startAt": 0,
  "maxResults": 20,
  "total": 32,
  "worklogs": [
    {
      "author": { "displayName": "Mia Krystof" },
      "updateAuthor": { "displayName": "Mia Krystof" },
      "comment": { "type": "doc", "version": 1, "content": [...] },
      "started": "2021-01-17T12:34:00.000+0000",
      "timeSpent": "3h 20m",
      "timeSpentSeconds": 12000
    }
  ]
}
```

Comment field is ADF. Can be null/absent/ADF object.

### 5. `votes`

```json
"votes": { "self": "...", "votes": 5, "hasVoted": false }
```

No voters array embedded — requires separate API call.

### 6. `watches`

```json
"watches": { "self": "...", "watchCount": 3, "isWatching": false }
```

No watchers array embedded — requires separate API call.

### 7. `progress` and `aggregateprogress`

```json
"progress": { "progress": 21600, "total": 36000, "percent": 60 },
"aggregateprogress": { "progress": 43200, "total": 72000, "percent": 60 }
```

Values in seconds. Both may be `{"progress": 0, "total": 0, "percent": 0}` when no tracking exists.

### 8. `project`

```json
"project": { "id": "10000", "key": "EX", "name": "Example Project", "projectTypeKey": "software" }
```

Always present on valid issues.

### 9. `duedate`

Plain `YYYY-MM-DD` string or `null`.

### 10. `environment`

ADF format in API v3 (same structure as description). `renderedFields.environment` may return HTML. Can be null.

### 11. `status.statusCategory`

4 fixed categories: `new` (To Do), `indeterminate` (In Progress), `done` (Done), `undefined` (No Category).

```json
"statusCategory": { "id": 4, "key": "indeterminate", "colorName": "yellow", "name": "In Progress" }
```

## Relevant Patterns

- All 11 fields are already returned by existing API call (`fields=*all&expand=renderedFields`). No changes to `jira_api_client.py` needed.
- `_generate_metadata_dict()` is the extension point for frontmatter fields.
- `compose_markdown()` is the extension point for new body sections.
- `_parse_adf_to_markdown()` already handles ADF → markdown conversion (reuse for environment, worklog comments).
- Null/absent guards should use `or {}` / `or []` patterns consistent with existing code.

## Risks

- **worklog pagination**: Embedded worklogs capped at 20. When `total > maxResults`, remaining entries silently truncated. Must detect and warn in output.
- **timetracking null**: Entire object is null when globally disabled — not just empty.
- **timetracking absent keys**: Individual keys like `timeSpent` are absent (not null) when no value set.
- **environment ADF bug**: `renderedFields.environment` may return raw ADF instead of HTML. Fallback to ADF parsing required.
- **issuelinks direction**: Must check for `inwardIssue` vs `outwardIssue` — they're mutually exclusive per entry.
- **subtask fields**: Only 4 fields guaranteed in subtask `fields`. Don't assume others exist.
- **progress zero-state**: Both progress fields return `{0, 0, 0}` when no estimates, not null.

## Recommendations

- Extend `_generate_metadata_dict()` for: project_key, project_name, status_category, duedate, votes, watch_count, time tracking fields, progress
- Add new compose methods for body sections: `_compose_linked_issues_section()`, `_compose_subtasks_section()`, `_compose_worklogs_section()`, `_compose_environment_section()`
- Reuse `_parse_adf_to_markdown()` for worklog comments and environment field
- Add truncation warning for worklogs when total > maxResults
- New test fixtures needed for each field type
- Empty field policy: always show sections with "None" and frontmatter with null/0 (per CONTEXT.md decisions)
