API Reference
=============

This section provides detailed API documentation for the jarkdown components.

Main Module
-----------

.. automodule:: jarkdown
   :members:
   :undoc-members:
   :show-inheritance:

JiraApiClient
-------------

.. autoclass:: jarkdown.jira_api_client.JiraApiClient
   :members:
   :undoc-members:
   :show-inheritance:
   :special-members: __init__

   The JiraApiClient handles all communication with the Jira REST API.

   Example usage::

       from jarkdown.jira_api_client import JiraApiClient

       client = JiraApiClient(
           domain="company.atlassian.net",
           email="user@company.com",
           api_token="your_token"
       )

       issue_data = client.get_issue("PROJ-123")

AttachmentHandler
-----------------

.. autoclass:: jarkdown.attachment_handler.AttachmentHandler
   :members:
   :undoc-members:
   :show-inheritance:
   :special-members: __init__

   The AttachmentHandler manages downloading and saving attachments.

   Example usage::

       from jarkdown.attachment_handler import AttachmentHandler

       handler = AttachmentHandler(auth_session, verbose=True)
       downloaded = handler.download_attachments(
           attachments_data,
           output_dir="/path/to/output"
       )

MarkdownConverter
-----------------

.. autoclass:: jarkdown.markdown_converter.MarkdownConverter
   :members:
   :undoc-members:
   :show-inheritance:

   The MarkdownConverter transforms Jira HTML content to clean Markdown.

   Example usage::

       from jarkdown.markdown_converter import MarkdownConverter

       converter = MarkdownConverter()
       markdown_content = converter.convert_issue(
           issue_data,
           attachment_mapping
       )

Exceptions
----------

.. automodule:: jarkdown.exceptions
   :members:
   :undoc-members:
   :show-inheritance:

   Custom exceptions for error handling.

   Exception Hierarchy::

       JarkdownError
       ├── ConfigurationError
       ├── JiraApiError
       │   ├── AuthenticationError
       │   └── IssueNotFoundError
       └── AttachmentDownloadError

   Example usage::

       from jarkdown.exceptions import AuthenticationError, IssueNotFoundError

       try:
           issue = client.get_issue(issue_key)
       except AuthenticationError:
           print("Invalid credentials")
       except IssueNotFoundError:
           print(f"Issue {issue_key} not found")
