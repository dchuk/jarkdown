"""Tests for the refactored component classes."""

import json
from unittest.mock import Mock
import pytest
import requests

from jarkdown.jira_api_client import JiraApiClient
from jarkdown.attachment_handler import AttachmentHandler
from jarkdown.markdown_converter import MarkdownConverter
from jarkdown.exceptions import (
    JiraApiError,
    AuthenticationError,
    IssueNotFoundError,
    AttachmentDownloadError,
)


@pytest.fixture
def api_client():
    """Create a JiraApiClient instance"""
    return JiraApiClient("example.atlassian.net", "test@example.com", "test-token-123")


@pytest.fixture
def attachment_handler(api_client):
    """Create an AttachmentHandler instance"""
    return AttachmentHandler(api_client)


@pytest.fixture
def markdown_converter():
    """Create a MarkdownConverter instance"""
    return MarkdownConverter("https://example.atlassian.net", "example.atlassian.net")


@pytest.fixture
def issue_with_attachments():
    """Load mock issue data with attachments"""
    with open("tests/data/issue_with_attachments.json") as f:
        return json.load(f)


@pytest.fixture
def issue_no_description():
    """Load mock issue data without description"""
    with open("tests/data/issue_no_description.json") as f:
        return json.load(f)


@pytest.fixture
def issue_no_attachments():
    """Load mock issue data without attachments"""
    with open("tests/data/issue_no_attachments.json") as f:
        return json.load(f)


@pytest.fixture
def issue_with_comments():
    """Load mock issue data with comments"""
    with open("tests/data/issue_with_comments.json") as f:
        return json.load(f)


class TestJiraApiClient:
    """Tests for JiraApiClient class"""

    def test_init_with_valid_credentials(self):
        """Test initialization sets up session correctly"""
        client = JiraApiClient(
            "example.atlassian.net", "test@example.com", "test-token-123"
        )

        assert client.domain == "example.atlassian.net"
        assert client.email == "test@example.com"
        assert client.api_token == "test-token-123"
        assert client.base_url == "https://example.atlassian.net"
        assert client.api_base == "https://example.atlassian.net/rest/api/3"
        assert client.session.auth == ("test@example.com", "test-token-123")
        assert client.session.headers["Accept"] == "application/json"
        assert client.session.headers["Content-Type"] == "application/json"

    def test_successful_api_call(self, api_client, issue_with_attachments, mocker):
        """Test successful API call returns JSON data"""
        mock_response = Mock()
        mock_response.raise_for_status = Mock()
        mock_response.json.return_value = issue_with_attachments

        mocker.patch.object(api_client.session, "get", return_value=mock_response)

        result = api_client.fetch_issue("TEST-123")

        assert result == issue_with_attachments
        api_client.session.get.assert_called_once_with(
            "https://example.atlassian.net/rest/api/3/issue/TEST-123",
            params={
                "fields": "summary,description,issuetype,status,priority,attachment,assignee,reporter,created,updated,comment",
                "expand": "renderedFields",
            },
        )

    def test_401_authentication_error(self, api_client, mocker):
        """Test 401 response raises AuthenticationError"""
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError()

        mocker.patch.object(api_client.session, "get", return_value=mock_response)

        with pytest.raises(AuthenticationError) as exc_info:
            api_client.fetch_issue("TEST-123")

        assert "401" in str(exc_info.value) or "Authentication" in str(exc_info.value)

    def test_404_not_found_error(self, api_client, mocker):
        """Test 404 response raises IssueNotFoundError"""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError()

        mocker.patch.object(api_client.session, "get", return_value=mock_response)

        with pytest.raises(IssueNotFoundError) as exc_info:
            api_client.fetch_issue("TEST-123")

        assert "TEST-123" in str(exc_info.value)

    def test_generic_http_error(self, api_client, mocker):
        """Test generic HTTP error raises JiraApiError"""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(
            "Server error"
        )

        mocker.patch.object(api_client.session, "get", return_value=mock_response)

        with pytest.raises(JiraApiError) as exc_info:
            api_client.fetch_issue("TEST-123")

        assert exc_info.value.status_code == 500

    def test_network_error(self, api_client, mocker):
        """Test network error raises JiraApiError"""
        mocker.patch.object(
            api_client.session,
            "get",
            side_effect=requests.exceptions.ConnectionError("Network error"),
        )

        with pytest.raises(JiraApiError) as exc_info:
            api_client.fetch_issue("TEST-123")

        assert "Network error" in str(exc_info.value)


