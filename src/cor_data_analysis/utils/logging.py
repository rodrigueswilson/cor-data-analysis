"""Logging utilities for COR Data Analysis.

This module provides a centralized logging setup with configuration options,
log rotation, and context providers.
"""

import logging
import logging.handlers
import os
import sys
from pathlib import Path
from typing import Any, Dict, Optional, Union

from cor_data_analysis.config import get_settings, is_feature_enabled


def get_log_level(level_str: str) -> int:
    """Convert string log level to logging module constant.
    
    Args:
        level_str: String representation of log level
        
    Returns:
        Integer log level from logging module
    """
    level_map = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL,
    }
    return level_map.get(level_str.upper(), logging.INFO)


def configure_logger(
    name: str = "cor_data_analysis",
    log_level: str = "INFO",
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    log_file: Optional[Union[str, Path]] = None,
    max_bytes: int = 10 * 1024 * 1024,  # 10 MB
    backup_count: int = 5,
) -> logging.Logger:
    """Configure a logger with the specified settings.
    
    Args:
        name: Logger name
        log_level: Optional override for log level
        log_format: Optional override for log format
        log_file: Optional log file path
        max_bytes: Maximum size in bytes before rotating log file
        backup_count: Number of backup files to keep
        
    Returns:
        Configured logger instance
    """
    # No need to get settings from config since we provide defaults in parameters
    
    # Get or create logger
    logger = logging.getLogger(name)
    logger.setLevel(get_log_level(log_level))
    
    # Remove existing handlers to avoid duplicates during reconfigurations
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Create formatter
    formatter = logging.Formatter(log_format)
    
    # Always add console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # Add file handler if path provided
    if log_file:
        log_path = Path(log_file)
        
        # Ensure directory exists
        if not log_path.parent.exists():
            log_path.parent.mkdir(parents=True, exist_ok=True)
            
        # Set up rotating file handler
        file_handler = logging.handlers.RotatingFileHandler(
            filename=log_path,
            maxBytes=max_bytes,
            backupCount=backup_count,
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger


class LoggingContext:
    """Context manager for adding temporary context to logs."""
    
    def __init__(self, logger: logging.Logger, **kwargs: Any):
        """Initialize with logger and context variables.
        
        Args:
            logger: Logger instance
            **kwargs: Context variables to add to logs
        """
        self.logger = logger
        self.context = kwargs
        self.old_context: Dict[str, Any] = {}
        
    def __enter__(self) -> "LoggingContext":
        """Save old context and set new context."""
        if not hasattr(self.logger, "context"):
            self.logger.context = {}  # type: ignore
            
        self.old_context = getattr(self.logger, "context", {}).copy()
        
        # Update logger context with new values
        logger_context = getattr(self.logger, "context", {}).copy()
        logger_context.update(self.context)
        self.logger.context = logger_context  # type: ignore
        
        return self
        
    def __exit__(self, *args: Any) -> None:
        """Restore old context."""
        self.logger.context = self.old_context  # type: ignore


class ContextAdapter(logging.LoggerAdapter):
    """Adapter to add context information to log records."""
    
    def process(self, msg: str, kwargs: Dict[str, Any]) -> tuple:
        """Process the log message by adding context.
        
        Args:
            msg: Log message
            kwargs: Keyword arguments for logger
            
        Returns:
            Tuple of (modified message, kwargs)
        """
        # Get context from logger or empty dict
        context = getattr(self.logger, "context", {})
        
        # If there's context, format and add to message
        if context:
            context_str = " ".join(f"{k}={v}" for k, v in context.items())
            msg = f"{msg} [{context_str}]"
            
        return msg, kwargs


def get_logger(name: str = "cor_data_analysis") -> logging.Logger:
    """Get a logger with the specified name.
    
    This is the main entry point for getting loggers in the application.
    It returns a logger that is configured according to the application settings.
    For production use, this function will check settings and feature flags.
    
    Args:
        name: Logger name
        
    Returns:
        Configured logger instance with context adapter
    """
    # Default configuration values
    log_level = "INFO"
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    log_file = None
    matplotlib_level = "WARNING"
    
    # Try to get configuration from settings if available
    try:
        settings = get_settings()
        log_level = settings.logging.level
        log_format = settings.logging.format
        matplotlib_level = settings.logging.matplotlib_level
        
        # Configure logger with file if feature enabled
        if is_feature_enabled("enable_logging_to_file"):
            logs_dir = settings.directories.logs_directory
            log_file = logs_dir / f"{name}.log"
    except Exception:
        # If any error occurs with settings or feature flags,
        # we'll use the default values defined above
        pass
        
    # Configure matplotlib logger
    matplotlib_logger = logging.getLogger("matplotlib")
    matplotlib_logger.setLevel(get_log_level(matplotlib_level))
    
    # Configure the main logger
    logger = configure_logger(
        name=name,
        log_level=log_level,
        log_format=log_format,
        log_file=log_file,
    )
    
    # Create context adapter
    if not hasattr(logger, "context"):
        logger.context = {}  # type: ignore
        
    return ContextAdapter(logger, {})
