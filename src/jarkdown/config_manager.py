"""Configuration manager for jarkdown field selection."""

import logging
import sys
from pathlib import Path

if sys.version_info >= (3, 11):
    import tomllib
else:
    try:
        import tomli as tomllib
    except ImportError:
        tomllib = None


class ConfigManager:
    """Manages field selection configuration from TOML file and CLI args."""

    CONFIG_FILENAME = ".jarkdown.toml"

    def __init__(self, config_dir=None):
        """Initialize the config manager.

        Args:
            config_dir: Directory to search for config file.
                        Defaults to current working directory.
        """
        self.logger = logging.getLogger(__name__)
        self._config_dir = Path(config_dir) if config_dir else Path.cwd()
        self._config = None  # Lazy-loaded

    @property
    def config_path(self):
        """Path to the config file."""
        return self._config_dir / self.CONFIG_FILENAME

    def _load_config(self):
        """Load configuration from TOML file.

        Returns:
            dict: Parsed config dict, or empty dict if file not found.
        """
        if self._config is not None:
            return self._config

        config_path = self.config_path
        if not config_path.exists():
            self._config = {}
            return self._config

        if tomllib is None:
            self.logger.warning(
                "TOML parsing unavailable (install tomli for Python < 3.11). "
                "Config file ignored."
            )
            self._config = {}
            return self._config

        try:
            with open(config_path, "rb") as f:
                self._config = tomllib.load(f)
            self.logger.debug(f"Loaded config from {config_path}")
        except Exception as e:
            self.logger.warning(f"Error reading config file {config_path}: {e}")
            self._config = {}

        return self._config

    def get_field_filter(self, cli_include=None, cli_exclude=None):
        """Get resolved field include/exclude sets.

        CLI args override config file settings. If CLI args are provided,
        config file settings for the same key are ignored entirely.

        Args:
            cli_include: Comma-separated include field names from CLI, or None.
            cli_exclude: Comma-separated exclude field names from CLI, or None.

        Returns:
            dict: {"include": set|None, "exclude": set}
                  include=None means "include all" (default behavior).
                  include=set means "only include these fields".
                  exclude=set of field names to exclude (always a set, may be empty).
        """
        config = self._load_config()
        fields_config = config.get("fields", {})

        # Determine include list
        if cli_include is not None:
            include = {name.strip() for name in cli_include.split(",") if name.strip()}
        elif fields_config.get("include"):
            include = set(fields_config["include"])
        else:
            include = None  # None means "include all"

        # Determine exclude list
        if cli_exclude is not None:
            exclude = {name.strip() for name in cli_exclude.split(",") if name.strip()}
        elif fields_config.get("exclude"):
            exclude = set(fields_config["exclude"])
        else:
            exclude = set()

        return {"include": include, "exclude": exclude}

    @staticmethod
    def should_include_field(field_name, field_filter=None):
        """Check if a field should be included in output.

        Args:
            field_name: Display name of the field.
            field_filter: Pre-computed filter from get_field_filter().
                          If None, defaults to include all.

        Returns:
            bool: True if the field should be included.
        """
        if field_filter is None:
            return True

        # Check exclude first
        if field_name in field_filter.get("exclude", set()):
            return False

        # If include is None (default), include all
        include_set = field_filter.get("include")
        if include_set is None:
            return True

        # Otherwise, only include if in the include set
        return field_name in include_set
