# Technical Design: Comment Exporting Feature

## 1. Introduction

This document outlines the technical design for extending the `jarkdown` tool to support the fetching, conversion, and exporting of Jira issue comments. This feature was identified as a "Day 2 Requirement" in the original technical design and is the next logical step in creating a complete, offline archive of a Jira issue.

The goal is to append a formatted "Comments" section to the Markdown export, including the comment author, date, and the full body content, while ensuring any attachments referenced in comments are correctly linked.

## 2. Solution Overview

The implementation will follow the existing modular architecture, primarily extending the `JiraApiClient` to fetch comment data and the `MarkdownConverter` to process and format it.

The high-level steps are:
1.  **Modify the API call** to request the `comment` field and its rendered HTML body from the Jira API.
2.  **Create a new method** within the `MarkdownConverter` to iterate through the comments, convert their HTML bodies to Markdown, and format them for readability.
3.  **Reuse the existing link replacement logic** to handle any inline attachments within the comment bodies.
4.  **Update the main composition method** to append the formatted comments section to the final Markdown file.
5.  **Add comprehensive tests** to validate the new functionality.

## 3. Detailed Implementation Plan

### Step 3.1: Update `JiraApiClient`

The `fetch_issue` method in `jira_api_client.py` will be updated to include comments in the API request.

-   **Action:** Modify the `fields` and `expand` parameters in the `fetch_issue` method.
    -   The `fields` string will be updated to include `comment`.
    -   The `expand` string will be updated to include `renderedFields` for the comments. The Jira API documentation indicates that `renderedFields` will expand the body of comments, so a separate `comment.renderedBody` is not needed.

-   **Current Code:**
    ```python
    fields = "summary,description,issuetype,status,priority,attachment,assignee,reporter,created,updated"
    params = {
        'fields': fields,
        'expand': 'renderedFields'
    }
    ```

-   **New Code:**
    ```python
    fields = "summary,description,issuetype,status,priority,attachment,assignee,reporter,created,updated,comment"
    params = {
        'fields': fields,
        'expand': 'renderedFields' # This also expands comment bodies
    }
    ```

### Step 3.2: Update `MarkdownConverter`

The `MarkdownConverter` in `markdown_converter.py` will handle the logic for formatting the comments.

-   **Action 1: Create a `_compose_comments_section` method.**
    -   This private helper method will be responsible for generating the Markdown for the "Comments" section.
    -   It will take the `issue_data` and `downloaded_attachments` as input.
    -   It will check if `issue_data['fields']['comment']['comments']` exists and is not empty.
    -   If comments exist, it will iterate through each comment object. For each comment, it will:
        1.  Extract the author's display name (`comment['author']['displayName']`).
        2.  Extract and format the creation date (`comment['created']`).
        3.  Extract the HTML body from `comment['renderedBody']`.
        4.  Convert the HTML body to Markdown using the existing `convert_html_to_markdown` method.
        5.  Replace attachment links in the converted Markdown using the existing `replace_attachment_links` method.
        6.  Format the output using a blockquote (`>`) for the comment body and a sub-heading or bold text for the author and date.

-   **Action 2: Update the `compose_markdown` method.**
    -   The main `compose_markdown` method will be modified to call the new `_compose_comments_section` method.
    -   The generated comments section will be appended to the Markdown output, logically placed after the "Description" section and before the "Attachments" section.

-   **Example Comment Formatting:**
    ```markdown
    ## Comments

    **John Doe** - _2025-08-16 10:30 AM_
    > This is the first comment. It looks like we need to update the design mockups.
    >
    > Here is the new version:
    > ![new_mockup.png](new_mockup.png)

    **Jane Smith** - _2025-08-16 11:15 AM_
    > Thanks, John! This looks much better. I have approved the changes.
    ```

### Step 3.3: No Changes to `AttachmentHandler`

The current design for handling attachments is sufficient. The Jira API provides a single, flat list of all attachments for an issue. The existing `replace_attachment_links` function in the `MarkdownConverter` is generic enough that it can be used on any piece of Markdown text (the description or a comment body) to replace URLs with local file links. No changes are required for the attachment downloading logic itself.

## 4. Testing Strategy

A new set of tests will be added to ensure the comment exporting functionality is working correctly and does not introduce regressions.

-   **Test Data:**
    -   A new mock API response file, `tests/data/issue_with_comments.json`, will be created. This file will be a copy of `issue_with_attachments.json` but will include a `comment` object containing an array of at least two comments. One of these comments will reference an attachment.

-   **Component Tests (`test_components.py`):**
    -   Add a new test, `test_comments_section_formatting`, to `TestMarkdownConverter`. This test will use the new `issue_with_comments.json` fixture to verify:
        -   The "Comments" section is generated correctly.
        -   Author names and dates are formatted as expected.
        -   Comment bodies are correctly converted from HTML to Markdown.
        -   Attachment links within comments are properly replaced.
    -   Add a test case, `test_issue_with_no_comments`, to ensure that if an issue has no comments, the "Comments" section is not added to the output.

-   **CLI / End-to-End Tests (`test_cli.py`):**
    -   Add a new E2E test, `test_successful_download_with_comments`, that runs the full `jarkdown` command using the `issue_with_comments.json` mock data.
    -   This test will assert that the final generated `.md` file contains the correctly formatted "Comments" section.

## 5. Expected Outcome

After implementing this design, the `jarkdown` tool will be able to export a Jira issue's description, attachments, and all of its comments into a single, self-contained Markdown file, providing a more complete offline record of the issue.
