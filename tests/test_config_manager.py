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


class TestFieldFilter:
    """Tests for field filter resolution and CLI/config precedence."""

    def test_default_filter(self, config_dir):
        """No config file and no CLI args returns default filter."""
        manager = ConfigManager(config_dir=config_dir)
        result = manager.get_field_filter()

        assert result == {"include": None, "exclude": set()}

    def test_config_include_only(self, config_dir):
        """Config with include list populates include set."""
        config_file = config_dir / ".jarkdown.toml"
        config_file.write_text('[fields]\ninclude = ["Story Points", "Sprint"]\n')

        manager = ConfigManager(config_dir=config_dir)
        result = manager.get_field_filter()

        assert result["include"] == {"Story Points", "Sprint"}
        assert result["exclude"] == set()

    def test_config_exclude_only(self, config_dir):
        """Config with exclude list populates exclude set."""
        config_file = config_dir / ".jarkdown.toml"
        config_file.write_text('[fields]\nexclude = ["Internal Notes"]\n')

        manager = ConfigManager(config_dir=config_dir)
        result = manager.get_field_filter()

        assert result["include"] is None
        assert result["exclude"] == {"Internal Notes"}

    def test_config_both_include_exclude(self, config_dir):
        """Config with both include and exclude populates both sets."""
        config_file = config_dir / ".jarkdown.toml"
        config_file.write_text(
            '[fields]\n'
            'include = ["Story Points", "Sprint"]\n'
            'exclude = ["Internal Notes"]\n'
        )

        manager = ConfigManager(config_dir=config_dir)
        result = manager.get_field_filter()

        assert result["include"] == {"Story Points", "Sprint"}
        assert result["exclude"] == {"Internal Notes"}

    def test_cli_include_overrides_config(self, config_dir):
        """CLI include arg completely overrides config include."""
        config_file = config_dir / ".jarkdown.toml"
        config_file.write_text('[fields]\ninclude = ["A", "B"]\n')

        manager = ConfigManager(config_dir=config_dir)
        result = manager.get_field_filter(cli_include="C,D")

        assert result["include"] == {"C", "D"}

    def test_cli_exclude_overrides_config(self, config_dir):
        """CLI exclude arg completely overrides config exclude."""
        config_file = config_dir / ".jarkdown.toml"
        config_file.write_text('[fields]\nexclude = ["A"]\n')

        manager = ConfigManager(config_dir=config_dir)
        result = manager.get_field_filter(cli_exclude="B")

        assert result["exclude"] == {"B"}

    def test_cli_empty_string(self, config_dir):
        """CLI empty string for include yields empty set (not None)."""
        config_file = config_dir / ".jarkdown.toml"
        config_file.write_text('[fields]\ninclude = ["A", "B"]\n')

        manager = ConfigManager(config_dir=config_dir)
        result = manager.get_field_filter(cli_include="")

        assert result["include"] == set()

    def test_cli_comma_separated_whitespace(self, config_dir):
        """CLI comma-separated values have whitespace stripped."""
        manager = ConfigManager(config_dir=config_dir)
        result = manager.get_field_filter(
            cli_include="Story Points, Sprint, Epic Link"
        )

        assert result["include"] == {"Story Points", "Sprint", "Epic Link"}


class TestShouldIncludeField:
    """Tests for the should_include_field static method."""

    def test_include_all_default(self):
        """No filter (None) includes all fields."""
        assert ConfigManager.should_include_field("Story Points") is True
        assert ConfigManager.should_include_field("Anything") is True

    def test_include_specific_fields(self):
        """Include set only allows listed fields."""
        field_filter = {"include": {"Story Points"}, "exclude": set()}

        assert ConfigManager.should_include_field("Story Points", field_filter) is True
        assert ConfigManager.should_include_field("Sprint", field_filter) is False

    def test_exclude_specific_field(self):
        """Exclude set blocks listed fields, allows others."""
        field_filter = {"include": None, "exclude": {"Internal Notes"}}

        assert (
            ConfigManager.should_include_field("Internal Notes", field_filter) is False
        )
        assert (
            ConfigManager.should_include_field("Story Points", field_filter) is True
        )

    def test_exclude_takes_precedence_over_include(self):
        """Field in both include and exclude is excluded."""
        field_filter = {"include": {"Story Points"}, "exclude": {"Story Points"}}

        assert (
            ConfigManager.should_include_field("Story Points", field_filter) is False
        )

    def test_empty_include_set(self):
        """Empty include set (not None) excludes all fields."""
        field_filter = {"include": set(), "exclude": set()}

        assert ConfigManager.should_include_field("Story Points", field_filter) is False
        assert ConfigManager.should_include_field("Sprint", field_filter) is False
