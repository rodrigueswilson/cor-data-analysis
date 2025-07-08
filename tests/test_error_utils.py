"""Tests for error handling utilities."""

import unittest
from unittest import mock

import pytest

from cor_data_analysis.utils.errors import (
    ApplicationError, ErrorCode, ConfigError, FileSystemError, DataError,
    ValidationError, capture_exception, safe_operation, try_except_with_default
)


class TestErrorUtils(unittest.TestCase):
    """Test error handling utility functions and classes."""
    
    def test_application_error(self):
        """Test the ApplicationError base class."""
        # Test basic error
        error = ApplicationError("Something went wrong")
        assert error.message == "Something went wrong"
        assert error.code == ErrorCode.UNKNOWN_ERROR
        assert error.details == {}
        
        # Test with custom error code
        error = ApplicationError("Invalid config", code=ErrorCode.CONFIGURATION_ERROR)
        assert error.message == "Invalid config"
        assert error.code == ErrorCode.CONFIGURATION_ERROR
        
        # Test with details
        details = {"param": "value", "reason": "missing"}
        error = ApplicationError("Data error", code=ErrorCode.DATA_FORMAT_ERROR, details=details)
        assert error.details == details
        
        # Test with cause
        cause = ValueError("Original error")
        error = ApplicationError("Wrapped error", cause=cause)
        assert error.cause == cause
        assert "ValueError" in error.details["cause_type"]
        
        # Test string representation
        assert "UNKNOWN_ERROR: Something went wrong" in str(ApplicationError("Something went wrong"))
        assert "Details:" in str(error)
    
    def test_specific_error_classes(self):
        """Test specific error subclasses."""
        # Test ConfigError
        error = ConfigError("Invalid config")
        assert error.code == ErrorCode.CONFIGURATION_ERROR
        assert "CONFIGURATION_ERROR" in str(error)
        
        # Test FileSystemError
        error = FileSystemError("File not found")
        assert error.code == ErrorCode.INVALID_PATH
        assert "INVALID_PATH" in str(error)
        
        # Test with specific code
        error = FileSystemError("Access denied", code=ErrorCode.PERMISSION_ERROR)
        assert error.code == ErrorCode.PERMISSION_ERROR
        
        # Test DataError
        error = DataError("Invalid data")
        assert error.code == ErrorCode.DATA_FORMAT_ERROR
        assert "DATA_FORMAT_ERROR" in str(error)
        
        # Test ValidationError
        errors = ["Field1 is required", "Field2 has invalid format"]
        error = ValidationError("Validation failed", errors=errors)
        assert error.code == ErrorCode.VALIDATION_ERROR
        assert "validation_errors" in error.details
        assert error.details["validation_errors"] == errors
    
    def test_capture_exception_decorator(self):
        """Test the capture_exception decorator."""
        # Test basic functionality
        @capture_exception(reraise=False, log_error=False)
        def func_with_error():
            raise ValueError("Test error")
        
        result = func_with_error()
        assert result is None
        
        # Test with specific exception type
        @capture_exception(exc_type=ValueError, reraise=False, log_error=False)
        def func_with_specific_error():
            raise ValueError("Test error")
        
        result = func_with_specific_error()
        assert result is None
        
        # Test exception type filtering
        @capture_exception(exc_type=ValueError, reraise=False, log_error=False)
        def func_with_different_error():
            raise TypeError("Test error")
        
        # Should re-raise since we're only catching ValueError
        with pytest.raises(TypeError):
            func_with_different_error()
        
        # Test with reraising
        @capture_exception(reraise=True, log_error=False)
        def func_with_reraise():
            raise ValueError("Test error")
        
        with pytest.raises(ApplicationError):
            func_with_reraise()
    
    def test_try_except_with_default(self):
        """Test the try_except_with_default decorator."""
        # Test returning default on error
        @try_except_with_default(default_value=42)
        def func_with_error():
            raise ValueError("Test error")
        
        assert func_with_error() == 42
        
        # Test normal execution
        @try_except_with_default(default_value=42)
        def func_without_error():
            return 100
        
        assert func_without_error() == 100
    
    def test_safe_operation(self):
        """Test the safe_operation decorator."""
        # Mock logger for testing
        logger_mock = mock.Mock()
        
        # Test with error
        @safe_operation(
            operation_name="test_op",
            error_message="Operation failed",
            log_level="error"
        )
        def func_with_error():
            raise ValueError("Test error")
        
        # Execute with mocked logger
        with mock.patch("cor_data_analysis.utils.errors.logger", logger_mock):
            result = func_with_error()
        
        assert result is None
        assert logger_mock.error.called
        
        # Test with fallback
        def fallback_func():
            return "fallback"
        
        @safe_operation(
            operation_name="test_op",
            error_message="Operation failed",
            fallback=fallback_func,
            log_level="warning"
        )
        def func_with_fallback():
            raise ValueError("Test error")
        
        # Reset mock
        logger_mock.reset_mock()
        
        # Execute with mocked logger
        with mock.patch("cor_data_analysis.utils.errors.logger", logger_mock):
            result = func_with_fallback()
        
        assert result == "fallback"
        assert logger_mock.warning.called
