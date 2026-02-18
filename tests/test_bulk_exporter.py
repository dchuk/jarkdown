"""Comprehensive tests for BulkExporter and related search_jql functionality."""

import asyncio
import re
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from aioresponses import aioresponses

from jarkdown.bulk_exporter import BulkExporter, ExportResult
from jarkdown.exceptions import IssueNotFoundError, JiraApiError
from jarkdown.jira_api_client import JiraApiClient


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_mock_client(domain="example.atlassian.net"):
    """Return a minimal async mock JiraApiClient (already entered)."""
    client = MagicMock()
    client.domain = domain
    client.base_url = f"https://{domain}"
    return client


# ---------------------------------------------------------------------------
# TestBulkExporterInit
# ---------------------------------------------------------------------------


class TestBulkExporterInit:
    """Tests for BulkExporter initialisation."""

    def test_default_concurrency(self):
        """Default concurrency is 3."""
        client = _make_mock_client()
        exporter = BulkExporter(client)
        assert exporter.semaphore._value == 3

    def test_custom_concurrency(self):
        """Custom concurrency sets semaphore value."""
        client = _make_mock_client()
        exporter = BulkExporter(client, concurrency=5)
        assert exporter.semaphore._value == 5

    def test_batch_name_creates_subdir(self, tmp_path):
        """batch_name is appended to output_dir."""
        client = _make_mock_client()
        exporter = BulkExporter(client, output_dir=tmp_path, batch_name="sprint-42")
        assert exporter.output_dir == tmp_path / "sprint-42"

    def test_no_batch_name(self, tmp_path):
        """Without batch_name output_dir is unchanged."""
        client = _make_mock_client()
        exporter = BulkExporter(client, output_dir=tmp_path)
        assert exporter.output_dir == tmp_path

    def test_output_dir_defaults_to_cwd(self):
        """output_dir defaults to Path.cwd() when not provided."""
        client = _make_mock_client()
        exporter = BulkExporter(client)
        assert exporter.output_dir == Path.cwd()


# ---------------------------------------------------------------------------
# TestExportBulk
# ---------------------------------------------------------------------------


class TestExportBulk:
    """Tests for BulkExporter.export_bulk."""

    async def test_all_succeed(self, tmp_path):
        """All 3 keys succeed → 3 successes, 0 failures."""
        client = _make_mock_client()
        exporter = BulkExporter(client, output_dir=tmp_path)

        async def fake_export_one(key, n, total):
            return ExportResult(issue_key=key, success=True, output_path=tmp_path / key)

        with patch.object(exporter, "_export_one", side_effect=fake_export_one):
            successes, failures = await exporter.export_bulk(
                ["PROJ-1", "PROJ-2", "PROJ-3"]
            )

        assert len(successes) == 3
        assert len(failures) == 0
        assert all(r.success for r in successes)

    async def test_partial_failure_continues(self, tmp_path):
        """One failure out of 3 → 2 successes, 1 failure; others still exported."""
        client = _make_mock_client()
        exporter = BulkExporter(client, output_dir=tmp_path)

        async def fake_export_one(key, n, total):
            if key == "PROJ-2":
                return ExportResult(
                    issue_key=key,
                    success=False,
                    error="Issue PROJ-2 not found or not accessible.",
                )
            return ExportResult(issue_key=key, success=True, output_path=tmp_path / key)

        with patch.object(exporter, "_export_one", side_effect=fake_export_one):
            successes, failures = await exporter.export_bulk(
                ["PROJ-1", "PROJ-2", "PROJ-3"]
            )

        assert len(successes) == 2
        assert len(failures) == 1
        assert failures[0].issue_key == "PROJ-2"
        success_keys = {r.issue_key for r in successes}
        assert "PROJ-1" in success_keys
        assert "PROJ-3" in success_keys

    async def test_all_fail(self, tmp_path):
        """All 3 exports fail → 0 successes, 3 failures."""
        client = _make_mock_client()
        exporter = BulkExporter(client, output_dir=tmp_path)

        async def fake_export_one(key, n, total):
            return ExportResult(
                issue_key=key,
                success=False,
                error=f"JQL search failed for {key}",
            )

        with patch.object(exporter, "_export_one", side_effect=fake_export_one):
            successes, failures = await exporter.export_bulk(
                ["PROJ-1", "PROJ-2", "PROJ-3"]
            )

        assert len(successes) == 0
        assert len(failures) == 3

    async def test_semaphore_limits_concurrency(self, tmp_path):
        """With concurrency=1, _do_export runs one at a time (semaphore in _export_one)."""
        client = _make_mock_client()
        exporter = BulkExporter(client, output_dir=tmp_path, concurrency=1)

        call_order = []
        active = []

        async def fake_do_export(key):
            active.append(key)
            assert len(active) <= 1, "More than 1 concurrent export detected"
            await asyncio.sleep(0)  # yield to event loop
            active.remove(key)
            call_order.append(key)
            return ExportResult(issue_key=key, success=True)

        keys = ["A-1", "A-2", "A-3", "A-4", "A-5"]
        with patch.object(exporter, "_do_export", side_effect=fake_do_export):
            successes, failures = await exporter.export_bulk(keys)

        assert len(successes) == 5
        assert set(call_order) == set(keys)

    async def test_unexpected_exception_becomes_failure(self, tmp_path):
        """Unexpected exception from gather treated as failure."""
        client = _make_mock_client()
        exporter = BulkExporter(client, output_dir=tmp_path)

        async def exploding_export_one(key, n, total):
            raise RuntimeError("Unexpected crash")

        with patch.object(
            exporter, "_export_one", side_effect=exploding_export_one
        ):
            successes, failures = await exporter.export_bulk(["PROJ-1"])

        assert len(successes) == 0
        assert len(failures) == 1
        assert "Unexpected crash" in failures[0].error


