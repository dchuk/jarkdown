import json
import os
from unittest.mock import patch, Mock
from io import StringIO
import pytest
import requests

from jarkdown.jarkdown import main


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


class TestCLI:
    """End-to-end tests for the CLI interface"""

    def test_successful_download_with_attachments(
        self, mock_env, issue_with_attachments, mocker, tmp_path
    ):
        """Verify successful download creates correct files"""
        # Mock the requests to return our test data
        mock_session = Mock()
        mock_get = Mock()
        mock_response = Mock()
        mock_response.raise_for_status = Mock()
        mock_response.json.return_value = issue_with_attachments
        mock_response.iter_content = Mock(return_value=[b"fake_content"])
        mock_get.return_value = mock_response
        mock_session.get = mock_get

        with patch("requests.Session", return_value=mock_session):
            with patch.dict(os.environ, mock_env):
                # Change to temp directory
                original_cwd = os.getcwd()
                os.chdir(tmp_path)

                try:
                    # Mock sys.argv for in-process execution
                    with patch("sys.argv", ["jarkdown", "TEST-123"]):
                        # Call main directly - successful execution doesn't raise SystemExit
                        main()

                    # Check that directory was created
                    assert os.path.exists("TEST-123")

                    # Check that markdown file was created
                    assert os.path.exists("TEST-123/TEST-123.md")

                    # Check that attachments were downloaded
                    assert os.path.exists("TEST-123/screenshot.png")
                    assert os.path.exists("TEST-123/design_document.pdf")
                    assert os.path.exists("TEST-123/diagram.jpg")

                finally:
                    os.chdir(original_cwd)

    def test_markdown_content_correct(
        self, mock_env, issue_with_attachments, mocker, tmp_path
    ):
        """Verify markdown content is correct"""
        mock_session = Mock()
        mock_get = Mock()
        mock_response = Mock()
        mock_response.raise_for_status = Mock()
        mock_response.json.return_value = issue_with_attachments
        mock_response.iter_content = Mock(return_value=[b"fake_content"])
        mock_get.return_value = mock_response
        mock_session.get = mock_get

        with patch("requests.Session", return_value=mock_session):
            with patch.dict(os.environ, mock_env):
                original_cwd = os.getcwd()
                os.chdir(tmp_path)

                try:
                    with patch("sys.argv", ["jarkdown", "TEST-123"]):
                        # Call main directly - successful execution doesn't raise SystemExit
                        main()

                    # Read and verify markdown content
                    with open("TEST-123/TEST-123.md", "r") as f:
                        content = f.read()

                    assert (
                        "# [TEST-123](https://example.atlassian.net/browse/TEST-123): Test Issue with Attachments"
                        in content
                    )
                    assert "**Type:** Task" in content
                    assert "**Status:** To Do" in content
                    assert "## Description" in content
                    assert "## Attachments" in content

                finally:
                    os.chdir(original_cwd)

    def test_custom_output_directory(
        self, mock_env, issue_no_attachments, mocker, tmp_path
    ):
        """Verify --output flag works correctly"""
        mock_session = Mock()
        mock_get = Mock()
        mock_response = Mock()
        mock_response.raise_for_status = Mock()
        mock_response.json.return_value = issue_no_attachments
        mock_get.return_value = mock_response
        mock_session.get = mock_get

        with patch("requests.Session", return_value=mock_session):
            with patch.dict(os.environ, mock_env):
                custom_output = tmp_path / "custom_output"

                with patch(
                    "sys.argv",
                    ["jarkdown", "TEST-789", "--output", str(custom_output)],
                ):
                    # Call main directly - successful execution doesn't raise SystemExit
                    main()

                # Check that files were created in custom directory
                assert os.path.exists(custom_output / "TEST-789")
                assert os.path.exists(custom_output / "TEST-789" / "TEST-789.md")

    def test_missing_environment_variables(self, tmp_path):
        """Verify error when environment variables are missing"""
        # Clear Jira environment variables and patch load_dotenv to do nothing
        clean_env = {k: v for k, v in os.environ.items() if not k.startswith("JIRA_")}

        with patch.dict(os.environ, clean_env, clear=True):
            with patch(
                "jarkdown.jarkdown.load_dotenv"
            ):  # Mock load_dotenv to prevent loading any .env files
                with patch("sys.argv", ["jarkdown", "TEST-123"]):
                    # Capture stderr
                    with patch("sys.stderr", new=StringIO()) as mock_stderr:
                        with pytest.raises(SystemExit) as exc_info:
                            main()

                        assert exc_info.value.code != 0
                        stderr_output = mock_stderr.getvalue()
                        assert (
                            "Configuration error" in stderr_output
                            or "Missing" in stderr_output
                        )

    def test_invalid_issue_key_404(self, mock_env, mocker, tmp_path):
        """Verify 404 error handling"""
        mock_session = Mock()
        mock_get = Mock()
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError()
        mock_get.return_value = mock_response
        mock_session.get = mock_get

        with patch("requests.Session", return_value=mock_session):
            with patch.dict(os.environ, mock_env):
                with patch("sys.argv", ["jarkdown", "INVALID-999"]):
                    with patch("sys.stderr", new=StringIO()) as mock_stderr:
                        with pytest.raises(SystemExit) as exc_info:
                            main()

                        assert exc_info.value.code != 0
                        stderr_output = mock_stderr.getvalue()
                        assert (
                            "not found" in stderr_output.lower()
                            or "404" in stderr_output
                        )

    def test_invalid_credentials_401(self, mocker, tmp_path):
        """Verify 401 authentication error"""
        mock_session = Mock()
        mock_get = Mock()
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError()
        mock_get.return_value = mock_response
        mock_session.get = mock_get

        bad_env = {
            "JIRA_DOMAIN": "example.atlassian.net",
            "JIRA_EMAIL": "bad@example.com",
            "JIRA_API_TOKEN": "invalid-token",
        }

        with patch("requests.Session", return_value=mock_session):
            with patch.dict(os.environ, bad_env):
                with patch("sys.argv", ["jarkdown", "TEST-123"]):
                    with patch("sys.stderr", new=StringIO()) as mock_stderr:
                        with pytest.raises(SystemExit) as exc_info:
                            main()

                        assert exc_info.value.code != 0
                        stderr_output = mock_stderr.getvalue()
                        assert (
                            "authentication" in stderr_output.lower()
                            or "401" in stderr_output
                        )

    def test_verbose_flag(self, mock_env, issue_no_description, mocker):
        """Test verbose flag provides additional output"""
        mock_session = Mock()
        mock_get = Mock()
        mock_response = Mock()
        mock_response.raise_for_status = Mock()
        mock_response.json.return_value = issue_no_description
        mock_get.return_value = mock_response
        mock_session.get = mock_get

        with patch("requests.Session", return_value=mock_session):
            with patch.dict(os.environ, mock_env):
                with patch("sys.argv", ["jarkdown", "TEST-456", "--verbose"]):
                    # Since verbose affects logging level, we can't easily test the output
                    # Just verify the command succeeds without raising SystemExit
                    main()

    def test_successful_download_with_comments(
        self, mock_env, issue_with_comments, tmp_path, mocker
    ):
        """Test successful download with comments section"""
        mock_session = Mock()
        mock_get = Mock()
        mock_response = Mock()
        mock_response.raise_for_status = Mock()
        mock_response.json.return_value = issue_with_comments
        mock_get.return_value = mock_response
        mock_session.get = mock_get

        # Mock attachment downloads
        attachment_response = Mock()
        attachment_response.iter_content = Mock(return_value=[b"test content"])
        mock_session.get = Mock(
            side_effect=[mock_response, attachment_response, attachment_response]
        )

        with patch("requests.Session", return_value=mock_session):
            with patch.dict(os.environ, mock_env):
                with patch(
                    "sys.argv", ["jarkdown", "TEST-456", "--output", str(tmp_path)]
                ):
                    main()

                    # Check markdown file was created with comments
                    output_dir = tmp_path / "TEST-456"
                    md_file = output_dir / "TEST-456.md"

                    assert md_file.exists()
                    content = md_file.read_text()

                    # Verify comments section exists
                    assert "## Comments" in content
                    assert "**John Doe** - _2025-08-16 10:30 AM_" in content
                    assert "This is the first comment" in content
                    assert "**Jane Smith** - _2025-08-16 11:15 AM_" in content
                    assert "**Alice Developer** - _2025-08-16 02:45 PM_" in content

                    # Check that comments are separated by horizontal rules
                    assert "---" in content

                    # Verify attachment links in comments are replaced
                    assert "![new_mockup.png](new_mockup.png)" in content
                    # Check that no secure attachment URLs remain
                    assert "/secure/attachment/" not in content.replace(
                        "[TEST-456](https://example.atlassian.net/browse/TEST-456)", ""
                    )
                    assert "/attachment/content/" not in content
