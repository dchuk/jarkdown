#!/usr/bin/env python3
"""
Jira Ticket to Markdown Exporter CLI Tool

This tool exports a Jira Cloud issue into a markdown file with all its attachments
downloaded locally and referenced inline.
"""

import os
import sys
import argparse
import logging
from pathlib import Path
from importlib.metadata import version, PackageNotFoundError

from dotenv import load_dotenv

from .jira_api_client import JiraApiClient
from .attachment_handler import AttachmentHandler
from .markdown_converter import MarkdownConverter
from .exceptions import (
    JarkdownError,
    ConfigurationError,
)


def get_version():
    """Get the version of jarkdown."""
    try:
        return version("jarkdown")
    except PackageNotFoundError:
        return "unknown"


def export_issue(api_client, issue_key, output_dir=None):
    """Export a Jira issue to markdown.

    Args:
        api_client: JiraApiClient instance
        issue_key: Jira issue key (e.g., 'PROJ-123')
        output_dir: Optional output directory

    Returns:
        Path: The output directory where files were saved

    Raises:
        JarkdownError: If export fails
    """
    logger = logging.getLogger(__name__)

    # Fetch issue data
    issue_data = api_client.fetch_issue(issue_key)

    # Determine output directory
    if output_dir:
        output_path = Path(output_dir) / issue_key
    else:
        output_path = Path.cwd() / issue_key

    output_path.mkdir(parents=True, exist_ok=True)

    # Download attachments
    attachment_handler = AttachmentHandler(api_client)
    attachments = issue_data.get("fields", {}).get("attachment", [])
    downloaded_attachments = attachment_handler.download_all_attachments(
        attachments, output_path
    )

    # Convert to markdown
    markdown_converter = MarkdownConverter(api_client.base_url, api_client.domain)
    markdown_content = markdown_converter.compose_markdown(
        issue_data, downloaded_attachments
    )

    # Write markdown file
    markdown_file = output_path / f"{issue_key}.md"
    with open(markdown_file, "w", encoding="utf-8") as f:
        f.write(markdown_content)

    logger.info(f"\nSuccessfully exported {issue_key} to {output_path}")
    logger.info(f"  - Markdown file: {markdown_file}")
    if downloaded_attachments:
        logger.info(f"  - Downloaded {len(downloaded_attachments)} attachment(s)")

    return output_path


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Export Jira issues to Markdown with attachments",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  jarkdown PROJ-123
  jarkdown PROJ-123 --output ~/Documents/jira-exports

Environment variables:
  JIRA_DOMAIN     - Your Jira domain (e.g., your-company.atlassian.net)
  JIRA_EMAIL      - Your Jira account email
  JIRA_API_TOKEN  - Your Jira API token
        """,
    )

    parser.add_argument("issue_key", help="Jira issue key (e.g., PROJ-123)")
    parser.add_argument(
        "--output", "-o", help="Output directory (default: current directory)"
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose logging"
    )
    parser.add_argument(
        "--version",
        action="version",
        version=get_version(),
        help="Show program version and exit",
    )

    args = parser.parse_args()

    # Set up logging
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s: %(message)s",
    )

    # Load environment variables
    load_dotenv()

    # Export the issue
    try:
        # Get credentials from environment
        domain = os.getenv("JIRA_DOMAIN")
        email = os.getenv("JIRA_EMAIL")
        api_token = os.getenv("JIRA_API_TOKEN")

        # Validate credentials
        if not all([domain, email, api_token]):
            raise ConfigurationError(
                "Missing required environment variables. "
                "Please set JIRA_DOMAIN, JIRA_EMAIL, and JIRA_API_TOKEN"
            )
        api_client = JiraApiClient(domain, email, api_token)
        export_issue(api_client, args.issue_key, args.output)

    except JarkdownError as e:
        # Catch all JarkdownError subclasses with a single handler
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nOperation cancelled by user", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
