import json
import os
from io import StringIO
from pathlib import Path
from unittest.mock import patch, MagicMock, AsyncMock
import pytest

from jarkdown.jarkdown import main
from jarkdown.exceptions import AuthenticationError, IssueNotFoundError


@pytest.fixture
def mock_env():
    """Mock environment variables for CLI tests"""
    return {
        "JIRA_DOMAIN": "example.atlassian.net",
        "JIRA_EMAIL": "test@example.com",
        "JIRA_API_TOKEN": "test-token-123",
    }


@pytest.fixture
def issue_with_attachments():
    """Load mock issue data with attachments"""
    with open("tests/data/issue_with_attachments.json") as f:
        return json.load(f)


@pytest.fixture
def issue_no_description():
    """Load mock issue data without description"""
    with open("tests/data/issue_no_description.json") as f:
        return json.load(f)


@pytest.fixture
def issue_no_attachments():
    """Load mock issue data without attachments"""
    with open("tests/data/issue_no_attachments.json") as f:
        return json.load(f)


@pytest.fixture
def issue_with_comments():
    """Load mock issue data with comments"""
    with open("tests/data/issue_with_comments.json") as f:
        return json.load(f)


@pytest.fixture
def issue_with_adf_media():
    """Load mock issue whose comments contain ADF media attachments"""
    with open("tests/data/issue_with_adf_media.json") as f:
        return json.load(f)


def _make_client_mock(issue_data, domain="example.atlassian.net"):
    """Create mock class and instance for async JiraApiClient context manager.

    Returns:
        tuple: (mock_class, mock_instance) where mock_class replaces JiraApiClient
    """
    mock_client = AsyncMock()
    mock_client.base_url = f"https://{domain}"
    mock_client.domain = domain
    mock_client.fetch_issue = AsyncMock(return_value=issue_data)
    mock_client.fetch_fields = AsyncMock(return_value=[])

    mock_class = MagicMock()
    mock_class.return_value.__aenter__ = AsyncMock(return_value=mock_client)
    mock_class.return_value.__aexit__ = AsyncMock(return_value=False)
    return mock_class, mock_client


def _fake_download_all(attachments, out_dir):
    """Side effect for AttachmentHandler.download_all_attachments.

    Creates dummy files on disk so tests checking file existence pass.
    """
    results = []
    for att in attachments:
        fname = att["filename"]
        fpath = Path(out_dir) / fname
        fpath.write_bytes(b"fake_content")
        results.append({
            "attachment_id": att.get("id"),
            "filename": fname,
            "original_filename": fname,
            "mime_type": att.get("mimeType", ""),
            "path": fpath,
        })
    return results


