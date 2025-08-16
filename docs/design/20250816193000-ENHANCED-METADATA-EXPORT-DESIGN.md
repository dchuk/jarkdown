
# Technical Design: Enhanced Metadata Export

**Date:** 2025-08-16
**Author:** Gemini
**Status:** Proposed

## 1. Background

The Jarkdown tool currently exports a limited, hardcoded set of metadata from a Jira issue (e.g., summary, type, status, priority, assignee, reporter). The user request is to expand this functionality to fetch and include **all** available metadata for an issue, such as labels, components, parent issue links, versions, resolution status, and more.

This document outlines the technical plan to implement this enhancement, ensuring the output is structured, scalable, and useful.

## 2. Current Implementation Analysis

The current data flow for metadata is as follows:

1.  **`JiraApiClient.fetch_issue`**: This method makes a GET request to the `/rest/api/3/issue/{issue_key}` endpoint. It explicitly requests a small, predefined set of fields using the `fields` query parameter: `fields=summary,description,issuetype,status,priority,attachment,assignee,reporter,created,updated,comment`. This is the primary bottleneck preventing the retrieval of complete metadata.
2.  **`MarkdownConverter.compose_markdown`**: This method receives the partial issue data. It extracts the known metadata fields and formats them as a simple list of key-value pairs with bolded labels at the top of the Markdown file. This format is not ideal for a large, variable number of metadata fields as it would become visually cluttered and difficult to parse programmatically.
3.  **Test Data**: The mock API responses in `tests/data/` reflect this limited field set, which is insufficient for testing the new, comprehensive metadata export.

## 3. Proposed Changes

To address the limitations, we will modify both the API client and the Markdown converter. The core proposal is to fetch all fields and present them in a structured YAML frontmatter block at the top of the exported Markdown file.

### 3.1. Step 1: Modify Jira API Client to Fetch All Fields

The `fetch_issue` method in `src/jarkdown/jira_api_client.py` will be updated to retrieve all available fields for an issue.

-   **Action:** Change the `fields` parameter in the API call.
-   **File:** `src/jarkdown/jira_api_client.py`
-   **Current Code:**
    ```python
    fields = "summary,description,issuetype,status,priority,attachment,assignee,reporter,created,updated,comment"
    params = {"fields": fields, "expand": "renderedFields"}
    ```
-   **Proposed Code:**
    ```python
    # The '*all' value instructs Jira to return all non-system fields.
    # We continue to expand renderedFields for rich text content.
    params = {"fields": "*all", "expand": "renderedFields"}
    ```
    *(Note: The `fields` variable can be removed entirely)*

This single change will ensure that the application receives the full issue data from the Jira API.

### 3.2. Step 2: Implement YAML Frontmatter in Markdown Converter

The current metadata format is not scalable. We will replace it with YAML frontmatter, a widely-used standard for embedding structured metadata in Markdown files.

-   **Action:** Refactor the `compose_markdown` method in `src/jarkdown/markdown_converter.py` to generate a YAML block.
-   **File:** `src/jarkdown/markdown_converter.py`

The new process within `compose_markdown` will be:
1.  Create a new private helper method, e.g., `_generate_metadata_dict(fields)`.
2.  This method will parse the `fields` object from the API response and build a clean Python dictionary containing the desired metadata. It will handle the extraction and simplification of complex Jira field objects.
3.  The main `compose_markdown` method will then use a library like `PyYAML` (which would need to be added as a dependency) or a simple custom formatter to serialize this dictionary into a YAML string.
4.  This YAML string will be wrapped in `---` separators and prepended to the rest of the Markdown content.

### 3.3. Metadata Mapping and Formatting

The `_generate_metadata_dict` helper will implement the following mapping from the Jira API response to the final YAML keys. Fields that are empty or `None` in the Jira response should be omitted from the YAML output.

| YAML Key | Jira API Path (`fields.*`) | Data Type | Notes |
| :--- | :--- | :--- | :--- |
| `key` | `issue.key` | String | Already available |
| `summary` | `summary` | String | |
| `type` | `issuetype.name` | String | |
| `status` | `status.name` | String | |
| `priority` | `priority.name` | String | |
| `resolution` | `resolution.name` | String | Omit if unresolved |
| `assignee` | `assignee.displayName` | String | Omit if unassigned |
| `reporter` | `reporter.displayName` | String | |
| `creator` | `creator.displayName` | String | |
| `labels` | `labels` | List[String] | `['label1', 'label2']` |
| `components` | `components` | List[String] | Extract `name` from each object |
| `parent_key` | `parent.key` | String | For sub-tasks |
| `parent_summary`| `parent.fields.summary` | String | For sub-tasks |
| `affects_versions`| `versions` | List[String] | Extract `name` from each object |
| `fix_versions` | `fixVersions` | List[String] | Extract `name` from each object |
| `created_at` | `created` | String (ISO) | |
| `updated_at` | `updated` | String (ISO) | |
| `resolved_at` | `resolutiondate` | String (ISO) | Omit if unresolved |

**Example Output:**

```markdown
---
key: PROJ-123
summary: This is an example ticket
type: Story
status: In Progress
priority: High
resolution: null
assignee: Ada Lovelace
reporter: Charles Babbage
creator: Charles Babbage
labels:
  - backend
  - performance
components:
  - API
  - Database
parent_key: PROJ-100
parent_summary: Epic for Q3 Features
affects_versions:
  - v1.1
fix_versions:
  - v1.2
created_at: '2025-08-15T10:00:00.000+0000'
updated_at: '2025-08-16T14:30:00.000+0000'
resolved_at: null
---

# [PROJ-123](https://your-domain.atlassian.net/browse/PROJ-123): This is an example ticket

## Description

... rest of the markdown file ...
```

## 4. Testing Strategy

The existing test suite must be updated to validate this new functionality.

1.  **Update Mock API Data:**
    -   The JSON files in `tests/data/` (e.g., `issue_with_attachments.json`) must be updated to be a more complete representation of a Jira issue response when `fields=*all` is used. This includes adding `labels`, `components`, `parent`, `fixVersions`, etc.

2.  **Update Unit Tests:**
    -   Modify tests in `tests/test_components.py` that check the output of `MarkdownConverter`.
    -   Instead of checking for the old bolded key-value pairs, the tests should parse the YAML frontmatter from the output string.
    -   Add assertions to verify:
        -   The presence of the `---` separators.
        -   The correctness of key metadata fields (`key`, `summary`, `status`).
        -   The correct formatting of list-based fields (`labels`, `components`).
        -   The graceful omission of fields that are `null` or not present in the mock data (e.g., a ticket with no `parent` or `labels`).

## 5. Dependencies

This change may introduce a new dependency to handle YAML serialization reliably.

-   **`PyYAML`**: This is the standard library for YAML in Python. It should be added to `pyproject.toml`.

## 6. Summary of Work

1.  Update `JiraApiClient.fetch_issue` to use `fields=*all`.
2.  Add `PyYAML` as a project dependency.
3.  Refactor `MarkdownConverter.compose_markdown` to generate and prepend a YAML frontmatter block.
4.  Implement the logic for mapping and cleaning the full Jira `fields` object into a Python dictionary.
5.  Update the mock data in `tests/data/` to reflect a complete API response.
6.  Update the unit tests in `tests/test_components.py` to parse and validate the new YAML frontmatter output.
