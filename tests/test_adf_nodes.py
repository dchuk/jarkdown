"""Tests for ADF node type parsing in MarkdownConverter."""

import json
import pytest

from jarkdown.markdown_converter import MarkdownConverter


@pytest.fixture
def converter():
    return MarkdownConverter("https://example.atlassian.net", "example.atlassian.net")


class TestAdfTable:
    """Tests for ADF table node parsing."""

    def test_basic_table(self, converter):
        """3x3 table renders with pipe delimiters and header separator."""
        with open("tests/data/adf_table.json") as f:
            adf = json.load(f)

        result = converter._parse_adf_to_markdown(adf)

        assert "| Name | Role | Status |" in result
        assert "| --- | --- | --- |" in result
        assert "| Alice | Developer | Active |" in result
        assert "| Bob | Designer | On Leave |" in result

    def test_table_with_formatted_content(self, converter):
        """Table cells with bold/italic text render correctly."""
        adf = {
            "type": "table",
            "content": [
                {
                    "type": "tableRow",
                    "content": [
                        {
                            "type": "tableCell",
                            "content": [
                                {
                                    "type": "paragraph",
                                    "content": [
                                        {
                                            "type": "text",
                                            "text": "important",
                                            "marks": [{"type": "strong"}],
                                        }
                                    ],
                                }
                            ],
                        },
                        {
                            "type": "tableCell",
                            "content": [
                                {
                                    "type": "paragraph",
                                    "content": [
                                        {
                                            "type": "text",
                                            "text": "note",
                                            "marks": [{"type": "em"}],
                                        }
                                    ],
                                }
                            ],
                        },
                    ],
                }
            ],
        }

        result = converter._parse_adf_to_markdown(adf)

        assert "**important**" in result
        assert "*note*" in result
        assert "|" in result

    def test_empty_table(self, converter):
        """Table with no rows returns empty string."""
        adf = {"type": "table", "content": []}

        result = converter._parse_adf_to_markdown(adf)

        assert result == ""


class TestAdfPanel:
    """Tests for ADF panel node parsing."""

    def test_info_panel(self, converter):
        """Panel with panelType info renders with Info prefix."""
        adf = {
            "type": "panel",
            "attrs": {"panelType": "info"},
            "content": [
                {
                    "type": "paragraph",
                    "content": [{"type": "text", "text": "Important info here."}],
                }
            ],
        }

        result = converter._parse_adf_to_markdown(adf)

        assert "> **Info:**" in result
        assert "> Important info here." in result

    def test_warning_panel(self, converter):
        """Panel with panelType warning renders with Warning prefix."""
        adf = {
            "type": "panel",
            "attrs": {"panelType": "warning"},
            "content": [
                {
                    "type": "paragraph",
                    "content": [{"type": "text", "text": "Be careful!"}],
                }
            ],
        }

        result = converter._parse_adf_to_markdown(adf)

        assert "> **Warning:**" in result
        assert "> Be careful!" in result

    def test_error_panel(self, converter):
        """Panel with panelType error renders with Error prefix."""
        adf = {
            "type": "panel",
            "attrs": {"panelType": "error"},
            "content": [
                {
                    "type": "paragraph",
                    "content": [{"type": "text", "text": "Something went wrong."}],
                }
            ],
        }

        result = converter._parse_adf_to_markdown(adf)

        assert "> **Error:**" in result
        assert "> Something went wrong." in result

    def test_panel_multiline(self, converter):
        """Panel with multiple paragraphs, all prefixed with >."""
        adf = {
            "type": "panel",
            "attrs": {"panelType": "note"},
            "content": [
                {
                    "type": "paragraph",
                    "content": [{"type": "text", "text": "First line."}],
                },
                {
                    "type": "paragraph",
                    "content": [{"type": "text", "text": "Second line."}],
                },
            ],
        }

        result = converter._parse_adf_to_markdown(adf)

        assert "> **Note:**" in result
        # All content lines should be blockquoted
        for line in result.split("\n"):
            if line.strip():
                assert line.startswith(">")


class TestAdfExpand:
    """Tests for ADF expand node parsing."""

    def test_expand_with_title(self, converter):
        """Expand block renders bold title + indented content."""
        adf = {
            "type": "expand",
            "attrs": {"title": "Click to expand"},
            "content": [
                {
                    "type": "paragraph",
                    "content": [{"type": "text", "text": "Hidden content."}],
                }
            ],
        }

        result = converter._parse_adf_to_markdown(adf)

        assert "**Click to expand**" in result
        assert "  Hidden content." in result

    def test_expand_default_title(self, converter):
        """Expand without title attr defaults to 'Details'."""
        adf = {
            "type": "expand",
            "attrs": {},
            "content": [
                {
                    "type": "paragraph",
                    "content": [{"type": "text", "text": "Some content."}],
                }
            ],
        }

        result = converter._parse_adf_to_markdown(adf)

        assert "**Details**" in result


class TestAdfRule:
    """Tests for ADF rule node parsing."""

    def test_rule(self, converter):
        """Rule node renders as ---."""
        adf = {"type": "rule"}

        result = converter._parse_adf_to_markdown(adf)

        assert result == "---"