class TestAttachmentHandler:
    """Tests for AttachmentHandler class"""

    def test_single_attachment_download(self, attachment_handler, mocker, tmp_path):
        """Test downloading a single attachment"""
        attachment = {
            "filename": "test.pdf",
            "content": "https://example.atlassian.net/rest/api/3/attachment/content/123",
            "mimeType": "application/pdf",
            "size": 1024,
        }

        mock_response = Mock()
        mock_response.iter_content = Mock(return_value=[b"fake_content"])
        mocker.patch.object(
            attachment_handler.api_client,
            "download_attachment_stream",
            return_value=mock_response,
        )

        result = attachment_handler.download_attachment(attachment, tmp_path)

        assert result["filename"] == "test.pdf"
        assert result["original_filename"] == "test.pdf"
        assert result["mime_type"] == "application/pdf"
        assert (tmp_path / "test.pdf").exists()

        with open(tmp_path / "test.pdf", "rb") as f:
            assert f.read() == b"fake_content"

    def test_filename_conflict_resolution(self, attachment_handler, mocker, tmp_path):
        """Test filename conflict resolution adds counter"""
        attachment = {
            "filename": "test.pdf",
            "content": "https://example.atlassian.net/rest/api/3/attachment/content/123",
            "mimeType": "application/pdf",
            "size": 1024,
        }

        # Create existing file
        (tmp_path / "test.pdf").write_text("existing")

        mock_response = Mock()
        mock_response.iter_content = Mock(return_value=[b"new_content"])
        mocker.patch.object(
            attachment_handler.api_client,
            "download_attachment_stream",
            return_value=mock_response,
        )

        result = attachment_handler.download_attachment(attachment, tmp_path)

        assert result["filename"] == "test_1.pdf"
        assert result["original_filename"] == "test.pdf"
        assert (tmp_path / "test_1.pdf").exists()

        with open(tmp_path / "test_1.pdf", "rb") as f:
            assert f.read() == b"new_content"

    def test_download_error_raises_exception(
        self, attachment_handler, mocker, tmp_path
    ):
        """Test download error raises AttachmentDownloadError"""
        attachment = {
            "filename": "test.pdf",
            "content": "https://example.atlassian.net/rest/api/3/attachment/content/123",
            "mimeType": "application/pdf",
            "size": 1024,
        }

        mocker.patch.object(
            attachment_handler.api_client,
            "download_attachment_stream",
            side_effect=Exception("Download failed"),
        )

        with pytest.raises(AttachmentDownloadError) as exc_info:
            attachment_handler.download_attachment(attachment, tmp_path)

        assert "test.pdf" in str(exc_info.value)
        assert "Download failed" in str(exc_info.value)

    def test_multiple_attachments_download(self, attachment_handler, mocker, tmp_path):
        """Test downloading multiple attachments"""
        attachments = [
            {
                "filename": "file1.pdf",
                "content": "url1",
                "mimeType": "application/pdf",
                "size": 1024,
            },
            {
                "filename": "file2.jpg",
                "content": "url2",
                "mimeType": "image/jpeg",
                "size": 2048,
            },
        ]

        mock_response = Mock()
        mock_response.iter_content = Mock(return_value=[b"content"])
        mocker.patch.object(
            attachment_handler.api_client,
            "download_attachment_stream",
            return_value=mock_response,
        )

        results = attachment_handler.download_all_attachments(attachments, tmp_path)

        assert len(results) == 2
        assert results[0]["filename"] == "file1.pdf"
        assert results[1]["filename"] == "file2.jpg"
        assert (tmp_path / "file1.pdf").exists()
        assert (tmp_path / "file2.jpg").exists()

    def test_empty_attachments_list(self, attachment_handler, tmp_path):
        """Test empty attachments list returns empty list"""
        result = attachment_handler.download_all_attachments([], tmp_path)
        assert result == []

    def test_size_formatting(self, attachment_handler):
        """Test file size formatting"""
        assert attachment_handler._format_size(500) == "500.0 B"
        assert attachment_handler._format_size(1500) == "1.5 KB"
        assert attachment_handler._format_size(1500000) == "1.4 MB"
        assert attachment_handler._format_size(1500000000) == "1.4 GB"
        assert attachment_handler._format_size(1500000000000) == "1.4 TB"


