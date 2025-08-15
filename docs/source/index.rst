.. jira-download documentation master file

Welcome to jira-download's documentation!
==========================================

jira-download is a command-line tool that exports Jira Cloud issues to Markdown files with all attachments downloaded locally.

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   installation
   usage
   api
   contributing

Features
--------

* Fetches Jira issues via the Jira Cloud REST API
* Downloads all attachments to a local folder
* Converts issue descriptions from HTML to GitHub-flavored Markdown
* Preserves formatting (headings, lists, code blocks, tables)
* Embeds images inline and links other file types
* Maintains the same visual structure as in Jira

Quick Start
-----------

Install jira-download::

    pip install jira-download

Export a Jira issue::

    jira-download PROJ-123

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`