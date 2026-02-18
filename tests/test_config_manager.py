"""Tests for jarkdown ConfigManager."""

import logging

import pytest

from jarkdown.config_manager import ConfigManager


@pytest.fixture
def config_dir(tmp_path):
    """Temporary directory for config files."""
    return tmp_path


class TestConfigLoading:
    """Tests for config file loading and TOML parsing."""

    def test_load_valid_config(self, config_dir):
        """Valid .jarkdown.toml is parsed correctly."""
        config_file = config_dir / ".jarkdown.toml"
        config_file.write_text('[fields]\ninclude = ["Story Points", "Sprint"]\n')

        manager = ConfigManager(config_dir=config_dir)
        result = manager._load_config()

        assert result == {"fields": {"include": ["Story Points", "Sprint"]}}

    def test_no_config_file(self, config_dir):
        """Missing config file returns empty dict without error."""
        manager = ConfigManager(config_dir=config_dir)
        result = manager._load_config()

        assert result == {}

    def test_invalid_toml(self, config_dir, caplog):
        """Invalid TOML content returns empty dict and logs warning."""
        config_file = config_dir / ".jarkdown.toml"
        config_file.write_bytes(b"not valid [[[ toml")

        manager = ConfigManager(config_dir=config_dir)
        with caplog.at_level(logging.WARNING):
            result = manager._load_config()

        assert result == {}
        assert "Error reading config file" in caplog.text

    def test_empty_config(self, config_dir):
        """Empty config file returns empty dict."""
        config_file = config_dir / ".jarkdown.toml"
        config_file.write_text("")

        manager = ConfigManager(config_dir=config_dir)
        result = manager._load_config()

        assert result == {}

    def test_config_without_fields_section(self, config_dir):
        """Config with no [fields] section returns default filter."""
        config_file = config_dir / ".jarkdown.toml"
        config_file.write_text('[other]\nkey = "value"\n')

        manager = ConfigManager(config_dir=config_dir)
        result = manager.get_field_filter()

        assert result == {"include": None, "exclude": set()}
