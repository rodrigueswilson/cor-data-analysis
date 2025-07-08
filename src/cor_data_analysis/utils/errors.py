"""Error handling utilities for COR Data Analysis.

This module provides a consistent error handling framework,
including custom exception classes, error codes, and recovery mechanisms.
"""

import sys
import traceback
from enum import Enum, auto
from typing import Any, Callable, Dict, List, Optional, Type, TypeVar, cast

from cor_data_analysis.utils.logging import get_logger

logger = get_logger(__name__)

# Generic type for function return values
T = TypeVar('T')


class ErrorCode(Enum):
    """Enumeration of error codes used in the application."""
    
    # General errors
    UNKNOWN_ERROR = auto()
    VALIDATION_ERROR = auto()
    CONFIGURATION_ERROR = auto()
    
    # File system errors
    FILE_NOT_FOUND = auto()
    PERMISSION_ERROR = auto()
    INVALID_PATH = auto()
    
    # Data processing errors
    PARSE_ERROR = auto()
    DATA_FORMAT_ERROR = auto()
    DATA_INTEGRITY_ERROR = auto()
    
    # Operation errors
    OPERATION_TIMEOUT = auto()
    OPERATION_CANCELLED = auto()
    RESOURCE_UNAVAILABLE = auto()


class ApplicationError(Exception):
    """Base exception class for all application-specific errors."""
    
    def __init__(
        self, 
        message: str,
        code: ErrorCode = ErrorCode.UNKNOWN_ERROR,
        details: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None
    ):
        """Initialize the exception with details.
        
        Args:
            message: Error message
            code: Error code
            details: Additional details about the error
            cause: Original exception that caused this error
        """
        self.message = message
        self.code = code
        self.details = details or {}
        self.cause = cause
        
        # Include the cause in the details
        if cause:
            self.details['cause'] = str(cause)
            self.details['cause_type'] = type(cause).__name__
        
        super().__init__(self.message)
    
    def __str__(self) -> str:
        """Return string representation of the error."""
        result = f"{self.code.name}: {self.message}"
        if self.details:
            result += f" (Details: {self.details})"
        return result
    
    def log(self, include_traceback: bool = True) -> None:
        """Log this error with appropriate level and details.
        
        Args:
            include_traceback: Whether to include traceback in the log
        """
        log_message = str(self)
        
        if include_traceback:
            tb = traceback.format_exc()
            logger.error(f"{log_message}\nTraceback: {tb}")
        else:
            logger.error(log_message)


class ConfigError(ApplicationError):
    """Exception for configuration-related errors."""
    
    def __init__(
        self, 
        message: str,
        details: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None
    ):
        super().__init__(
            message,
            code=ErrorCode.CONFIGURATION_ERROR,
            details=details,
            cause=cause
        )


class FileSystemError(ApplicationError):
    """Exception for file system-related errors."""
    
    def __init__(
        self, 
        message: str,
        code: ErrorCode = ErrorCode.INVALID_PATH,
        details: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None
    ):
        super().__init__(message, code=code, details=details, cause=cause)


class DataError(ApplicationError):
    """Exception for data processing errors."""
    
    def __init__(
        self, 
        message: str,
        code: ErrorCode = ErrorCode.DATA_FORMAT_ERROR,
        details: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None
    ):
        super().__init__(message, code=code, details=details, cause=cause)


class ValidationError(ApplicationError):
    """Exception for validation errors."""
    
    def __init__(
        self, 
        message: str,
        details: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None,
        errors: Optional[List[str]] = None
    ):
        if errors:
            if not details:
                details = {}
            details['validation_errors'] = errors
            
        super().__init__(
            message,
            code=ErrorCode.VALIDATION_ERROR,
            details=details,
            cause=cause
        )


def capture_exception(
    exc_type: Optional[Type[Exception]] = None,
    reraise: bool = True,
    log_error: bool = True,
    include_traceback: bool = True
) -> Callable[[Callable[..., T]], Callable[..., Optional[T]]]:
    """Decorator to capture and handle exceptions.
    
    Args:
        exc_type: Type of exception to catch (None for all)
        reraise: Whether to re-raise the exception after handling
        log_error: Whether to log the error
        include_traceback: Whether to include traceback in the log
        
    Returns:
        Decorated function
    """
    def decorator(func: Callable[..., T]) -> Callable[..., Optional[T]]:
        def wrapper(*args: Any, **kwargs: Any) -> Optional[T]:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                # Only handle specified exception type or all if None
                if exc_type is not None and not isinstance(e, exc_type):
                    raise
                
                # Wrap in ApplicationError if it's not already
                if not isinstance(e, ApplicationError):
                    error = ApplicationError(
                        message=str(e),
                        code=ErrorCode.UNKNOWN_ERROR,
                        cause=e
                    )
                else:
                    error = cast(ApplicationError, e)
                
                # Log the error if requested
                if log_error:
                    error.log(include_traceback=include_traceback)
                
                # Re-raise if requested
                if reraise:
                    if isinstance(e, ApplicationError):
                        raise
                    else:
                        raise error
                
                return None
        
        return wrapper
    
    return decorator


def try_except_with_default(default_value: T) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """Decorator that returns a default value if the function raises an exception.
    
    Args:
        default_value: Value to return if an exception occurs
        
    Returns:
        Decorated function
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        def wrapper(*args: Any, **kwargs: Any) -> T:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger.warning(f"Error in {func.__name__}: {str(e)}, returning default value")
                return default_value
        
        return wrapper
    
    return decorator


def safe_operation(
    operation_name: str,
    error_message: str,
    fallback: Optional[Callable[..., T]] = None,
    log_level: str = "error"
) -> Callable[[Callable[..., T]], Callable[..., Optional[T]]]:
    """Decorator for operations that should be handled gracefully.
    
    Args:
        operation_name: Name of the operation for logging
        error_message: Message to log on error
        fallback: Optional fallback function to call on error
        log_level: Level to log errors at (error, warning, info)
        
    Returns:
        Decorated function
    """
    def decorator(func: Callable[..., T]) -> Callable[..., Optional[T]]:
        def wrapper(*args: Any, **kwargs: Any) -> Optional[T]:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                full_error_msg = f"{error_message}: {str(e)}"
                
                if log_level == "error":
                    logger.error(f"Error in {operation_name}: {full_error_msg}")
                elif log_level == "warning":
                    logger.warning(f"Warning in {operation_name}: {full_error_msg}")
                else:
                    logger.info(f"Info in {operation_name}: {full_error_msg}")
                
                if fallback:
                    try:
                        return fallback(*args, **kwargs)
                    except Exception as fallback_error:
                        logger.error(f"Fallback for {operation_name} also failed: {str(fallback_error)}")
                
                return None
        
        return wrapper
    
    return decorator


def get_exception_details(exc: Exception) -> Dict[str, Any]:
    """Extract useful details from an exception.
    
    Args:
        exc: Exception to analyze
        
    Returns:
        Dictionary with exception details
    """
    exc_type = type(exc)
    
    details = {
        'type': exc_type.__name__,
        'module': exc_type.__module__,
        'message': str(exc),
        'traceback': traceback.format_exc(),
    }
    
    # Add all public attributes of the exception
    for attr in dir(exc):
        if not attr.startswith('_') and attr not in ('args', 'with_traceback'):
            try:
                value = getattr(exc, attr)
                if not callable(value):
                    details[attr] = str(value)
            except Exception:
                pass
    
    return details
