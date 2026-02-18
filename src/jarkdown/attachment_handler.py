"""Handler for downloading and managing Jira attachments."""

import asyncio
import logging
from pathlib import Path

from .exceptions import AttachmentDownloadError


class AttachmentHandler:
    """Manages downloading and saving of issue attachments."""

    def __init__(self, api_client):
        """Initialize the attachment handler.

        Args:
            api_client: JiraApiClient instance for API communication
        """
        self.api_client = api_client
        self.logger = logging.getLogger(__name__)

    async def download_attachment(self, attachment, output_dir):
        """Download a single attachment asynchronously.

        Args:
            attachment: Attachment metadata from Jira API
            output_dir: Directory to save the attachment to

        Returns:
            dict: Information about the downloaded attachment including
                  filename, original_filename, mime_type, and path

        Raises:
            AttachmentDownloadError: If download fails
        """
        filename = attachment["filename"]
        content_url = attachment["content"]
        mime_type = attachment.get("mimeType", "")
        size = attachment.get("size", 0)

        file_path = output_dir / filename

        # Handle filename conflicts (sync — just stat checks)
        counter = 1
        original_path = file_path
        while file_path.exists():
            stem = original_path.stem
            suffix = original_path.suffix
            file_path = original_path.parent / f"{stem}_{counter}{suffix}"
            counter += 1

        self.logger.info(f"  Downloading {filename} ({self._format_size(size)})...")

        try:
            response = await self.api_client.download_attachment_stream(content_url)
            # Buffer entire attachment then write via thread to avoid blocking event loop
            data = await response.read()
            await asyncio.to_thread(file_path.write_bytes, data)

            return {
                "attachment_id": attachment.get("id"),
                "filename": file_path.name,
                "original_filename": filename,
                "mime_type": mime_type,
                "path": file_path,
            }

        except Exception as e:
            raise AttachmentDownloadError(
                f"Error downloading {filename}: {e}", filename=filename
            )

    async def download_all_attachments(self, attachments, output_dir):
        """Download all attachments for an issue asynchronously (sequential).

        Args:
            attachments: List of attachment metadata from Jira API
            output_dir: Directory to save attachments to

        Returns:
            list: Information about all successfully downloaded attachments
        """
        if not attachments:
            return []

        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        self.logger.info(f"Downloading {len(attachments)} attachment(s)...")

        downloaded = []
        for attachment in attachments:
            try:
                result = await self.download_attachment(attachment, output_dir)
                if result:
                    downloaded.append(result)
            except AttachmentDownloadError as e:
                self.logger.error(str(e))
                # Continue downloading other attachments

        return downloaded

    def _format_size(self, size):
        """Format file size in human-readable format.

        Args:
            size: Size in bytes

        Returns:
            str: Formatted size string
        """
        for unit in ["B", "KB", "MB", "GB"]:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"
