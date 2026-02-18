"""Jira API client for handling all communication with Jira Cloud REST API."""

import asyncio
import logging

import aiohttp

from .exceptions import JiraApiError, AuthenticationError, IssueNotFoundError


class JiraApiClient:
    """Handles all communication with the Jira Cloud REST API using async aiohttp."""

    def __init__(self, domain, email, api_token):
        """Initialize the Jira API client.

        Args:
            domain: Jira domain (e.g., 'company.atlassian.net')
            email: User email for authentication
            api_token: API token for authentication
        """
        self.domain = domain
        self.email = email
        self.api_token = api_token
        self.base_url = f"https://{domain}"
        self.api_base = f"{self.base_url}/rest/api/3"
        self.session = None

        self.logger = logging.getLogger(__name__)

    async def __aenter__(self):
        """Create aiohttp session with connection pooling and auth.

        Returns:
            JiraApiClient: Self with active session
        """
        connector = aiohttp.TCPConnector(limit_per_host=5)
        auth = aiohttp.BasicAuth(self.email, self.api_token)
        timeout = aiohttp.ClientTimeout(total=30)
        self.session = aiohttp.ClientSession(
            connector=connector,
            auth=auth,
            timeout=timeout,
            headers={"Accept": "application/json", "Content-Type": "application/json"},
        )
        return self

    async def __aexit__(self, *args):
        """Close session with SSL cleanup delay."""
        await self.session.close()
        await asyncio.sleep(0.250)  # SSL cleanup per research

    async def fetch_issue(self, issue_key):
        """Fetch issue data from Jira API.

        Args:
            issue_key: The Jira issue key (e.g., 'PROJ-123')

        Returns:
            dict: Raw JSON response from Jira API

        Raises:
            AuthenticationError: If authentication fails
            IssueNotFoundError: If issue is not found
            JiraApiError: For other API errors
        """
        url = f"{self.api_base}/issue/{issue_key}"
        params = {"fields": "*all", "expand": "renderedFields"}

        self.logger.info(f"Fetching issue {issue_key}...")

        try:
            response = await self.session.get(url, params=params)
            response.raise_for_status()
            return await response.json()

        except aiohttp.ClientResponseError as e:
            if e.status == 401:
                raise AuthenticationError(
                    "Authentication failed. Please check your API token and email.",
                    status_code=401,
                )
            elif e.status == 404:
                raise IssueNotFoundError(
                    f"Issue {issue_key} not found or not accessible.",
                    status_code=404,
                )
            else:
                raise JiraApiError(
                    f"HTTP error occurred: {e}",
                    status_code=e.status,
                )

        except aiohttp.ClientError as e:
            raise JiraApiError(f"Error fetching issue: {e}")

    async def fetch_fields(self):
        """Fetch all field definitions from Jira.

        Returns:
            list: List of field definition dicts with id, name, schema keys.

        Raises:
            AuthenticationError: If authentication fails
            JiraApiError: If the API call fails.
        """
        url = f"{self.api_base}/field"
        self.logger.info("Fetching field metadata...")

        try:
            response = await self.session.get(url)
            response.raise_for_status()
            return await response.json()

        except aiohttp.ClientResponseError as e:
            if e.status == 401:
                raise AuthenticationError(
                    "Authentication failed while fetching field metadata.",
                    status_code=401,
                )
            raise JiraApiError(
                f"Error fetching field metadata: {e}",
                status_code=e.status,
            )

        except aiohttp.ClientError as e:
            raise JiraApiError(f"Error fetching field metadata: {e}")

    def get_attachment_content_url(self, attachment):
        """Get the download URL for an attachment.

        Args:
            attachment: Attachment metadata from Jira API

        Returns:
            str: The content URL for downloading the attachment
        """
        return attachment.get("content", "")

    async def download_attachment_stream(self, content_url):
        """Stream download an attachment.

        Args:
            content_url: The URL to download the attachment from

        Returns:
            aiohttp.ClientResponse: Active response object for streaming

        Raises:
            JiraApiError: If download fails
        """
        try:
            response = await self.session.get(content_url)
            response.raise_for_status()
            return response
        except aiohttp.ClientResponseError as e:
            raise JiraApiError(f"Error downloading attachment: HTTP {e.status}")
        except aiohttp.ClientError as e:
            raise JiraApiError(f"Error downloading attachment: {e}")
