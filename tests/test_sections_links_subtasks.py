"""Tests for linked issues and subtasks section renderers."""

import json
import pytest

from jarkdown.markdown_converter import MarkdownConverter


@pytest.fixture
def converter():
    return MarkdownConverter("https://example.atlassian.net", "example.atlassian.net")


@pytest.fixture
def issue_with_links():
    with open("tests/data/issue_with_links.json") as f:
        return json.load(f)


@pytest.fixture
def issue_with_subtasks():
    with open("tests/data/issue_with_subtasks.json") as f:
        return json.load(f)


class TestLinkedIssuesSection:
    """Tests for _compose_linked_issues_section."""

    def test_linked_issues_with_data(self, converter, issue_with_links):
        """Test linked issues are grouped by directional label."""
        result = "\n".join(converter._compose_linked_issues_section(issue_with_links))

        assert "## Linked Issues" in result
        assert "### Blocks" in result
        assert (
            "[LINK-200](https://example.atlassian.net/browse/LINK-200): Blocked Issue (To Do)"
            in result
        )
        assert "### Is Blocked By" in result
        assert (
            "[LINK-50](https://example.atlassian.net/browse/LINK-50): Blocking Issue (In Progress)"
            in result
        )
        assert "### Relates To" in result
        assert (
            "[LINK-300](https://example.atlassian.net/browse/LINK-300): Related Issue (Done)"
            in result
        )

    def test_linked_issues_empty(self, converter):
        """Test empty issuelinks produces None."""
        issue_data = {"fields": {"issuelinks": []}}
        result = "\n".join(converter._compose_linked_issues_section(issue_data))

        assert "## Linked Issues" in result
        assert "None" in result

    def test_linked_issues_missing(self, converter):
        """Test missing issuelinks key produces None."""
        issue_data = {"fields": {}}
        result = "\n".join(converter._compose_linked_issues_section(issue_data))

        assert "## Linked Issues" in result
        assert "None" in result


class TestSubtasksSection:
    """Tests for _compose_subtasks_section."""

    def test_subtasks_with_data(self, converter, issue_with_subtasks):
        """Test subtasks rendered as flat bullet list."""
        result = "\n".join(converter._compose_subtasks_section(issue_with_subtasks))

        assert "## Subtasks" in result
        assert (
            "[SUB-101](https://example.atlassian.net/browse/SUB-101): Write unit tests (To Do) \u2014 Sub-task"
            in result
        )
        assert (
            "[SUB-102](https://example.atlassian.net/browse/SUB-102): Update documentation (Done) \u2014 Sub-task"
            in result
        )

    def test_subtasks_empty(self, converter):
        """Test empty subtasks produces None."""
        issue_data = {"fields": {"subtasks": []}}
        result = "\n".join(converter._compose_subtasks_section(issue_data))

        assert "## Subtasks" in result
        assert "None" in result

    def test_subtasks_missing(self, converter):
        """Test missing subtasks key produces None."""
        issue_data = {"fields": {}}
        result = "\n".join(converter._compose_subtasks_section(issue_data))

        assert "## Subtasks" in result
        assert "None" in result
