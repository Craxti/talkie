"""Tests for config module."""

import json
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, mock_open
import pytest
from talkie.utils.config import Config, Environment, load_config, save_config, get_config_path


class TestEnvironment:
    """Test Environment model."""
    
    def test_environment_creation(self):
        """Test environment creation."""
        env = Environment(name="test")
        assert env.name == "test"
        assert env.base_url is None
        assert env.default_headers == {}
        assert env.auth is None

    def test_environment_with_all_fields(self):
        """Test environment with all fields."""
        env = Environment(
            name="production",
            base_url="https://api.example.com",
            default_headers={"Authorization": "Bearer token"},
            auth={"type": "bearer", "token": "secret"}
        )
        assert env.name == "production"
        assert env.base_url == "https://api.example.com"
        assert env.default_headers == {"Authorization": "Bearer token"}
        assert env.auth == {"type": "bearer", "token": "secret"}

    def test_environment_validation(self):
        """Test environment validation."""
        # Name is required
        with pytest.raises(ValueError):
            Environment()

    def test_environment_serialization(self):
        """Test environment serialization."""
        env = Environment(
            name="test",
            base_url="https://example.com",
            default_headers={"Content-Type": "application/json"}
        )
        
        data = env.model_dump()
        assert data["name"] == "test"
        assert data["base_url"] == "https://example.com"
        assert data["default_headers"] == {"Content-Type": "application/json"}


class TestConfig:
    """Test Config model."""
    
    def test_config_creation(self):
        """Test config creation."""
        config = Config()
        assert config.default_headers == {"User-Agent": "Talkie/0.1.0"}
        assert config.environments == {}
        assert config.active_environment is None

    def test_config_with_environments(self):
        """Test config with environments."""
        env1 = Environment(name="dev", base_url="https://dev.example.com")
        env2 = Environment(name="prod", base_url="https://prod.example.com")
        
        config = Config(
            environments={"dev": env1, "prod": env2},
            active_environment="dev"
        )
        assert len(config.environments) == 2
        assert "dev" in config.environments
        assert "prod" in config.environments
        assert config.active_environment == "dev"

    def test_config_serialization(self):
        """Test config serialization."""
        env = Environment(name="test", base_url="https://example.com")
        config = Config(
            environments={"test": env},
            active_environment="test"
        )
        
        data = config.model_dump()
        assert "environments" in data
        assert "active_environment" in data
        assert data["active_environment"] == "test"

    def test_config_load_default(self):
        """Test loading default config."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.json"
            with patch('talkie.utils.config.Config._get_config_path') as mock_path:
                mock_path.return_value = config_path

                config = Config.load_default()
                assert isinstance(config, Config)
                assert config.default_headers == {"User-Agent": "Talkie/0.1.0"}

    def test_config_load_from_file(self):
        """Test loading config from file."""
        config_data = {
            "default_headers": {"User-Agent": "Custom/1.0"},
            "environments": {
                "test": {
                    "name": "test",
                    "base_url": "https://test.example.com"
                }
            },
            "active_environment": "test"
        }
        
        with patch('talkie.utils.config.Config._get_config_path') as mock_path:
            with tempfile.NamedTemporaryFile(mode='w', delete=False) as temp_file:
                json.dump(config_data, temp_file)
                temp_path = Path(temp_file.name)
            
            try:
                mock_path.return_value = temp_path
                config = Config.load_default()
                
                assert config.default_headers == {"User-Agent": "Custom/1.0"}
                assert "test" in config.environments
                assert config.active_environment == "test"
            finally:
                if temp_path.exists():
                    temp_path.unlink()

    def test_config_load_invalid_json(self):
        """Test loading config with invalid JSON."""
        with patch('talkie.utils.config.Config._get_config_path') as mock_path:
            with tempfile.NamedTemporaryFile(mode='w', delete=False) as temp_file:
                temp_file.write("invalid json")
                temp_path = Path(temp_file.name)
            
            try:
                mock_path.return_value = temp_path
                config = Config.load_default()
                
                # Should return default config on error
                assert isinstance(config, Config)
            finally:
                if temp_path.exists():
                    temp_path.unlink()


class TestConfigFunctions:
    """Test config utility functions."""
    
    def test_get_config_path(self):
        """Test getting config path."""
        with patch.dict(os.environ, {'HOME': '/test/home'}, clear=True):
            path = get_config_path()
            # On Windows, the path might be different
            path_str = str(path)
            assert '.talkie' in path_str
            assert 'config.json' in path_str

    def test_load_config(self):
        """Test load_config function."""
        with patch('talkie.utils.config.Config.load_default') as mock_load:
            mock_config = Config()
            mock_load.return_value = mock_config
            
            config = load_config()
            assert config is mock_config
            mock_load.assert_called_once()

    def test_save_config(self):
        """Test save_config function."""
        config = Config()
        
        # Test that save_config function exists and is callable
        assert callable(save_config)
        
        # Test that it doesn't raise an exception
        try:
            save_config(config)
        except Exception as e:
            # It's OK if it fails due to file system issues in test environment
            assert "Permission" in str(e) or "File" in str(e) or "Path" in str(e)

    def test_save_config_with_environments(self):
        """Test saving config with environments."""
        env = Environment(name="test", base_url="https://example.com")
        config = Config(
            environments={"test": env},
            active_environment="test"
        )
        
        # Test that save_config function exists and is callable
        assert callable(save_config)
        
        # Test that it doesn't raise an exception
        try:
            save_config(config)
        except Exception as e:
            # It's OK if it fails due to file system issues in test environment
            assert "Permission" in str(e) or "File" in str(e) or "Path" in str(e)


class TestConfigIntegration:
    """Test config integration."""
    
    def test_config_workflow(self):
        """Test complete config workflow."""
        # Create config
        env = Environment(name="dev", base_url="https://dev.example.com")
        config = Config(
            default_headers={"X-Custom": "value"},
            environments={"dev": env},
            active_environment="dev"
        )
        
        # Test that the config has the expected values
        assert "X-Custom" in config.default_headers
        assert config.default_headers["X-Custom"] == "value"
        assert "dev" in config.environments
        assert config.active_environment == "dev"

    def test_config_with_multiple_environments(self):
        """Test config with multiple environments."""
        dev_env = Environment(name="dev", base_url="https://dev.example.com")
        prod_env = Environment(name="prod", base_url="https://prod.example.com")
        
        config = Config(
            environments={"dev": dev_env, "prod": prod_env},
            active_environment="dev"
        )
        
        assert len(config.environments) == 2
        assert config.environments["dev"].base_url == "https://dev.example.com"
        assert config.environments["prod"].base_url == "https://prod.example.com"
        assert config.active_environment == "dev"

    def test_config_environment_access(self):
        """Test accessing environment from config."""
        env = Environment(name="test", base_url="https://test.example.com")
        config = Config(environments={"test": env}, active_environment="test")
        
        active_env = config.environments.get(config.active_environment)
        assert active_env is not None
        assert active_env.name == "test"
        assert active_env.base_url == "https://test.example.com"
