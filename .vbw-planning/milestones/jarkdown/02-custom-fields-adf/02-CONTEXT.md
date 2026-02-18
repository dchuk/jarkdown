# Phase 2: Custom Fields & ADF — Context

Gathered: 2026-02-17
Calibration: architect

## Phase Boundary
Support configurable custom field rendering and complete ADF document format parsing. Covers REQ-07 (custom field mapping) and REQ-08 (complete ADF support).

## Decisions

### Custom Field Discovery
- Fetch field metadata from `/rest/api/3/field` and cache to `~/.config/jarkdown/` (XDG-compliant)
- One cache file per Jira domain with a timestamp in the filename
- 24-hour TTL — re-fetch when stale
- Degrade gracefully: if cache is stale and API unreachable, use raw `customfield_12345` IDs with a warning to the user
- CLI flag `--refresh-fields` to force cache refresh

### Custom Field Selection UX
- Default behavior: include all custom fields with non-null values
- Config file: `.jarkdown.toml` (TOML format) for persistent include/exclude lists
- CLI flags: `--include-fields` and `--exclude-fields` for per-run overrides
- CLI flags override config file when both are present

### ADF Node Coverage
- Full coverage of all missing ADF nodes in Phase 2 (no deferral):
  - table → Markdown tables
  - panel (info, warning, note, error) → blockquote with type prefix header
  - expand → bold header + indented content (best-effort, no HTML)
  - emoji → Unicode character or `:name:` shortcode
  - inlineCard → regular `[text](url)` link
  - taskList/taskItem → `- [ ]` / `- [x]` checkboxes
  - decisionList/decisionItem → numbered list or blockquote
  - status (colored lozenges) → bold text
  - date → formatted date string
  - rule → `---` horizontal rule
- Rendering strategy: best-effort Markdown only, no HTML fallbacks
- Pure Markdown output throughout

### Custom Field Type Rendering
- Type-aware rendering using field metadata (select → value, user → displayName, date → formatted, array → comma-joined)
- Generic fallback via value shape inspection when type metadata is unavailable:
  - string → as-is
  - dict with 'value' key → extract value
  - dict with 'displayName' key → extract name
  - list → comma-join extracted values
- All custom fields appear in a dedicated `## Custom Fields` body section (not in frontmatter)
- Custom text area fields containing ADF content are parsed through the existing ADF parser

### Open (Claude's discretion)
- Exact TOML config schema (field names, nesting structure)
- Cache filename format (e.g., `fields-{domain}-{timestamp}.json`)
- Order of custom fields in output (alphabetical by display name vs. Jira API order)
- Handling of empty/null custom fields in "all with values" mode (skip vs. show as "None")

## Deferred Ideas
None.
