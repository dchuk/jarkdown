"""Renderer for Jira custom fields with type-aware formatting."""

import logging


class CustomFieldRenderer:
    """Renders custom field values based on field type metadata."""

    def __init__(self, adf_parser=None):
        """Initialize the custom field renderer.

        Args:
            adf_parser: Callable that converts ADF dict to markdown string.
                        Typically MarkdownConverter._parse_adf_to_markdown.
        """
        self.logger = logging.getLogger(__name__)
        self._adf_parser = adf_parser

    def render_value(self, value, schema=None):
        """Render a custom field value to markdown string.

        Uses schema type for type-aware rendering when available,
        falls back to value shape inspection.

        Args:
            value: The field value from Jira API (any type).
            schema: Field schema dict with 'type' key, or None.

        Returns:
            str: Markdown-formatted string representation, or None if value is empty.
        """
        if value is None:
            return None

        # Try schema-based rendering first
        if schema:
            schema_type = schema.get("type", "")
            rendered = self._render_by_schema(value, schema_type)
            if rendered is not None:
                return rendered

        # Fall back to value shape inspection
        return self._render_by_shape(value)

    def _render_by_schema(self, value, schema_type):
        """Render value based on schema type.

        Args:
            value: Field value.
            schema_type: Schema type string (string, number, option, user, date, array, etc.)

        Returns:
            str or None: Rendered string, or None if type not recognized.
        """
        if schema_type in ("string", "number"):
            return str(value)
        elif schema_type == "date":
            return str(value)
        elif schema_type == "datetime":
            return str(value)[:19] if len(str(value)) > 19 else str(value)
        elif schema_type == "option":
            if isinstance(value, dict):
                return value.get("value", str(value))
            return str(value)
        elif schema_type == "user":
            if isinstance(value, dict):
                return value.get("displayName", value.get("name", str(value)))
            return str(value)
        elif schema_type == "array":
            return self._render_array(value)
        elif schema_type in ("any",):
            # ADF rich text fields often have schema type "any"
            return self._render_by_shape(value)
        return None

    def _render_array(self, value):
        """Render an array field value.

        Args:
            value: List of values (options, users, strings, etc.)

        Returns:
            str: Comma-joined string of rendered items.
        """
        if not isinstance(value, list):
            return str(value)
        if not value:
            return None

        items = []
        for item in value:
            if isinstance(item, dict):
                # Try common dict patterns
                text = (
                    item.get("value")
                    or item.get("displayName")
                    or item.get("name")
                    or str(item)
                )
                items.append(str(text))
            else:
                items.append(str(item))
        return ", ".join(items)

    def _render_by_shape(self, value):
        """Render value by inspecting its shape (generic fallback).

        Args:
            value: Any value from Jira API.

        Returns:
            str: Rendered string, or None if value is effectively empty.
        """
        if isinstance(value, str):
            return value if value else None

        if isinstance(value, (int, float)):
            return str(value)

        if isinstance(value, dict):
            # ADF document
            if value.get("type") == "doc" and self._adf_parser:
                rendered = self._adf_parser(value)
                return rendered if rendered else None

            # Option/select field
            if "value" in value:
                return str(value["value"])

            # User/people field
            if "displayName" in value:
                return str(value["displayName"])

            # Named entity
            if "name" in value:
                return str(value["name"])

            return str(value)

        if isinstance(value, list):
            return self._render_array(value)

        return str(value) if value is not None else None
