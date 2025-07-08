"""Tests for date and time utilities."""

import calendar
from datetime import date, timedelta
import pytest

from cor_data_analysis.utils.dt import (
    get_month_name, get_month_abbr, parse_date, format_date, 
    get_month_start_end, date_range, get_quarter_for_month,
    get_quarter_months, get_quarter_start_end, is_business_day,
    add_business_days, months_between, first_day_of_month,
    last_day_of_month, parse_month_year
)


class TestDateTimeUtils:
    """Test date and time utility functions."""
    
    def test_get_month_name(self):
        """Test getting month names."""
        assert get_month_name(1) == "January"
        assert get_month_name(12) == "December"
        
        # Test invalid month numbers
        with pytest.raises(ValueError):
            get_month_name(0)
        with pytest.raises(ValueError):
            get_month_name(13)
    
    def test_get_month_abbr(self):
        """Test getting abbreviated month names."""
        assert get_month_abbr(1) == "Jan"
        assert get_month_abbr(12) == "Dec"
        
        # Test invalid month numbers
        with pytest.raises(ValueError):
            get_month_abbr(0)
        with pytest.raises(ValueError):
            get_month_abbr(13)
    
    def test_parse_date(self, caplog):
        """Test parsing date strings."""
        # Test various formats
        assert parse_date("2023-07-15") == date(2023, 7, 15)
        assert parse_date("15/07/2023") == date(2023, 7, 15)
        assert parse_date("07/15/2023") == date(2023, 7, 15)
        assert parse_date("2023.07.15") == date(2023, 7, 15)

        # Test with specific formats
        assert parse_date("15-07-2023", formats=["%d-%m-%Y"]) == date(2023, 7, 15)

        # Test invalid date and check for warning
        assert parse_date("invalid-date") is None
        assert "Could not parse date string: invalid-date" in caplog.text
    
    def test_format_date(self):
        """Test formatting date objects."""
        test_date = date(2023, 7, 15)
        
        assert format_date(test_date) == "2023-07-15"
        assert format_date(test_date, fmt="%d/%m/%Y") == "15/07/2023"
        assert format_date(test_date, fmt="%B %d, %Y") == "July 15, 2023"
    
    def test_get_month_start_end(self):
        """Test getting the start and end dates of a month."""
        # Test January
        start, end = get_month_start_end(2023, 1)
        assert start == date(2023, 1, 1)
        assert end == date(2023, 1, 31)
        
        # Test February in a leap year
        start, end = get_month_start_end(2020, 2)
        assert start == date(2020, 2, 1)
        assert end == date(2020, 2, 29)
        
        # Test February in a non-leap year
        start, end = get_month_start_end(2023, 2)
        assert start == date(2023, 2, 1)
        assert end == date(2023, 2, 28)
        
        # Test December
        start, end = get_month_start_end(2023, 12)
        assert start == date(2023, 12, 1)
        assert end == date(2023, 12, 31)
        
        # Test invalid month
        with pytest.raises(ValueError):
            get_month_start_end(2023, 13)
    
    def test_date_range(self):
        """Test generating a range of dates."""
        # Test single day
        start = date(2023, 7, 15)
        end = date(2023, 7, 15)
        dates = date_range(start, end)
        assert len(dates) == 1
        assert dates[0] == start
        
        # Test multiple days
        start = date(2023, 7, 15)
        end = date(2023, 7, 20)
        dates = date_range(start, end)
        assert len(dates) == 6
        assert dates[0] == start
        assert dates[-1] == end
        
        # Test invalid range (end before start)
        start = date(2023, 7, 20)
        end = date(2023, 7, 15)
        with pytest.raises(ValueError):
            date_range(start, end)
    
    def test_get_quarter_for_month(self):
        """Test getting quarter number for a month."""
        assert get_quarter_for_month(1) == 1
        assert get_quarter_for_month(3) == 1
        assert get_quarter_for_month(4) == 2
        assert get_quarter_for_month(6) == 2
        assert get_quarter_for_month(7) == 3
        assert get_quarter_for_month(9) == 3
        assert get_quarter_for_month(10) == 4
        assert get_quarter_for_month(12) == 4
        
        # Test invalid month
        with pytest.raises(ValueError):
            get_quarter_for_month(13)
    
    def test_get_quarter_months(self):
        """Test getting months in a quarter."""
        assert get_quarter_months(1) == [1, 2, 3]
        assert get_quarter_months(2) == [4, 5, 6]
        assert get_quarter_months(3) == [7, 8, 9]
        assert get_quarter_months(4) == [10, 11, 12]
        
        # Test invalid quarter
        with pytest.raises(ValueError):
            get_quarter_months(5)
    
    def test_get_quarter_start_end(self):
        """Test getting start and end dates of a quarter."""
        # Test Q1
        start, end = get_quarter_start_end(2023, 1)
        assert start == date(2023, 1, 1)
        assert end == date(2023, 3, 31)
        
        # Test Q2
        start, end = get_quarter_start_end(2023, 2)
        assert start == date(2023, 4, 1)
        assert end == date(2023, 6, 30)
        
        # Test Q3
        start, end = get_quarter_start_end(2023, 3)
        assert start == date(2023, 7, 1)
        assert end == date(2023, 9, 30)
        
        # Test Q4
        start, end = get_quarter_start_end(2023, 4)
        assert start == date(2023, 10, 1)
        assert end == date(2023, 12, 31)
        
        # Test invalid quarter
        with pytest.raises(ValueError):
            get_quarter_start_end(2023, 5)
    
    def test_is_business_day(self):
        """Test checking if a date is a business day."""
        # In Python's date.weekday(), Monday=0 and Sunday=6
        monday = date(2023, 7, 3)  # Monday (weekday=0)
        friday = date(2023, 7, 7)  # Friday (weekday=4)
        saturday = date(2023, 7, 8)  # Saturday (weekday=5)
        sunday = date(2023, 7, 9)  # Sunday (weekday=6)
        
        assert is_business_day(monday)
        assert is_business_day(friday)
        assert not is_business_day(saturday)
        assert not is_business_day(sunday)
        
        # Test with custom weekend days
        assert is_business_day(saturday, weekend_days=(6, 0))  # Saturday is a business day if we set Sunday and Monday as weekends
        assert not is_business_day(monday, weekend_days=(0, 6))  # Monday is a weekend
    
    def test_add_business_days(self):
        """Test adding business days to a date."""
        monday = date(2023, 7, 3)  # Monday
        
        # Add 1 business day (Tuesday)
        assert add_business_days(monday, 1) == date(2023, 7, 4)
        
        # Add 5 business days (next Monday)
        assert add_business_days(monday, 5) == date(2023, 7, 10)
        
        # Add 0 business days (same day)
        assert add_business_days(monday, 0) == monday
        
        # Test with custom weekend days
        # When Monday(0) is a weekend, adding 1 business day should get us to Tuesday(1)
        assert add_business_days(monday, 1, weekend_days=(0, 6)) == date(2023, 7, 4)  # Skip Monday (the starting day)
        
        # Test invalid number of days
        with pytest.raises(ValueError):
            add_business_days(monday, -1)
    
    def test_months_between(self):
        """Test calculating months between dates."""
        # Same month
        start = date(2023, 7, 15)
        end = date(2023, 7, 30)
        assert months_between(start, end) == 1
        assert months_between(start, end, inclusive=False) == 0
        
        # Different months, same year
        start = date(2023, 7, 15)
        end = date(2023, 9, 10)
        assert months_between(start, end) == 3
        assert months_between(start, end, inclusive=False) == 2
        
        # Different years
        start = date(2023, 11, 15)
        end = date(2024, 2, 10)
        assert months_between(start, end) == 4
        assert months_between(start, end, inclusive=False) == 3
        
        # Invalid range (end before start)
        start = date(2023, 7, 20)
        end = date(2023, 7, 15)
        with pytest.raises(ValueError):
            months_between(start, end)
    
    def test_first_day_of_month(self):
        """Test getting the first day of a month."""
        assert first_day_of_month(2023, 1) == date(2023, 1, 1)
        assert first_day_of_month(2023, 12) == date(2023, 12, 1)
        
        # Test invalid month
        with pytest.raises(ValueError):
            first_day_of_month(2023, 13)
    
    def test_last_day_of_month(self):
        """Test getting the last day of a month."""
        assert last_day_of_month(2023, 1) == date(2023, 1, 31)
        assert last_day_of_month(2023, 2) == date(2023, 2, 28)
        assert last_day_of_month(2020, 2) == date(2020, 2, 29)  # Leap year
        assert last_day_of_month(2023, 4) == date(2023, 4, 30)
        assert last_day_of_month(2023, 12) == date(2023, 12, 31)
        
        # Test invalid month
        with pytest.raises(ValueError):
            last_day_of_month(2023, 13)
    
    def test_parse_month_year(self):
        """Test parsing month and year from a string."""
        # Test full month names
        assert parse_month_year("January 2023") == (1, 2023)
        assert parse_month_year("December 2023") == (12, 2023)
        
        # Test abbreviated month names
        assert parse_month_year("Jan 2023") == (1, 2023)
        assert parse_month_year("Dec 2023") == (12, 2023)
        
        # Test case insensitivity
        assert parse_month_year("january 2023") == (1, 2023)
        assert parse_month_year("JANUARY 2023") == (1, 2023)
        
        # Test invalid formats
        assert parse_month_year("2023 January") == (None, None)
        assert parse_month_year("Invalid 2023") == (None, 2023)
        assert parse_month_year("January Invalid") == (1, None)
