"""Date and time utilities for COR Data Analysis.

This module provides helper functions for working with dates, times, and
calendar periods, including formatting, parsing, and calculations.
"""

import calendar
import datetime
from datetime import date, datetime, time, timedelta
from typing import Dict, List, Optional, Tuple, Union

from cor_data_analysis.utils.logging import get_logger

logger = get_logger(__name__)


def get_month_name(month: int) -> str:
    """Get the full name of a month from its number.
    
    Args:
        month: Month number (1-12)
        
    Returns:
        Full month name
        
    Raises:
        ValueError: If month is not between 1 and 12
    """
    if not 1 <= month <= 12:
        raise ValueError(f"Month must be between 1 and 12, got {month}")
    
    return calendar.month_name[month]


def get_month_abbr(month: int) -> str:
    """Get the abbreviated name of a month from its number.
    
    Args:
        month: Month number (1-12)
        
    Returns:
        Abbreviated month name
        
    Raises:
        ValueError: If month is not between 1 and 12
    """
    if not 1 <= month <= 12:
        raise ValueError(f"Month must be between 1 and 12, got {month}")
    
    return calendar.month_abbr[month]


def parse_date(date_str: str, formats: Optional[List[str]] = None) -> Optional[date]:
    """Parse a date string into a date object.
    
    Args:
        date_str: Date string to parse
        formats: List of format strings to try, defaults to common formats
        
    Returns:
        Date object if parsing succeeded, None otherwise
    """
    if formats is None:
        formats = [
            '%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y', 
            '%d-%m-%Y', '%m-%d-%Y', '%d.%m.%Y', 
            '%Y/%m/%d', '%Y.%m.%d'
        ]
    
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt).date()
        except ValueError:
            continue
            
    logger.warning(f"Could not parse date string: {date_str}")
    return None


def format_date(date_obj: date, fmt: str = '%Y-%m-%d') -> str:
    """Format a date object to a string.
    
    Args:
        date_obj: Date object to format
        fmt: Format string
        
    Returns:
        Formatted date string
    """
    return date_obj.strftime(fmt)


def get_month_start_end(year: int, month: int) -> Tuple[date, date]:
    """Get the first and last day of a month.
    
    Args:
        year: Year number
        month: Month number (1-12)
        
    Returns:
        Tuple of (first day, last day)
        
    Raises:
        ValueError: If month is not between 1 and 12
    """
    if not 1 <= month <= 12:
        raise ValueError(f"Month must be between 1 and 12, got {month}")
    
    start_date = date(year, month, 1)
    # Get the last day by getting the first day of next month and subtracting 1 day
    if month == 12:
        end_date = date(year + 1, 1, 1) - timedelta(days=1)
    else:
        end_date = date(year, month + 1, 1) - timedelta(days=1)
    
    return start_date, end_date


def date_range(start_date: date, end_date: date) -> List[date]:
    """Generate a list of dates between start and end inclusive.
    
    Args:
        start_date: Start date
        end_date: End date
        
    Returns:
        List of dates
        
    Raises:
        ValueError: If end_date is before start_date
    """
    if end_date < start_date:
        raise ValueError(f"End date {end_date} is before start date {start_date}")
    
    days = (end_date - start_date).days + 1
    return [start_date + timedelta(days=i) for i in range(days)]


def get_quarter_for_month(month: int) -> int:
    """Get the quarter number for a given month.
    
    Args:
        month: Month number (1-12)
        
    Returns:
        Quarter number (1-4)
        
    Raises:
        ValueError: If month is not between 1 and 12
    """
    if not 1 <= month <= 12:
        raise ValueError(f"Month must be between 1 and 12, got {month}")
    
    return (month - 1) // 3 + 1


def get_quarter_months(quarter: int) -> List[int]:
    """Get the months in a given quarter.
    
    Args:
        quarter: Quarter number (1-4)
        
    Returns:
        List of month numbers
        
    Raises:
        ValueError: If quarter is not between 1 and 4
    """
    if not 1 <= quarter <= 4:
        raise ValueError(f"Quarter must be between 1 and 4, got {quarter}")
    
    start_month = (quarter - 1) * 3 + 1
    return [start_month, start_month + 1, start_month + 2]


