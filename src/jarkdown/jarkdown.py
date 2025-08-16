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
from getpass import getpass

from dotenv import load_dotenv

from .jira_api_client import JiraApiClient
from .attachment_handler import AttachmentHandler
from .markdown_converter import MarkdownConverter
from .exceptions import (
    JarkdownError,
)


def get_version():
    """Get the version of jarkdown."""
    try:
        return version("jarkdown")
    except PackageNotFoundError:
        return "unknown"


def setup_configuration():
    """Interactive setup to create .env file with Jira credentials."""
    print("\n=== Jarkdown Configuration Setup ===")
    print("\nThis will help you create a .env file with your Jira credentials.")
    print("\nYou'll need:")
    print("1. Your Jira domain (e.g., company.atlassian.net)")
    print("2. Your Jira email address")
    print("3. A Jira API token")
    print("\nTo create an API token:")
    print("1. Go to https://id.atlassian.com/manage-profile/security/api-tokens")
    print("2. Click 'Create API token'")
    print("3. Give it a name and copy the token")
    print()

    # Check if .env already exists
    env_path = Path.cwd() / ".env"
    if env_path.exists():
        response = input(".env file already exists. Overwrite? (y/N): ").strip().lower()
        if response != "y":
            print("Setup cancelled.")
            return

    # Collect information
    domain = input("\nJira domain (e.g., company.atlassian.net): ").strip()
    if not domain:
        print("Error: Domain is required")
        sys.exit(1)

    # Remove https:// if provided
    if domain.startswith("https://"):
        domain = domain[8:]
    elif domain.startswith("http://"):
        domain = domain[7:]

    email = input("Jira email address: ").strip()
    if not email:
        print("Error: Email is required")
        sys.exit(1)

    # Use getpass for API token to hide it from display
    api_token = getpass("Jira API token (hidden): ").strip()
    if not api_token:
        print("Error: API token is required")
        sys.exit(1)

    # Write .env file
    try:
        with open(env_path, "w") as f:
            f.write(f"JIRA_DOMAIN={domain}\n")
            f.write(f"JIRA_EMAIL={email}\n")
            f.write(f"JIRA_API_TOKEN={api_token}\n")

        print(f"\nConfiguration saved to {env_path}")
        print("You can now run: jarkdown ISSUE-KEY")

    except Exception as e:
        print(f"Error writing .env file: {e}")
        sys.exit(1)


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

    parser.add_argument(
        "issue_key",
        nargs="?",  # Make optional to allow --setup without issue key
        help="Jira issue key (e.g., PROJ-123)",
    )
    parser.add_argument(
        "--setup",
        action="store_true",
        help="Interactive setup to configure Jira credentials",
    )
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

    # Handle --setup command
    if args.setup:
        setup_configuration()
        sys.exit(0)

    # If not setup, issue_key is required
    if not args.issue_key:
        parser.error("issue_key is required unless using --setup")

    # Set up logging
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s: %(message)s",
    )

    # Load environment variables
    load_dotenv()

    # Check if .env file exists
    env_path = Path.cwd() / ".env"
    if not env_path.exists():
        print("Error: Configuration file '.env' not found.")
        print("\nTo set up your configuration, run: jarkdown --setup")
        print("Or create a .env file manually with:")
        print("  JIRA_DOMAIN=your-company.atlassian.net")
        print("  JIRA_EMAIL=your-email@example.com")
        print("  JIRA_API_TOKEN=your-api-token")
        sys.exit(1)

    # Export the issue
    try:
        # Get credentials from environment
        domain = os.getenv("JIRA_DOMAIN")
        email = os.getenv("JIRA_EMAIL")
        api_token = os.getenv("JIRA_API_TOKEN")

        # Validate credentials with helpful error messages
        missing = []
        if not domain:
            missing.append("JIRA_DOMAIN")
        if not email:
            missing.append("JIRA_EMAIL")
        if not api_token:
            missing.append("JIRA_API_TOKEN")

        if missing:
            print(
                f"Error: Missing required environment variables: {', '.join(missing)}"
            )
            print("\nTo set up your configuration, run: jarkdown --setup")
            print("Or add the missing variables to your .env file.")
            sys.exit(1)
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
