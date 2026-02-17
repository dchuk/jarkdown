# jarkdown Roadmap

**Goal:** jarkdown

**Scope:** 4 phases

## Progress
| Phase | Status | Plans | Tasks | Commits |
|-------|--------|-------|-------|---------|
| 1 | Pending | 0 | 0 | 0 |
| 2 | Pending | 0 | 0 | 0 |
| 3 | Pending | 0 | 0 | 0 |
| 4 | Pending | 0 | 0 | 0 |

---

## Phase List
- [ ] [Phase 1: Standard Field Coverage](#phase-1-standard-field-coverage)
- [ ] [Phase 2: Custom Fields & ADF](#phase-2-custom-fields-adf)
- [ ] [Phase 3: uv Migration & Tooling](#phase-3-uv-migration-tooling)
- [ ] [Phase 4: Bulk Export & JQL](#phase-4-bulk-export-jql)

---

## Phase 1: Standard Field Coverage

**Goal:** Expand markdown output to cover all standard Jira fields returned by the API, closing the gap identified from PSOP-419

**Requirements:** REQ-06

**Success Criteria:**
- project name/key included in frontmatter
- issuelinks rendered as a linked issues section
- subtasks listed with keys and summaries
- time tracking fields (estimate, spent, remaining) in frontmatter
- progress/aggregateprogress shown
- votes/watches count in frontmatter
- worklog entries rendered
- duedate and environment included
- statusCategory in frontmatter
- All fields from PSOP-419 that have values appear in output

**Dependencies:** None

---

## Phase 2: Custom Fields & ADF

**Goal:** Support configurable custom field rendering and complete ADF document format parsing

**Requirements:** REQ-07, REQ-08

**Success Criteria:**
- Custom fields with values rendered in a dedicated section
- Field name resolution via Jira field metadata API
- ADF tables converted to Markdown tables
- ADF panels rendered as blockquotes with headers
- ADF expand blocks, emoji, inline cards, task lists handled
- Config file or CLI flag for field selection

**Dependencies:** Phase 1

---

## Phase 3: uv Migration & Tooling

**Goal:** Migrate from pip to uv package manager for cleaner install and usage experience

**Requirements:** REQ-11

**Success Criteria:**
- uv.lock file replaces pip dependency resolution
- pyproject.toml updated for uv compatibility
- README and docs updated with uv install instructions
- CI workflows updated to use uv
- Development setup uses uv for venv and dependency management

**Dependencies:** Phase 2

---

## Phase 4: Bulk Export & JQL

**Goal:** Enable exporting multiple issues at once via key lists or JQL queries

**Requirements:** REQ-09, REQ-10

**Success Criteria:**
- Accept multiple issue keys on CLI
- Accept --jql flag with JQL query string
- Batch API calls with rate limiting
- Summary index file listing all exported issues
- Progress reporting during bulk operations
- Error handling for partial failures in batch

**Dependencies:** Phase 3

