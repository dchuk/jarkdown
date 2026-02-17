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
        self._downloaded_attachments = []
        self._attachments_by_id = {}
        self._attachments_by_name = {}

    def _prepare_attachment_lookup(self, downloaded_attachments):
        """Create lookup dictionaries for downloaded attachments."""
        self._downloaded_attachments = downloaded_attachments or []
        self._attachments_by_id = {}
        self._attachments_by_name = {}

        for attachment in self._downloaded_attachments:
            if not attachment:
                continue

            attachment_id = attachment.get("attachment_id")
            if attachment_id is not None:
                self._attachments_by_id[str(attachment_id)] = attachment

            for name in filter(
                None,
                [
                    attachment.get("original_filename"),
                    attachment.get("filename"),
                ],
            ):
                self._attachments_by_name[name.lower()] = attachment

    def _get_attachment_for_media(self, attachment_id=None, filename_hint=None):
        """Find a downloaded attachment by id or filename hint."""
        if attachment_id is not None:
            attachment = self._attachments_by_id.get(str(attachment_id))
            if attachment:
                return attachment

        if filename_hint:
            normalized = filename_hint.strip().lower()
            attachment = self._attachments_by_name.get(normalized)
            if attachment:
                return attachment

        return None

    def _media_attrs_to_markdown(self, attrs):
        """Convert ADF media attributes to Markdown image syntax."""
        if not isinstance(attrs, dict):
            return "![attachment](attachment)"

        media_type = attrs.get("type", "file")
        filename_hint = (
            attrs.get("alt") or attrs.get("title") or attrs.get("fileName") or ""
        )

        if media_type == "external":
            url = attrs.get("url")
            if url:
                alt_text = filename_hint or url
                return f"![{alt_text}]({url})"

        attachment = self._get_attachment_for_media(
            attachment_id=attrs.get("id"),
            filename_hint=filename_hint,
        )

        if attachment:
            local_name = attachment.get("filename")
            encoded_filename = quote(local_name, safe="") if local_name else ""
            alt_text = (
                filename_hint
                or attachment.get("original_filename")
                or local_name
                or "attachment"
            )
            if encoded_filename:
                return f"![{alt_text}]({encoded_filename})"

        alt_text = filename_hint or "attachment"
        return f"![{alt_text}](attachment)"

    def convert_html_to_markdown(self, html_content):
        """Convert HTML content to Markdown.

        Args:
            html_content: HTML string to convert

        Returns:
            str: Converted markdown content
        """
        if not html_content:
            return ""

        # Remove Atlassian-specific wrappers around images to keep plain Markdown embeds
        html_content = re.sub(
            r"<jira-attachment-thumbnail[^>]*>(.*?)</jira-attachment-thumbnail>",
            r"\1",
            html_content,
            flags=re.IGNORECASE | re.DOTALL,
        )
        html_content = re.sub(
            r"<a\b[^>]*>\s*(<img\b[^>]*>)\s*</a>",
            r"\1",
            html_content,
            flags=re.IGNORECASE | re.DOTALL,
        )

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
        optional_domain = f"(?:https?://{escaped_domain})?"
        rest_prefix = f"{optional_domain}/(?:jira/)?rest/api/[0-9]+/attachment"
        secure_prefix = f"{optional_domain}/secure/attachment"

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
                    f"{secure_prefix}/[0-9]+/{escaped_original}",
                    f"{secure_prefix}/[0-9]+/{encoded_original}",
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
            attachment_id = attachment.get("attachment_id")
            if attachment_id:
                escaped_id = re.escape(str(attachment_id))
                id_pattern = f"{rest_prefix}/(?:content|thumbnail)/{escaped_id}"
                markdown_content = re.sub(
                    f"(!\\[[^\\]]*\\])\\({id_pattern}\\)",
                    f"\\1({encoded_filename})",
                    markdown_content,
                )
                markdown_content = re.sub(
                    f"(\\[[^\\]]+\\])\\({id_pattern}\\)",
                    f"\\1({encoded_filename})",
                    markdown_content,
                )

        # For generic attachment content URLs (without filename in path)
        # Replace all remaining Jira attachment URLs with placeholder
        # This is a fallback for URLs that don't have the filename in them
        patterns = [
            f"{optional_domain}/jira/rest/api/[0-9]+/attachment/content/[0-9]+",
            f"{optional_domain}/rest/api/[0-9]+/attachment/content/[0-9]+",
            f"{optional_domain}/jira/rest/api/[0-9]+/attachment/thumbnail/[0-9]+",
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

    def _compose_linked_issues_section(self, issue_data):
        """Compose the linked issues section of the markdown.

        Args:
            issue_data: Raw issue data from Jira API

        Returns:
            list: Lines of markdown content for linked issues section
        """
        lines = ["## Linked Issues", ""]
        issuelinks = issue_data.get("fields", {}).get("issuelinks", [])

        if not issuelinks:
            lines.append("None")
            lines.append("")
            return lines

        groups = {}
        for link in issuelinks:
            link_type = link.get("type", {})
            if "outwardIssue" in link:
                label = link_type.get("outward", "Related").title()
                issue = link["outwardIssue"]
            elif "inwardIssue" in link:
                label = link_type.get("inward", "Related").title()
                issue = link["inwardIssue"]
            else:
                continue

            groups.setdefault(label, []).append(issue)

        for label, issues in groups.items():
            lines.append(f"### {label}")
            lines.append("")
            for issue in issues:
                key = issue.get("key", "UNKNOWN")
                summary = issue.get("fields", {}).get("summary", "")
                status = issue.get("fields", {}).get("status", {}).get("name", "")
                lines.append(
                    f"- [{key}]({self.base_url}/browse/{key}): {summary} ({status})"
                )
            lines.append("")

        return lines

    def _compose_subtasks_section(self, issue_data):
        """Compose the subtasks section of the markdown.

        Args:
            issue_data: Raw issue data from Jira API

        Returns:
            list: Lines of markdown content for subtasks section
        """
        lines = ["## Subtasks", ""]
        subtasks = issue_data.get("fields", {}).get("subtasks", [])

        if not subtasks:
            lines.append("None")
            lines.append("")
            return lines

        for subtask in subtasks:
            key = subtask.get("key", "UNKNOWN")
            summary = subtask.get("fields", {}).get("summary", "")
            status = subtask.get("fields", {}).get("status", {}).get("name", "")
            issue_type = subtask.get("fields", {}).get("issuetype", {}).get("name", "")
            lines.append(
                f"- [{key}]({self.base_url}/browse/{key}): {summary} ({status}) \u2014 {issue_type}"
            )

        lines.append("")
        return lines

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

        elif doc_type == "mediaSingle":
            # Media container - render contained media nodes
            content = adf_content.get("content", [])
            rendered = [self._parse_adf_to_markdown(node) for node in content if node]
            combined = "\n".join(filter(None, rendered))
            if combined:
                return combined

            # Fall back to attributes if there is no nested media node
            attrs = adf_content.get("attrs", {})
            return self._media_attrs_to_markdown(attrs)

        elif doc_type == "media":
            # Concrete media node
            attrs = adf_content.get("attrs", {})
            return self._media_attrs_to_markdown(attrs)

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

    def _compose_environment_section(self, issue_data):
        """Compose the environment section of the markdown.

        Args:
            issue_data: Raw issue data from Jira API

        Returns:
            list: Lines of markdown content for environment section
        """
        lines = ["## Environment", ""]

        # Try rendered HTML first
        rendered_env = issue_data.get("renderedFields", {}).get("environment")
        if rendered_env:
            lines.append(self.convert_html_to_markdown(rendered_env))
        else:
            # Fallback to fields.environment (ADF or string)
            raw_env = issue_data.get("fields", {}).get("environment")
            if raw_env and isinstance(raw_env, dict):
                lines.append(self._parse_adf_to_markdown(raw_env))
            elif raw_env and isinstance(raw_env, str):
                lines.append(raw_env)
            else:
                lines.append("None")

        lines.append("")
        return lines

    def _adf_to_plain_text(self, adf_content):
        """Extract plain text from ADF content, stripping all formatting.

        Args:
            adf_content: ADF structure (dict), string, or None

        Returns:
            str: Plain text content
        """
        if adf_content is None:
            return ""
        if isinstance(adf_content, str):
            return adf_content
        if not isinstance(adf_content, dict):
            return ""

        if adf_content.get("type") == "text":
            return adf_content.get("text", "")

        children = adf_content.get("content", [])
        parts = [self._adf_to_plain_text(child) for child in children]
        return " ".join(part for part in parts if part)

    def _compose_worklogs_section(self, issue_data):
        """Compose the worklogs section of the markdown.

        Args:
            issue_data: Raw issue data from Jira API

        Returns:
            list: Lines of markdown content for worklogs section
        """
        fields = issue_data.get("fields", {})
        worklog_data = fields.get("worklog") or {}
        worklogs = worklog_data.get("worklogs", [])
        total = worklog_data.get("total", 0)
        max_results = worklog_data.get("maxResults", 20)

        lines = ["## Worklogs", ""]

        if not worklogs:
            lines.append("None")
            lines.append("")
            return lines

        # Calculate total time
        total_seconds = sum(entry.get("timeSpentSeconds", 0) for entry in worklogs)
        lines.append(f"**Total Time Logged:** {self._format_time(total_seconds)}")
        lines.append("")

        # Truncation warning
        if total > max_results or total > len(worklogs):
            lines.append(
                f"> **Note:** Showing {len(worklogs)} of {total} worklogs."
                " Additional worklogs may exist."
            )
            lines.append("")

        # Table header
        lines.append("| Author | Time Spent | Date | Comment |")
        lines.append("|--------|-----------|------|---------|")

        for entry in worklogs:
            author = entry.get("author", {}).get("displayName", "Unknown")
            time_spent = entry.get("timeSpent", "")
            started = entry.get("started", "")
            date = started[:10] if started else ""
            comment = self._adf_to_plain_text(entry.get("comment"))
            # Escape pipes for table safety
            comment = comment.replace("|", "\\|")
            lines.append(f"| {author} | {time_spent} | {date} | {comment} |")

        lines.append("")
        return lines

    @staticmethod
    def _format_time(seconds):
        """Format seconds into human-readable time string.

        Args:
            seconds: Total seconds to format

        Returns:
            str: Formatted string like '1d 4h 30m'
        """
        days = seconds // 28800  # 8h workday
        remaining = seconds % 28800
        hours = remaining // 3600
        remaining = remaining % 3600
        minutes = remaining // 60

        parts = []
        if days:
            parts.append(f"{days}d")
        if hours:
            parts.append(f"{hours}h")
        if minutes:
            parts.append(f"{minutes}m")
        return " ".join(parts) if parts else "0m"

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
        rendered_comment_lookup = {}
        rendered_comments = (
            issue_data.get("renderedFields", {}).get("comment", {}).get("comments", [])
        )
        for rendered in rendered_comments:
            rendered_comment_lookup[rendered.get("id")] = rendered

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
            if not body_html:
                rendered_comment = rendered_comment_lookup.get(comment.get("id"))
                if rendered_comment:
                    body_html = rendered_comment.get("body", "")

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
        metadata["type"] = (fields.get("issuetype") or {}).get("name")
        metadata["status"] = (fields.get("status") or {}).get("name")

        # Priority
        metadata["priority"] = (fields.get("priority") or {}).get("name")

        # Resolution
        metadata["resolution"] = (fields.get("resolution") or {}).get("name")

        # People
        metadata["assignee"] = (fields.get("assignee") or {}).get("displayName")
        metadata["reporter"] = (fields.get("reporter") or {}).get("displayName")
        metadata["creator"] = (fields.get("creator") or {}).get("displayName")

        # Labels
        metadata["labels"] = fields.get("labels", [])

        # Components
        metadata["components"] = [
            comp.get("name")
            for comp in fields.get("components", [])
            if comp.get("name")
        ]

        # Parent issue (for sub-tasks)
        metadata["parent_key"] = (fields.get("parent") or {}).get("key")
        metadata["parent_summary"] = (
            (fields.get("parent") or {}).get("fields", {}).get("summary")
        )

        # Versions
        metadata["affects_versions"] = [
            ver.get("name")
            for ver in fields.get("versions", [])
            if ver.get("name")
        ]
        metadata["fix_versions"] = [
            ver.get("name")
            for ver in fields.get("fixVersions", [])
            if ver.get("name")
        ]

        # Dates
        metadata["created_at"] = fields.get("created")
        metadata["updated_at"] = fields.get("updated")
        metadata["resolved_at"] = fields.get("resolutiondate")

        return metadata

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

        # Allow ADF parsing to resolve downloaded attachments
        self._prepare_attachment_lookup(downloaded_attachments)

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
