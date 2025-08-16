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
        
        # Escape special regex characters in domain
        escaped_domain = re.escape(self.domain)
        
        # For secure attachment URLs with filename in path
        for attachment in downloaded_attachments:
            filename = attachment['filename']
            original_filename = attachment['original_filename']
            
            # URL encode filename for markdown links
            encoded_filename = quote(filename, safe='')
            
            if original_filename:
                # Escape the original filename for regex
                escaped_original = re.escape(original_filename)
                # Also try URL-encoded version of the filename
                encoded_original = re.escape(quote(original_filename, safe=''))
                # Pattern for secure URLs with this specific filename (regular or URL-encoded)
                patterns_to_try = [
                    f"https?://{escaped_domain}/secure/attachment/[0-9]+/{escaped_original}",
                    f"https?://{escaped_domain}/secure/attachment/[0-9]+/{encoded_original}"
                ]
                
                for pattern in patterns_to_try:
                    # Replace in images: ![alt](url) -> ![alt](filename)
                    markdown_content = re.sub(
                        f"(!\\[[^\\]]*\\])\\({pattern}\\)",
                        f"\\1({encoded_filename})",
                        markdown_content
                    )
                    # Replace in links: [text](url) -> [text](filename)
                    markdown_content = re.sub(
                        f"(\\[[^\\]]+\\])\\({pattern}\\)",
                        f"\\1({encoded_filename})",
                        markdown_content
                    )
        
        # For generic attachment content URLs (without filename in path)
        # Replace all remaining Jira attachment URLs with placeholder
        # This is a fallback for URLs that don't have the filename in them
        patterns = [
            f"https?://{escaped_domain}/jira/rest/api/[0-9]/attachment/content/[0-9]+",
            f"https?://{escaped_domain}/rest/api/[0-9]/attachment/content/[0-9]+",
            f"https?://{escaped_domain}/jira/rest/api/[0-9]/attachment/thumbnail/[0-9]+",
        ]
        
        for pattern in patterns:
            # For any remaining attachment URLs, try to infer from context
            # Look for patterns like ![filename](url) and use the filename from the alt text
            markdown_content = re.sub(
                f"!\\[([^\\]]*)\\]\\({pattern}\\)",
                lambda m: f"![{m.group(1)}]({quote(m.group(1), safe='')})" if m.group(1) else m.group(0),
                markdown_content
            )
            # For links, keep the link text but replace URL
            markdown_content = re.sub(
                f"\\[([^\\]]+)\\]\\({pattern}\\)",
                lambda m: f"[{m.group(1)}]({quote(m.group(1), safe='')})" if m.group(1) else m.group(0),
                markdown_content
            )
        
        return markdown_content
    
    def _compose_comments_section(self, issue_data, downloaded_attachments):
        """Compose the comments section of the markdown.
        
        Args:
            issue_data: Raw issue data from Jira API
            downloaded_attachments: List of downloaded attachment info
            
        Returns:
            list: Lines of markdown content for the comments section, or empty list if no comments
        """
        fields = issue_data.get('fields', {})
        comment_data = fields.get('comment', {})
        comments = comment_data.get('comments', [])
        
        if not comments:
            return []
        
        lines = []
        lines.append("## Comments")
        lines.append("")
        
        for comment in comments:
            # Extract author and date
            author = comment.get('author', {}).get('displayName', 'Unknown')
            created = comment.get('created', '')
            
            # Format the date (ISO 8601 to readable format)
            if created:
                # Parse and format: '2025-08-16T10:30:00.000+0000' -> '2025-08-16 10:30 AM'
                from datetime import datetime
                try:
                    # Handle various ISO formats
                    if created.endswith('Z'):
                        created = created[:-1] + '+00:00'
                    elif '+' in created and not created.endswith('+00:00'):
                        # Replace +0000 with +00:00
                        created = created.replace('+0000', '+00:00')
                    
                    dt = datetime.fromisoformat(created)
                    formatted_date = dt.strftime('%Y-%m-%d %I:%M %p')
                except Exception:
                    formatted_date = created
            else:
                formatted_date = 'Unknown date'
            
            # Get the rendered body
            body_html = comment.get('renderedBody', '')
            if not body_html and comment.get('body'):
                # Fallback to plain text body if no rendered version
                body_html = f"<p>{comment.get('body')}</p>"
            
            # Convert HTML to Markdown
            body_md = self.convert_html_to_markdown(body_html) if body_html else '*No comment body*'
            
            # Replace attachment links in the comment
            body_md = self.replace_attachment_links(body_md, downloaded_attachments)
            
            # Format the comment with author, date, and body
            lines.append(f"**{author}** - _{formatted_date}_")
            
            # Add body as blockquote
            for line in body_md.split('\n'):
                if line.strip():
                    lines.append(f"> {line}")
                else:
                    lines.append(">")
            
            lines.append("")  # Add spacing between comments
        
        return lines
    
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
        
        # Comments section (after description, before attachments)
        comment_lines = self._compose_comments_section(issue_data, downloaded_attachments)
        if comment_lines:
            lines.extend(comment_lines)
        
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