def get_quarter_start_end(year: int, quarter: int) -> Tuple[date, date]:
    """Get the first and last day of a quarter.
    
    Args:
        year: Year number
        quarter: Quarter number (1-4)
        
    Returns:
        Tuple of (first day, last day)
        
    Raises:
        ValueError: If quarter is not between 1 and 4
    """
    if not 1 <= quarter <= 4:
        raise ValueError(f"Quarter must be between 1 and 4, got {quarter}")
    
    months = get_quarter_months(quarter)
    start_date = date(year, months[0], 1)
    
    if quarter == 4:
        end_date = date(year + 1, 1, 1) - timedelta(days=1)
    else:
        end_date = date(year, months[-1] + 1, 1) - timedelta(days=1)
    
    return start_date, end_date


def is_business_day(date_obj: date, weekend_days: Tuple[int, int] = (5, 6)) -> bool:
    """Check if a date is a business day (not weekend).
    
    Args:
        date_obj: Date to check
        weekend_days: Tuple of weekday numbers (0=Monday, 6=Sunday)
        
    Returns:
        True if business day, False otherwise
    """
    return date_obj.weekday() not in weekend_days


def add_business_days(date_obj: date, days: int, 
                    weekend_days: Tuple[int, int] = (5, 6)) -> date:
    """Add a given number of business days to a date.
    
    Args:
        date_obj: Starting date
        days: Number of business days to add
        weekend_days: Tuple of weekday numbers (0=Monday, 6=Sunday)
        
    Returns:
        New date after adding business days
    """
    if days < 0:
        raise ValueError(f"Number of days must be non-negative, got {days}")
    
    result = date_obj
    added = 0
    
    while added < days:
        result += timedelta(days=1)
        if result.weekday() not in weekend_days:
            added += 1
            
    return result


def months_between(start_date: date, end_date: date, inclusive: bool = True) -> int:
    """Calculate the number of months between two dates.
    
    Args:
        start_date: Start date
        end_date: End date
        inclusive: Whether to include both start and end months
        
    Returns:
        Number of months
        
    Raises:
        ValueError: If end_date is before start_date
    """
    if end_date < start_date:
        raise ValueError(f"End date {end_date} is before start date {start_date}")
    
    year_diff = end_date.year - start_date.year
    month_diff = end_date.month - start_date.month
    
    result = year_diff * 12 + month_diff
    
    if inclusive:
        result += 1
        
    return result


def first_day_of_month(year: int, month: int) -> date:
    """Get the first day of a month.
    
    Args:
        year: Year number
        month: Month number (1-12)
        
    Returns:
        Date object for first day
        
    Raises:
        ValueError: If month is not between 1 and 12
    """
    if not 1 <= month <= 12:
        raise ValueError(f"Month must be between 1 and 12, got {month}")
    
    return date(year, month, 1)


def last_day_of_month(year: int, month: int) -> date:
    """Get the last day of a month.
    
    Args:
        year: Year number
        month: Month number (1-12)
        
    Returns:
        Date object for last day
        
    Raises:
        ValueError: If month is not between 1 and 12
    """
    if not 1 <= month <= 12:
        raise ValueError(f"Month must be between 1 and 12, got {month}")
    
    if month == 12:
        return date(year + 1, 1, 1) - timedelta(days=1)
    else:
        return date(year, month + 1, 1) - timedelta(days=1)


def parse_month_year(month_year_str: str) -> Tuple[Optional[int], Optional[int]]:
    """Parse a month and year from a string like 'January 2023' or 'Jan 2023'.
    
    Args:
        month_year_str: String to parse
        
    Returns:
        Tuple of (month, year), with None for any part that couldn't be parsed
    """
    month_names = {
        m.lower(): i for i, m in enumerate(calendar.month_name) if m
    }
    
    month_abbrs = {
        m.lower(): i for i, m in enumerate(calendar.month_abbr) if m
    }
    
    parts = month_year_str.strip().split()
    if len(parts) != 2:
        logger.warning(f"Could not parse month and year from: {month_year_str}")
        return None, None
    
    month_part, year_part = parts
    
    # Try to parse month
    month = None
    month_part_lower = month_part.lower()
    if month_part_lower in month_names:
        month = month_names[month_part_lower]
    elif month_part_lower in month_abbrs:
        month = month_abbrs[month_part_lower]
    
    # Try to parse year
    year = None
    try:
        year = int(year_part)
    except ValueError:
        pass
    
    if month is None:
        logger.warning(f"Could not parse month from: {month_part}")
    if year is None:
        logger.warning(f"Could not parse year from: {year_part}")
    
    return month, year
