import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch, Mock
import pytest
import requests

# Add parent directory to path to import jira_download
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture
def mock_env():
    """Mock environment variables for CLI tests"""
    return {
        'JIRA_DOMAIN': 'example.atlassian.net',
        'JIRA_EMAIL': 'test@example.com',
        'JIRA_API_TOKEN': 'test-token-123'
    }


@pytest.fixture
def issue_with_attachments():
    """Load mock issue data with attachments"""
    with open('tests/data/issue_with_attachments.json') as f:
        return json.load(f)


@pytest.fixture
def issue_no_description():
    """Load mock issue data without description"""
    with open('tests/data/issue_no_description.json') as f:
        return json.load(f)


@pytest.fixture
def issue_no_attachments():
    """Load mock issue data without attachments"""
    with open('tests/data/issue_no_attachments.json') as f:
        return json.load(f)


class TestCLI:
    """End-to-end tests for the CLI interface"""
    
    def test_successful_download_with_attachments(self, mock_env, issue_with_attachments, mocker, tmp_path):
        """Test Case 5.8.1: Verify successful download creates correct files"""
        # Mock the requests to return our test data
        mock_session = Mock()
        mock_get = Mock()
        mock_response = Mock()
        mock_response.raise_for_status = Mock()
        mock_response.json.return_value = issue_with_attachments
        mock_response.iter_content = Mock(return_value=[b'fake_content'])
        mock_get.return_value = mock_response
        mock_session.get = mock_get
        
        with patch('requests.Session', return_value=mock_session):
            with patch.dict(os.environ, mock_env):
                # Change to temp directory
                original_cwd = os.getcwd()
                os.chdir(tmp_path)
                
                try:
                    # Run the script
                    result = subprocess.run(
                        [sys.executable, os.path.join(original_cwd, 'jira_download.py'), 'TEST-123'],
                        capture_output=True,
                        text=True,
                        env={**os.environ, **mock_env}
                    )
                    
                    # Check that the command succeeded
                    assert result.returncode == 0
                    
                    # Check that directory was created
                    assert os.path.exists('TEST-123')
                    
                    # Check that markdown file was created
                    assert os.path.exists('TEST-123/TEST-123.md')
                    
                    # Check that attachments were downloaded
                    assert os.path.exists('TEST-123/screenshot.png')
                    assert os.path.exists('TEST-123/design_document.pdf')
                    assert os.path.exists('TEST-123/diagram.jpg')
                    
                finally:
                    os.chdir(original_cwd)
    
    def test_markdown_content_correct(self, mock_env, issue_with_attachments, mocker, tmp_path):
        """Test Case 5.8.2: Verify markdown content is correct"""
        mock_session = Mock()
        mock_get = Mock()
        mock_response = Mock()
        mock_response.raise_for_status = Mock()
        mock_response.json.return_value = issue_with_attachments
        mock_response.iter_content = Mock(return_value=[b'fake_content'])
        mock_get.return_value = mock_response
        mock_session.get = mock_get
        
        with patch('requests.Session', return_value=mock_session):
            with patch.dict(os.environ, mock_env):
                original_cwd = os.getcwd()
                os.chdir(tmp_path)
                
                try:
                    result = subprocess.run(
                        [sys.executable, os.path.join(original_cwd, 'jira_download.py'), 'TEST-123'],
                        capture_output=True,
                        text=True,
                        env={**os.environ, **mock_env}
                    )
                    
                    assert result.returncode == 0
                    
                    # Read and verify markdown content
                    with open('TEST-123/TEST-123.md', 'r') as f:
                        content = f.read()
                    
                    assert '# TEST-123: Test Issue with Attachments' in content
                    assert '**Type:** Task' in content
                    assert '**Status:** To Do' in content
                    assert '## Description' in content
                    assert '## Attachments' in content
                    
                finally:
                    os.chdir(original_cwd)
    
    def test_custom_output_directory(self, mock_env, issue_no_attachments, mocker, tmp_path):
        """Test Case 5.8.3: Verify --output flag works correctly"""
        mock_session = Mock()
        mock_get = Mock()
        mock_response = Mock()
        mock_response.raise_for_status = Mock()
        mock_response.json.return_value = issue_no_attachments
        mock_get.return_value = mock_response
        mock_session.get = mock_get
        
        with patch('requests.Session', return_value=mock_session):
            with patch.dict(os.environ, mock_env):
                custom_output = tmp_path / 'custom_output'
                
                result = subprocess.run(
                    [sys.executable, 'jira_download.py', 'TEST-789', '--output', str(custom_output)],
                    capture_output=True,
                    text=True,
                    env={**os.environ, **mock_env}
                )
                
                assert result.returncode == 0
                
                # Check that files were created in custom directory
                assert os.path.exists(custom_output / 'TEST-789')
                assert os.path.exists(custom_output / 'TEST-789' / 'TEST-789.md')
    
    def test_missing_environment_variables(self, tmp_path):
        """Test Case 5.8.4: Verify error when environment variables are missing"""
        # Run without environment variables
        result = subprocess.run(
            [sys.executable, 'jira_download.py', 'TEST-123'],
            capture_output=True,
            text=True,
            env={k: v for k, v in os.environ.items() if not k.startswith('JIRA_')}
        )
        
        assert result.returncode != 0
        assert 'Error' in result.stderr or 'Missing' in result.stderr
    
    def test_invalid_issue_key_404(self, mock_env, mocker, tmp_path):
        """Test Case 5.8.5: Verify 404 error handling"""
        mock_session = Mock()
        mock_get = Mock()
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError()
        mock_get.return_value = mock_response
        mock_session.get = mock_get
        
        with patch('requests.Session', return_value=mock_session):
            with patch.dict(os.environ, mock_env):
                result = subprocess.run(
                    [sys.executable, 'jira_download.py', 'INVALID-999'],
                    capture_output=True,
                    text=True,
                    env={**os.environ, **mock_env}
                )
                
                assert result.returncode != 0
                assert 'not found' in result.stderr.lower() or '404' in result.stderr
    
    def test_invalid_credentials_401(self, mocker, tmp_path):
        """Test Case 5.8.6: Verify 401 authentication error"""
        mock_session = Mock()
        mock_get = Mock()
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError()
        mock_get.return_value = mock_response
        mock_session.get = mock_get
        
        bad_env = {
            'JIRA_DOMAIN': 'example.atlassian.net',
            'JIRA_EMAIL': 'bad@example.com',
            'JIRA_API_TOKEN': 'invalid-token'
        }
        
        with patch('requests.Session', return_value=mock_session):
            with patch.dict(os.environ, bad_env):
                result = subprocess.run(
                    [sys.executable, 'jira_download.py', 'TEST-123'],
                    capture_output=True,
                    text=True,
                    env={**os.environ, **bad_env}
                )
                
                assert result.returncode != 0
                assert 'authentication' in result.stderr.lower() or '401' in result.stderr
    
    def test_verbose_flag(self, mock_env, issue_no_description, mocker):
        """Test verbose flag provides additional output"""
        mock_session = Mock()
        mock_get = Mock()
        mock_response = Mock()
        mock_response.raise_for_status = Mock()
        mock_response.json.return_value = issue_no_description
        mock_get.return_value = mock_response
        mock_session.get = mock_get
        
        with patch('requests.Session', return_value=mock_session):
            with patch.dict(os.environ, mock_env):
                result = subprocess.run(
                    [sys.executable, 'jira_download.py', 'TEST-456', '--verbose'],
                    capture_output=True,
                    text=True,
                    env={**os.environ, **mock_env}
                )
                
                assert result.returncode == 0
                # Verbose output should contain more information
                assert 'Fetching' in result.stderr or 'Processing' in result.stderr or len(result.stderr) > 0