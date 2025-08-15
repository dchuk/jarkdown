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

from dotenv import load_dotenv

from .jira_api_client import JiraApiClient
from .attachment_handler import AttachmentHandler
from .markdown_converter import MarkdownConverter
from .exceptions import (
    JiraDownloadError,
    ConfigurationError,
    AuthenticationError,
    IssueNotFoundError,
    AttachmentDownloadError
)


def export_issue(api_client, issue_key, output_dir=None):
    """Export a Jira issue to markdown.
    
    Args:
        api_client: Configured JiraApiClient instance
        issue_key: The Jira issue key to export
        output_dir: Optional output directory path
        
    Returns:
        Path: The path to the created markdown file
        
    Raises:
        IssueNotFoundError: If the issue doesn't exist
        AttachmentDownloadError: If attachment download fails
        JiraDownloadError: For other errors
    """
    # Fetch issue data
    issue_data = api_client.fetch_issue(issue_key)
    
    # Prepare output directory
    output_path = Path(output_dir) if output_dir else Path.cwd()
    issue_dir = output_path / issue_key
    issue_dir.mkdir(parents=True, exist_ok=True)
    
    # Download attachments if present
    attachment_mapping = {}
    if 'attachment' in issue_data['fields'] and issue_data['fields']['attachment']:
        handler = AttachmentHandler(api_client)
        attachment_mapping = handler.download_all_attachments(
            issue_data['fields']['attachment'],
            issue_dir
        )
    
    # Convert to markdown
    converter = MarkdownConverter(api_client.base_url, api_client.domain)
    markdown_content = converter.compose_markdown(issue_data, attachment_mapping)
    
    # Save markdown file
    markdown_file = issue_dir / f"{issue_key}.md"
    markdown_file.write_text(markdown_content, encoding='utf-8')
    
    return markdown_file


def main():
    """Main entry point for the CLI."""
    # Load environment variables
    load_dotenv()
    
    # Set up argument parser
    parser = argparse.ArgumentParser(
        description='Export Jira Cloud issues to Markdown with attachments',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Environment variables:
  JIRA_DOMAIN    Your Jira Cloud domain (e.g., company.atlassian.net)
  JIRA_EMAIL     Your Jira Cloud email
  JIRA_API_TOKEN Your Jira Cloud API token

Example:
  %(prog)s PROJ-123
  %(prog)s PROJ-123 --output ~/Documents/jira-exports
  %(prog)s PROJ-123 --verbose
        """
    )
    
    parser.add_argument('issue_key', help='The Jira issue key to export (e.g., PROJ-123)')
    parser.add_argument(
        '--output', '-o',
        help='Output directory (default: current directory)',
        default=None
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose logging'
    )
    
    args = parser.parse_args()
    
    # Configure logging
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format='%(levelname)s: %(message)s'
    )
    
    # Validate environment variables
    required_env_vars = ['JIRA_DOMAIN', 'JIRA_EMAIL', 'JIRA_API_TOKEN']
    missing_vars = [var for var in required_env_vars if not os.getenv(var)]
    
    if missing_vars:
        logging.error(f"Missing required environment variables: {', '.join(missing_vars)}")
        logging.error("Please set them in your .env file or environment")
        sys.exit(1)
    
    try:
        # Create API client
        api_client = JiraApiClient(
            domain=os.getenv('JIRA_DOMAIN'),
            email=os.getenv('JIRA_EMAIL'),
            api_token=os.getenv('JIRA_API_TOKEN')
        )
        
        # Export the issue
        markdown_file = export_issue(api_client, args.issue_key, args.output)
        
        logging.info(f"✓ Successfully exported {args.issue_key} to {markdown_file}")
        
    except ConfigurationError as e:
        logging.error(f"Configuration error: {e}")
        sys.exit(1)
    except AuthenticationError as e:
        logging.error(f"Authentication failed: {e}")
        logging.error("Please check your JIRA_EMAIL and JIRA_API_TOKEN")
        sys.exit(1)
    except IssueNotFoundError as e:
        logging.error(f"Issue not found: {e}")
        sys.exit(1)
    except AttachmentDownloadError as e:
        logging.error(f"Attachment download failed: {e}")
        sys.exit(1)
    except JiraDownloadError as e:
        logging.error(f"Export failed: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        logging.info("Export cancelled by user")
        sys.exit(130)
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        if args.verbose:
            logging.exception("Full traceback:")
        sys.exit(1)


if __name__ == '__main__':
    main()