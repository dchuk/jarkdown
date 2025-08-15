import json
import os
import sys
from pathlib import Path
from unittest.mock import Mock, patch, mock_open, MagicMock, call
import pytest
import requests

# Add parent directory to path to import jira_download
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from jira_download import JiraDownloader


@pytest.fixture
def mock_env():
    """Mock environment variables"""
    with patch.dict(os.environ, {
        'JIRA_DOMAIN': 'example.atlassian.net',
        'JIRA_EMAIL': 'test@example.com',
        'JIRA_API_TOKEN': 'test-token-123'
    }):
        yield


@pytest.fixture
def downloader():
    """Create a JiraDownloader instance"""
    return JiraDownloader('example.atlassian.net', 'test@example.com', 'test-token-123')


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


class TestJiraDownloaderInit:
    """Test cases for JiraDownloader.__init__"""
    
    def test_init_with_valid_credentials(self):
        """Test Case 5.1.1: Verify correct initialization"""
        downloader = JiraDownloader('example.atlassian.net', 'test@example.com', 'test-token-123')
        
        assert downloader.domain == 'example.atlassian.net'
        assert downloader.email == 'test@example.com'
        assert downloader.api_token == 'test-token-123'
        assert downloader.base_url == 'https://example.atlassian.net'
        assert downloader.api_base == 'https://example.atlassian.net/rest/api/3'
        assert isinstance(downloader.session, requests.Session)
        assert downloader.session.auth == ('test@example.com', 'test-token-123')


class TestFetchIssue:
    """Test cases for fetch_issue method"""
    
    def test_successful_api_call(self, downloader, issue_with_attachments, mocker):
        """Test Case 5.2.1: Verify successful API call returns correct JSON"""
        mock_response = Mock()
        mock_response.raise_for_status = Mock()
        mock_response.json.return_value = issue_with_attachments
        
        mocker.patch.object(downloader.session, 'get', return_value=mock_response)
        
        result = downloader.fetch_issue('TEST-123')
        
        assert result == issue_with_attachments
        downloader.session.get.assert_called_once_with(
            'https://example.atlassian.net/rest/api/3/issue/TEST-123',
            params={
                'fields': 'summary,description,issuetype,status,priority,attachment,assignee,reporter,created,updated',
                'expand': 'renderedFields'
            }
        )
    
    def test_401_authentication_error(self, downloader, mocker):
        """Test Case 5.2.2: Verify 401 error handling"""
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError()
        
        mocker.patch.object(downloader.session, 'get', return_value=mock_response)
        mock_exit = mocker.patch('sys.exit')
        
        downloader.fetch_issue('TEST-123')
        
        mock_exit.assert_called_once_with(1)
    
    def test_404_not_found_error(self, downloader, mocker):
        """Test Case 5.2.3: Verify 404 error handling"""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError()
        
        mocker.patch.object(downloader.session, 'get', return_value=mock_response)
        mock_exit = mocker.patch('sys.exit')
        
        downloader.fetch_issue('TEST-999')
        
        mock_exit.assert_called_once_with(1)
    
    def test_generic_http_error(self, downloader, mocker):
        """Test Case 5.2.4: Verify generic HTTP error handling"""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError()
        
        mocker.patch.object(downloader.session, 'get', return_value=mock_response)
        mock_exit = mocker.patch('sys.exit')
        
        downloader.fetch_issue('TEST-123')
        
        mock_exit.assert_called_once_with(1)
    
    def test_network_error(self, downloader, mocker):
        """Test Case 5.2.5: Verify network error handling"""
        mocker.patch.object(downloader.session, 'get', 
                          side_effect=requests.exceptions.RequestException("Network error"))
        mock_exit = mocker.patch('sys.exit')
        
        downloader.fetch_issue('TEST-123')
        
        mock_exit.assert_called_once_with(1)


