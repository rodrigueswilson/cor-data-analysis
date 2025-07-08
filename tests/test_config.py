"""Tests for configuration module."""

import os
import tempfile
from pathlib import Path
from unittest import mock

import pytest
import yaml

from cor_data_analysis.config import (
    DirectoryConfig,
    FeatureFlags,
    LoggingConfig,
    SecuritySettings,
    Settings,
    get_settings,
    is_feature_enabled,
    load_config,
)
from cor_data_analysis.config.loader import (
    _merge_dicts,
    load_env_config,
    load_yaml_config,
)


def test_directory_config_defaults():
    """Test DirectoryConfig creates default directories."""
    with tempfile.TemporaryDirectory() as tempdir:
        with mock.patch("os.getcwd", return_value=tempdir):
            config = DirectoryConfig()
            
            # Check directories are created with correct paths
            assert config.base_directory == Path(tempdir)
            assert config.mp3_directory == Path(tempdir) / "mp3_files"
            assert config.jpg_directory == Path(tempdir) / "jpg_files"
            assert config.output_directory == Path(tempdir) / "output"
            assert config.logs_directory == Path(tempdir) / "logs"
            
            # Check directories were created
            assert config.mp3_directory.exists()
            assert config.jpg_directory.exists()
            assert config.output_directory.exists()
            assert config.logs_directory.exists()


def test_logging_config_validation():
    """Test LoggingConfig validates log levels."""
    # Valid log levels should pass
    valid_config = LoggingConfig(level="INFO", matplotlib_level="WARNING")
    assert valid_config.level == "INFO"
    assert valid_config.matplotlib_level == "WARNING"
    
    # Invalid log levels should raise ValueError
    with pytest.raises(ValueError):
        LoggingConfig(level="INVALID")
        
    # Log levels should be normalized to uppercase
    mixed_case_config = LoggingConfig(level="info")
    assert mixed_case_config.level == "INFO"


def test_feature_flags_defaults():
    """Test FeatureFlags default values."""
    flags = FeatureFlags()
    assert flags.enable_logging_to_file is True
    assert flags.enable_mp3_processing is True
    assert flags.enable_jpg_processing is True
    assert flags.enable_chart_generation is True


def test_security_settings_env_vars():
    """Test SecuritySettings loads from environment variables."""
    with mock.patch.dict(os.environ, {
        "ENCRYPTION_KEY": "test_key",
        "SSL_CERT_PATH": "/path/to/cert",
        "SSL_KEY_PATH": "/path/to/key"
    }):
        security = SecuritySettings()
        assert security.encryption_key == "test_key"
        assert security.ssl_cert_path == Path("/path/to/cert")
        assert security.ssl_key_path == Path("/path/to/key")


def test_settings_from_dict():
    """Test creating Settings from a dictionary."""
    config_dict = {
        "directories": {
            "base_directory": "/test/base",
            "logs_directory": "/test/logs"
        },
        "logging": {
            "level": "DEBUG"
        },
        "features": {
            "enable_chart_generation": False
        }
    }
    
    settings = Settings.from_dict(config_dict)
    
    assert settings.directories.base_directory == Path("/test/base")
    assert settings.directories.logs_directory == Path("/test/logs")
    assert settings.logging.level == "DEBUG"
    assert settings.features.enable_chart_generation is False
    
    # Check defaults are used for unspecified values
    assert settings.features.enable_mp3_processing is True


def test_merge_dicts():
    """Test _merge_dicts function."""
    base = {
        "a": 1,
        "b": {
            "c": 2,
            "d": 3
        }
    }
    
    override = {
        "b": {
            "c": 4
        },
        "e": 5
    }
    
    result = _merge_dicts(base, override)
    
    assert result == {
        "a": 1,
        "b": {
            "c": 4,
            "d": 3
        },
        "e": 5
    }


def test_load_yaml_config():
    """Test loading configuration from YAML file."""
    config_data = {
        "directories": {
            "base_directory": "/test/base"
        },
        "features": {
            "enable_chart_generation": False
        }
    }
    
    # Use a temporary directory instead of just a temp file to avoid permission issues
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_file_path = Path(temp_dir) / "config.yaml"
        
        with open(temp_file_path, "w") as f:
            yaml.dump(config_data, f)
        
        loaded_config = load_yaml_config(temp_file_path)
        assert loaded_config == config_data
        
        # Test with non-existent file
        with pytest.raises(FileNotFoundError):
            load_yaml_config("non_existent_file.yaml")


def test_load_env_config():
    """Test loading configuration from environment variables."""
    with mock.patch.dict(os.environ, {
        "COR_DIRECTORIES__BASE_DIRECTORY": "/env/base",
        "COR_FEATURES__ENABLE_MP3_PROCESSING": "false",
        "OTHER_VAR": "ignored"
    }):
        env_config = load_env_config()

        expected_config = {
            "directories": {
                "base_directory": "/env/base"
            },
            "features": {
                "enable_mp3_processing": "false"
            }
        }

        assert env_config == expected_config
        assert "other_var" not in env_config


def test_get_settings_singleton():
    """Test get_settings returns singleton instance."""
    # Reset singleton for test
    from cor_data_analysis.config import _settings
    _settings = None
    
    # First call should create instance
    settings1 = get_settings()
    
    # Second call should return same instance
    settings2 = get_settings()
    assert settings1 is settings2
    
    # With reload=True, should create new instance
    settings3 = get_settings(reload=True)
    assert settings1 is not settings3


def test_is_feature_enabled():
    """Test is_feature_enabled function."""
    # Reset singleton for test
    from cor_data_analysis.config import _settings
    _settings = None
    
    with mock.patch(
        "cor_data_analysis.config.get_settings", 
        return_value=Settings(
            features=FeatureFlags(enable_chart_generation=False)
        )
    ):
        assert is_feature_enabled("enable_mp3_processing") is True
        assert is_feature_enabled("enable_chart_generation") is False
        
        # Test for non-existent feature
        with pytest.raises(AttributeError):
            is_feature_enabled("non_existent_feature")
