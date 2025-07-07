"""Configuration package for COR Data Analysis.

This package provides settings management and feature flag functionality
for the COR Data Analysis application.
"""

from typing import Optional, Union
from pathlib import Path

from cor_data_analysis.config.settings import (
    DirectoryConfig,
    FeatureFlags,
    LoggingConfig,
    SecuritySettings,
    Settings,
)
from cor_data_analysis.config.loader import load_config

# Global settings instance
_settings: Optional[Settings] = None


def get_settings(
    config_path: Optional[Union[str, Path]] = None,
    env_override: bool = True,
    reload: bool = False,
) -> Settings:
    """Get the application settings.
    
    This function returns a singleton instance of the Settings class,
    creating it if it doesn't exist.
    
    Args:
        config_path: Optional path to a configuration file
        env_override: Whether to allow environment variables to override file settings
        reload: Force reload of configuration
        
    Returns:
        Settings instance
    """
    global _settings
    if _settings is None or reload:
        _settings = load_config(config_path=config_path, env_override=env_override)
    return _settings


def is_feature_enabled(feature_name: str) -> bool:
    """Check if a feature is enabled.
    
    Args:
        feature_name: Name of the feature to check
        
    Returns:
        True if feature is enabled, False otherwise
        
    Raises:
        AttributeError: If the feature doesn't exist
    """
    settings = get_settings()
    return getattr(settings.features, feature_name)


# Expose main settings components
__all__ = [
    "DirectoryConfig",
    "FeatureFlags",
    "LoggingConfig",
    "SecuritySettings",
    "Settings",
    "get_settings",
    "is_feature_enabled",
    "load_config",
]