class TestDownloadAttachment:
    """Test cases for download_attachment method"""
    
    def test_single_attachment_download(self, downloader, mocker, tmp_path):
        """Test Case 5.3.1: Verify single attachment downloads correctly"""
        attachment = {
            'filename': 'test.png',
            'size': 1024,
            'mimeType': 'image/png',
            'content': 'https://example.atlassian.net/rest/api/3/attachment/content/10001'
        }
        
        mock_response = Mock()
        mock_response.iter_content = Mock(return_value=[b'test_content'])
        mock_response.raise_for_status = Mock()
        
        mocker.patch.object(downloader.session, 'get', return_value=mock_response)
        mock_file = mocker.patch('builtins.open', mock_open())
        
        result = downloader.download_attachment(attachment, tmp_path)
        
        assert result is not None
        assert result['filename'] == 'test.png'
        assert result['original_filename'] == 'test.png'
        assert result['mime_type'] == 'image/png'
        mock_file.assert_called_once()
        mock_file().write.assert_called_once_with(b'test_content')
    
    def test_filename_conflict_resolution(self, downloader, mocker, tmp_path):
        """Test Case 5.3.4: Verify filename conflict resolution"""
        attachment = {
            'filename': 'test.png',
            'size': 1024,
            'mimeType': 'image/png',
            'content': 'https://example.atlassian.net/rest/api/3/attachment/content/10001'
        }
        
        # Create a file that already exists
        existing_file = tmp_path / 'test.png'
        existing_file.write_text('existing')
        
        mock_response = Mock()
        mock_response.iter_content = Mock(return_value=[b'new_content'])
        mock_response.raise_for_status = Mock()
        
        mocker.patch.object(downloader.session, 'get', return_value=mock_response)
        
        result = downloader.download_attachment(attachment, tmp_path)
        
        assert result is not None
        assert result['filename'] == 'test_1.png'
        assert result['original_filename'] == 'test.png'
        
        # Check that the new file was created
        assert (tmp_path / 'test_1.png').exists()
    
    def test_download_error_returns_none(self, downloader, mocker, tmp_path):
        """Test Case 5.3.5: Verify download error returns None"""
        attachment = {
            'filename': 'fail.png',
            'size': 1024,
            'mimeType': 'image/png',
            'content': 'https://example.atlassian.net/rest/api/3/attachment/content/10001'
        }
        
        mocker.patch.object(downloader.session, 'get', 
                          side_effect=requests.exceptions.HTTPError())
        
        result = downloader.download_attachment(attachment, tmp_path)
        
        assert result is None


class TestDownloadAttachments:
    """Test cases for download_attachments method"""
    
    def test_multiple_attachments_download(self, downloader, mocker, tmp_path):
        """Test Case 5.3.2: Verify multiple attachments download successfully"""
        attachments = [
            {'filename': 'file1.png', 'size': 1024, 'mimeType': 'image/png',
             'content': 'https://example.atlassian.net/rest/api/3/attachment/content/10001'},
            {'filename': 'file2.pdf', 'size': 2048, 'mimeType': 'application/pdf',
             'content': 'https://example.atlassian.net/rest/api/3/attachment/content/10002'}
        ]
        
        mock_response = Mock()
        mock_response.iter_content = Mock(return_value=[b'content'])
        mock_response.raise_for_status = Mock()
        
        mocker.patch.object(downloader.session, 'get', return_value=mock_response)
        
        result = downloader.download_attachments(attachments, tmp_path)
        
        assert len(result) == 2
        assert result[0]['filename'] == 'file1.png'
        assert result[1]['filename'] == 'file2.pdf'
    
    def test_empty_attachments_list(self, downloader, tmp_path):
        """Test Case 5.3.3: Verify empty attachments list is handled gracefully"""
        result = downloader.download_attachments([], tmp_path)
        
        assert result == []
        # Directory should not be created for empty attachments
        assert not any(tmp_path.iterdir())


