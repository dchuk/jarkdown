"""Tests for worklog and environment section renderers."""

import json
import pytest

from jarkdown.markdown_converter import MarkdownConverter


@pytest.fixture
def converter():
    return MarkdownConverter("https://example.atlassian.net", "example.atlassian.net")


@pytest.fixture
def issue_with_worklogs():
    with open("tests/data/issue_with_worklogs.json") as f:
        return json.load(f)


@pytest.fixture
def issue_with_worklogs_truncated():
    with open("tests/data/issue_with_worklogs_truncated.json") as f:
        return json.load(f)


@pytest.fixture
def issue_with_environment():
    with open("tests/data/issue_with_environment.json") as f:
        return json.load(f)


class TestEnvironmentSection:
    """Tests for _compose_environment_section."""

    def test_environment_html(self, converter, issue_with_environment):
        """Rendered HTML environment is converted to markdown."""
        lines = converter._compose_environment_section(issue_with_environment)
        text = "\n".join(lines)

        assert "## Environment" in text
        assert "Production" in text
        assert "Ubuntu 20.04" in text
        assert "Java 11" in text

    def test_environment_adf_fallback(self, converter):
        """ADF fallback used when no rendered HTML."""
        issue_data = {
            "renderedFields": {},
            "fields": {
                "environment": {
                    "type": "doc",
                    "version": 1,
                    "content": [
                        {
                            "type": "paragraph",
                            "content": [
                                {"type": "text", "text": "Staging server, Node 18"}
                            ],
                        }
                    ],
                }
            },
        }
        lines = converter._compose_environment_section(issue_data)
        text = "\n".join(lines)

        assert "## Environment" in text
        assert "Staging server, Node 18" in text

    def test_environment_string_fallback(self, converter):
        """Plain string environment is used as-is."""
        issue_data = {
            "renderedFields": {},
            "fields": {"environment": "Windows 10, Chrome 120"},
        }
        lines = converter._compose_environment_section(issue_data)
        text = "\n".join(lines)

        assert "## Environment" in text
        assert "Windows 10, Chrome 120" in text

    def test_environment_empty(self, converter):
        """Null environment shows None."""
        issue_data = {
            "renderedFields": {"environment": None},
            "fields": {"environment": None},
        }
        lines = converter._compose_environment_section(issue_data)
        text = "\n".join(lines)

        assert "## Environment" in text
        assert "None" in text

    def test_environment_missing(self, converter):
        """Missing environment keys show None."""
        issue_data = {"renderedFields": {}, "fields": {}}
        lines = converter._compose_environment_section(issue_data)
        text = "\n".join(lines)

        assert "## Environment" in text
        assert "None" in text


class TestWorklogsSection:
    """Tests for _compose_worklogs_section."""

    def test_worklogs_with_data(self, converter, issue_with_worklogs):
        """Worklogs render as table with total time."""
        lines = converter._compose_worklogs_section(issue_with_worklogs)
        text = "\n".join(lines)

        assert "## Worklogs" in text
        assert "**Total Time Logged:**" in text
        assert "| Author | Time Spent | Date | Comment |" in text
        assert "| Alice Dev | 3h 20m | 2025-03-10 | Fixed the login bug |" in text
        assert "| Bob Eng | 1h | 2025-03-11 |  |" in text

    def test_worklogs_truncated(self, converter, issue_with_worklogs_truncated):
        """Truncation warning when total > embedded count."""
        lines = converter._compose_worklogs_section(issue_with_worklogs_truncated)
        text = "\n".join(lines)

        assert "> **Note:** Showing 2 of 32 worklogs" in text

    def test_worklogs_empty(self, converter):
        """Empty worklogs list shows None."""
        issue_data = {
            "fields": {"worklog": {"worklogs": [], "total": 0, "maxResults": 20}}
        }
        lines = converter._compose_worklogs_section(issue_data)
        text = "\n".join(lines)

        assert "## Worklogs" in text
        assert "None" in text

    def test_worklogs_missing(self, converter):
        """Missing worklog key shows None."""
        issue_data = {"fields": {}}
        lines = converter._compose_worklogs_section(issue_data)
        text = "\n".join(lines)

        assert "## Worklogs" in text
        assert "None" in text

    def test_worklogs_null_comment(self, converter):
        """Null comment in worklog entry does not crash."""
        issue_data = {
            "fields": {
                "worklog": {
                    "startAt": 0,
                    "maxResults": 20,
                    "total": 1,
                    "worklogs": [
                        {
                            "author": {"displayName": "Test User"},
                            "started": "2025-06-01T10:00:00.000+0000",
                            "timeSpent": "2h",
                            "timeSpentSeconds": 7200,
                            "comment": None,
                        }
                    ],
                }
            }
        }
        lines = converter._compose_worklogs_section(issue_data)
        text = "\n".join(lines)

        assert "| Test User | 2h | 2025-06-01 |  |" in text


class TestAdfToPlainText:
    """Tests for _adf_to_plain_text."""

    def test_simple_text(self, converter):
        """ADF doc with single paragraph returns plain text."""
        adf = {
            "type": "doc",
            "version": 1,
            "content": [
                {
                    "type": "paragraph",
                    "content": [{"type": "text", "text": "Hello world"}],
                }
            ],
        }
        assert converter._adf_to_plain_text(adf) == "Hello world"

    def test_formatted_text(self, converter):
        """ADF with bold/italic marks returns text without formatting markers."""
        adf = {
            "type": "doc",
            "version": 1,
            "content": [
                {
                    "type": "paragraph",
                    "content": [
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
                    ],
                }
            ],
        }
        result = converter._adf_to_plain_text(adf)
        assert "bold" in result
        assert "italic" in result
        assert "**" not in result
        assert "*" not in result or result.count("*") == 0

    def test_nested_content(self, converter):
        """ADF with list items returns concatenated text."""
        adf = {
            "type": "doc",
            "version": 1,
            "content": [
                {
                    "type": "bulletList",
                    "content": [
                        {
                            "type": "listItem",
                            "content": [
                                {
                                    "type": "paragraph",
                                    "content": [
                                        {"type": "text", "text": "Item one"}
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
                                        {"type": "text", "text": "Item two"}
                                    ],
                                }
                            ],
                        },
                    ],
                }
            ],
        }
        result = converter._adf_to_plain_text(adf)
        assert "Item one" in result
        assert "Item two" in result

    def test_null_input(self, converter):
        """None returns empty string."""
        assert converter._adf_to_plain_text(None) == ""

    def test_string_input(self, converter):
        """Plain string returned as-is."""
        assert converter._adf_to_plain_text("plain comment") == "plain comment"