class TestMarkdownConverter:
    """Tests for MarkdownConverter class"""

    def test_standard_html_conversion(self, markdown_converter):
        """Test basic HTML to Markdown conversion"""
        html = """
        <h1>Heading 1</h1>
        <h2>Heading 2</h2>
        <p>This is a <strong>bold</strong> paragraph with <em>italic</em> text.</p>
        <ul>
            <li>Item 1</li>
            <li>Item 2</li>
        </ul>
        <ol>
            <li>First</li>
            <li>Second</li>
        </ol>
        <p>Here's a <a href="https://example.com">link</a>.</p>
        <pre><code>code block</code></pre>
        <blockquote>This is a quote</blockquote>
        """

        result = markdown_converter.convert_html_to_markdown(html)

        assert "# Heading 1" in result
        assert "## Heading 2" in result
        assert "**bold**" in result
        assert "*italic*" in result
        assert "* Item 1" in result or "- Item 1" in result
        assert "1. First" in result
        assert "[link](https://example.com)" in result
        assert "> This is a quote" in result

    def test_empty_or_none_input(self, markdown_converter):
        """Test empty or None input returns empty string"""
        assert markdown_converter.convert_html_to_markdown("") == ""
        assert markdown_converter.convert_html_to_markdown(None) == ""

    def test_unhandled_html_tags_stripped(self, markdown_converter):
        """Test unhandled HTML tags are stripped"""
        html = '<p>Text with <custom-tag>custom</custom-tag> tag and <script>alert("hi")</script></p>'
        result = markdown_converter.convert_html_to_markdown(html)

        assert "custom-tag" not in result
        assert "script" not in result
        assert "alert" not in result
        assert "Text with custom tag and" in result

    def test_excessive_newlines_cleaned(self, markdown_converter):
        """Test excessive newlines are reduced"""
        html = "<p>First paragraph</p>\n\n\n\n<p>Second paragraph</p>\n\n\n\n\n<p>Third</p>"
        result = markdown_converter.convert_html_to_markdown(html)

        lines = result.split("\n")
        # Check no more than 2 consecutive empty lines
        empty_count = 0
        for line in lines:
            if line.strip() == "":
                empty_count += 1
                assert empty_count <= 2
            else:
                empty_count = 0

    def test_image_url_replacement(self, markdown_converter):
        """Test image URLs are replaced with local filenames"""
        content = "![Screenshot](https://example.atlassian.net/secure/attachment/12345/screenshot.png)"
        attachments = [
            {"filename": "screenshot.png", "original_filename": "screenshot.png"}
        ]

        result = markdown_converter.replace_attachment_links(content, attachments)

        assert "![Screenshot](screenshot.png)" in result
        assert "https://example.atlassian.net" not in result

    def test_link_url_replacement(self, markdown_converter):
        """Test link URLs are replaced with local filenames"""
        content = "[Document](https://example.atlassian.net/secure/attachment/12345/document.pdf)"
        attachments = [
            {"filename": "document.pdf", "original_filename": "document.pdf"}
        ]

        result = markdown_converter.replace_attachment_links(content, attachments)

        assert "[Document](document.pdf)" in result
        assert "https://example.atlassian.net" not in result

    def test_multiple_url_patterns(self, markdown_converter):
        """Test various Jira URL patterns are replaced"""
        content = """
        ![Image1](https://example.atlassian.net/rest/api/3/attachment/content/123)
        ![Image2](https://example.atlassian.net/secure/attachment/456/file.jpg)
        [Link](https://example.atlassian.net/jira/rest/api/3/attachment/content/789)
        """

        attachments = [
            {"filename": "image1.png", "original_filename": "image1.png"},
            {"filename": "file.jpg", "original_filename": "file.jpg"},
            {"filename": "doc.pdf", "original_filename": "doc.pdf"},
        ]

        result = markdown_converter.replace_attachment_links(content, attachments)

        # Should not contain any Jira URLs
        assert "atlassian.net" not in result

    def test_filename_with_spaces_encoded(self, markdown_converter):
        """Test filenames with spaces are URL encoded"""
        content = "![Image](https://example.atlassian.net/secure/attachment/123/my%20file.png)"
        attachments = [{"filename": "my file.png", "original_filename": "my file.png"}]

        result = markdown_converter.replace_attachment_links(content, attachments)

        # Filename should be URL encoded in markdown
        assert "![Image](my%20file.png)" in result

    def test_no_attachments_content_unchanged(self, markdown_converter):
        """Test content unchanged when no attachments"""
        content = """
        # Heading
        Some text with [regular link](https://example.com)
        """

        result = markdown_converter.replace_attachment_links(content, [])

        assert result == content

    def test_complete_markdown_structure(
        self, markdown_converter, issue_with_attachments
    ):
        """Test complete markdown generation"""
        attachments = [
            {
                "filename": "screenshot.png",
                "mime_type": "image/png",
                "original_filename": "screenshot.png",
            },
            {
                "filename": "document.pdf",
                "mime_type": "application/pdf",
                "original_filename": "document.pdf",
            },
        ]

        result = markdown_converter.compose_markdown(
            issue_with_attachments, attachments
        )

        # Check structure
        assert (
            "# [TEST-123](https://example.atlassian.net/browse/TEST-123): Test Issue with Attachments"
            in result
        )
        assert "**Type:** Task" in result
        assert "**Status:** To Do" in result
        assert "**Priority:** Medium" in result
        assert "**Assignee:** John Doe" in result
        assert "**Reporter:** Jane Smith" in result
        assert "## Description" in result
        assert "## Attachments" in result

        # Check attachments formatting
        assert "![screenshot.png](screenshot.png)" in result  # Image
        assert "[document.pdf](document.pdf)" in result  # Non-image

    def test_issue_no_description(self, markdown_converter, issue_no_description):
        """Test issue without description shows placeholder"""
        result = markdown_converter.compose_markdown(issue_no_description, [])

        assert "*No description provided*" in result

    def test_issue_no_attachments(self, markdown_converter, issue_no_attachments):
        """Test issue without attachments omits attachments section"""
        result = markdown_converter.compose_markdown(issue_no_attachments, [])

        assert "## Attachments" not in result

    def test_attachments_section_formatting(self, markdown_converter):
        """Test attachments section formatting"""
        issue_data = {
            "key": "TEST-123",
            "fields": {
                "summary": "Test",
                "issuetype": {"name": "Task"},
                "status": {"name": "Open"},
            },
            "renderedFields": {},
        }

        attachments = [
            {
                "filename": "image.png",
                "mime_type": "image/png",
                "original_filename": "image.png",
            },
            {
                "filename": "image.jpg",
                "mime_type": "image/jpeg",
                "original_filename": "image.jpg",
            },
            {
                "filename": "document.pdf",
                "mime_type": "application/pdf",
                "original_filename": "document.pdf",
            },
            {
                "filename": "data.csv",
                "mime_type": "text/csv",
                "original_filename": "data.csv",
            },
        ]

        result = markdown_converter.compose_markdown(issue_data, attachments)

        # Check all attachments are listed
        assert "- ![image.png](image.png)" in result
        assert "- ![image.jpg](image.jpg)" in result
        assert "- [document.pdf](document.pdf)" in result
        assert "- [data.csv](data.csv)" in result

    def test_comments_section_formatting(self, markdown_converter, issue_with_comments):
        """Test comments section formatting with attachments"""
        attachments = [
            {
                "filename": "error_log.txt",
                "mime_type": "text/plain",
                "original_filename": "error_log.txt",
            },
            {
                "filename": "new_mockup.png",
                "mime_type": "image/png",
                "original_filename": "new_mockup.png",
            },
        ]

        result = markdown_converter.compose_markdown(issue_with_comments, attachments)

        # Check comments section exists
        assert "## Comments" in result

        # Check first comment header and body
        assert "**John Doe** - _2025-08-16 10:30 AM_" in result
        assert (
            "This is the first comment. It looks like we need to update the design mockups."
            in result
        )
        assert "![new_mockup.png](new_mockup.png)" in result  # Attachment link replaced

        # Check second comment
        assert "**Jane Smith** - _2025-08-16 11:15 AM_" in result
        assert (
            "Thanks, John! This looks **much better**. I have approved the changes."
            in result
        )

        # Check third comment with list
        assert "**Alice Developer** - _2025-08-16 02:45 PM_" in result
        assert "I've reviewed the error logs attached to this issue" in result
        assert (
            "* Memory leak in the connection pool" in result
            or "- Memory leak in the connection pool" in result
        )
        assert (
            "* Incorrect timeout settings" in result
            or "- Incorrect timeout settings" in result
        )

        # Check that comments are separated by horizontal rules
        assert "---" in result

        # Ensure attachment URLs are replaced
        assert "/secure/attachment/" not in result
        assert "/attachment/content/" not in result

    def test_issue_with_no_comments(self, markdown_converter):
        """Test issue with no comments doesn't include comments section"""
        issue_data = {
            "key": "TEST-789",
            "fields": {
                "summary": "Issue without comments",
                "issuetype": {"name": "Task"},
                "status": {"name": "Open"},
                "comment": {"comments": [], "total": 0},
            },
            "renderedFields": {"description": "<p>Test description</p>"},
        }

        result = markdown_converter.compose_markdown(issue_data, [])

        # Comments section should not be present
        assert "## Comments" not in result
        assert "TEST-789" in result
        assert "Test description" in result

    def test_comments_with_empty_body(self, markdown_converter):
        """Test handling of comments with empty body"""
        issue_data = {
            "key": "TEST-999",
            "fields": {
                "summary": "Test",
                "issuetype": {"name": "Task"},
                "status": {"name": "Open"},
                "comment": {
                    "comments": [
                        {
                            "author": {"displayName": "Test User"},
                            "created": "2025-08-16T10:00:00.000+0000",
                            "body": "",
                            "renderedBody": "",
                        }
                    ]
                },
            },
            "renderedFields": {},
        }

        result = markdown_converter.compose_markdown(issue_data, [])

        assert "## Comments" in result
        assert "**Test User**" in result
        assert "*No comment body*" in result

    def test_adf_comment_parsing(self, markdown_converter):
        """Test parsing of Atlassian Document Format comments"""
        issue_data = {
            "key": "TEST-ADF",
            "fields": {
                "summary": "Test ADF Comments",
                "issuetype": {"name": "Task"},
                "status": {"name": "Open"},
                "comment": {
                    "comments": [
                        {
                            "author": {"displayName": "Test User"},
                            "created": "2025-08-16T10:00:00.000+0000",
                            "body": {
                                "type": "doc",
                                "version": 1,
                                "content": [
                                    {
                                        "type": "paragraph",
                                        "content": [
                                            {"type": "text", "text": "This is "},
                                            {
                                                "type": "text",
                                                "text": "bold",
                                                "marks": [{"type": "strong"}],
                                            },
                                            {"type": "text", "text": " and "},
                                            {
                                                "type": "text",
                                                "text": "italic",
                                                "marks": [{"type": "em"}],
                                            },
                                            {"type": "text", "text": " text."},
                                        ],
                                    },
                                    {
                                        "type": "bulletList",
                                        "content": [
                                            {
                                                "type": "listItem",
                                                "content": [
                                                    {
                                                        "type": "paragraph",
                                                        "content": [
                                                            {
                                                                "type": "text",
                                                                "text": "First item",
                                                            }
                                                        ],
                                                    }
                                                ],
                                            },
                                            {
                                                "type": "listItem",
                                                "content": [
                                                    {
                                                        "type": "paragraph",
                                                        "content": [
                                                            {
                                                                "type": "text",
                                                                "text": "Second item",
                                                            }
                                                        ],
                                                    }
                                                ],
                                            },
                                        ],
                                    },
                                ],
                            },
                        }
                    ]
                },
            },
            "renderedFields": {},
        }

        result = markdown_converter.compose_markdown(issue_data, [])

        # Check ADF was properly parsed
        assert "## Comments" in result
        assert "**Test User**" in result
        assert "This is **bold** and *italic* text." in result
        assert "- First item" in result
        assert "- Second item" in result
