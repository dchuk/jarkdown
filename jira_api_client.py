"""Jira API client for handling all communication with Jira Cloud REST API."""

import logging
import requests

from exceptions import JiraApiError, AuthenticationError, IssueNotFoundError


class JiraApiClient:
    """Handles all communication with the Jira Cloud REST API."""
    
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
        
        self.session = requests.Session()
        self.session.auth = (email, api_token)
        self.session.headers.update({
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        })
        
        self.logger = logging.getLogger(__name__)
    
    def fetch_issue(self, issue_key):
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
                raise AuthenticationError(
                    "Authentication failed. Please check your API token and email.",
                    status_code=401,
                    response=response
                )
            elif response.status_code == 404:
                raise IssueNotFoundError(
                    f"Issue {issue_key} not found or not accessible.",
                    status_code=404,
                    response=response
                )
            else:
                raise JiraApiError(
                    f"HTTP error occurred: {e}",
                    status_code=response.status_code,
                    response=response
                )
                
        except requests.exceptions.RequestException as e:
            raise JiraApiError(f"Error fetching issue: {e}")
    
    def get_attachment_content_url(self, attachment):
        """Get the download URL for an attachment.
        
        Args:
            attachment: Attachment metadata from Jira API
            
        Returns:
            str: The content URL for downloading the attachment
        """
        return attachment.get('content', '')
    
    def download_attachment_stream(self, content_url):
        """Stream download an attachment.
        
        Args:
            content_url: The URL to download the attachment from
            
        Returns:
            requests.Response: Streaming response object
            
        Raises:
            JiraApiError: If download fails
        """
        try:
            response = self.session.get(content_url, stream=True)
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            raise JiraApiError(f"Error downloading attachment: {e}")