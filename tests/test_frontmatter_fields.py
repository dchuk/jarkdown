"""Tests for frontmatter field coverage in MarkdownConverter."""

import json

import pytest

from jarkdown.markdown_converter import MarkdownConverter


@pytest.fixture
def converter():
    return MarkdownConverter("https://example.atlassian.net", "example.atlassian.net")


@pytest.fixture
def issue_standard_fields():
    with open("tests/data/issue_standard_fields.json") as f:
        return json.load(f)


class TestFrontmatterPopulated:
    """Tests that all new frontmatter fields are correctly populated."""

    def test_project_name(self, converter, issue_standard_fields):
        metadata = converter._generate_metadata_dict(issue_standard_fields)
        assert metadata["project"] == "Example Project"

    def test_project_key(self, converter, issue_standard_fields):
        metadata = converter._generate_metadata_dict(issue_standard_fields)
        assert metadata["project_key"] == "PROJ"

    def test_status_category(self, converter, issue_standard_fields):
        metadata = converter._generate_metadata_dict(issue_standard_fields)
        assert metadata["status_category"] == "In Progress"

    def test_duedate(self, converter, issue_standard_fields):
        metadata = converter._generate_metadata_dict(issue_standard_fields)
        assert metadata["duedate"] == "2025-06-15"

    def test_votes(self, converter, issue_standard_fields):
        metadata = converter._generate_metadata_dict(issue_standard_fields)
        assert metadata["votes"] == 5

    def test_watches(self, converter, issue_standard_fields):
        metadata = converter._generate_metadata_dict(issue_standard_fields)
        assert metadata["watches"] == 3

    def test_original_estimate(self, converter, issue_standard_fields):
        metadata = converter._generate_metadata_dict(issue_standard_fields)
        assert metadata["original_estimate"] == "1d 2h"

    def test_time_spent(self, converter, issue_standard_fields):
        metadata = converter._generate_metadata_dict(issue_standard_fields)
        assert metadata["time_spent"] == "6h"

    def test_remaining_estimate(self, converter, issue_standard_fields):
        metadata = converter._generate_metadata_dict(issue_standard_fields)
        assert metadata["remaining_estimate"] == "3h 25m"

    def test_progress(self, converter, issue_standard_fields):
        metadata = converter._generate_metadata_dict(issue_standard_fields)
        assert metadata["progress"] == 60

    def test_aggregate_progress(self, converter, issue_standard_fields):
        metadata = converter._generate_metadata_dict(issue_standard_fields)
        assert metadata["aggregate_progress"] == 45


class TestFrontmatterEmpty:
    """Tests that missing/null fields produce correct defaults."""

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
            },
        }

    def test_project_null_when_absent(self, converter, minimal_issue):
        metadata = converter._generate_metadata_dict(minimal_issue)
        assert metadata["project"] is None

    def test_project_key_null_when_absent(self, converter, minimal_issue):
        metadata = converter._generate_metadata_dict(minimal_issue)
        assert metadata["project_key"] is None

    def test_status_category_null_when_absent(self, converter, minimal_issue):
        metadata = converter._generate_metadata_dict(minimal_issue)
        assert metadata["status_category"] is None

    def test_duedate_null_when_absent(self, converter, minimal_issue):
        metadata = converter._generate_metadata_dict(minimal_issue)
        assert metadata["duedate"] is None

    def test_original_estimate_null_when_timetracking_null(self, converter):
        issue = {
            "key": "TT-1",
            "fields": {
                "summary": "Time tracking null",
                "timetracking": None,
            },
        }
        metadata = converter._generate_metadata_dict(issue)
        assert metadata["original_estimate"] is None

    def test_time_spent_null_when_timetracking_null(self, converter):
        issue = {
            "key": "TT-1",
            "fields": {
                "summary": "Time tracking null",
                "timetracking": None,
            },
        }
        metadata = converter._generate_metadata_dict(issue)
        assert metadata["time_spent"] is None

    def test_remaining_estimate_null_when_timetracking_null(self, converter):
        issue = {
            "key": "TT-1",
            "fields": {
                "summary": "Time tracking null",
                "timetracking": None,
            },
        }
        metadata = converter._generate_metadata_dict(issue)
        assert metadata["remaining_estimate"] is None

    def test_progress_zero_when_absent(self, converter, minimal_issue):
        metadata = converter._generate_metadata_dict(minimal_issue)
        assert metadata["progress"] == 0

    def test_aggregate_progress_zero_when_absent(self, converter, minimal_issue):
        metadata = converter._generate_metadata_dict(minimal_issue)
        assert metadata["aggregate_progress"] == 0

    def test_votes_zero_when_absent(self, converter, minimal_issue):
        metadata = converter._generate_metadata_dict(minimal_issue)
        assert metadata["votes"] == 0

    def test_watches_zero_when_absent(self, converter, minimal_issue):
        metadata = converter._generate_metadata_dict(minimal_issue)
        assert metadata["watches"] == 0


class TestFrontmatterFieldOrdering:
    """Tests that frontmatter fields appear in the specified order."""

    EXPECTED_ORDER = [
        "key",
        "summary",
        "type",
        "status",
        "status_category",
        "priority",
        "resolution",
        "project",
        "project_key",
        "assignee",
        "reporter",
        "creator",
        "labels",
        "components",
        "parent_key",
        "parent_summary",
        "affects_versions",
        "fix_versions",
        "created_at",
        "updated_at",
        "resolved_at",
        "duedate",
        "original_estimate",
        "time_spent",
        "remaining_estimate",
        "progress",
        "aggregate_progress",
        "votes",
        "watches",
    ]

    def test_field_order_matches_spec(self, converter, issue_standard_fields):
        metadata = converter._generate_metadata_dict(issue_standard_fields)
        keys = list(metadata.keys())
        assert keys == self.EXPECTED_ORDER

    def test_total_field_count(self, converter, issue_standard_fields):
        metadata = converter._generate_metadata_dict(issue_standard_fields)
        assert len(metadata) == 29
