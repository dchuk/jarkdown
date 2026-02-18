"""Integration tests for Phase 2: ADF parsing and custom field rendering pipeline."""

import json
from unittest.mock import Mock

import pytest

from jarkdown.markdown_converter import MarkdownConverter


@pytest.fixture
def converter():
    """Create a MarkdownConverter instance."""
    return MarkdownConverter("https://example.atlassian.net", "example.atlassian.net")


@pytest.fixture
def issue_with_adf_rich():
    """Load ADF-rich issue fixture."""
    with open("tests/data/issue_with_adf_rich.json") as f:
        return json.load(f)


@pytest.fixture
def issue_with_custom_fields():
    """Load custom fields issue fixture."""
    with open("tests/data/issue_with_custom_fields.json") as f:
        return json.load(f)


@pytest.fixture
def mock_field_cache():
    """Create a mock FieldMetadataCache with field resolution."""
    cache = Mock()
    cache.get_field_name.side_effect = lambda fid: {
        "customfield_10001": "Story Points",
        "customfield_10002": "Team",
        "customfield_10003": "Reviewer",
        "customfield_10004": "Sprint Goal",
        "customfield_10005": "Target Quarters",
    }.get(fid, fid)
    cache.get_field_schema.side_effect = lambda fid: {
        "customfield_10001": {"type": "string"},
        "customfield_10002": {"type": "option"},
        "customfield_10003": {"type": "user"},
        "customfield_10004": {"type": "string"},
        "customfield_10005": {"type": "array"},
    }.get(fid, {})
    return cache


class TestAdfIntegration:
    """End-to-end ADF rendering through compose_markdown."""

    def test_adf_table_in_compose(self, converter):
        """ADF description with table renders pipe-delimited table."""
        issue_data = {
            "key": "TEST-1",
            "fields": {
                "summary": "Table test",
                "issuetype": {"name": "Task"},
                "status": {"name": "Open", "statusCategory": {"name": "To Do"}},
                "priority": {"name": "Medium"},
                "resolution": None,
                "project": {"key": "TEST", "name": "Test"},
                "assignee": None,
                "reporter": None,
                "creator": None,
                "labels": [],
                "components": [],
                "parent": None,
                "versions": [],
                "fixVersions": [],
                "created": "2025-01-01T00:00:00.000+0000",
                "updated": "2025-01-01T00:00:00.000+0000",
                "resolutiondate": None,
                "duedate": None,
                "timetracking": {},
                "votes": {"votes": 0},
                "watches": {"watchCount": 0},
                "progress": {"percent": 0},
                "aggregateprogress": {"percent": 0},
                "issuelinks": [],
                "subtasks": [],
                "worklog": {"worklogs": [], "total": 0, "maxResults": 20},
                "comment": {"comments": []},
                "attachment": [],
                "environment": None,
                "description": {
                    "type": "doc",
                    "content": [
                        {
                            "type": "table",
                            "content": [
                                {
                                    "type": "tableRow",
                                    "content": [
                                        {"type": "tableCell", "content": [{"type": "paragraph", "content": [{"type": "text", "text": "Col1"}]}]},
                                        {"type": "tableCell", "content": [{"type": "paragraph", "content": [{"type": "text", "text": "Col2"}]}]}
                                    ]
                                },
                                {
                                    "type": "tableRow",
                                    "content": [
                                        {"type": "tableCell", "content": [{"type": "paragraph", "content": [{"type": "text", "text": "A"}]}]},
                                        {"type": "tableCell", "content": [{"type": "paragraph", "content": [{"type": "text", "text": "B"}]}]}
                                    ]
                                }
                            ]
                        }
                    ]
                }
            },
            "renderedFields": {}
        }
        output = converter.compose_markdown(issue_data, [])
        assert "| Col1 | Col2 |" in output
        assert "| --- | --- |" in output
        assert "| A | B |" in output

    def test_adf_panel_in_compose(self, converter):
        """ADF description with panel renders blockquote with type prefix."""
        issue_data = {
            "key": "TEST-2",
            "fields": {
                "summary": "Panel test",
                "issuetype": {"name": "Task"},
                "status": {"name": "Open", "statusCategory": {"name": "To Do"}},
                "priority": {"name": "Medium"},
                "resolution": None,
                "project": {"key": "TEST", "name": "Test"},
                "assignee": None,
                "reporter": None,
                "creator": None,
                "labels": [],
                "components": [],
                "parent": None,
                "versions": [],
                "fixVersions": [],
                "created": "2025-01-01T00:00:00.000+0000",
                "updated": "2025-01-01T00:00:00.000+0000",
                "resolutiondate": None,
                "duedate": None,
                "timetracking": {},
                "votes": {"votes": 0},
                "watches": {"watchCount": 0},
                "progress": {"percent": 0},
                "aggregateprogress": {"percent": 0},
                "issuelinks": [],
                "subtasks": [],
                "worklog": {"worklogs": [], "total": 0, "maxResults": 20},
                "comment": {"comments": []},
                "attachment": [],
                "environment": None,
                "description": {
                    "type": "doc",
                    "content": [
                        {
                            "type": "panel",
                            "attrs": {"panelType": "warning"},
                            "content": [
                                {"type": "paragraph", "content": [{"type": "text", "text": "Caution needed"}]}
                            ]
                        }
                    ]
                }
            },
            "renderedFields": {}
        }
        output = converter.compose_markdown(issue_data, [])
        assert "> **Warning:**" in output
        assert "Caution needed" in output

    def test_adf_mixed_content(self, converter, issue_with_adf_rich):
        """ADF with heading + table + task list + emoji + rule all render."""
        output = converter.compose_markdown(issue_with_adf_rich, [])
        # Heading
        assert "## Overview" in output
        # Table
        assert "| Browser | Version |" in output
        assert "| Chrome | 120.0 |" in output
        # Panel
        assert "> **Info:**" in output
        assert "important context" in output
        # Task list
        assert "- [x] Reproduce bug" in output
        assert "- [ ] Write fix" in output
        # Emoji
        assert ":warning:" in output
        # Rule
        assert "---" in output


