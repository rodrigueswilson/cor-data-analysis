"""Utilities package for COR Data Analysis.

This module provides shared utility functions and classes,
including logging, file operations, date/time utilities, error handling,
and formatting helpers.
"""

# Logging utilities
from cor_data_analysis.utils.logging import get_logger, LoggingContext

# File system utilities
from cor_data_analysis.utils.fs import (
    ensure_directory, safe_filename, list_files, safe_delete, safe_copy,
    batch_process_files, create_temp_directory, file_size_format
)

# Date and time utilities
from cor_data_analysis.utils.dt import (
    get_month_name, get_month_abbr, parse_date, format_date,
    get_month_start_end, date_range, get_quarter_for_month,
    is_business_day, add_business_days, months_between
)

# Error handling utilities
from cor_data_analysis.utils.errors import (
    ApplicationError, ErrorCode, ConfigError, FileSystemError, DataError,
    ValidationError, capture_exception, safe_operation, try_except_with_default
)

# Formatting utilities
from cor_data_analysis.utils.formatting import (
    format_number, format_percentage, format_currency, format_list,
    truncate_text, format_table, camel_to_snake, snake_to_camel,
    format_phone_number, format_file_size, format_title, format_filename
)

__all__ = [
    # Logging
    "get_logger",
    "LoggingContext",
    
    # File system
    "ensure_directory",
    "safe_filename",
    "list_files",
    "safe_delete",
    "safe_copy",
    "batch_process_files",
    "create_temp_directory",
    "file_size_format",
    
    # Date and time
    "get_month_name",
    "get_month_abbr",
    "parse_date",
    "format_date",
    "get_month_start_end",
    "date_range",
    "get_quarter_for_month",
    "is_business_day",
    "add_business_days",
    "months_between",
    
    # Error handling
    "ApplicationError",
    "ErrorCode",
    "ConfigError",
    "FileSystemError",
    "DataError",
    "ValidationError",
    "capture_exception",
    "safe_operation",
    "try_except_with_default",
    
    # Formatting
    "format_number",
    "format_percentage",
    "format_currency",
    "format_list",
    "truncate_text",
    "format_table",
    "camel_to_snake",
    "snake_to_camel",
    "format_phone_number",
    "format_file_size",
    "format_title",
    "format_filename",
]
