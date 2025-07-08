"""
Tests for the refactored SchoolCalendar module.

These tests verify that the SchoolCalendar class correctly loads data from a YAML
file and that its core functionality (like checking for collection days)
works as expected with the new data structures.
"""

import pytest
from datetime import date
import yaml
from pathlib import Path

from cor_data_analysis.data.calendar.school_calendar import SchoolCalendar, Holiday, SpecialPeriod, SchoolYear


@pytest.fixture
def calendar_file(tmp_path: Path) -> Path:
    """Create a temporary calendar YAML file for testing."""
    config = {
        'school_year': {
            'start_date': '2023-09-01',
            'end_date': '2024-06-15'
        },
        'holidays': [
            {'name': 'Winter Break', 'start_date': '2023-12-22', 'end_date': '2024-01-05'}
        ],
        'special_periods': [
            {'name': 'Final Exams', 'start_date': '2024-06-10', 'end_date': '2024-06-14'}
        ]
    }
    
    calendar_path = tmp_path / "calendar.yaml"
    with open(calendar_path, 'w') as f:
        yaml.dump(config, f)
    
    return calendar_path


class TestSchoolCalendarFromYAML:
    """Test loading SchoolCalendar from a YAML file and its functionality."""

    def test_yaml_loading(self, calendar_file: Path):
        """Test that the calendar is loaded correctly from the YAML file."""
        calendar = SchoolCalendar.from_yaml(calendar_file)
        
        assert len(calendar.school_years) == 1
        
        year_key = "2023-2024"
        assert year_key in calendar.school_years
        
        school_year = calendar.school_years[year_key]
        assert school_year.start_date == date(2023, 9, 1)
        assert school_year.end_date == date(2024, 6, 15)
        
        # Check holidays
        assert len(school_year.holidays) == 1
        assert school_year.holidays[0].name == "Winter Break"
        assert school_year.holidays[0].start_date == date(2023, 12, 22)
        
        # Check special periods
        assert len(school_year.special_periods) == 1
        assert school_year.special_periods[0].name == "Final Exams"

    def test_is_collection_day(self, calendar_file: Path):
        """Test the is_collection_day method with the loaded calendar."""
        calendar = SchoolCalendar.from_yaml(calendar_file)
        
        # A regular school day (weekday, not a holiday)
        assert calendar.is_collection_day(date(2023, 9, 4))  # Monday
        
        # A weekend
        assert not calendar.is_collection_day(date(2023, 9, 2))  # Saturday
        
        # A day during a holiday
        assert not calendar.is_collection_day(date(2023, 12, 25))
        
        # A day outside the school year
        assert not calendar.is_collection_day(date(2023, 8, 1))
        
        # A day within a special period (should still be a collection day unless it's a weekend/holiday)
        assert calendar.is_collection_day(date(2024, 6, 10))  # Monday

    def test_find_period_for_date(self, calendar_file: Path):
        """Test finding a special period for a given date."""
        calendar = SchoolCalendar.from_yaml(calendar_file)
        
        period = calendar.find_period_for_date(date(2024, 6, 12))
        assert period is not None
        assert period.name == "Final Exams"
        
        # Test a date with no special period
        period = calendar.find_period_for_date(date(2023, 10, 10))
        assert period is None