class TestCustomFieldIntegration:
    """End-to-end custom field rendering through compose_markdown."""

    def test_custom_fields_full_pipeline(self, converter, issue_with_custom_fields, mock_field_cache):
        """Custom fields with cache resolve names and format values."""
        output = converter.compose_markdown(
            issue_with_custom_fields, [],
            field_cache=mock_field_cache,
        )
        assert "## Custom Fields" in output
        assert "Story Points" in output
        assert "Team Alpha" in output
        assert "Jane Smith" in output
        assert "Q1, Q2" in output

    def test_custom_fields_without_cache(self, converter, issue_with_custom_fields):
        """Without cache, fields appear with raw customfield IDs."""
        output = converter.compose_markdown(issue_with_custom_fields, [])
        assert "## Custom Fields" in output
        assert "customfield_10001" in output
        assert "customfield_10002" in output

    def test_field_filter_integration(self, converter, issue_with_custom_fields, mock_field_cache):
        """Field filter excludes specified fields from output."""
        field_filter = {"include": None, "exclude": {"Team", "Reviewer"}}
        output = converter.compose_markdown(
            issue_with_custom_fields, [],
            field_cache=mock_field_cache,
            field_filter=field_filter,
        )
        assert "## Custom Fields" in output
        assert "Story Points" in output
        assert "Team" not in output.split("## Custom Fields")[1].split("##")[0] if "Team" in output else True
        # More precise: check the custom fields section doesn't have "Team"
        sections = output.split("## Custom Fields")
        assert len(sections) == 2
        custom_section = sections[1]
        assert "**Team:**" not in custom_section
        assert "**Reviewer:**" not in custom_section

    def test_compose_markdown_backward_compatible(self, converter, issue_with_custom_fields):
        """compose_markdown works without new params (backward compatible)."""
        # This is the old calling pattern
        output = converter.compose_markdown(issue_with_custom_fields, [])
        assert "PROJ-200" in output
        assert "Issue with Custom Fields" in output