class TestConvertHtmlToMarkdown:
    """Test cases for convert_html_to_markdown method"""
    
    def test_standard_html_conversion(self, downloader):
        """Test Case 5.4.1: Verify standard HTML converts correctly"""
        html = """
        <h1>Heading 1</h1>
        <h2>Heading 2</h2>
        <p>This is <strong>bold</strong> and <em>italic</em> text.</p>
        <ul>
            <li>Item 1</li>
            <li>Item 2</li>
        </ul>
        <ol>
            <li>First</li>
            <li>Second</li>
        </ol>
        <p>A <a href="https://example.com">link</a></p>
        """
        
        result = downloader.convert_html_to_markdown(html)
        
        assert '# Heading 1' in result
        assert '## Heading 2' in result
        assert '**bold**' in result
        assert '*italic*' in result
        assert 'Item 1' in result
        assert 'First' in result
        assert '[link](https://example.com)' in result
    
    def test_empty_or_none_input(self, downloader):
        """Test Case 5.4.2: Verify empty/None input returns empty string"""
        assert downloader.convert_html_to_markdown(None) == ''
        assert downloader.convert_html_to_markdown('') == ''
    
    def test_unhandled_html_tags_stripped(self, downloader):
        """Test Case 5.4.3: Verify unhandled HTML tags are stripped"""
        html = '<div>Text with <custom-tag>custom tag</custom-tag></div>'
        result = downloader.convert_html_to_markdown(html)
        
        assert 'Text with custom tag' in result
        assert '<custom-tag>' not in result
        assert '<div>' not in result
    
    def test_excessive_newlines_cleaned(self, downloader):
        """Test Case 5.4.4: Verify excessive newlines are cleaned up"""
        html = '<p>Line 1</p>\n\n\n\n<p>Line 2</p>\n\n\n\n\n<p>Line 3</p>'
        result = downloader.convert_html_to_markdown(html)
        
        # Should have maximum of 2 consecutive newlines
        assert '\n\n\n' not in result
        assert 'Line 1' in result
        assert 'Line 2' in result
        assert 'Line 3' in result


class TestReplaceAttachmentLinks:
    """Test cases for replace_attachment_links method"""
    
    def test_image_url_replacement(self, downloader):
        """Test Case 5.5.1: Verify Jira image URL replacement in Markdown"""
        content = '![Screenshot](https://example.atlassian.net/secure/attachment/10001/screenshot.png)'
        downloaded_files = [
            {'filename': 'screenshot.png', 'original_filename': 'screenshot.png', 'mime_type': 'image/png'}
        ]
        
        result = downloader.replace_attachment_links(content, downloaded_files, 'example.atlassian.net')
        
        assert '![Screenshot](screenshot.png)' in result
    
    def test_link_url_replacement(self, downloader):
        """Test Case 5.5.2: Verify Jira attachment URL replacement in links"""
        content = '[Document](https://example.atlassian.net/secure/attachment/10002/document.pdf)'
        downloaded_files = [
            {'filename': 'document.pdf', 'original_filename': 'document.pdf', 'mime_type': 'application/pdf'}
        ]
        
        result = downloader.replace_attachment_links(content, downloaded_files, 'example.atlassian.net')
        
        assert '[Document](document.pdf)' in result
    
    def test_multiple_url_patterns(self, downloader):
        """Test Case 5.5.3: Verify multiple Jira URL patterns are replaced"""
        # Test that different URL patterns are all replaced (even if with the same file)
        # The implementation replaces all URLs with each file in sequence
        content = '''
        ![Image1](https://example.atlassian.net/secure/attachment/10001/image1.png)
        [File1](https://example.atlassian.net/rest/api/3/attachment/content/10002)
        ![Image2](https://example.atlassian.net/jira/rest/api/3/attachment/thumbnail/10003)
        '''
        downloaded_files = [
            {'filename': 'image1.png', 'original_filename': 'image1.png', 'mime_type': 'image/png'}
        ]
        
        result = downloader.replace_attachment_links(content, downloaded_files, 'example.atlassian.net')
        
        # All URLs should be replaced with the downloaded file
        assert '![Image1](image1.png)' in result
        # Since we only have image1.png downloaded, all URLs get replaced with it
        assert 'atlassian.net' not in result  # No Jira URLs should remain
    
    def test_filename_with_spaces_encoded(self, downloader):
        """Test Case 5.5.4: Verify filenames with spaces are URL-encoded"""
        content = '![My Image](https://example.atlassian.net/secure/attachment/10001/my%20image.png)'
        downloaded_files = [
            {'filename': 'my image.png', 'original_filename': 'my image.png', 'mime_type': 'image/png'}
        ]
        
        result = downloader.replace_attachment_links(content, downloaded_files, 'example.atlassian.net')
        
        # The replacement should URL-encode the filename with spaces
        assert 'my%20image.png' in result
    
    def test_no_attachments_content_unchanged(self, downloader):
        """Test Case 5.5.5: Verify content unchanged when no attachments"""
        content = 'This is content with [external link](https://google.com)'
        downloaded_files = []
        
        result = downloader.replace_attachment_links(content, downloaded_files, 'example.atlassian.net')
        
        assert result == content


