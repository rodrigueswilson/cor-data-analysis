"""
Error utilities for COR Data Analysis.

This module provides utilities for error handling and reporting.
"""

import functools
import logging
import traceback
from typing import Any, Callable, TypeVar, cast

T = TypeVar('T')

def capture_exception(func: Callable[..., T]) -> Callable[..., T]:
    """
    Decorator to capture exceptions and log them.
    
    Args:
        func: The function to decorate
        
    Returns:
        Wrapped function that catches and logs exceptions
    """
    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> T:
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger = logging.getLogger(func.__module__)
            logger.error(f"Error in {func.__name__}: {e}")
            logger.debug(traceback.format_exc())
            raise
    
    return cast(Callable[..., T], wrapper)


def safe_execute(default_value: Any = None) -> Callable:
    """
    Decorator to safely execute a function and return a default value on exception.
    
    Args:
        default_value: Value to return if an exception occurs
        
    Returns:
        Decorator function
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger = logging.getLogger(func.__module__)
                logger.warning(f"Error in {func.__name__}: {e}")
                logger.debug(traceback.format_exc())
                return default_value
        
        return wrapper
    
    return decorator
