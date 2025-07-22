import json
import tempfile
import pytest
from datetime import datetime
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open
import yaml

from main import authenticate_reddit, export_communities


class TestRedditAPI:
    @patch('main.praw.Reddit')
    def test_authenticate_reddit_success(self, mock_reddit_class):
        """Test successful Reddit authentication."""
        # Mock Reddit instance
        mock_reddit = MagicMock()
        mock_reddit_class.return_value = mock_reddit
        
        # Mock successful authentication (user.me() doesn't raise)
        mock_reddit.user.me.return_value = MagicMock()
        
        result = authenticate_reddit('test_id', 'test_secret', 'test_user', 'test_pass', 'test_agent')
        
        assert result == mock_reddit
        mock_reddit_class.assert_called_once_with(
            client_id='test_id',
            client_secret='test_secret',
            username='test_user',
            password='test_pass',
            user_agent='test_agent'
        )
        mock_reddit.user.me.assert_called_once()

    @patch('main.praw.Reddit')
    def test_authenticate_reddit_failure(self, mock_reddit_class):
        """Test failed Reddit authentication."""
        from click.exceptions import ClickException
        
        # Mock Reddit instance that raises exception on auth test
        mock_reddit = MagicMock()
        mock_reddit_class.return_value = mock_reddit
        mock_reddit.user.me.side_effect = Exception("Invalid credentials")
        
        with pytest.raises(ClickException, match="Authentication failed"):
            authenticate_reddit('bad_id', 'bad_secret', 'bad_user', 'bad_pass', 'test_agent')

    def test_export_communities_json(self):
        """Test exporting communities to JSON format."""
        # Mock Reddit instance with subreddits
        mock_reddit = MagicMock()
        
        # Mock subreddit objects
        mock_subreddit1 = MagicMock()
        mock_subreddit1.display_name = 'python'
        mock_subreddit1.title = 'Python'
        mock_subreddit1.public_description = 'Python programming language'
        mock_subreddit1.subscribers = 1000000
        mock_subreddit1.created_utc = 1200000000  # Timestamp
        
        mock_subreddit2 = MagicMock()
        mock_subreddit2.display_name = 'javascript'
        mock_subreddit2.title = 'JavaScript'
        mock_subreddit2.public_description = 'JavaScript programming'
        mock_subreddit2.subscribers = 500000
        mock_subreddit2.created_utc = 1300000000
        
        mock_reddit.user.subreddits.return_value = [mock_subreddit1, mock_subreddit2]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            output_file = f.name
        
        try:
            with patch('builtins.open', mock_open()) as mock_file:
                with patch('main.json.dump') as mock_json_dump:
                    export_communities(mock_reddit, 'json', output_file)
                    
                    # Verify json.dump was called
                    mock_json_dump.assert_called_once()
                    
                    # Check the data structure passed to json.dump
                    call_args = mock_json_dump.call_args[0]
                    export_data = call_args[0]
                    
                    assert 'exported_at' in export_data
                    assert export_data['total_communities'] == 2
                    assert len(export_data['communities']) == 2
                    
                    # Check first community data
                    community1 = export_data['communities'][0]
                    assert community1['name'] == 'python'
                    assert community1['title'] == 'Python'
                    assert community1['description'] == 'Python programming language'
                    assert community1['subscribers'] == 1000000
                    assert community1['url'] == 'https://reddit.com/r/python'
        finally:
            Path(output_file).unlink(missing_ok=True)

    def test_export_communities_yaml(self):
        """Test exporting communities to YAML format."""
        # Mock Reddit instance with one subreddit
        mock_reddit = MagicMock()
        
        mock_subreddit = MagicMock()
        mock_subreddit.display_name = 'test'
        mock_subreddit.title = 'Test Community'
        mock_subreddit.public_description = 'Test description'
        mock_subreddit.subscribers = 100
        mock_subreddit.created_utc = 1234567890
        
        mock_reddit.user.subreddits.return_value = [mock_subreddit]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            output_file = f.name
        
        try:
            with patch('builtins.open', mock_open()) as mock_file:
                with patch('main.yaml.dump') as mock_yaml_dump:
                    export_communities(mock_reddit, 'yaml', output_file)
                    
                    # Verify yaml.dump was called
                    mock_yaml_dump.assert_called_once()
                    
                    # Check the data structure passed to yaml.dump
                    call_args = mock_yaml_dump.call_args[0]
                    export_data = call_args[0]
                    
                    assert 'exported_at' in export_data
                    assert export_data['total_communities'] == 1
                    assert len(export_data['communities']) == 1
                    
                    # Check community data
                    community = export_data['communities'][0]
                    assert community['name'] == 'test'
                    assert community['url'] == 'https://reddit.com/r/test'
        finally:
            Path(output_file).unlink(missing_ok=True)

    def test_export_communities_empty_description(self):
        """Test export with subreddit that has no description."""
        mock_reddit = MagicMock()
        
        mock_subreddit = MagicMock()
        mock_subreddit.display_name = 'nodesc'
        mock_subreddit.title = 'No Description'
        mock_subreddit.public_description = None  # No description
        mock_subreddit.subscribers = 50
        mock_subreddit.created_utc = 1000000000
        
        mock_reddit.user.subreddits.return_value = [mock_subreddit]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            output_file = f.name
        
        try:
            with patch('builtins.open', mock_open()):
                with patch('main.json.dump') as mock_json_dump:
                    export_communities(mock_reddit, 'json', output_file)
                    
                    call_args = mock_json_dump.call_args[0]
                    export_data = call_args[0]
                    community = export_data['communities'][0]
                    
                    # Should default to empty string
                    assert community['description'] == ''
        finally:
            Path(output_file).unlink(missing_ok=True)

    def test_export_communities_api_error(self):
        """Test export when Reddit API fails."""
        from click.exceptions import ClickException
        
        mock_reddit = MagicMock()
        mock_reddit.user.subreddits.side_effect = Exception("API Error")
        
        with pytest.raises(ClickException, match="Export failed"):
            export_communities(mock_reddit, 'json', 'test.json')

    def test_export_communities_file_error(self):
        """Test export when file writing fails."""
        from click.exceptions import ClickException
        
        mock_reddit = MagicMock()
        mock_reddit.user.subreddits.return_value = []
        
        # Test with invalid file path
        with pytest.raises(ClickException, match="Export failed"):
            export_communities(mock_reddit, 'json', '/invalid/path/file.json')