class TestComposeMarkdown:
    """Test cases for compose_markdown method"""
    
    def test_complete_markdown_structure(self, downloader, issue_with_attachments):
        """Test Case 5.6.1: Verify complete Markdown structure"""
        downloaded_files = [
            {'filename': 'screenshot.png', 'original_filename': 'screenshot.png', 'mime_type': 'image/png'},
            {'filename': 'design_document.pdf', 'original_filename': 'design_document.pdf', 'mime_type': 'application/pdf'},
            {'filename': 'diagram.jpg', 'original_filename': 'diagram.jpg', 'mime_type': 'image/jpeg'}
        ]
        
        result = downloader.compose_markdown(issue_with_attachments, downloaded_files)
        
        # Check title with link
        assert '[TEST-123](https://example.atlassian.net/browse/TEST-123): Test Issue with Attachments' in result
        
        # Check metadata section
        assert '**Type:** Task' in result
        assert '**Status:** To Do' in result
        assert '**Priority:** High' in result
        assert '**Assignee:** John Doe' in result
        assert '**Reporter:** Jane Smith' in result
        
        # Check description section
        assert '## Description' in result
        assert 'Overview' in result
        
        # Check attachments section
        assert '## Attachments' in result
        assert '![screenshot.png](screenshot.png)' in result
        assert '[design_document.pdf](design_document.pdf)' in result
        assert '![diagram.jpg](diagram.jpg)' in result
    
    def test_issue_no_description(self, downloader, issue_no_description):
        """Test Case 5.6.2: Verify output for issue with no description"""
        result = downloader.compose_markdown(issue_no_description, [])
        
        assert '## Description' in result
        assert '*No description provided*' in result
    
    def test_issue_no_attachments(self, downloader, issue_no_attachments):
        """Test Case 5.6.3: Verify output for issue with no attachments"""
        result = downloader.compose_markdown(issue_no_attachments, [])
        
        # Attachments section should not be present
        assert '## Attachments' not in result
        
        # But description should be present
        assert '## Description' in result
        assert 'Main Heading' in result
    
    def test_attachments_section_formatting(self, downloader):
        """Test Case 5.6.4: Verify attachments section embeds images and links files"""
        issue = {
            'key': 'TEST-999',
            'fields': {
                'summary': 'Test Issue',
                'issuetype': {'name': 'Task'},
                'status': {'name': 'Open'},
                'priority': None,
                'assignee': None,
                'reporter': None
            },
            'renderedFields': {
                'description': '<p>Simple description</p>'
            }
        }
        
        downloaded_files = [
            {'filename': 'image.png', 'original_filename': 'image.png', 'mime_type': 'image/png'},
            {'filename': 'image.jpg', 'original_filename': 'image.jpg', 'mime_type': 'image/jpeg'},
            {'filename': 'image.gif', 'original_filename': 'image.gif', 'mime_type': 'image/gif'},
            {'filename': 'document.pdf', 'original_filename': 'document.pdf', 'mime_type': 'application/pdf'},
            {'filename': 'spreadsheet.xlsx', 'original_filename': 'spreadsheet.xlsx',
             'mime_type': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'}
        ]
        
        result = downloader.compose_markdown(issue, downloaded_files)
        
        # Images should be embedded
        assert '![image.png](image.png)' in result
        assert '![image.jpg](image.jpg)' in result
        assert '![image.gif](image.gif)' in result
        
        # Other files should be linked
        assert '[document.pdf](document.pdf)' in result
        assert '[spreadsheet.xlsx](spreadsheet.xlsx)' in result


class TestFormatSize:
    """Test cases for _format_size method"""
    
    def test_size_formatting(self, downloader):
        """Test Case 5.7.1: Verify correct size formatting"""
        assert downloader._format_size(512) == '512.0 B'
        assert downloader._format_size(1024) == '1.0 KB'
        assert downloader._format_size(1536) == '1.5 KB'
        assert downloader._format_size(1048576) == '1.0 MB'
        assert downloader._format_size(1572864) == '1.5 MB'
        assert downloader._format_size(1073741824) == '1.0 GB'
        assert downloader._format_size(1610612736) == '1.5 GB'