class TestAdfInlineNodes:
    """Tests for ADF inline node parsing."""

    def test_emoji(self, converter):
        """Emoji with shortName :thumbsup: renders as :thumbsup:."""
        adf = {
            "type": "emoji",
            "attrs": {"shortName": ":thumbsup:", "id": "1f44d", "text": "\ud83d\udc4d"},
        }

        result = converter._parse_adf_to_markdown(adf)

        assert result == ":thumbsup:"

    def test_emoji_fallback_to_text(self, converter):
        """Emoji without shortName falls back to text attr."""
        adf = {"type": "emoji", "attrs": {"text": "\ud83d\udc4d"}}

        result = converter._parse_adf_to_markdown(adf)

        assert result == "\ud83d\udc4d"

    def test_status(self, converter):
        """Status with text 'IN PROGRESS' renders as **IN PROGRESS**."""
        adf = {
            "type": "status",
            "attrs": {"text": "IN PROGRESS", "color": "blue"},
        }

        result = converter._parse_adf_to_markdown(adf)

        assert result == "**IN PROGRESS**"

    def test_date(self, converter):
        """Date with timestamp 1672531200000 (2023-01-01 UTC) renders as 2023-01-01."""
        adf = {"type": "date", "attrs": {"timestamp": "1672531200000"}}

        result = converter._parse_adf_to_markdown(adf)

        assert result == "2023-01-01"

    def test_date_invalid_timestamp(self, converter):
        """Date with invalid timestamp returns the raw string."""
        adf = {"type": "date", "attrs": {"timestamp": "not-a-number"}}

        result = converter._parse_adf_to_markdown(adf)

        assert result == "not-a-number"

    def test_date_empty_timestamp(self, converter):
        """Date with empty timestamp returns empty string."""
        adf = {"type": "date", "attrs": {"timestamp": ""}}

        result = converter._parse_adf_to_markdown(adf)

        assert result == ""

    def test_inline_card(self, converter):
        """InlineCard with URL renders as [url](url)."""
        adf = {
            "type": "inlineCard",
            "attrs": {"url": "https://example.com/issue/123"},
        }

        result = converter._parse_adf_to_markdown(adf)

        assert result == "[https://example.com/issue/123](https://example.com/issue/123)"

    def test_inline_card_no_url(self, converter):
        """InlineCard without URL returns empty string."""
        adf = {"type": "inlineCard", "attrs": {}}

        result = converter._parse_adf_to_markdown(adf)

        assert result == ""


class TestAdfTaskDecision:
    """Tests for ADF taskList/decisionList parsing."""

    def test_task_list_mixed(self, converter):
        """TaskList with TODO and DONE items renders as checkboxes."""
        with open("tests/data/adf_task_decision.json") as f:
            adf = json.load(f)

        # Parse just the taskList (first content node)
        task_list = adf["content"][0]
        result = converter._parse_adf_to_markdown(task_list)

        assert "- [x] Set up project structure" in result
        assert "- [ ] Write unit tests" in result
        assert "- [ ] Deploy to staging" in result

    def test_decision_list(self, converter):
        """DecisionList renders as blockquoted decision items."""
        with open("tests/data/adf_task_decision.json") as f:
            adf = json.load(f)

        # Parse just the decisionList (second content node)
        decision_list = adf["content"][1]
        result = converter._parse_adf_to_markdown(decision_list)

        assert "> **Decision:** Use PostgreSQL for the database" in result
        assert "> **Decision:** Deploy on AWS ECS" in result

    def test_task_item_done(self, converter):
        """TaskItem with state DONE renders as checked checkbox."""
        adf = {
            "type": "taskItem",
            "attrs": {"localId": "t1", "state": "DONE"},
            "content": [{"type": "text", "text": "Completed task"}],
        }

        result = converter._parse_adf_to_markdown(adf)

        assert result == "- [x] Completed task"

    def test_task_item_todo(self, converter):
        """TaskItem with state TODO renders as unchecked checkbox."""
        adf = {
            "type": "taskItem",
            "attrs": {"localId": "t2", "state": "TODO"},
            "content": [{"type": "text", "text": "Pending task"}],
        }

        result = converter._parse_adf_to_markdown(adf)

        assert result == "- [ ] Pending task"


class TestAdfMediaGroup:
    """Tests for ADF mediaGroup parsing."""

    def test_media_group(self, converter):
        """MediaGroup with 2 media children renders both."""
        adf = {
            "type": "mediaGroup",
            "content": [
                {
                    "type": "media",
                    "attrs": {
                        "type": "external",
                        "url": "https://example.com/image1.png",
                    },
                },
                {
                    "type": "media",
                    "attrs": {
                        "type": "external",
                        "url": "https://example.com/image2.png",
                    },
                },
            ],
        }

        result = converter._parse_adf_to_markdown(adf)

        assert "![https://example.com/image1.png](https://example.com/image1.png)" in result
        assert "![https://example.com/image2.png](https://example.com/image2.png)" in result

    def test_media_group_empty(self, converter):
        """Empty mediaGroup returns empty string."""
        adf = {"type": "mediaGroup", "content": []}

        result = converter._parse_adf_to_markdown(adf)

        assert result == ""
