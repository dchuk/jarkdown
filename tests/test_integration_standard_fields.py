"""Integration tests for standard field coverage in compose_markdown output."""

import json

import pytest
import yaml

from jarkdown.markdown_converter import MarkdownConverter


@pytest.fixture
def converter():
    return MarkdownConverter("https://example.atlassian.net", "example.atlassian.net")


@pytest.fixture
def issue_full_fields():
    with open("tests/data/issue_full_fields.json") as f:
        return json.load(f)


class TestFullFieldsIntegration:
    """End-to-end tests using the comprehensive fixture."""

    @pytest.fixture(autouse=True)
    def _render(self, converter, issue_full_fields):
        self.output = converter.compose_markdown(issue_full_fields, [])

    def test_all_sections_present(self):
        """All 7 body section headings appear in output."""
        expected = [
            "## Description",
            "## Environment",
            "## Linked Issues",
            "## Subtasks",
            "## Worklogs",
            "## Comments",
        ]
        for heading in expected:
            assert heading in self.output, f"Missing section: {heading}"

    def test_section_ordering(self):
        """Section headings appear in the specified order."""
        ordered_headings = [
            "## Description",
            "## Environment",
            "## Linked Issues",
            "## Subtasks",
            "## Worklogs",
            "## Comments",
        ]
        indices = [self.output.index(h) for h in ordered_headings]
        assert indices == sorted(indices), (
            f"Sections out of order: {list(zip(ordered_headings, indices))}"
        )

    def test_frontmatter_complete(self):
        """YAML frontmatter contains all 29 fields with non-null values."""
        # Extract YAML between --- markers
        parts = self.output.split("---", 2)
        assert len(parts) >= 3, "Missing YAML frontmatter delimiters"
        metadata = yaml.safe_load(parts[1])

        assert len(metadata) == 29, f"Expected 29 fields, got {len(metadata)}"

        # All values should be non-null for the full fixture
        for key, value in metadata.items():
            assert value is not None, f"Frontmatter field '{key}' is null"

    def test_linked_issues_in_output(self):
        """Linked issues show directional labels and Jira browse URLs."""
        assert "### Blocks" in self.output
        assert "[FULL-200](https://example.atlassian.net/browse/FULL-200)" in self.output
        assert "### Is Blocked By" in self.output
        assert "[FULL-50](https://example.atlassian.net/browse/FULL-50)" in self.output
        assert "### Relates To" in self.output
        assert "[FULL-300](https://example.atlassian.net/browse/FULL-300)" in self.output

    def test_subtasks_in_output(self):
        """Subtasks rendered as bullet list with key, summary, status, type."""
        assert (
            "[FULL-101](https://example.atlassian.net/browse/FULL-101): "
            "Write unit tests (To Do) \u2014 Sub-task"
        ) in self.output
        assert (
            "[FULL-102](https://example.atlassian.net/browse/FULL-102): "
            "Update documentation (Done) \u2014 Sub-task"
        ) in self.output

    def test_worklogs_in_output(self):
        """Worklogs rendered as table with headers and data rows."""
        assert "| Author | Time Spent | Date | Comment |" in self.output
        assert "| Alice Dev | 4h | 2025-02-10 | Implemented core API endpoints |" in self.output
        assert "| Bob Eng | 2h 30m | 2025-02-11 | Code review and fixes |" in self.output
        assert "**Total Time Logged:**" in self.output

    def test_environment_in_output(self):
        """Environment section contains rendered content."""
        # Find the Environment section
        env_idx = self.output.index("## Environment")
        linked_idx = self.output.index("## Linked Issues")
        env_section = self.output[env_idx:linked_idx]

        assert "Ubuntu 22.04" in env_section


class TestEmptyFieldsIntegration:
    """Tests that empty/missing data produces correct placeholder output."""

    @pytest.fixture
    def minimal_issue(self):
        return {
            "key": "MIN-1",
            "fields": {
                "summary": "Minimal issue",
                "issuetype": {"name": "Task"},
                "status": {"name": "Open"},
                "created": "2025-01-01T00:00:00.000+0000",
                "updated": "2025-01-01T00:00:00.000+0000",
                "comment": {"comments": [], "total": 0},
            },
            "renderedFields": {
                "description": "<p>Simple description</p>",
            },
        }

    def test_empty_new_sections_show_none(self, converter, minimal_issue):
        """All 4 new sections show 'None' when data is absent."""
        output = converter.compose_markdown(minimal_issue, [])

        for heading in ["## Environment", "## Linked Issues", "## Subtasks", "## Worklogs"]:
            idx = output.index(heading)
            # Get the text between this heading and the next ## heading (or end)
            rest = output[idx + len(heading) :]
            next_section = rest.find("\n## ")
            section_body = rest[:next_section] if next_section != -1 else rest
            assert "None" in section_body, f"'{heading}' section missing 'None'"

    def test_comments_still_conditional(self, converter, minimal_issue):
        """Comments section does NOT appear when comment list is empty."""
        output = converter.compose_markdown(minimal_issue, [])
        assert "## Comments" not in output

    def test_attachments_still_conditional(self, converter, minimal_issue):
        """Attachments section does NOT appear when no attachments passed."""
        output = converter.compose_markdown(minimal_issue, [])
        assert "## Attachments" not in output
