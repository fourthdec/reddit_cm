import json
import tempfile
import pytest
from pathlib import Path
import yaml

from main import load_config


class TestConfigLoading:
    def test_load_yaml_config(self):
        """Test loading YAML configuration file."""
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
            loaded_config = load_config(config_file)
            assert loaded_config == config_data
        finally:
            Path(config_file).unlink()

    def test_load_json_config(self):
        """Test loading JSON configuration file."""
        config_data = {
            'client_id': 'test_id',
            'client_secret': 'test_secret',
            'username': 'test_user',
            'password': 'test_pass',
            'format': 'json'
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_data, f)
            config_file = f.name
        
        try:
            loaded_config = load_config(config_file)
            assert loaded_config == config_data
        finally:
            Path(config_file).unlink()

    def test_load_config_file_not_found(self):
        """Test error handling when config file doesn't exist."""
        from click.exceptions import ClickException
        
        with pytest.raises(ClickException, match="Config file not found"):
            load_config("non_existent_file.yaml")

    def test_load_invalid_yaml_config(self):
        """Test error handling for invalid YAML file."""
        from click.exceptions import ClickException
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("invalid: yaml: content: [")
            config_file = f.name
        
        try:
            with pytest.raises(ClickException, match="Failed to parse config file"):
                load_config(config_file)
        finally:
            Path(config_file).unlink()

    def test_load_invalid_json_config(self):
        """Test error handling for invalid JSON file."""
        from click.exceptions import ClickException
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write('{"invalid": json,}')
            config_file = f.name
        
        try:
            with pytest.raises(ClickException, match="Failed to parse config file"):
                load_config(config_file)
        finally:
            Path(config_file).unlink()

    def test_load_empty_config(self):
        """Test loading empty configuration file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("")
            config_file = f.name
        
        try:
            loaded_config = load_config(config_file)
            assert loaded_config == {}
        finally:
            Path(config_file).unlink()

    def test_auto_detect_json_format(self):
        """Test auto-detection of JSON format for files without extension."""
        config_data = {'client_id': 'test_id'}
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='', delete=False) as f:
            json.dump(config_data, f)
            config_file = f.name
        
        try:
            loaded_config = load_config(config_file)
            assert loaded_config == config_data
        finally:
            Path(config_file).unlink()

    def test_auto_detect_yaml_format(self):
        """Test auto-detection of YAML format for files without extension."""
        config_data = {'client_id': 'test_id', 'username': 'test_user'}
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='', delete=False) as f:
            # Write valid YAML that's not valid JSON
            yaml.dump(config_data, f)
            config_file = f.name
        
        try:
            loaded_config = load_config(config_file)
            assert loaded_config == config_data
        finally:
            Path(config_file).unlink()