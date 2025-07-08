"""Configuration loader module.

This module provides functions to load configuration from various sources,
including YAML files, environment variables, and default values.
"""

import os
from pathlib import Path
from typing import Any, Dict, Optional, Union

import yaml

from cor_data_analysis.config.settings import Settings


def _merge_dicts(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    """Recursively merge dictionaries.
    
    Args:
        base: Base dictionary
        override: Dictionary with overrides
        
    Returns:
        Merged dictionary
    """
    result = base.copy()
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _merge_dicts(result[key], value)
        else:
            result[key] = value
    return result


def load_yaml_config(path: Union[str, Path]) -> Dict[str, Any]:
    """Load configuration from a YAML file.
    
    Args:
        path: Path to YAML configuration file
        
    Returns:
        Configuration dictionary
        
    Raises:
        FileNotFoundError: If the file doesn't exist
        yaml.YAMLError: If the file is not valid YAML
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Configuration file not found: {path}")
    
    with open(path, "r") as f:
        return yaml.safe_load(f) or {}


def load_env_config() -> Dict[str, Any]:
    """Load configuration from environment variables.

    Looks for environment variables with the prefix COR_ and converts them
    to a nested dictionary structure. A double underscore '__' is used
    to indicate nesting. For example:

    COR_DIRECTORIES__BASE_DIRECTORY=/path/to/base

    becomes:

    {
        "directories": {
            "base_directory": "/path/to/base"
        }
    }

    Returns:
        Configuration dictionary from environment variables
    """
    env_config: Dict[str, Any] = {}

    for key, value in os.environ.items():
        if not key.startswith("COR_"):
            continue

        # Remove prefix and split by double underscore for nesting
        parts = key[4:].lower().split("__")

        # Build nested dictionary
        current = env_config
        for part in parts[:-1]:
            # Create nested dict if it doesn't exist
            current = current.setdefault(part, {})

        # Set value for the last part
        current[parts[-1]] = value

    return env_config


def get_default_config_path() -> Path:
    """Get the default configuration file path.
    
    Returns:
        Path to default configuration file
    """
    # Check for config in current directory first
    local_config = Path("config.yaml")
    if local_config.exists():
        return local_config
        
    # Then check for config in user's config directory
    user_config_dir = Path(os.path.expanduser("~/.config/cor-data-analysis"))
    user_config = user_config_dir / "config.yaml"
    if user_config.exists():
        return user_config
        
    # Finally check for system-wide config
    system_config = Path("/etc/cor-data-analysis/config.yaml")
    if system_config.exists():
        return system_config
        
    # Return local path as default if no config file found
    return local_config


def load_config(
    config_path: Optional[Union[str, Path]] = None, 
    env_override: bool = True
) -> Settings:
    """Load configuration from file and environment variables.
    
    Args:
        config_path: Path to configuration file (optional)
        env_override: Whether to allow environment variables to override file settings
        
    Returns:
        Settings object with loaded configuration
    """
    # Start with empty configuration
    config_dict: Dict[str, Any] = {}
    
    # Load from file if specified or use default
    try:
        file_path = Path(config_path) if config_path else get_default_config_path()
        if file_path.exists():
            config_dict = load_yaml_config(file_path)
    except (FileNotFoundError, yaml.YAMLError) as e:
        # Log error but continue with default config
        # We'll implement proper logging later
        print(f"Error loading configuration file: {e}")
    
    # Override with environment variables if enabled
    if env_override:
        env_config = load_env_config()
        config_dict = _merge_dicts(config_dict, env_config)
    
    # Create Settings object
    return Settings.from_dict(config_dict)
