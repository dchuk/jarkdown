"""Cache for Jira field metadata with XDG-compliant storage."""

import json
import logging
import time
from pathlib import Path

from platformdirs import user_config_dir


class FieldMetadataCache:
    """Manages cached Jira field metadata with 24-hour TTL."""

    CACHE_TTL_SECONDS = 86400  # 24 hours

    def __init__(self, domain):
        """Initialize field metadata cache.

        Args:
            domain: Jira domain for cache isolation (e.g., 'company.atlassian.net')
        """
        self.domain = domain
        self.logger = logging.getLogger(__name__)
        self._cache_dir = Path(user_config_dir("jarkdown"))
        self._cache_file = self._cache_dir / f"fields-{domain}.json"
        self._field_map = None  # Lazy-loaded id→name dict

    def _ensure_cache_dir(self):
        """Create cache directory if it doesn't exist."""
        self._cache_dir.mkdir(parents=True, exist_ok=True)

    def is_stale(self):
        """Check if cached data is older than TTL.

        Returns:
            bool: True if cache doesn't exist or is older than 24 hours.
        """
        if not self._cache_file.exists():
            return True
        try:
            data = json.loads(self._cache_file.read_text())
            cached_at = data.get("cached_at", 0)
            return (time.time() - cached_at) > self.CACHE_TTL_SECONDS
        except (json.JSONDecodeError, OSError):
            return True

    def save(self, fields):
        """Save field metadata to cache with timestamp.

        Args:
            fields: List of field definition dicts from Jira API.
        """
        self._ensure_cache_dir()
        cache_data = {
            "cached_at": time.time(),
            "domain": self.domain,
            "fields": fields,
        }
        self._cache_file.write_text(json.dumps(cache_data, indent=2))
        self._field_map = None  # Reset lazy cache

    def load(self):
        """Load field metadata from cache.

        Returns:
            list: List of field definition dicts, or empty list if no cache.
        """
        if not self._cache_file.exists():
            return []
        try:
            data = json.loads(self._cache_file.read_text())
            return data.get("fields", [])
        except (json.JSONDecodeError, OSError):
            return []

    def get_field_name(self, field_id):
        """Resolve a field ID to its display name.

        Args:
            field_id: Jira field ID (e.g., 'customfield_10001')

        Returns:
            str: Display name or the raw field_id if not found.
        """
        if self._field_map is None:
            fields = self.load()
            self._field_map = {
                f["id"]: f.get("name", f["id"]) for f in fields if "id" in f
            }
        return self._field_map.get(field_id, field_id)

    def get_field_schema(self, field_id):
        """Get the schema for a field by ID.

        Args:
            field_id: Jira field ID

        Returns:
            dict: Schema dict with 'type', 'custom' keys, or empty dict.
        """
        fields = self.load()
        for f in fields:
            if f.get("id") == field_id:
                return f.get("schema", {})
        return {}

    def refresh(self, api_client, force=False):
        """Refresh cache from API if stale or forced.

        Args:
            api_client: JiraApiClient instance for API calls.
            force: If True, refresh regardless of TTL.

        Returns:
            list: Field metadata list (from fresh fetch or cache).
        """
        if not force and not self.is_stale():
            return self.load()

        try:
            fields = api_client.fetch_fields()
            self.save(fields)
            self.logger.info(f"Field metadata cached ({len(fields)} fields)")
            return fields
        except Exception as e:
            self.logger.warning(f"Failed to refresh field metadata: {e}")
            cached = self.load()
            if cached:
                self.logger.warning("Using stale cached field metadata")
                return cached
            self.logger.warning("No cached field metadata available")
            return []
