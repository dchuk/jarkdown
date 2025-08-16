API Reference
=============

This section provides detailed API documentation for the jira-download components.

Main Module
-----------

.. automodule:: jira_download
   :members:
   :undoc-members:
   :show-inheritance:

JiraApiClient
-------------

.. autoclass:: jira_api_client.JiraApiClient
   :members:
   :undoc-members:
   :show-inheritance:
   :special-members: __init__

   The JiraApiClient handles all communication with the Jira REST API.

   Example usage::

       from jira_api_client import JiraApiClient
       
       client = JiraApiClient(
           domain="company.atlassian.net",
           email="user@company.com",
           api_token="your_token"
       )
       
       issue_data = client.get_issue("PROJ-123")

AttachmentHandler
-----------------

.. autoclass:: attachment_handler.AttachmentHandler
   :members:
   :undoc-members:
   :show-inheritance:
   :special-members: __init__

   The AttachmentHandler manages downloading and saving attachments.

   Example usage::

       from attachment_handler import AttachmentHandler
       
       handler = AttachmentHandler(auth_session, verbose=True)
       downloaded = handler.download_attachments(
           attachments_data,
           output_dir="/path/to/output"
       )

MarkdownConverter
-----------------

.. autoclass:: markdown_converter.MarkdownConverter
   :members:
   :undoc-members:
   :show-inheritance:

   The MarkdownConverter transforms Jira HTML content to clean Markdown.

   Example usage::

       from markdown_converter import MarkdownConverter
       
       converter = MarkdownConverter()
       markdown_content = converter.convert_issue(
           issue_data,
           attachment_mapping
       )

Exceptions
----------

.. automodule:: exceptions
   :members:
   :undoc-members:
   :show-inheritance:

   Custom exceptions for error handling.

   Exception Hierarchy::

       JiraDownloadError
       ├── ConfigurationError
       ├── JiraApiError
       │   ├── AuthenticationError
       │   └── IssueNotFoundError
       └── AttachmentDownloadError

   Example usage::

       from exceptions import AuthenticationError, IssueNotFoundError
       
       try:
           issue = client.get_issue(issue_key)
       except AuthenticationError:
           print("Invalid credentials")
       except IssueNotFoundError:
           print(f"Issue {issue_key} not found")