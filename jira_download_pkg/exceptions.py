"""Custom exceptions for jira-download."""


class JiraDownloadError(Exception):
    """Base exception for all jira-download errors."""

    pass


class JiraApiError(JiraDownloadError):
    """Raised when there's an error communicating with the Jira API."""

    def __init__(self, message, status_code=None, response=None):
        super().__init__(message)
        self.status_code = status_code
        self.response = response


class AuthenticationError(JiraApiError):
    """Raised when authentication with Jira fails."""

    pass


class IssueNotFoundError(JiraApiError):
    """Raised when the requested issue is not found."""

    pass


class AttachmentDownloadError(JiraDownloadError):
    """Raised when there's an error downloading an attachment."""

    def __init__(self, message, filename=None):
        super().__init__(message)
        self.filename = filename


class ConfigurationError(JiraDownloadError):
    """Raised when there's a configuration problem."""

    pass
