"""Converter for transforming Jira issues to Markdown format."""

import re
import yaml
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
        markdown = re.sub(r"<[^>]+>", "", markdown)

        # Clean up excessive whitespace
        markdown = re.sub(r"\n{3,}", "\n\n", markdown)

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
            filename = attachment["filename"]
            original_filename = attachment["original_filename"]

            # URL encode filename for markdown links
            encoded_filename = quote(filename, safe="")

            if original_filename:
                # Escape the original filename for regex
                escaped_original = re.escape(original_filename)
                # Also try URL-encoded version of the filename
                encoded_original = re.escape(quote(original_filename, safe=""))
                # Pattern for secure URLs with this specific filename (regular or URL-encoded)
                patterns_to_try = [
                    f"https?://{escaped_domain}/secure/attachment/[0-9]+/{escaped_original}",
                    f"https?://{escaped_domain}/secure/attachment/[0-9]+/{encoded_original}",
                ]

                for pattern in patterns_to_try:
                    # Replace in images: ![alt](url) -> ![alt](filename)
                    markdown_content = re.sub(
                        f"(!\\[[^\\]]*\\])\\({pattern}\\)",
                        f"\\1({encoded_filename})",
                        markdown_content,
                    )
                    # Replace in links: [text](url) -> [text](filename)
                    markdown_content = re.sub(
                        f"(\\[[^\\]]+\\])\\({pattern}\\)",
                        f"\\1({encoded_filename})",
                        markdown_content,
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
                lambda m: f"![{m.group(1)}]({quote(m.group(1), safe='')})"
                if m.group(1)
                else m.group(0),
                markdown_content,
            )
            # For links, keep the link text but replace URL
            markdown_content = re.sub(
                f"\\[([^\\]]+)\\]\\({pattern}\\)",
                lambda m: f"[{m.group(1)}]({quote(m.group(1), safe='')})"
                if m.group(1)
                else m.group(0),
                markdown_content,
            )

        return markdown_content

    def _parse_adf_to_markdown(self, adf_content):
        """Parse Atlassian Document Format to Markdown.

        Args:
            adf_content: ADF structure (dict) or string content

        Returns:
            str: Converted markdown text
        """
        if isinstance(adf_content, str):
            # If it's just a string, return it as-is
            return adf_content

        if not isinstance(adf_content, dict):
            return ""

        doc_type = adf_content.get("type", "")

        # Handle different node types
        if doc_type == "doc":
            # Document root - process all content nodes
            content = adf_content.get("content", [])
            return "\n\n".join(self._parse_adf_to_markdown(node) for node in content)

        elif doc_type == "paragraph":
            # Paragraph - process inline content
            content = adf_content.get("content", [])
            if not content:
                return ""
            return "".join(self._parse_adf_to_markdown(node) for node in content)

        elif doc_type == "text":
            # Text node - apply marks if any
            text = adf_content.get("text", "")
            marks = adf_content.get("marks", [])

            for mark in marks:
                mark_type = mark.get("type", "")
                if mark_type == "strong":
                    text = f"**{text}**"
                elif mark_type == "em":
                    text = f"*{text}*"
                elif mark_type == "code":
                    text = f"`{text}`"
                elif mark_type == "link":
                    href = mark.get("attrs", {}).get("href", "")
                    text = f"[{text}]({href})"

            return text

        elif doc_type == "bulletList":
            # Bullet list
            content = adf_content.get("content", [])
            items = []
            for item in content:
                item_text = self._parse_adf_to_markdown(item)
                # Add bullet point prefix
                for line in item_text.split("\n"):
                    if line:
                        items.append(f"- {line}")
            return "\n".join(items)

        elif doc_type == "orderedList":
            # Ordered list
            content = adf_content.get("content", [])
            items = []
            for i, item in enumerate(content, 1):
                item_text = self._parse_adf_to_markdown(item)
                # Add number prefix
                for j, line in enumerate(item_text.split("\n")):
                    if line:
                        if j == 0:
                            items.append(f"{i}. {line}")
                        else:
                            items.append(f"   {line}")
            return "\n".join(items)

        elif doc_type == "listItem":
            # List item - process content
            content = adf_content.get("content", [])
            return "\n".join(self._parse_adf_to_markdown(node) for node in content)

        elif doc_type == "heading":
            # Heading
            level = adf_content.get("attrs", {}).get("level", 1)
            content = adf_content.get("content", [])
            text = "".join(self._parse_adf_to_markdown(node) for node in content)
            return f"{'#' * level} {text}"

        elif doc_type == "codeBlock":
            # Code block
            content = adf_content.get("content", [])
            code = "\n".join(self._parse_adf_to_markdown(node) for node in content)
            language = adf_content.get("attrs", {}).get("language", "")
            return f"```{language}\n{code}\n```"

        elif doc_type == "blockquote":
            # Blockquote
            content = adf_content.get("content", [])
            quote_text = "\n".join(
                self._parse_adf_to_markdown(node) for node in content
            )
            # Add > prefix to each line
            return "\n".join(f"> {line}" for line in quote_text.split("\n"))

        elif doc_type == "mediaSingle" or doc_type == "media":
            # Media/attachment
            attrs = adf_content.get("attrs", {})
            # Try to get filename or alt text
            filename = attrs.get("alt", "") or attrs.get("title", "") or "attachment"
            # For now, just create a placeholder that will be replaced later
            return f"![{filename}](attachment)"

        elif doc_type == "mention":
            # User mention
            attrs = adf_content.get("attrs", {})
            text = attrs.get("text", "") or attrs.get("id", "@user")
            return f"@{text}"

        elif doc_type == "hardBreak":
            return "\n"

        else:
            # Unknown type - try to process content if it exists
            content = adf_content.get("content", [])
            if content:
                return "\n".join(self._parse_adf_to_markdown(node) for node in content)
            return ""

    def _compose_comments_section(self, issue_data, downloaded_attachments):
        """Compose the comments section of the markdown.

        Args:
            issue_data: Raw issue data from Jira API
            downloaded_attachments: List of downloaded attachment info

        Returns:
            list: Lines of markdown content for the comments section, or empty list if no comments
        """
        fields = issue_data.get("fields", {})
        comment_data = fields.get("comment", {})
        comments = comment_data.get("comments", [])

        if not comments:
            return []

        lines = []
        lines.append("## Comments")
        lines.append("")

        for i, comment in enumerate(comments):
            # Extract author and date
            author = comment.get("author", {}).get("displayName", "Unknown")
            created = comment.get("created", "")

            # Format the date (ISO 8601 to readable format)
            if created:
                # Parse and format: '2025-08-16T10:30:00.000+0000' -> '2025-08-16 10:30 AM'
                from datetime import datetime

                try:
                    # Handle various ISO formats
                    if created.endswith("Z"):
                        created = created[:-1] + "+00:00"
                    elif "+" in created and not created.endswith("+00:00"):
                        # Replace +0000 with +00:00
                        created = created.replace("+0000", "+00:00")

                    dt = datetime.fromisoformat(created)
                    formatted_date = dt.strftime("%Y-%m-%d %I:%M %p")
                except Exception:
                    formatted_date = created
            else:
                formatted_date = "Unknown date"

            # Format the comment header
            lines.append(f"**{author}** - _{formatted_date}_")
            lines.append("")

            # Process the comment body
            # Check if we have rendered HTML first
            body_html = comment.get("renderedBody", "")

            if body_html:
                # Use rendered HTML if available
                body_md = self.convert_html_to_markdown(body_html)
            else:
                # Check for ADF body structure
                body = comment.get("body")
                if isinstance(body, dict):
                    # Parse ADF structure
                    body_md = self._parse_adf_to_markdown(body)
                elif isinstance(body, str) and body:
                    # Plain text body
                    body_md = body
                else:
                    body_md = "*No comment body*"

            # Replace attachment links in the comment
            body_md = self.replace_attachment_links(body_md, downloaded_attachments)

            # Add the comment body
            lines.append(body_md)

            # Add separator between comments (except after the last one)
            if i < len(comments) - 1:
                lines.append("")
                lines.append("---")
                lines.append("")

        lines.append("")  # Add final spacing

        return lines

    def _generate_metadata_dict(self, issue_data):
        """Generate metadata dictionary from Jira issue data.

        Args:
            issue_data: Raw issue data from Jira API

        Returns:
            dict: Metadata dictionary for YAML frontmatter
        """
        fields = issue_data.get("fields", {})
        metadata = {}

        # Required fields
        metadata["key"] = issue_data.get("key", "UNKNOWN")
        metadata["summary"] = fields.get("summary", "No Summary")

        # Type and status
        if fields.get("issuetype"):
            metadata["type"] = fields["issuetype"].get("name")
        if fields.get("status"):
            metadata["status"] = fields["status"].get("name")

        # Priority
        if fields.get("priority"):
            metadata["priority"] = fields["priority"].get("name")

        # Resolution
        if fields.get("resolution"):
            metadata["resolution"] = fields["resolution"].get("name")

        # People
        if fields.get("assignee"):
            metadata["assignee"] = fields["assignee"].get("displayName")
        if fields.get("reporter"):
            metadata["reporter"] = fields["reporter"].get("displayName")
        if fields.get("creator"):
            metadata["creator"] = fields["creator"].get("displayName")

        # Labels
        if fields.get("labels"):
            metadata["labels"] = fields["labels"]

        # Components
        if fields.get("components"):
            metadata["components"] = [
                comp.get("name") for comp in fields["components"] if comp.get("name")
            ]

        # Parent issue (for sub-tasks)
        if fields.get("parent"):
            metadata["parent_key"] = fields["parent"].get("key")
            if fields["parent"].get("fields", {}).get("summary"):
                metadata["parent_summary"] = fields["parent"]["fields"]["summary"]

        # Versions
        if fields.get("versions"):
            metadata["affects_versions"] = [
                ver.get("name") for ver in fields["versions"] if ver.get("name")
            ]
        if fields.get("fixVersions"):
            metadata["fix_versions"] = [
                ver.get("name") for ver in fields["fixVersions"] if ver.get("name")
            ]

        # Dates
        if fields.get("created"):
            metadata["created_at"] = fields["created"]
        if fields.get("updated"):
            metadata["updated_at"] = fields["updated"]
        if fields.get("resolutiondate"):
            metadata["resolved_at"] = fields["resolutiondate"]

        # Remove None values and empty lists
        return {
            k: v
            for k, v in metadata.items()
            if v is not None and (not isinstance(v, list) or v)
        }

    def compose_markdown(self, issue_data, downloaded_attachments):
        """Compose the final markdown file content.

        Args:
            issue_data: Raw issue data from Jira API
            downloaded_attachments: List of downloaded attachment info

        Returns:
            str: Complete markdown content for the issue
        """
        fields = issue_data.get("fields", {})
        rendered_fields = issue_data.get("renderedFields", {})

        # Generate metadata dictionary
        metadata = self._generate_metadata_dict(issue_data)

        # Extract key and summary for the title
        key = metadata.get("key", "UNKNOWN")
        summary = metadata.get("summary", "No Summary")

        # Start composing markdown
        lines = []

        # YAML frontmatter
        yaml_content = yaml.dump(
            metadata, default_flow_style=False, allow_unicode=True, sort_keys=False
        )
        lines.append("---")
        lines.append(yaml_content.rstrip())
        lines.append("---")
        lines.append("")

        # Title with link to Jira issue
        lines.append(f"# [{key}]({self.base_url}/browse/{key}): {summary}")
        lines.append("")

        # Description section
        lines.append("## Description")
        lines.append("")

        # Convert description from HTML to Markdown
        description_html = rendered_fields.get("description", "")
        if not description_html and fields.get("description"):
            # If no rendered HTML, try to use raw description
            # (This would need ADF to Markdown conversion for full support)
            description_html = f"<p>{fields.get('description')}</p>"

        if description_html:
            description_md = self.convert_html_to_markdown(description_html)
            # Replace attachment links
            description_md = self.replace_attachment_links(
                description_md, downloaded_attachments
            )
            lines.append(description_md)
        else:
            lines.append("*No description provided*")

        lines.append("")

        # Comments section (after description, before attachments)
        comment_lines = self._compose_comments_section(
            issue_data, downloaded_attachments
        )
        if comment_lines:
            lines.extend(comment_lines)

        # Attachments section
        if downloaded_attachments:
            lines.append("## Attachments")
            lines.append("")
            for attachment in downloaded_attachments:
                filename = attachment["filename"]
                mime_type = attachment["mime_type"]
                encoded_filename = quote(filename, safe="")

                # Check if it's an image
                if mime_type and mime_type.startswith("image/"):
                    # Embed images
                    lines.append(f"- ![{filename}]({encoded_filename})")
                else:
                    # Link other files
                    lines.append(f"- [{filename}]({encoded_filename})")
            lines.append("")

        return "\n".join(lines)
