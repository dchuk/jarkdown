"""Bulk export engine for exporting multiple Jira issues concurrently."""

import asyncio
import json
import logging
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from .exceptions import AuthenticationError, IssueNotFoundError, JarkdownError

logger = logging.getLogger(__name__)


@dataclass
class ExportResult:
    """Result of a single issue export attempt.

    Attributes:
        issue_key: Jira issue key (e.g., 'PROJ-123')
        success: Whether the export succeeded
        output_path: Path to the output directory (None on failure)
        error: Error message (None on success)
    """

    issue_key: str
    success: bool
    output_path: Optional[Path] = None
    error: Optional[str] = None


class BulkExporter:
    """Orchestrates concurrent export of multiple Jira issues.

    Args:
        api_client: Async JiraApiClient instance (must be entered as context manager)
        concurrency: Maximum simultaneous exports (default: 3)
        output_dir: Root output directory (default: current working directory)
        batch_name: Optional subdirectory name to wrap all issue directories
        refresh_fields: Force refresh of cached Jira field metadata
        include_fields: Comma-separated custom field names to include
        exclude_fields: Comma-separated custom field names to exclude
        include_json: Write raw JSON response alongside each Markdown file
    """

    def __init__(
        self,
        api_client,
        concurrency: int = 3,
        output_dir=None,
        batch_name: Optional[str] = None,
        refresh_fields: bool = False,
        include_fields: Optional[str] = None,
        exclude_fields: Optional[str] = None,
        include_json: bool = False,
    ):
        self.api_client = api_client
        self.semaphore = asyncio.Semaphore(concurrency)
        self.output_dir = Path(output_dir) if output_dir else Path.cwd()
        if batch_name:
            self.output_dir = self.output_dir / batch_name
        self.refresh_fields = refresh_fields
        self.include_fields = include_fields
        self.exclude_fields = exclude_fields
        self.include_json = include_json

    async def export_bulk(
        self, issue_keys: List[str]
    ) -> Tuple[List[ExportResult], List[ExportResult]]:
        """Export multiple issues concurrently with semaphore-limited concurrency.

        Args:
            issue_keys: List of Jira issue keys to export

        Returns:
            Tuple of (successes, failures) — both are lists of ExportResult
        """
        total = len(issue_keys)
        tasks = [
            self._export_one(key, i + 1, total) for i, key in enumerate(issue_keys)
        ]
        raw_results = await asyncio.gather(*tasks, return_exceptions=True)
        print("", file=sys.stderr)  # newline after progress line

        successes = []
        failures = []
        for i, result in enumerate(raw_results):
            if isinstance(result, BaseException):
                # Unexpected exception not caught by _export_one — defensive handling
                failures.append(
                    ExportResult(
                        issue_key=issue_keys[i],
                        success=False,
                        error=str(result),
                    )
                )
            elif result.success:
                successes.append(result)
            else:
                failures.append(result)

        return successes, failures

    async def _export_one(self, issue_key: str, n: int, total: int) -> ExportResult:
        """Export a single issue under the shared semaphore.

        Args:
            issue_key: Jira issue key to export
            n: 1-based position in the export batch (for progress display)
            total: Total number of issues in the batch

        Returns:
            ExportResult indicating success or failure
        """
        async with self.semaphore:
            print(
                f"\rExporting {n}/{total}... ({issue_key})",
                end="",
                flush=True,
                file=sys.stderr,
            )
            try:
                return await self._do_export(issue_key)
            except (IssueNotFoundError, AuthenticationError) as e:
                return ExportResult(issue_key=issue_key, success=False, error=str(e))
            except JarkdownError as e:
                return ExportResult(issue_key=issue_key, success=False, error=str(e))

    async def _do_export(self, issue_key: str) -> ExportResult:
        """Perform the actual export workflow for a single issue.

        Replicates the logic from jarkdown.export_issue() inline to avoid a
        circular import (jarkdown.py imports BulkExporter; BulkExporter must
        not import from jarkdown.py).

        Args:
            issue_key: Jira issue key to export

        Returns:
            ExportResult with success=True and output_path set

        Raises:
            JarkdownError: If export fails for any reason
        """
        from .attachment_handler import AttachmentHandler
        from .config_manager import ConfigManager
        from .field_cache import FieldMetadataCache
        from .markdown_converter import MarkdownConverter

        # Fetch issue data
        issue_data = await self.api_client.fetch_issue(issue_key)

        # Resolve output path
        output_path = self.output_dir / issue_key
        output_path.mkdir(parents=True, exist_ok=True)

        # Download attachments
        attachment_handler = AttachmentHandler(self.api_client)
        attachments = issue_data.get("fields", {}).get("attachment", [])
        downloaded_attachments = await attachment_handler.download_all_attachments(
            attachments, output_path
        )

        # Set up field metadata and config
        field_cache = FieldMetadataCache(self.api_client.domain)
        if self.refresh_fields or field_cache.is_stale():
            try:
                fields = await self.api_client.fetch_fields()
                field_cache.save(fields)
            except Exception as e:
                logger.warning(f"Failed to refresh field metadata: {e}")

        config_manager = ConfigManager()
        field_filter = config_manager.get_field_filter(
            cli_include=self.include_fields,
            cli_exclude=self.exclude_fields,
        )

        # Convert to markdown
        markdown_converter = MarkdownConverter(
            self.api_client.base_url, self.api_client.domain
        )
        markdown_content = markdown_converter.compose_markdown(
            issue_data,
            downloaded_attachments,
            field_cache=field_cache,
            field_filter=field_filter,
        )

        # Write JSON (opt-in) and markdown files
        if self.include_json:
            json_file = output_path / f"{issue_key}.json"
            await asyncio.to_thread(
                json_file.write_text,
                json.dumps(issue_data, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )

        md_file = output_path / f"{issue_key}.md"
        await asyncio.to_thread(md_file.write_text, markdown_content, encoding="utf-8")

        return ExportResult(issue_key=issue_key, success=True, output_path=output_path)

    def generate_index_md(
        self, results: List[ExportResult], all_issues_data: Dict
    ) -> str:
        """Generate index.md content as a Markdown summary table.

        Args:
            results: List of ExportResult instances (success and failure)
            all_issues_data: Dict mapping issue key → Jira API issue data dict,
                used to populate summary/status/type/assignee columns

        Returns:
            str: Markdown content for the index file
        """
        total = len(results)
        succeeded = sum(1 for r in results if r.success)
        failed = total - succeeded
        today = datetime.now(tz=timezone.utc).strftime("%Y-%m-%d")

        lines = [
            "# Export Summary",
            "",
            f"Exported: {succeeded} of {total} issues | Date: {today} | Failed: {failed}",
            "",
            "| Key | Summary | Status | Type | Assignee | Result |",
            "|-----|---------|--------|------|----------|--------|",
        ]

        for result in sorted(results, key=lambda r: r.issue_key):
            issue_data = all_issues_data.get(result.issue_key, {})
            fields = issue_data.get("fields", {})

            summary = fields.get("summary") or "-"
            status = (fields.get("status") or {}).get("name", "-")
            issue_type = (fields.get("issuetype") or {}).get("name", "-")
            assignee_field = fields.get("assignee")
            assignee = (
                assignee_field.get("displayName", "-") if assignee_field else "-"
            )

            if result.success:
                key_link = f"[{result.issue_key}]({result.issue_key}/{result.issue_key}.md)"
                result_col = "✓"
            else:
                key_link = f"[{result.issue_key}](#)"
                result_col = f"✗ {result.error or 'Unknown error'}"

            lines.append(
                f"| {key_link} | {summary} | {status} | {issue_type} | {assignee} | {result_col} |"
            )

        return "\n".join(lines) + "\n"

    async def write_index_md(
        self, results: List[ExportResult], issues_data: Dict
    ) -> None:
        """Write index.md to the output directory.

        Args:
            results: List of ExportResult instances
            issues_data: Dict mapping issue key → Jira API issue data dict
        """
        self.output_dir.mkdir(parents=True, exist_ok=True)
        content = self.generate_index_md(results, issues_data)
        index_path = self.output_dir / "index.md"
        await asyncio.to_thread(index_path.write_text, content, encoding="utf-8")
