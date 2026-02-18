#!/usr/bin/env python3
"""
Jira Ticket to Markdown Exporter CLI Tool

This tool exports a Jira Cloud issue into a markdown file with all its attachments
downloaded locally and referenced inline.
"""

import asyncio
import json
import os
import re
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
from .bulk_exporter import BulkExporter
from .exceptions import (
    JarkdownError,
)

_ISSUE_KEY_RE = re.compile(r"^[A-Z]+-\d+$")


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
        print("You can now run: jarkdown export ISSUE-KEY")

    except Exception as e:
        print(f"Error writing .env file: {e}")
        sys.exit(1)


async def export_issue(api_client, issue_key, output_dir=None,
                       refresh_fields=False, include_fields=None, exclude_fields=None):
    """Export a Jira issue to markdown.

    Args:
        api_client: JiraApiClient instance (async context manager)
        issue_key: Jira issue key (e.g., 'PROJ-123')
        output_dir: Optional output directory
        refresh_fields: Force refresh of cached field metadata
        include_fields: Comma-separated custom field names to include
        exclude_fields: Comma-separated custom field names to exclude

    Returns:
        Path: The output directory where files were saved

    Raises:
        JarkdownError: If export fails
    """
    logger = logging.getLogger(__name__)

    # Fetch issue data (async)
    issue_data = await api_client.fetch_issue(issue_key)

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

    # Set up field metadata cache and config
    from .field_cache import FieldMetadataCache
    from .config_manager import ConfigManager

    field_cache = FieldMetadataCache(api_client.domain)
    # Async-aware field refresh: call fetch_fields directly to avoid sync wrapper
    if refresh_fields or field_cache.is_stale():
        try:
            fields = await api_client.fetch_fields()
            field_cache.save(fields)
            logger.info(f"Field metadata cached ({len(fields)} fields)")
        except Exception as e:
            logger.warning(f"Failed to refresh field metadata: {e}")

    config_manager = ConfigManager()
    field_filter = config_manager.get_field_filter(
        cli_include=include_fields,
        cli_exclude=exclude_fields,
    )

    markdown_content = markdown_converter.compose_markdown(
        issue_data, downloaded_attachments,
        field_cache=field_cache, field_filter=field_filter,
    )

    # Write raw JSON response
    json_file = output_path / f"{issue_key}.json"
    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(issue_data, f, indent=2, ensure_ascii=False)

    # Write markdown file
    markdown_file = output_path / f"{issue_key}.md"
    with open(markdown_file, "w", encoding="utf-8") as f:
        f.write(markdown_content)

    logger.info(f"\nSuccessfully exported {issue_key} to {output_path}")
    logger.info(f"  - Raw JSON: {json_file}")
    logger.info(f"  - Markdown file: {markdown_file}")
    if downloaded_attachments:
        logger.info(f"  - Downloaded {len(downloaded_attachments)} attachment(s)")

    return output_path


async def _async_export(args, domain, email, api_token):
    """Async inner function for the export subcommand.

    Args:
        args: Parsed CLI arguments
        domain: Jira domain from environment
        email: Jira email from environment
        api_token: Jira API token from environment
    """
    async with JiraApiClient(domain, email, api_token) as client:
        await export_issue(
            client,
            args.issue_key,
            args.output,
            refresh_fields=getattr(args, "refresh_fields", False),
            include_fields=getattr(args, "include_fields", None),
            exclude_fields=getattr(args, "exclude_fields", None),
        )


def _load_credentials():
    """Load and validate Jira credentials from environment variables.

    Returns:
        tuple: (domain, email, api_token) strings

    Exits:
        sys.exit(1) if credentials are missing or .env file not found
    """
    load_dotenv()

    domain = os.getenv("JIRA_DOMAIN")
    email = os.getenv("JIRA_EMAIL")
    api_token = os.getenv("JIRA_API_TOKEN")

    # Check if .env file exists and no environment variables are set
    env_path = Path.cwd() / ".env"
    if not env_path.exists() and not all([domain, email, api_token]):
        print("Error: Configuration file '.env' not found.")
        print("\nTo set up your configuration, run: jarkdown setup")
        print("Or create a .env file manually with:")
        print("  JIRA_DOMAIN=your-company.atlassian.net")
        print("  JIRA_EMAIL=your-email@example.com")
        print("  JIRA_API_TOKEN=your-api-token")
        sys.exit(1)

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
        print("\nTo set up your configuration, run: jarkdown setup")
        print("Or add the missing variables to your .env file.")
        sys.exit(1)

    return domain, email, api_token


