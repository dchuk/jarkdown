"""Custom exceptions for jarkdown."""


class JarkdownError(Exception):
    """Base exception for all jarkdown errors."""

    pass


class JiraApiError(JarkdownError):
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


class AttachmentDownloadError(JarkdownError):
    """Raised when there's an error downloading an attachment."""

    def __init__(self, message, filename=None):
        super().__init__(message)
        self.filename = filename


class ConfigurationError(JarkdownError):
    """Raised when there's a configuration problem."""

    pass
