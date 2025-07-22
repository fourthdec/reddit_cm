import json
import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from click.testing import CliRunner
import yaml

from main import cli


class TestCLI:
    def test_cli_help(self):
        """Test CLI help command."""
        runner = CliRunner()
        result = runner.invoke(cli, ['--help'])
        
        assert result.exit_code == 0
        assert 'Export Reddit communities' in result.output
        assert '--config' in result.output
        assert '--client-id' in result.output
        assert '--format' in result.output

    def test_cli_missing_required_params(self):
        """Test CLI with missing required parameters."""
        runner = CliRunner()
        result = runner.invoke(cli, [])
        
        assert result.exit_code != 0
        assert 'Missing required parameters' in result.output

    def test_cli_with_command_line_args(self):
        """Test CLI with command line arguments (will fail auth but test parsing)."""
        runner = CliRunner()
        result = runner.invoke(cli, [
            '--client-id', 'test_id',
            '--client-secret', 'test_secret',
            '--username', 'test_user',
            '--password', 'test_pass'
        ])
        
        # Should fail at authentication, but args should be parsed correctly
        assert 'Authenticating with Reddit as test_user' in result.output
        assert 'Authentication failed' in result.output

    def test_cli_with_config_file(self):
        """Test CLI with configuration file."""
        config_data = {
            'client_id': 'config_id',
            'client_secret': 'config_secret',
            'username': 'config_user',
            'password': 'config_pass',
            'format': 'yaml'
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(config_data, f)
            config_file = f.name
        
        try:
            runner = CliRunner()
            result = runner.invoke(cli, ['--config', config_file])
            
            # Should fail at authentication, but config should be loaded
            assert 'Authenticating with Reddit as config_user' in result.output
            assert 'Authentication failed' in result.output
        finally:
            Path(config_file).unlink()

    def test_cli_command_line_overrides_config(self):
        """Test that command line args override config file values."""
        config_data = {
            'client_id': 'config_id',
            'client_secret': 'config_secret',
            'username': 'config_user',
            'password': 'config_pass'
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(config_data, f)
            config_file = f.name
        
        try:
            runner = CliRunner()
            result = runner.invoke(cli, [
                '--config', config_file,
                '--username', 'override_user'
            ])
            
            # Should use override username, not config username
            assert 'Authenticating with Reddit as override_user' in result.output
            assert 'config_user' not in result.output
        finally:
            Path(config_file).unlink()

    def test_cli_invalid_config_file(self):
        """Test CLI with invalid config file."""
        runner = CliRunner()
        result = runner.invoke(cli, ['--config', 'nonexistent.yaml'])
        
        assert result.exit_code != 0
        assert 'does not exist' in result.output

    def test_cli_format_validation(self):
        """Test CLI format parameter validation."""
        runner = CliRunner()
        result = runner.invoke(cli, [
            '--client-id', 'test_id',
            '--client-secret', 'test_secret',
            '--username', 'test_user',
            '--password', 'test_pass',
            '--format', 'invalid_format'
        ])
        
        assert result.exit_code != 0
        assert 'Invalid value for' in result.output or 'Usage:' in result.output

    @patch('main.authenticate_reddit')
    @patch('main.export_communities')
    def test_cli_output_file_extension_adjustment(self, mock_export, mock_auth):
        """Test automatic adjustment of output file extension based on format."""
        # Mock the Reddit authentication and export
        mock_reddit = MagicMock()
        mock_auth.return_value = mock_reddit
        mock_export.return_value = None
        
        config_data = {
            'client_id': 'test_id',
            'client_secret': 'test_secret',
            'username': 'test_user',
            'password': 'test_pass',
            'format': 'yaml'
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(config_data, f)
            config_file = f.name
        
        try:
            runner = CliRunner()
            result = runner.invoke(cli, ['--config', config_file])
            
            assert result.exit_code == 0
            assert 'Exporting communities to YAML format' in result.output
            
            # Verify export was called with communities.yaml instead of communities.json
            mock_export.assert_called_once_with(mock_reddit, 'yaml', 'communities.yaml')
        finally:
            Path(config_file).unlink()

    @patch('main.authenticate_reddit')
    @patch('main.export_communities')
    def test_cli_successful_flow(self, mock_export, mock_auth):
        """Test successful CLI execution flow with mocked Reddit API."""
        # Mock the Reddit authentication
        mock_reddit = MagicMock()
        mock_auth.return_value = mock_reddit
        
        # Mock the export function
        mock_export.return_value = None
        
        runner = CliRunner()
        result = runner.invoke(cli, [
            '--client-id', 'test_id',
            '--client-secret', 'test_secret',
            '--username', 'test_user',
            '--password', 'test_pass',
            '--format', 'json',
            '--output', 'test_output.json'
        ])
        
        assert result.exit_code == 0
        assert 'Authenticating with Reddit as test_user' in result.output
        assert 'Exporting communities to JSON format' in result.output
        
        # Verify the mocked functions were called with correct parameters
        mock_auth.assert_called_once_with('test_id', 'test_secret', 'test_user', 'test_pass', 'reddit-cm:v0.1.0')
        mock_export.assert_called_once_with(mock_reddit, 'json', 'test_output.json')