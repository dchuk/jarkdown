# Phase 2: Custom Fields & ADF — Research

## Findings

### 1. Codebase Structure & ADF Parser Extension Points

The current `_parse_adf_to_markdown()` method in `markdown_converter.py` (lines 306-442) implements a recursive descent parser with clear extension patterns:

**Current Coverage (12 node types):**
- Block nodes: `doc`, `paragraph`, `heading`, `codeBlock`, `blockquote`, `bulletList`, `orderedList`, `mediaSingle`, `media`
- Inline nodes: `text`, `mention`, `hardBreak`
- Text marks: `strong`, `em`, `code`, `link`

**Extension Point Pattern:**
Each node type is handled as an `elif doc_type == "typename"` branch. The pattern is:
1. Extract content array (if block node)
2. Extract attrs dict (if node has attributes)
3. Recursively parse children
4. Apply markdown formatting wrapping

The fallback `else` clause already handles unknown types by attempting content processing.

### 2. ADF Specification — Missing Node Types

Block-level nodes needed:
- `table` (with `tableRow`, `tableHeader`, `tableCell` children)
- `panel` (info/warning/note/error subtypes via attrs)
- `expand` (collapsible blocks)
- `rule` (horizontal rule / divider)
- `mediaGroup` (gallery container for multiple media)

Inline nodes needed:
- `emoji` (attrs: shortName, id)
- `status` (attrs: text, color, localId)
- `date` (attrs: timestamp)
- `inlineCard` (attrs: url, data)

List-related nodes:
- `taskList` (checkbox list items)
- `decisionList` (decision/status tracking items)

**Nesting Rules:**
- `tableRow`/`tableHeader` can only contain `tableCell` nodes
- `tableCell` can contain block AND inline content
- `expand` contains a `title` (single paragraph) + `content` (array of blocks)
- `listItem` can nest other lists

### 3. Custom Fields API

- Custom fields appear as `customfield_XXXXX` keys in the `fields` object
- Metadata via `GET /rest/api/3/field` — returns id, name, schema, customId
- Schema contains: `type` (array, string, option, user, date), `custom`, `customId`
- Must fetch all fields; no single-field endpoint

**Type rendering patterns:**
- String/text: Direct string value
- Select: `{value: "...", id: "..."}`
- Multi-select: Array of option objects
- User/People: `{displayName: "...", accountId: "..."}`
- Date: ISO 8601 string
- Number: Direct numeric value
- Rich text (ADF): Dict with `type: "doc"` structure — reuse ADF parser

### 4. TOML Configuration

- `tomllib` built into Python 3.11+ (PEP 680, read-only)
- `tomli>=2.0.0` backport for Python 3.8-3.10
- Conditional import pattern: `sys.version_info >= (3, 11)`

### 5. Cache Directory

- `platformdirs>=4.0.0` for XDG-compliant cache dirs
- `user_config_dir("jarkdown")` → `~/.config/jarkdown/` on Linux/macOS

## Relevant Patterns

1. **ADF Parser Enhancement:** Each new node type adds an `elif` branch — extract attrs/content, recurse children, wrap in markdown
2. **Table rendering:** Pipe-delimited markdown with column count from first row
3. **Panel rendering:** Blockquote + type prefix (e.g., `> **Note:**`)
4. **Expand rendering:** Bold header + content (best-effort, no HTML `<details>`)
5. **Custom field type dispatch:** Schema type inspection → specific renderer, with generic fallback via value shape
6. **Config precedence:** CLI args > .toml file > hardcoded defaults

## Risks

1. **Table cell complexity:** ADF tables with nested lists/emphasis don't map cleanly to markdown tables — need single-line flattening
2. **Custom field type proliferation:** New Jira field types may not be anticipated — need robust generic fallback
3. **TOML compatibility:** `tomli` backport may have edge-case differences from `tomllib` — pin version, test on CI
4. **Cache coherency:** Field metadata changes between cache refresh — 24h TTL acceptable per design decision
5. **Recursive depth:** Deeply nested ADF documents could cause issues — add depth tracking

## Recommendations

1. **Add ADF nodes in priority order:** table > panel > expand > rule > emoji > inlineCard > status > date > taskList > decisionList
2. **New classes:** `FieldMetadataCache` (caching), `CustomFieldRenderer` (type dispatch), `ConfigManager` (TOML + CLI)
3. **Dependencies to add:** `platformdirs>=4.0.0`, `tomli>=2.0.0;python_version<'3.11'`
4. **Testing:** ADF fixture per node type, custom field fixtures per type, cache TTL tests, config precedence tests
5. **Extend existing parser** rather than adding external ADF library — avoids new deps, maintains control