class TestCLI:
    """End-to-end tests for the CLI interface"""

    def test_successful_download_with_attachments(
        self, mock_env, issue_with_attachments, tmp_path
    ):
        """Verify successful download creates correct files"""
        mock_jira_class, _ = _make_client_mock(issue_with_attachments)

        with patch("jarkdown.jarkdown.JiraApiClient", mock_jira_class):
            with patch("jarkdown.jarkdown.AttachmentHandler") as mock_ah_class:
                mock_ah_class.return_value.download_all_attachments.side_effect = (
                    _fake_download_all
                )
                with patch("jarkdown.field_cache.FieldMetadataCache") as mock_fmc:
                    mock_fmc.return_value.is_stale.return_value = False
                    mock_fmc.return_value.load.return_value = []
                    mock_fmc.return_value.get_field_name.side_effect = lambda x: x
                    mock_fmc.return_value.get_field_schema.return_value = {}
                    with patch.dict(os.environ, mock_env):
                        original_cwd = os.getcwd()
                        os.chdir(tmp_path)

                        with open(".env", "w") as f:
                            f.write("")

                        try:
                            with patch("sys.argv", ["jarkdown", "export", "TEST-123"]):
                                main()

                            assert os.path.exists("TEST-123")
                            assert os.path.exists("TEST-123/TEST-123.md")
                            assert os.path.exists("TEST-123/screenshot.png")
                            assert os.path.exists("TEST-123/design_document.pdf")
                            assert os.path.exists("TEST-123/diagram.jpg")
                        finally:
                            os.chdir(original_cwd)

    def test_markdown_content_correct(
        self, mock_env, issue_with_attachments, tmp_path
    ):
        """Verify markdown content is correct"""
        mock_jira_class, _ = _make_client_mock(issue_with_attachments)

        with patch("jarkdown.jarkdown.JiraApiClient", mock_jira_class):
            with patch("jarkdown.jarkdown.AttachmentHandler") as mock_ah_class:
                mock_ah_class.return_value.download_all_attachments.side_effect = (
                    _fake_download_all
                )
                with patch("jarkdown.field_cache.FieldMetadataCache") as mock_fmc:
                    mock_fmc.return_value.is_stale.return_value = False
                    mock_fmc.return_value.load.return_value = []
                    mock_fmc.return_value.get_field_name.side_effect = lambda x: x
                    mock_fmc.return_value.get_field_schema.return_value = {}
                    with patch.dict(os.environ, mock_env):
                        original_cwd = os.getcwd()
                        os.chdir(tmp_path)

                        with open(".env", "w") as f:
                            f.write("")

                        try:
                            with patch("sys.argv", ["jarkdown", "export", "TEST-123"]):
                                main()

                            with open("TEST-123/TEST-123.md", "r") as f:
                                content = f.read()

                            assert content.startswith("---\n")
                            assert "key: TEST-123" in content
                            assert "type: Task" in content
                            assert "status: To Do" in content
                            assert (
                                "# [TEST-123](https://example.atlassian.net/browse/TEST-123): Test Issue with Attachments"
                                in content
                            )
                            assert "## Description" in content
                            assert "## Attachments" in content
                        finally:
                            os.chdir(original_cwd)

    def test_custom_output_directory(
        self, mock_env, issue_no_attachments, tmp_path
    ):
        """Verify --output flag works correctly"""
        mock_jira_class, _ = _make_client_mock(issue_no_attachments)

        with patch("jarkdown.jarkdown.JiraApiClient", mock_jira_class):
            with patch("jarkdown.jarkdown.AttachmentHandler") as mock_ah_class:
                mock_ah_class.return_value.download_all_attachments.return_value = []
                with patch("jarkdown.field_cache.FieldMetadataCache") as mock_fmc:
                    mock_fmc.return_value.is_stale.return_value = False
                    mock_fmc.return_value.load.return_value = []
                    mock_fmc.return_value.get_field_name.side_effect = lambda x: x
                    mock_fmc.return_value.get_field_schema.return_value = {}
                    with patch.dict(os.environ, mock_env):
                        original_cwd = os.getcwd()
                        os.chdir(tmp_path)

                        with open(".env", "w") as f:
                            f.write("")

                        try:
                            custom_output = tmp_path / "custom_output"
                            with patch(
                                "sys.argv",
                                ["jarkdown", "export", "TEST-789", "--output", str(custom_output)],
                            ):
                                main()

                            assert os.path.exists(custom_output / "TEST-789")
                            assert os.path.exists(custom_output / "TEST-789" / "TEST-789.md")
                        finally:
                            os.chdir(original_cwd)

    def test_missing_environment_variables(self, tmp_path):
        """Verify error when environment variables are missing"""
        clean_env = {k: v for k, v in os.environ.items() if not k.startswith("JIRA_")}

        with patch.dict(os.environ, clean_env, clear=True):
            with patch("jarkdown.jarkdown.load_dotenv"):
                original_cwd = os.getcwd()
                os.chdir(tmp_path)

                with open(".env", "w") as f:
                    f.write("")

                try:
                    with patch("sys.argv", ["jarkdown", "export", "TEST-123"]):
                        with patch("sys.stdout", new=StringIO()) as mock_stdout:
                            with pytest.raises(SystemExit) as exc_info:
                                main()

                            assert exc_info.value.code != 0
                            stdout_output = mock_stdout.getvalue()
                            assert "Missing required environment variables" in stdout_output
                finally:
                    os.chdir(original_cwd)

    def test_invalid_issue_key_404(self, mock_env, tmp_path):
        """Verify 404 error handling"""
        mock_client = AsyncMock()
        mock_client.base_url = "https://example.atlassian.net"
        mock_client.domain = "example.atlassian.net"
        mock_client.fetch_issue = AsyncMock(
            side_effect=IssueNotFoundError(
                "Issue INVALID-999 not found or not accessible.", status_code=404
            )
        )

        mock_jira_class = MagicMock()
        mock_jira_class.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        mock_jira_class.return_value.__aexit__ = AsyncMock(return_value=False)

        with patch("jarkdown.jarkdown.JiraApiClient", mock_jira_class):
            with patch.dict(os.environ, mock_env):
                original_cwd = os.getcwd()
                os.chdir(tmp_path)

                with open(".env", "w") as f:
                    f.write("")

                try:
                    with patch("sys.argv", ["jarkdown", "export", "INVALID-999"]):
                        with patch("sys.stderr", new=StringIO()) as mock_stderr:
                            with pytest.raises(SystemExit) as exc_info:
                                main()

                            assert exc_info.value.code != 0
                            stderr_output = mock_stderr.getvalue()
                            assert (
                                "not found" in stderr_output.lower()
                                or "404" in stderr_output
                            )
                finally:
                    os.chdir(original_cwd)

    def test_invalid_credentials_401(self):
        """Verify 401 authentication error"""
        mock_client = AsyncMock()
        mock_client.base_url = "https://example.atlassian.net"
        mock_client.domain = "example.atlassian.net"
        mock_client.fetch_issue = AsyncMock(
            side_effect=AuthenticationError(
                "Authentication failed. Please check your API token and email.",
                status_code=401,
            )
        )

        mock_jira_class = MagicMock()
        mock_jira_class.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        mock_jira_class.return_value.__aexit__ = AsyncMock(return_value=False)

        bad_env = {
            "JIRA_DOMAIN": "example.atlassian.net",
            "JIRA_EMAIL": "bad@example.com",
            "JIRA_API_TOKEN": "invalid-token",
        }

        with patch("jarkdown.jarkdown.JiraApiClient", mock_jira_class):
            with patch.dict(os.environ, bad_env):
                with patch("sys.argv", ["jarkdown", "export", "TEST-123"]):
                    with patch("sys.stderr", new=StringIO()) as mock_stderr:
                        with pytest.raises(SystemExit) as exc_info:
                            main()

                        assert exc_info.value.code != 0
                        stderr_output = mock_stderr.getvalue()
                        assert (
                            "authentication" in stderr_output.lower()
                            or "401" in stderr_output
                        )

    def test_verbose_flag(self, mock_env, issue_no_description):
        """Test verbose flag provides additional output"""
        mock_jira_class, _ = _make_client_mock(issue_no_description)

        with patch("jarkdown.jarkdown.JiraApiClient", mock_jira_class):
            with patch("jarkdown.jarkdown.AttachmentHandler") as mock_ah_class:
                mock_ah_class.return_value.download_all_attachments.return_value = []
                with patch("jarkdown.field_cache.FieldMetadataCache") as mock_fmc:
                    mock_fmc.return_value.is_stale.return_value = False
                    mock_fmc.return_value.load.return_value = []
                    mock_fmc.return_value.get_field_name.side_effect = lambda x: x
                    mock_fmc.return_value.get_field_schema.return_value = {}
                    with patch.dict(os.environ, mock_env):
                        with patch(
                            "sys.argv", ["jarkdown", "export", "TEST-456", "--verbose"]
                        ):
                            # Verbose flag succeeds without raising SystemExit
                            main()

    def test_successful_download_with_comments(
        self, mock_env, issue_with_comments, tmp_path
    ):
        """Test successful download with comments section"""
        mock_jira_class, _ = _make_client_mock(issue_with_comments)

        with patch("jarkdown.jarkdown.JiraApiClient", mock_jira_class):
            with patch("jarkdown.jarkdown.AttachmentHandler") as mock_ah_class:
                mock_ah_class.return_value.download_all_attachments.side_effect = (
                    _fake_download_all
                )
                with patch("jarkdown.field_cache.FieldMetadataCache") as mock_fmc:
                    mock_fmc.return_value.is_stale.return_value = False
                    mock_fmc.return_value.load.return_value = []
                    mock_fmc.return_value.get_field_name.side_effect = lambda x: x
                    mock_fmc.return_value.get_field_schema.return_value = {}
                    with patch.dict(os.environ, mock_env):
                        original_cwd = os.getcwd()
                        os.chdir(tmp_path)

                        with open(".env", "w") as f:
                            f.write("")

                        try:
                            with patch(
                                "sys.argv",
                                ["jarkdown", "export", "TEST-456", "--output", str(tmp_path)],
                            ):
                                main()

                            output_dir = tmp_path / "TEST-456"
                            md_file = output_dir / "TEST-456.md"

                            assert md_file.exists()
                            content = md_file.read_text()

                            assert "## Comments" in content
                            assert "**John Doe** - _2025-08-16 10:30 AM_" in content
                            assert "This is the first comment" in content
                            assert "**Jane Smith** - _2025-08-16 11:15 AM_" in content
                            assert "**Alice Developer** - _2025-08-16 02:45 PM_" in content
                            assert "---" in content
                            assert "![new_mockup.png](new_mockup.png)" in content
                            assert "/secure/attachment/" not in content.replace(
                                "[TEST-456](https://example.atlassian.net/browse/TEST-456)", ""
                            )
                            assert "/attachment/content/" not in content
                        finally:
                            os.chdir(original_cwd)

    def test_adf_comment_media_embeds_attachments(
        self, mock_env, issue_with_adf_media, tmp_path
    ):
        """ADF-only comments should embed downloaded attachments instead of placeholder text."""
        mock_jira_class, _ = _make_client_mock(issue_with_adf_media)

        with patch("jarkdown.jarkdown.JiraApiClient", mock_jira_class):
            with patch("jarkdown.jarkdown.AttachmentHandler") as mock_ah_class:
                mock_ah_class.return_value.download_all_attachments.side_effect = (
                    _fake_download_all
                )
                with patch("jarkdown.field_cache.FieldMetadataCache") as mock_fmc:
                    mock_fmc.return_value.is_stale.return_value = False
                    mock_fmc.return_value.load.return_value = []
                    mock_fmc.return_value.get_field_name.side_effect = lambda x: x
                    mock_fmc.return_value.get_field_schema.return_value = {}
                    with patch.dict(os.environ, mock_env):
                        original_cwd = os.getcwd()
                        os.chdir(tmp_path)

                        with open(".env", "w") as f:
                            f.write("")

                        try:
                            with patch(
                                "sys.argv",
                                ["jarkdown", "export", "ADF-100", "--output", str(tmp_path)],
                            ):
                                main()

                            output_dir = tmp_path / "ADF-100"
                            md_file = output_dir / "ADF-100.md"
                            assert md_file.exists()
                            content = md_file.read_text()

                            assert "![evidence.png](evidence.png)" in content
                            assert "![attachment](attachment)" not in content
                        finally:
                            os.chdir(original_cwd)

    def test_backward_compat_bare_issue_key(
        self, mock_env, issue_no_attachments, tmp_path
    ):
        """jarkdown TEST-555 (no subcommand) works via backward-compat shim."""
        mock_jira_class, _ = _make_client_mock(issue_no_attachments)

        with patch("jarkdown.jarkdown.JiraApiClient", mock_jira_class):
            with patch("jarkdown.jarkdown.AttachmentHandler") as mock_ah_class:
                mock_ah_class.return_value.download_all_attachments.return_value = []
                with patch("jarkdown.field_cache.FieldMetadataCache") as mock_fmc:
                    mock_fmc.return_value.is_stale.return_value = False
                    mock_fmc.return_value.load.return_value = []
                    mock_fmc.return_value.get_field_name.side_effect = lambda x: x
                    mock_fmc.return_value.get_field_schema.return_value = {}
                    with patch.dict(os.environ, mock_env):
                        original_cwd = os.getcwd()
                        os.chdir(tmp_path)

                        with open(".env", "w") as f:
                            f.write("")

                        try:
                            # No "export" subcommand — shim injects it automatically
                            with patch("sys.argv", ["jarkdown", "TEST-555"]):
                                main()

                            assert os.path.exists("TEST-555")
                            assert os.path.exists("TEST-555/TEST-555.md")
                        finally:
                            os.chdir(original_cwd)

    def test_bulk_subcommand_routes_to_handler(self):
        """bulk subcommand routes to _handle_bulk (real implementation)."""
        with patch("jarkdown.jarkdown._handle_bulk") as mock_bulk:
            with patch("sys.argv", ["jarkdown", "bulk", "PROJ-1", "PROJ-2"]):
                main()
            mock_bulk.assert_called_once()

    def test_query_subcommand_routes_to_handler(self):
        """query subcommand routes to _handle_query (real implementation)."""
        with patch("jarkdown.jarkdown._handle_query") as mock_query:
            with patch("sys.argv", ["jarkdown", "query", "project = FOO"]):
                main()
            mock_query.assert_called_once()

    def test_setup_subcommand(self):
        """setup subcommand invokes setup_configuration and exits 0."""
        with patch("jarkdown.jarkdown.setup_configuration") as mock_setup:
            with patch("sys.argv", ["jarkdown", "setup"]):
                with pytest.raises(SystemExit) as exc_info:
                    main()
                mock_setup.assert_called_once()
                assert exc_info.value.code == 0

    def test_no_command_exits_one(self):
        """Running with no args shows help and exits 1."""
        with patch("sys.argv", ["jarkdown"]):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 1