def _print_summary(successes, failures):
    """Print a completion summary to stderr.

    Args:
        successes: List of successful ExportResult instances
        failures: List of failed ExportResult instances
    """
    total = len(successes) + len(failures)
    print(
        f"\nExport complete: {len(successes)}/{total} succeeded, "
        f"{len(failures)} failed.",
        file=sys.stderr,
    )
    if failures:
        print("\nFailed issues:", file=sys.stderr)
        for result in failures:
            print(f"  {result.issue_key}: {result.error}", file=sys.stderr)


def _handle_export(args):
    """Handle the export subcommand: validate env then run async export.

    Args:
        args: Parsed CLI arguments with issue_key and shared flags
    """
    # Set up logging
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s: %(message)s",
    )

    try:
        domain, email, api_token = _load_credentials()
        asyncio.run(_async_export(args, domain, email, api_token))

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


def _handle_bulk(args):
    """Handle 'bulk' subcommand: export multiple issues by key.

    Args:
        args: Parsed CLI arguments with issue_keys and shared flags
    """
    try:
        domain, email, api_token = _load_credentials()
        asyncio.run(_async_bulk(args, domain, email, api_token))
    except JarkdownError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nOperation cancelled by user", file=sys.stderr)
        sys.exit(1)
    except SystemExit:
        raise
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)


async def _async_bulk(args, domain, email, api_token):
    """Async implementation of bulk subcommand.

    Args:
        args: Parsed CLI arguments
        domain: Jira domain from environment
        email: Jira email from environment
        api_token: Jira API token from environment
    """
    async with JiraApiClient(domain, email, api_token) as client:
        exporter = BulkExporter(
            client,
            concurrency=args.concurrency,
            output_dir=args.output,
            batch_name=getattr(args, "batch_name", None),
            refresh_fields=getattr(args, "refresh_fields", False),
            include_fields=getattr(args, "include_fields", None),
            exclude_fields=getattr(args, "exclude_fields", None),
        )
        successes, failures = await exporter.export_bulk(args.issue_keys)
        await exporter.write_index_md(successes + failures, {})
        _print_summary(successes, failures)
        if failures:
            sys.exit(1)


def _handle_query(args):
    """Handle 'query' subcommand: export issues from JQL.

    Args:
        args: Parsed CLI arguments with jql and shared flags
    """
    try:
        domain, email, api_token = _load_credentials()
        asyncio.run(_async_query(args, domain, email, api_token))
    except JarkdownError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nOperation cancelled by user", file=sys.stderr)
        sys.exit(1)
    except SystemExit:
        raise
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)


async def _async_query(args, domain, email, api_token):
    """Async implementation of query subcommand.

    Args:
        args: Parsed CLI arguments
        domain: Jira domain from environment
        email: Jira email from environment
        api_token: Jira API token from environment
    """
    async with JiraApiClient(domain, email, api_token) as client:
        print(f"Searching: {args.jql}", file=sys.stderr)
        issues = await client.search_jql(args.jql, max_results=args.max_results)
        if not issues:
            print("No issues found.", file=sys.stderr)
            return
        issue_keys = [i["key"] for i in issues]
        print(f"Found {len(issue_keys)} issues.", file=sys.stderr)
        exporter = BulkExporter(
            client,
            concurrency=args.concurrency,
            output_dir=args.output,
            batch_name=getattr(args, "batch_name", None),
        )
        successes, failures = await exporter.export_bulk(issue_keys)
        issues_data = {i["key"]: i for i in issues}
        await exporter.write_index_md(successes + failures, issues_data)
        _print_summary(successes, failures)
        if failures:
            sys.exit(1)