# ---------------------------------------------------------------------------
# TestSearchJql
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_api():
    """aioresponses context for HTTP mocking."""
    with aioresponses() as m:
        yield m


class TestSearchJql:
    """Tests for JiraApiClient.search_jql pagination."""

    async def test_single_page_no_next_token(self, mock_api):
        """Returns all issues when no nextPageToken in response."""
        issues = [{"key": f"PROJ-{i}"} for i in range(3)]
        mock_api.get(
            re.compile(r"https://example\.atlassian\.net/rest/api/3/search/jql"),
            payload={"issues": issues},
            status=200,
        )

        async with JiraApiClient(
            "example.atlassian.net", "test@example.com", "token"
        ) as client:
            result = await client.search_jql("project = PROJ", max_results=50)

        assert len(result) == 3
        assert result[0]["key"] == "PROJ-0"

    async def test_pagination_two_pages(self, mock_api):
        """Follows nextPageToken to fetch second page."""
        page1 = [{"key": f"PROJ-{i}"} for i in range(3)]
        page2 = [{"key": f"PROJ-{i}"} for i in range(3, 5)]

        mock_api.get(
            re.compile(r"https://example\.atlassian\.net/rest/api/3/search/jql"),
            payload={"issues": page1, "nextPageToken": "token-abc"},
            status=200,
        )
        mock_api.get(
            re.compile(r"https://example\.atlassian\.net/rest/api/3/search/jql"),
            payload={"issues": page2},
            status=200,
        )

        async with JiraApiClient(
            "example.atlassian.net", "test@example.com", "token"
        ) as client:
            result = await client.search_jql("project = PROJ", max_results=50)

        assert len(result) == 5
        keys = [r["key"] for r in result]
        assert "PROJ-0" in keys
        assert "PROJ-4" in keys

    async def test_max_results_respected(self, mock_api):
        """max_results=2 stops after collecting 2 issues even if API returns more."""
        issues = [{"key": f"PROJ-{i}"} for i in range(5)]
        mock_api.get(
            re.compile(r"https://example\.atlassian\.net/rest/api/3/search/jql"),
            payload={"issues": issues},
            status=200,
        )

        async with JiraApiClient(
            "example.atlassian.net", "test@example.com", "token"
        ) as client:
            result = await client.search_jql("project = PROJ", max_results=2)

        assert len(result) == 2

    async def test_empty_result(self, mock_api):
        """Empty issues list returns []."""
        mock_api.get(
            re.compile(r"https://example\.atlassian\.net/rest/api/3/search/jql"),
            payload={"issues": []},
            status=200,
        )

        async with JiraApiClient(
            "example.atlassian.net", "test@example.com", "token"
        ) as client:
            result = await client.search_jql("project = EMPTY", max_results=50)

        assert result == []

    async def test_auth_error_raises(self, mock_api):
        """401 raises AuthenticationError."""
        from jarkdown.exceptions import AuthenticationError

        mock_api.get(
            re.compile(r"https://example\.atlassian\.net/rest/api/3/search/jql"),
            status=401,
        )

        async with JiraApiClient(
            "example.atlassian.net", "test@example.com", "bad-token"
        ) as client:
            with pytest.raises(AuthenticationError):
                await client.search_jql("project = FOO", max_results=10)


