"""Settings module for COR Data Analysis.

This module contains Pydantic models for application configuration,
including directories, logging, and feature flags.
"""

import os
from pathlib import Path
from typing import Dict, Optional, Union

from pydantic import BaseModel, Field, field_validator, model_validator


class DirectoryConfig(BaseModel):
    """Configuration for directories used in the application."""

    base_directory: Path = Field(
        default=None,
        description="Base directory for the application",
    )
    mp3_directory: Path = Field(
        default=None,
        description="Directory containing MP3 files",
    )
    jpg_directory: Path = Field(
        default=None,
        description="Directory containing JPG files",
    )
    output_directory: Path = Field(
        default=None,
        description="Directory for output files",
    )
    logs_directory: Path = Field(
        default=None,
        description="Directory for log files",
    )

    @model_validator(mode='after')
    def set_default_directories(self) -> "DirectoryConfig":
        """Set default directories if they are not provided."""
        if self.base_directory is None:
            self.base_directory = Path(os.getcwd())

        # Set dependent directories if they are not provided
        if self.mp3_directory is None:
            self.mp3_directory = self.base_directory / "mp3_files"
        if self.jpg_directory is None:
            self.jpg_directory = self.base_directory / "jpg_files"
        if self.output_directory is None:
            self.output_directory = self.base_directory / "output"
        if self.logs_directory is None:
            self.logs_directory = self.base_directory / "logs"

        return self

    @model_validator(mode='after')
    def ensure_directories_exist(self) -> "DirectoryConfig":
        """Ensure all directories exist, creating them if necessary."""
        for dir_attr in self.model_fields:
            dir_path = getattr(self, dir_attr)
            if isinstance(dir_path, Path) and not dir_path.exists():
                dir_path.mkdir(parents=True, exist_ok=True)
        return self


class LoggingConfig(BaseModel):
    """Configuration for logging."""

    level: str = Field(
        default="INFO",
        description="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)",
    )
    format: str = Field(
        default="%(asctime)s - %(levelname)s - %(message)s",
        description="Logging format string",
    )
    matplotlib_level: str = Field(
        default="WARNING",
        description="Logging level for matplotlib",
    )

    @field_validator("level", "matplotlib_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate and normalize log level strings."""
        valid_levels = ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL")
        v_upper = v.upper()
        if v_upper not in valid_levels:
            raise ValueError(f"Invalid log level: {v}. Must be one of {valid_levels}")
        return v_upper


class FeatureFlags(BaseModel):
    """Feature flags for enabling/disabling functionality."""

    enable_logging_to_file: bool = Field(
        default=True,
        description="Enable logging to file",
    )
    enable_mp3_processing: bool = Field(
        default=True,
        description="Enable MP3 file processing",
    )
    enable_jpg_processing: bool = Field(
        default=True,
        description="Enable JPG file processing",
    )
    enable_chart_generation: bool = Field(
        default=True,
        description="Enable chart generation in reports",
    )


class SecuritySettings(BaseModel):
    """Security settings for the application."""

    encryption_key: Optional[str] = Field(
        default=None,
        description="Encryption key for sensitive data",
    )
    ssl_cert_path: Optional[Path] = Field(
        default=None,
        description="Path to SSL certificate",
    )
    ssl_key_path: Optional[Path] = Field(
        default=None,
        description="Path to SSL key",
    )

    @model_validator(mode='after')
    def load_from_env(self) -> "SecuritySettings":
        """Load security settings from environment variables if not provided."""
        if self.encryption_key is None:
            self.encryption_key = os.getenv("ENCRYPTION_KEY", "default_key")
        if self.ssl_cert_path is None:
            cert_path = os.getenv("SSL_CERT_PATH")
            if cert_path:
                self.ssl_cert_path = Path(cert_path)
        if self.ssl_key_path is None:
            key_path = os.getenv("SSL_KEY_PATH")
            if key_path:
                self.ssl_key_path = Path(key_path)
        return self


class Settings(BaseModel):
    """Main settings class for the application."""

    directories: DirectoryConfig = Field(
        default_factory=DirectoryConfig,
        description="Directory configuration",
    )
    logging: LoggingConfig = Field(
        default_factory=LoggingConfig,
        description="Logging configuration",
    )
    features: FeatureFlags = Field(
        default_factory=FeatureFlags,
        description="Feature flags",
    )
    security: SecuritySettings = Field(
        default_factory=SecuritySettings,
        description="Security settings",
    )

    @classmethod
    def from_dict(cls, config_dict: Dict) -> "Settings":
        """Create a Settings instance from a dictionary."""
        return cls(
            directories=DirectoryConfig(**config_dict.get("directories", {})),
            logging=LoggingConfig(**config_dict.get("logging", {})),
            features=FeatureFlags(**config_dict.get("features", {})),
            security=SecuritySettings(**config_dict.get("security", {})),
        )
