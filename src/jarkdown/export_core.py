"""Shared async export workflow used by both the CLI and BulkExporter."""

import asyncio
import json
import logging
from pathlib import Path

from .attachment_handler import AttachmentHandler
from .config_manager import ConfigManager
from .field_cache import FieldMetadataCache
from .markdown_converter import MarkdownConverter

logger = logging.getLogger(__name__)


async def perform_export(
    api_client,
    issue_key: str,
    output_path: Path,
    refresh_fields: bool = False,
    include_fields=None,
    exclude_fields=None,
    include_json: bool = False,
) -> Path:
    """Run the full export workflow for a single Jira issue.

    Fetches issue data, downloads attachments, builds field metadata and
    config, converts to Markdown, and writes output files.  Callers are
    responsible for creating / resolving ``output_path`` before calling this
    function.

    Args:
        api_client: Active JiraApiClient instance (must already be entered as
            an async context manager).
        issue_key: Jira issue key (e.g. ``'PROJ-123'``).
        output_path: Directory where output files will be written.  The
            directory is created if it does not already exist.
        refresh_fields: Force a refresh of cached Jira field metadata.
        include_fields: Comma-separated custom field names to include, or
            ``None`` to use the config-file / default behaviour.
        exclude_fields: Comma-separated custom field names to exclude, or
            ``None``.
        include_json: When ``True``, write the raw Jira API JSON response
            alongside the Markdown file.

    Returns:
        Path: The directory where the exported files were written.

    Raises:
        JarkdownError: If any step of the export workflow fails.
    """
    # Ensure output directory exists
    output_path.mkdir(parents=True, exist_ok=True)

    # Fetch issue data
    issue_data = await api_client.fetch_issue(issue_key)

    # Download attachments
    attachment_handler = AttachmentHandler(api_client)
    attachments = issue_data.get("fields", {}).get("attachment", [])
    downloaded_attachments = await attachment_handler.download_all_attachments(
        attachments, output_path
    )

    # Build field metadata cache
    field_cache = FieldMetadataCache(api_client.domain)
    if refresh_fields or field_cache.is_stale():
        try:
            fields = await api_client.fetch_fields()
            field_cache.save(fields)
            logger.info("Field metadata cached (%d fields)", len(fields))
        except Exception as exc:
            logger.warning("Failed to refresh field metadata: %s", exc)

    # Build field filter from config / CLI overrides
    config_manager = ConfigManager()
    field_filter = config_manager.get_field_filter(
        cli_include=include_fields,
        cli_exclude=exclude_fields,
    )

    # Convert to Markdown
    markdown_converter = MarkdownConverter(api_client.base_url, api_client.domain)
    markdown_content = markdown_converter.compose_markdown(
        issue_data,
        downloaded_attachments,
        field_cache=field_cache,
        field_filter=field_filter,
    )

    # Write raw JSON (opt-in)
    if include_json:
        json_file = output_path / f"{issue_key}.json"
        await asyncio.to_thread(
            json_file.write_text,
            json.dumps(issue_data, indent=2, ensure_ascii=False),
            "utf-8",
        )

    # Write Markdown
    md_file = output_path / f"{issue_key}.md"
    await asyncio.to_thread(md_file.write_text, markdown_content, "utf-8")

    return output_path
