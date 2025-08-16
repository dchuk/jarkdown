# Technical Design Revision: Comment Exporting Feature

## 1. Introduction

This document revises the technical design for extending the `jarkdown` tool to support Jira issue comments. This revision is based on feedback that the original design did not align with the desired Markdown formatting and made incorrect assumptions about the Jira API's comment data structure.

The goal remains to append a formatted "Comments" section to the Markdown export, including the comment author, date, and the full body content, while ensuring any attachments referenced in comments are correctly linked.

## 2. Key Revisions

This design supersedes the previous version with the following changes:

1.  **Improved Markdown Formatting**: Comments will be separated by horizontal rules (`---`) instead of using blockquotes, creating a cleaner and more readable layout.
2.  **Corrected API Data Handling**: The design now acknowledges that Jira's REST API returns comment bodies in a structured JSON format (Atlassian Document Format), not pre-rendered HTML. This requires a more sophisticated parsing strategy.
3.  **Clarification on Test Data**: This document explicitly states that the `.json` files used in the `tests/data` directory are for mocking API responses during testing and are not part of the user-facing output.

## 3. Solution Overview

The implementation will follow the existing modular architecture, with targeted changes to the `JiraApiClient` and `MarkdownConverter`.

The high-level steps are:
1.  **Modify the API call** to request the `comment` field from the Jira API.
2.  **Create a new method** within the `MarkdownConverter` to parse the Atlassian Document Format, convert it to Markdown, and format it for readability.
3.  **Reuse the existing link replacement logic** to handle any inline attachments within the comment bodies.
4.  **Update the main composition method** to append the formatted comments section to the final Markdown file.
5.  **Add comprehensive tests** to validate the new functionality.

## 4. Detailed Implementation Plan

### Step 4.1: Update `JiraApiClient`

The `fetch_issue` method in `jira_api_client.py` will be updated to include comments in the API request.

-   **Action:** Modify the `fields` parameter in the `fetch_issue` method to include `comment`. The `expand` parameter is not necessary for fetching the raw comment body.

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
        'fields': fields
    }
    ```

### Step 4.2: Update `MarkdownConverter`

The `MarkdownConverter` in `markdown_converter.py` will handle the logic for parsing and formatting the comments.

-   **Action 1: Create a `_compose_comments_section` method.**
    -   This private helper method will generate the Markdown for the "Comments" section.
    -   It will take the `issue_data` and `downloaded_attachments` as input.
    -   It will check if `issue_data['fields']['comment']['comments']` exists and is not empty.
    -   If comments exist, it will iterate through each comment object. For each comment, it will:
        1.  Extract the author's display name (`comment['author']['displayName']`).
        2.  Extract and format the creation date (`comment['created']`).
        3.  Extract the comment body, which is in Atlassian Document Format.
        4.  **Parse the Atlassian Document Format** to extract text, links, and mentions. A simple recursive parser will be implemented to handle the nested structure.
        5.  Convert the parsed content to GitHub-flavored Markdown.
        6.  Replace attachment links in the converted Markdown using the existing `replace_attachment_links` method.
        7.  Format the output with a sub-heading for the author and date, followed by the comment body, and separated by a horizontal rule.

-   **Action 2: Update the `compose_markdown` method.**
    -   The main `compose_markdown` method will be modified to call the new `_compose_comments_section` method.
    -   The generated comments section will be appended to the Markdown output, placed after the "Description" section and before the "Attachments" section.

-   **Example Comment Formatting:**
    ```markdown
    ## Comments

    **John Doe** - _2025-08-16 10:30 AM_

    This is the first comment. It looks like we need to update the design mockups.

    Here is the new version:
    ![new_mockup.png](new_mockup.png)

    ---

    **Jane Smith** - _2025-08-16 11:15 AM_

    Thanks, John! This looks much better. I have approved the changes.

    ---
    ```

### Step 4.3: No Changes to `AttachmentHandler`

The existing `AttachmentHandler` is sufficient and requires no changes. The `replace_attachment_links` function in the `MarkdownConverter` will be reused to handle attachments referenced in comments.

## 5. Testing Strategy

The testing strategy will be updated to reflect the revised implementation.

-   **Test Data:**
    -   A new mock API response file, `tests/data/issue_with_comments.json`, will be created. This file will contain a `comment` object with an array of comments in Atlassian Document Format. One comment will reference an attachment.

-   **Component Tests (`test_components.py`):**
    -   Add a new test, `test_comments_section_formatting`, to `TestMarkdownConverter`. This test will use the new `issue_with_comments.json` fixture to verify:
        -   The "Comments" section is generated with the correct horizontal rule formatting.
        -   Author names and dates are formatted as expected.
        -   Comment bodies are correctly parsed from Atlassian Document Format and converted to Markdown.
        -   Attachment links within comments are properly replaced.
    -   Add a test case, `test_issue_with_no_comments`, to ensure that if an issue has no comments, the "Comments" section is not added.

-   **CLI / End-to-End Tests (`test_cli.py`):**
    -   Add a new E2E test, `test_successful_download_with_comments`, that runs the full `jarkdown` command using the `issue_with_comments.json` mock data.
    -   This test will assert that the final generated `.md` file contains the correctly formatted "Comments" section.

## 6. Expected Outcome

After implementing this revised design, the `jarkdown` tool will correctly parse and export a Jira issue's description, attachments, and all of its comments into a single, well-formatted, and self-contained Markdown file.
