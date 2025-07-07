"""Tests for logging module."""

import io
import logging
import os
import tempfile
from pathlib import Path
from unittest import mock

import pytest

from cor_data_analysis.config import Settings, FeatureFlags
from cor_data_analysis.utils.logging import (
    get_log_level,
    configure_logger,
    LoggingContext,
    ContextAdapter,
    get_logger,
)


def test_get_log_level():
    """Test conversion from string log levels to logging module constants."""
    assert get_log_level("DEBUG") == logging.DEBUG
    assert get_log_level("INFO") == logging.INFO
    assert get_log_level("WARNING") == logging.WARNING
    assert get_log_level("ERROR") == logging.ERROR
    assert get_log_level("CRITICAL") == logging.CRITICAL
    
    # Test case insensitivity
    assert get_log_level("debug") == logging.DEBUG
    assert get_log_level("info") == logging.INFO
    
    # Test default for unknown levels
    assert get_log_level("UNKNOWN") == logging.INFO


def test_configure_logger_console():
    """Test configuring a logger with console output."""
    # Use explicit parameters instead of relying on config
    logger = configure_logger(
        name="test_logger",
        log_level="INFO",
        log_format="%(levelname)s: %(message)s"
    )
    
    # Check that logger was configured correctly
    assert logger.name == "test_logger"
    assert logger.level == logging.INFO
    
    # Check that a console handler was added
    assert len(logger.handlers) == 1
    assert isinstance(logger.handlers[0], logging.StreamHandler)


def test_configure_logger_with_file():
    """Test configuring a logger with file output."""
    # Mock the RotatingFileHandler to avoid actual file operations
    with mock.patch("logging.handlers.RotatingFileHandler") as mock_handler:
        # Configure logger with explicit parameters
        logger = configure_logger(
            name="test_logger",
            log_level="INFO",
            log_format="%(levelname)s: %(message)s",
            log_file="test.log"
        )
        
        # Check that logger was configured correctly
        assert logger.name == "test_logger"
        assert logger.level == logging.INFO
        
        # Check that logger has the correct handlers
        # Note: The console handler is at index 0
        assert len(logger.handlers) >= 1
        assert isinstance(logger.handlers[0], logging.StreamHandler)
        
        # Verify the mock was called at least once (for file handler)
        mock_handler.assert_called_once()


def test_logging_context():
    """Test adding context to logs."""
    logger = logging.getLogger("test_context")
    
    # Initial state: no context
    assert not hasattr(logger, "context")
    
    # Add context
    with LoggingContext(logger, user="test", action="testing"):
        # Context should be added to logger
        assert hasattr(logger, "context")
        assert logger.context == {"user": "test", "action": "testing"}
        
        # Nested context
        with LoggingContext(logger, subsystem="auth"):
            assert logger.context == {
                "user": "test", 
                "action": "testing",
                "subsystem": "auth"
            }
        
        # After nested context, should revert to original context
        assert logger.context == {"user": "test", "action": "testing"}
    
    # After context, should have no context (or empty dict if first context created it)
    if hasattr(logger, "context"):
        assert logger.context == {}


def test_context_adapter():
    """Test that context is added to log messages."""
    logger = logging.getLogger("test_adapter")
    stream = io.StringIO()
    handler = logging.StreamHandler(stream)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    
    # Set context and create adapter
    logger.context = {"user": "test", "action": "testing"}
    adapter = ContextAdapter(logger, {})
    
    # Log a message
    adapter.info("Test message")
    
    # Check that context was added to message
    output = stream.getvalue()
    assert "Test message" in output
    assert "user=test" in output
    assert "action=testing" in output


@mock.patch("cor_data_analysis.utils.logging.get_settings")
def test_get_logger(mock_get_settings):
    """Test getting a logger with the right configuration."""
    # Mock settings to disable file logging
    mock_settings = mock.MagicMock()
    mock_settings.logging.level = "INFO"
    mock_settings.logging.format = "%(message)s"
    mock_settings.logging.matplotlib_level = "WARNING"
    mock_get_settings.return_value = mock_settings
    
    # Mock feature flag to disable file logging
    with mock.patch("cor_data_analysis.utils.logging.is_feature_enabled", return_value=False):
        logger = get_logger("test")
    
    # Check that it's a ContextAdapter
    assert isinstance(logger, ContextAdapter)
    
    # Check that it has a context attribute
    assert hasattr(logger.logger, "context")
    
    # Check that only console handler is added (no file handler)
    assert len(logger.logger.handlers) == 1
    assert isinstance(logger.logger.handlers[0], logging.StreamHandler)
