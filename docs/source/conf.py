"""Configuration file for the Sphinx documentation builder."""

import os
import sys
from datetime import datetime

# Add project root to path for autodoc
sys.path.insert(0, os.path.abspath("../.."))

# Project information
project = "jira-download"
copyright = f"{datetime.now().year}, Chris Reynolds"
author = "Chris Reynolds"
release = "1.0.0"

# General configuration
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
    "sphinx.ext.intersphinx",
    "myst_parser",
    "sphinx_autodoc_typehints",
]

templates_path = ["_templates"]
exclude_patterns = []

# Intersphinx mapping for Python stdlib
intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
}

# Autodoc settings
autodoc_default_options = {
    "members": True,
    "member-order": "bysource",
    "special-members": "__init__",
    "undoc-members": True,
    "exclude-members": "__weakref__",
}

# MyST parser configuration
myst_enable_extensions = [
    "deflist",
    "tasklist",
    "html_image",
]

# HTML output options using Furo theme
html_theme = "furo"
html_static_path = ["_static"]
html_title = "jira-download Documentation"

# Theme options
html_theme_options = {
    "light_css_variables": {
        "color-brand-primary": "#0052CC",  # Atlassian blue
        "color-brand-content": "#0052CC",
    },
    "dark_css_variables": {
        "color-brand-primary": "#579DFF",  # Lighter blue for dark mode
        "color-brand-content": "#579DFF",
    },
}

# Source suffix
source_suffix = {
    ".rst": "restructuredtext",
    ".md": "markdown",
}