# ---------------------------------------------------------------------------
# TestGenerateIndexMd
# ---------------------------------------------------------------------------


class TestGenerateIndexMd:
    """Tests for BulkExporter.generate_index_md and write_index_md."""

    def _make_exporter(self, tmp_path):
        return BulkExporter(_make_mock_client(), output_dir=tmp_path)

    def test_header_contains_count_and_date(self, tmp_path):
        """Header line shows exported count vs total."""
        exporter = self._make_exporter(tmp_path)
        results = [
            ExportResult("PROJ-1", success=True),
            ExportResult("PROJ-2", success=True),
            ExportResult("PROJ-3", success=False, error="not found"),
        ]
        content = exporter.generate_index_md(results, {})

        assert "Exported: 2 of 3 issues" in content
        assert "Failed: 1" in content

    def test_success_row_has_link(self, tmp_path):
        """Successful issue row contains [KEY](KEY/KEY.md) link."""
        exporter = self._make_exporter(tmp_path)
        results = [ExportResult("PROJ-1", success=True, output_path=tmp_path / "PROJ-1")]
        content = exporter.generate_index_md(results, {})

        assert "[PROJ-1](PROJ-1/PROJ-1.md)" in content
        assert "✓" in content

    def test_failure_row_has_error(self, tmp_path):
        """Failed issue row contains ✗ and error reason."""
        exporter = self._make_exporter(tmp_path)
        results = [ExportResult("PROJ-2", success=False, error="Issue not found")]
        content = exporter.generate_index_md(results, {})

        assert "[PROJ-2](#)" in content
        assert "✗" in content
        assert "Issue not found" in content

    async def test_writes_file_to_output_dir(self, tmp_path):
        """write_index_md creates index.md at output_dir/index.md."""
        exporter = self._make_exporter(tmp_path)
        results = [ExportResult("PROJ-1", success=True)]
        await exporter.write_index_md(results, {})

        index_file = tmp_path / "index.md"
        assert index_file.exists()
        assert "# Export Summary" in index_file.read_text(encoding="utf-8")

    def test_sorted_by_key(self, tmp_path):
        """Rows are sorted by issue key regardless of input order."""
        exporter = self._make_exporter(tmp_path)
        results = [
            ExportResult("PROJ-3", success=True),
            ExportResult("PROJ-1", success=True),
            ExportResult("PROJ-2", success=False, error="err"),
        ]
        content = exporter.generate_index_md(results, {})

        proj1_pos = content.index("PROJ-1")
        proj2_pos = content.index("PROJ-2")
        proj3_pos = content.index("PROJ-3")
        assert proj1_pos < proj2_pos < proj3_pos

    def test_issues_data_populates_columns(self, tmp_path):
        """Summary/status/type/assignee filled from all_issues_data when available."""
        exporter = self._make_exporter(tmp_path)
        results = [ExportResult("PROJ-1", success=True)]
        issues_data = {
            "PROJ-1": {
                "fields": {
                    "summary": "Fix login bug",
                    "status": {"name": "Done"},
                    "issuetype": {"name": "Bug"},
                    "assignee": {"displayName": "Jane Doe"},
                }
            }
        }
        content = exporter.generate_index_md(results, issues_data)

        assert "Fix login bug" in content
        assert "Done" in content
        assert "Bug" in content
        assert "Jane Doe" in content

    def test_missing_issues_data_shows_dashes(self, tmp_path):
        """Columns show '-' when issue data is absent."""
        exporter = self._make_exporter(tmp_path)
        results = [ExportResult("PROJ-99", success=True)]
        content = exporter.generate_index_md(results, {})

        # Summary, Status, Type, Assignee columns should all be '-'
        lines = [l for l in content.splitlines() if "PROJ-99" in l]
        assert len(lines) == 1
        # Row format: | key | summary | status | type | assignee | result |
        # Split on ' | ' to get individual column values
        cols = [c.strip() for c in lines[0].split(" | ")]
        dash_cols = [c for c in cols if c == "-"]
        assert len(dash_cols) == 4, f"Expected 4 dash columns, got {dash_cols} in: {lines[0]}"
