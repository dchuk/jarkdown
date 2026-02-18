"""Tests for custom field rendering and markdown section output."""

import json
from unittest.mock import Mock

import pytest

from jarkdown.custom_field_renderer import CustomFieldRenderer
from jarkdown.markdown_converter import MarkdownConverter


@pytest.fixture
def renderer():
    """Create a CustomFieldRenderer without ADF parser."""
    return CustomFieldRenderer()


@pytest.fixture
def renderer_with_adf():
    """Create a CustomFieldRenderer with ADF parser."""
    converter = MarkdownConverter("https://example.atlassian.net", "example.atlassian.net")
    return CustomFieldRenderer(adf_parser=converter._parse_adf_to_markdown)


@pytest.fixture
def converter():
    """Create a MarkdownConverter instance."""
    return MarkdownConverter("https://example.atlassian.net", "example.atlassian.net")


@pytest.fixture
def issue_with_custom_fields():
    """Load mock issue data with custom fields."""
    with open("tests/data/issue_with_custom_fields.json") as f:
        return json.load(f)


@pytest.fixture
def mock_field_cache():
    """Create a mock FieldMetadataCache."""
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


class TestCustomFieldRenderer:
    """Tests for CustomFieldRenderer value rendering."""

    def test_string_value(self, renderer):
        assert renderer.render_value("hello") == "hello"

    def test_number_value(self, renderer):
        assert renderer.render_value(42) == "42"

    def test_none_value(self, renderer):
        assert renderer.render_value(None) is None

    def test_option_value(self, renderer):
        assert renderer.render_value({"value": "High", "id": "1"}) == "High"

    def test_user_value(self, renderer):
        assert renderer.render_value({"displayName": "John Doe", "accountId": "abc"}) == "John Doe"

    def test_date_value(self, renderer):
        assert renderer.render_value("2025-01-15") == "2025-01-15"

    def test_array_of_options(self, renderer):
        assert renderer.render_value([{"value": "A"}, {"value": "B"}]) == "A, B"

    def test_array_of_users(self, renderer):
        result = renderer.render_value([{"displayName": "Alice"}, {"displayName": "Bob"}])
        assert result == "Alice, Bob"

    def test_array_of_strings(self, renderer):
        assert renderer.render_value(["tag1", "tag2"]) == "tag1, tag2"

    def test_empty_array(self, renderer):
        assert renderer.render_value([]) is None

    def test_empty_string(self, renderer):
        assert renderer.render_value("") is None

    def test_adf_document(self, renderer_with_adf):
        adf = {
            "type": "doc",
            "content": [
                {
                    "type": "paragraph",
                    "content": [{"type": "text", "text": "Hello world"}],
                }
            ],
        }
        result = renderer_with_adf.render_value(adf)
        assert "Hello world" in result

    def test_unknown_dict_fallback(self, renderer):
        result = renderer.render_value({"foo": "bar"})
        assert "foo" in result
        assert "bar" in result


class TestSchemaBasedRendering:
    """Tests for schema-type-aware rendering."""

    def test_option_schema(self, renderer):
        result = renderer.render_value({"value": "X"}, schema={"type": "option"})
        assert result == "X"

    def test_user_schema(self, renderer):
        result = renderer.render_value({"displayName": "Y"}, schema={"type": "user"})
        assert result == "Y"

    def test_array_schema(self, renderer):
        result = renderer.render_value([{"value": "A"}], schema={"type": "array"})
        assert result == "A"

    def test_number_schema(self, renderer):
        result = renderer.render_value(3.14, schema={"type": "number"})
        assert result == "3.14"


class TestCustomFieldsSection:
    """Tests for _compose_custom_fields_section in MarkdownConverter."""

    def test_custom_fields_rendered(self, converter, issue_with_custom_fields, mock_field_cache):
        lines = converter._compose_custom_fields_section(
            issue_with_custom_fields, field_cache=mock_field_cache
        )
        output = "\n".join(lines)
        assert "## Custom Fields" in output
        assert "Story Points" in output
        assert "Team" in output

    def test_custom_fields_alphabetical_order(self, converter, issue_with_custom_fields, mock_field_cache):
        lines = converter._compose_custom_fields_section(
            issue_with_custom_fields, field_cache=mock_field_cache
        )
        output = "\n".join(lines)
        # Reviewer < Story Points < Target Quarters < Team (alphabetical)
        reviewer_pos = output.index("Reviewer")
        story_pos = output.index("Story Points")
        target_pos = output.index("Target Quarters")
        team_pos = output.index("Team")
        assert reviewer_pos < story_pos < target_pos < team_pos

    def test_null_fields_skipped(self, converter, issue_with_custom_fields, mock_field_cache):
        lines = converter._compose_custom_fields_section(
            issue_with_custom_fields, field_cache=mock_field_cache
        )
        output = "\n".join(lines)
        # customfield_10004 is null, so "Sprint Goal" should not appear
        assert "Sprint Goal" not in output

    def test_custom_fields_with_filter_include(self, converter, issue_with_custom_fields, mock_field_cache):
        field_filter = {"include": {"Story Points", "Team"}, "exclude": set()}
        lines = converter._compose_custom_fields_section(
            issue_with_custom_fields, field_cache=mock_field_cache, field_filter=field_filter
        )
        output = "\n".join(lines)
        assert "Story Points" in output
        assert "Team" in output
        assert "Reviewer" not in output

    def test_custom_fields_with_filter_exclude(self, converter, issue_with_custom_fields, mock_field_cache):
        field_filter = {"include": None, "exclude": {"Team"}}
        lines = converter._compose_custom_fields_section(
            issue_with_custom_fields, field_cache=mock_field_cache, field_filter=field_filter
        )
        output = "\n".join(lines)
        assert "Team" not in output
        assert "Story Points" in output

    def test_no_custom_fields(self, converter):
        issue_data = {
            "fields": {
                "summary": "No custom fields",
                "status": {"name": "Open"},
            }
        }
        lines = converter._compose_custom_fields_section(issue_data)
        assert lines == []

    def test_adf_custom_field(self, converter, mock_field_cache):
        """ADF custom field renders as markdown under ### heading."""
        issue_data = {
            "fields": {
                "customfield_10099": {
                    "type": "doc",
                    "content": [
                        {
                            "type": "paragraph",
                            "content": [{"type": "text", "text": "Rich content here"}],
                        }
                    ],
                }
            }
        }
        mock_field_cache.get_field_name.side_effect = lambda fid: "Description (Rich)" if fid == "customfield_10099" else fid
        mock_field_cache.get_field_schema.return_value = {"type": "any"}
        lines = converter._compose_custom_fields_section(
            issue_data, field_cache=mock_field_cache
        )
        output = "\n".join(lines)
        # ADF content is multi-line if it contains newlines, but single paragraph won't be.
        # The actual behavior depends on the ADF parser output.
        assert "Rich content here" in output
