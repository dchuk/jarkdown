jarkdown Documentation
============================

**jarkdown** is a powerful command-line tool that exports Jira issues to clean, readable Markdown files with all attachments preserved locally. Perfect for archiving, documentation, or offline access to your Jira content.

Key Features
------------

* **Complete Issue Export**: Downloads issue description, comments, and all metadata
* **Attachment Preservation**: Automatically downloads and organizes all attachments
* **Clean Markdown Output**: Converts Jira's HTML to well-formatted Markdown
* **Local References**: Updates attachment links to point to downloaded files
* **Simple CLI**: Easy-to-use command-line interface with clear options

Why jarkdown?
------------------

Jira is excellent for issue tracking, but sometimes you need your data elsewhere:

* **Offline Access**: Work with issues when disconnected from the internet
* **Documentation**: Include real issue data in your project documentation
* **Archiving**: Create permanent, readable backups of important issues
* **Migration**: Move issues between systems or prepare for system changes
* **Analysis**: Process issue data with your favorite text processing tools

Quick Start
-----------

.. code-block:: bash

   # Install from PyPI (coming soon)
   pip install jarkdown

   # Export a single issue
   jarkdown PROJ-123

   # Export with custom output location
   jarkdown PROJ-123 --output ~/Documents/jira-exports

Contents
--------

.. toctree::
   :maxdepth: 2
   :caption: User Guide

   installation
   usage
   configuration

.. toctree::
   :maxdepth: 2
   :caption: Developer Guide

   architecture
   api_reference
   contributing

.. toctree::
   :maxdepth: 1
   :caption: Project

   changelog
   license

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
