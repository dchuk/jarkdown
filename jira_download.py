#!/usr/bin/env python3
"""
Jira Ticket to Markdown Exporter CLI Tool

This tool exports a Jira Cloud issue into a markdown file with all its attachments 
downloaded locally and referenced inline.
"""

import os
import sys
import argparse
import json
import re
from pathlib import Path
from urllib.parse import urlparse, quote
import logging

import requests
from markdownify import markdownify as md
from dotenv import load_dotenv


class JiraDownloader:
    def __init__(self, domain, email, api_token):
        """Initialize the Jira downloader with authentication credentials."""
        self.domain = domain
        self.email = email
        self.api_token = api_token
        self.base_url = f"https://{domain}"
        self.api_base = f"{self.base_url}/rest/api/3"
        self.session = requests.Session()
        self.session.auth = (email, api_token)
        self.session.headers.update({
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        })
        
        logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
        self.logger = logging.getLogger(__name__)

    def fetch_issue(self, issue_key):
        """Fetch issue data from Jira API."""
        fields = "summary,description,issuetype,status,priority,attachment,assignee,reporter,created,updated"
        url = f"{self.api_base}/issue/{issue_key}"
        params = {
            'fields': fields,
            'expand': 'renderedFields'
        }
        
        self.logger.info(f"Fetching issue {issue_key}...")
        
        try:
            response = self.session.get(url, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            if response.status_code == 401:
                self.logger.error("Authentication failed. Please check your API token and email.")
            elif response.status_code == 404:
                self.logger.error(f"Issue {issue_key} not found or not accessible.")
            else:
                self.logger.error(f"HTTP error occurred: {e}")
            sys.exit(1)
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error fetching issue: {e}")
            sys.exit(1)

    def download_attachment(self, attachment, output_dir):
        """Download a single attachment."""
        filename = attachment['filename']
        content_url = attachment['content']
        mime_type = attachment.get('mimeType', '')
        size = attachment.get('size', 0)
        
        file_path = output_dir / filename
        
        # Handle filename conflicts
        counter = 1
        original_path = file_path
        while file_path.exists():
            stem = original_path.stem
            suffix = original_path.suffix
            file_path = original_path.parent / f"{stem}_{counter}{suffix}"
            counter += 1
        
        self.logger.info(f"  Downloading {filename} ({self._format_size(size)})...")
        
        try:
            response = self.session.get(content_url, stream=True)
            response.raise_for_status()
            
            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            return {
                'filename': file_path.name,
                'original_filename': filename,
                'mime_type': mime_type,
                'path': file_path
            }
        except Exception as e:
            self.logger.error(f"Error downloading {filename}: {e}")
            return None

    def download_attachments(self, attachments, output_dir):
        """Download all attachments for an issue."""
        if not attachments:
            return []
        
        output_dir.mkdir(parents=True, exist_ok=True)
        
        self.logger.info(f"Downloading {len(attachments)} attachment(s)...")
        
        downloaded = []
        for attachment in attachments:
            result = self.download_attachment(attachment, output_dir)
            if result:
                downloaded.append(result)
        
        return downloaded

    def convert_html_to_markdown(self, html_content):
        """Convert HTML content to Markdown."""
        if not html_content:
            return ""
        
        # Convert HTML to Markdown using markdownify
        markdown = md(html_content, heading_style="ATX", bullets="*-+")
        
        # Clean up any residual HTML tags that weren't converted
        markdown = re.sub(r'<[^>]+>', '', markdown)
        
        # Clean up excessive whitespace
        markdown = re.sub(r'\n{3,}', '\n\n', markdown)
        
        return markdown.strip()

    def replace_attachment_links(self, markdown_content, downloaded_attachments, jira_domain):
        """Replace Jira attachment URLs with local file references."""
        if not downloaded_attachments:
            return markdown_content
        
        # Create a mapping of possible URLs to local filenames
        for attachment in downloaded_attachments:
            filename = attachment['filename']
            original_filename = attachment['original_filename']
            
            # Escape special regex characters in domain
            escaped_domain = re.escape(jira_domain)
            
            # Pattern for attachment URLs
            patterns = [
                # Direct attachment content URLs
                f"https?://{escaped_domain}/jira/rest/api/[0-9]/attachment/content/[0-9]+",
                f"https?://{escaped_domain}/rest/api/[0-9]/attachment/content/[0-9]+",
                # Secure attachment URLs
                f"https?://{escaped_domain}/secure/attachment/[0-9]+/[^)\\]\\s]*",
                # Thumbnail URLs
                f"https?://{escaped_domain}/jira/rest/api/[0-9]/attachment/thumbnail/[0-9]+",
            ]
            
            # URL encode filename for markdown links
            encoded_filename = quote(filename, safe='')
            
            for pattern in patterns:
                # For images: ![alt](url) -> ![alt](filename)
                markdown_content = re.sub(
                    f"(!\\[[^\\]]*\\])\\({pattern}\\)",
                    f"\\1({encoded_filename})",
                    markdown_content
                )
                # For links: [text](url) -> [text](filename)
                markdown_content = re.sub(
                    f"(\\[[^\\]]+\\])\\({pattern}\\)",
                    f"\\1({encoded_filename})",
                    markdown_content
                )
            
            # Also replace any references to the original filename if different
            if original_filename != filename:
                encoded_original = quote(original_filename, safe='')
                markdown_content = markdown_content.replace(encoded_original, encoded_filename)
        
        return markdown_content

    def compose_markdown(self, issue_data, downloaded_attachments):
        """Compose the final markdown file content."""
        fields = issue_data.get('fields', {})
        rendered_fields = issue_data.get('renderedFields', {})
        
        # Extract metadata
        key = issue_data.get('key', 'UNKNOWN')
        summary = fields.get('summary', 'No Summary')
        issue_type = fields.get('issuetype', {}).get('name', 'Unknown')
        status = fields.get('status', {}).get('name', 'Unknown')
        priority = fields.get('priority', {}).get('name', 'Normal') if fields.get('priority') else 'Normal'
        assignee = fields.get('assignee', {}).get('displayName', 'Unassigned') if fields.get('assignee') else 'Unassigned'
        reporter = fields.get('reporter', {}).get('displayName', 'Unknown') if fields.get('reporter') else 'Unknown'
        
        # Start composing markdown
        lines = []
        
        # Title with link to Jira issue
        lines.append(f"# [{key}]({self.base_url}/browse/{key}): {summary}")
        lines.append("")
        
        # Metadata section
        lines.append(f"**Type:** {issue_type}  ")
        lines.append(f"**Status:** {status}  ")
        lines.append(f"**Priority:** {priority}  ")
        lines.append(f"**Assignee:** {assignee}  ")
        lines.append(f"**Reporter:** {reporter}")
        lines.append("")
        
        # Description section
        lines.append("## Description")
        lines.append("")
        
        # Convert description from HTML to Markdown
        description_html = rendered_fields.get('description', '')
        if not description_html and fields.get('description'):
            # If no rendered HTML, try to use raw description
            # (This would need ADF to Markdown conversion for full support)
            description_html = f"<p>{fields.get('description')}</p>"
        
        if description_html:
            description_md = self.convert_html_to_markdown(description_html)
            # Replace attachment links
            description_md = self.replace_attachment_links(description_md, downloaded_attachments, self.domain)
            lines.append(description_md)
        else:
            lines.append("*No description provided*")
        
        lines.append("")
        
        # Attachments section
        if downloaded_attachments:
            lines.append("## Attachments")
            lines.append("")
            for attachment in downloaded_attachments:
                filename = attachment['filename']
                mime_type = attachment['mime_type']
                encoded_filename = quote(filename, safe='')
                
                # Check if it's an image
                if mime_type and mime_type.startswith('image/'):
                    # Embed images
                    lines.append(f"- ![{filename}]({encoded_filename})")
                else:
                    # Link other files
                    lines.append(f"- [{filename}]({encoded_filename})")
            lines.append("")
        
        return "\n".join(lines)

    def export_issue(self, issue_key, output_dir=None):
        """Main method to export a Jira issue to markdown."""
        # Fetch issue data
        issue_data = self.fetch_issue(issue_key)
        
        # Determine output directory
        if output_dir:
            output_path = Path(output_dir) / issue_key
        else:
            output_path = Path.cwd() / issue_key
        
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Download attachments
        attachments = issue_data.get('fields', {}).get('attachment', [])
        downloaded_attachments = self.download_attachments(attachments, output_path)
        
        # Compose markdown
        markdown_content = self.compose_markdown(issue_data, downloaded_attachments)
        
        # Write markdown file
        markdown_file = output_path / f"{issue_key}.md"
        with open(markdown_file, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
        
        self.logger.info(f"\nSuccessfully exported {issue_key} to {output_path}")
        self.logger.info(f"  - Markdown file: {markdown_file}")
        if downloaded_attachments:
            self.logger.info(f"  - Downloaded {len(downloaded_attachments)} attachment(s)")
        
        return output_path

    def _format_size(self, size):
        """Format file size in human-readable format."""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description='Export Jira issues to Markdown with attachments',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  jira-download PROJ-123
  jira-download PROJ-123 --output ~/Documents/jira-exports
  
Environment variables:
  JIRA_DOMAIN     - Your Jira domain (e.g., your-company.atlassian.net)
  JIRA_EMAIL      - Your Jira account email
  JIRA_API_TOKEN  - Your Jira API token
        '''
    )
    
    parser.add_argument('issue_key', help='Jira issue key (e.g., PROJ-123)')
    parser.add_argument('--output', '-o', help='Output directory (default: current directory)')
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose logging')
    
    args = parser.parse_args()
    
    # Load environment variables
    load_dotenv()
    
    # Get credentials from environment
    domain = os.getenv('JIRA_DOMAIN')
    email = os.getenv('JIRA_EMAIL')
    api_token = os.getenv('JIRA_API_TOKEN')
    
    # Validate credentials
    if not all([domain, email, api_token]):
        print("Error: Missing required environment variables.", file=sys.stderr)
        print("Please set JIRA_DOMAIN, JIRA_EMAIL, and JIRA_API_TOKEN", file=sys.stderr)
        sys.exit(1)
    
    # Set logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Create downloader and export issue
    try:
        downloader = JiraDownloader(domain, email, api_token)
        downloader.export_issue(args.issue_key, args.output)
    except KeyboardInterrupt:
        print("\nOperation cancelled by user", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()