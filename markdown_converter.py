"""Converter for transforming Jira issues to Markdown format."""

import re
from urllib.parse import quote
from markdownify import markdownify as md


class MarkdownConverter:
    """Converts Jira issue data into Markdown format."""
    
    def __init__(self, base_url, domain):
        """Initialize the markdown converter.
        
        Args:
            base_url: Base URL of the Jira instance (e.g., 'https://company.atlassian.net')
            domain: Jira domain (e.g., 'company.atlassian.net')
        """
        self.base_url = base_url
        self.domain = domain
    
    def convert_html_to_markdown(self, html_content):
        """Convert HTML content to Markdown.
        
        Args:
            html_content: HTML string to convert
            
        Returns:
            str: Converted markdown content
        """
        if not html_content:
            return ""
        
        # Convert HTML to Markdown using markdownify
        markdown = md(html_content, heading_style="ATX", bullets="*-+")
        
        # Clean up any residual HTML tags that weren't converted
        markdown = re.sub(r'<[^>]+>', '', markdown)
        
        # Clean up excessive whitespace
        markdown = re.sub(r'\n{3,}', '\n\n', markdown)
        
        return markdown.strip()
    
    def replace_attachment_links(self, markdown_content, downloaded_attachments):
        """Replace Jira attachment URLs with local file references.
        
        Args:
            markdown_content: Markdown content with Jira attachment URLs
            downloaded_attachments: List of downloaded attachment info
            
        Returns:
            str: Markdown content with local file references
        """
        if not downloaded_attachments:
            return markdown_content
        
        # Create a mapping of possible URLs to local filenames
        for attachment in downloaded_attachments:
            filename = attachment['filename']
            original_filename = attachment['original_filename']
            
            # Escape special regex characters in domain
            escaped_domain = re.escape(self.domain)
            
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
        """Compose the final markdown file content.
        
        Args:
            issue_data: Raw issue data from Jira API
            downloaded_attachments: List of downloaded attachment info
            
        Returns:
            str: Complete markdown content for the issue
        """
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
            description_md = self.replace_attachment_links(description_md, downloaded_attachments)
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