def main():
    """Main CLI entry point."""
    # Backward-compat shim: bare issue key on argv[1] → inject "export"
    if len(sys.argv) > 1 and _ISSUE_KEY_RE.match(sys.argv[1]):
        sys.argv.insert(1, "export")

    # Parent parser: shared flags inherited by all subcommands, no help
    parent_parser = argparse.ArgumentParser(add_help=False)
    parent_parser.add_argument(
        "--output", "-o", help="Output directory (default: current directory)"
    )
    parent_parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose logging"
    )
    parent_parser.add_argument(
        "--refresh-fields",
        action="store_true",
        help="Force refresh of cached Jira field metadata",
    )
    parent_parser.add_argument(
        "--include-fields",
        help="Comma-separated list of custom field names to include",
    )
    parent_parser.add_argument(
        "--exclude-fields",
        help="Comma-separated list of custom field names to exclude",
    )

    # Main parser
    parser = argparse.ArgumentParser(
        prog="jarkdown",
        description="Export Jira issues to Markdown with attachments",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  jarkdown export PROJ-123
  jarkdown PROJ-123                              # backward-compat form
  jarkdown export PROJ-123 --output ~/Documents/jira-exports
  jarkdown bulk PROJ-1 PROJ-2 PROJ-3
  jarkdown query 'project = FOO AND status = Done'
  jarkdown setup

Environment variables:
  JIRA_DOMAIN     - Your Jira domain (e.g., your-company.atlassian.net)
  JIRA_EMAIL      - Your Jira account email
  JIRA_API_TOKEN  - Your Jira API token
        """,
    )
    parser.add_argument(
        "--version",
        action="version",
        version=get_version(),
        help="Show program version and exit",
    )

    subparsers = parser.add_subparsers(dest="command")

    # export subcommand
    export_parser = subparsers.add_parser(
        "export",
        help="Export a single Jira issue to Markdown",
        parents=[parent_parser],
    )
    export_parser.add_argument(
        "issue_key", help="Jira issue key (e.g., PROJ-123)"
    )

    # bulk subcommand
    bulk_parser = subparsers.add_parser(
        "bulk",
        help="Export multiple Jira issues by key",
        parents=[parent_parser],
    )
    bulk_parser.add_argument(
        "issue_keys",
        nargs="+",
        help="One or more Jira issue keys (e.g., PROJ-1 PROJ-2 PROJ-3)",
    )
    bulk_parser.add_argument(
        "--max-results",
        type=int,
        default=None,
        help="Maximum number of issues to export",
    )
    bulk_parser.add_argument(
        "--batch-name",
        help="Optional name for output batch directory wrapper",
    )
    bulk_parser.add_argument(
        "--concurrency",
        type=int,
        default=3,
        help="Maximum concurrent exports (default: 3)",
    )

    # query subcommand
    query_parser = subparsers.add_parser(
        "query",
        help="Export Jira issues matching a JQL query",
        parents=[parent_parser],
    )
    query_parser.add_argument(
        "jql",
        help="JQL query string (e.g., 'project = FOO AND status = Done')",
    )
    query_parser.add_argument(
        "--max-results",
        type=int,
        default=50,
        help="Maximum number of issues to export (default: 50)",
    )
    query_parser.add_argument(
        "--batch-name",
        help="Optional name for output batch directory wrapper",
    )
    query_parser.add_argument(
        "--concurrency",
        type=int,
        default=3,
        help="Maximum concurrent exports (default: 3)",
    )

    # setup subcommand
    subparsers.add_parser(
        "setup",
        help="Interactive setup to configure Jira credentials",
    )

    args = parser.parse_args()

    if args.command == "export":
        _handle_export(args)
    elif args.command == "bulk":
        _handle_bulk(args)
    elif args.command == "query":
        _handle_query(args)
    elif args.command == "setup":
        setup_configuration()
        sys.exit(0)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
