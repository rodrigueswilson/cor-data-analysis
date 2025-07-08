from __future__ import annotations

"""
School Calendar Module

This module provides a flexible calendar system for managing school years,
collection periods, holidays, and non-collection days. It supports
calculations for active collection days across different time periods.
"""

from datetime import datetime, date, timedelta
from typing import Dict, List, Tuple, Optional, Any, Union, Set
import logging
import yaml
from pathlib import Path
from dataclasses import dataclass
import pandas as pd


@dataclass
class Holiday:
    """Represents a holiday or break period."""
    name: str
    start_date: date
    end_date: date

    def contains_date(self, d: date) -> bool:
        """Check if this holiday period contains the given date."""
        return self.start_date <= d <= self.end_date

@dataclass
class SpecialPeriod:
    """Represents a special period like exams or testing."""
    name: str
    start_date: date
    end_date: date

    def contains_date(self, d: date) -> bool:
        """Check if this special period contains the given date."""
        return self.start_date <= d <= self.end_date


@dataclass
class SchoolYear:
    """Represents a school year with its main dates and periods."""
    start_date: date
    end_date: date
    holidays: List[Holiday]
    special_periods: List[SpecialPeriod]


class SchoolCalendar:
    """
    Manages school years and provides calendar-related functionality
    such as identifying collection days and mapping dates to periods.
    """
    def __init__(self):
        self.school_years: Dict[str, SchoolYear] = {}
        
    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> 'SchoolCalendar':
        """Create a SchoolCalendar from a configuration dictionary."""
        calendar = cls()

        # Parse school year
        year_data = config_dict.get('school_year', {})
        if not year_data:
            raise ValueError("Configuration must contain a 'school_year' section.")

        start_date = pd.to_datetime(year_data['start_date']).date()
        end_date = pd.to_datetime(year_data['end_date']).date()

        # Parse holidays
        holidays = []
        for holiday_data in config_dict.get('holidays', []):
            holidays.append(Holiday(
                name=holiday_data['name'],
                start_date=pd.to_datetime(holiday_data['start_date']).date(),
                end_date=pd.to_datetime(holiday_data['end_date']).date()
            ))

        # Parse special periods
        special_periods = []
        for period_data in config_dict.get('special_periods', []):
            special_periods.append(SpecialPeriod(
                name=period_data['name'],
                start_date=pd.to_datetime(period_data['start_date']).date(),
                end_date=pd.to_datetime(period_data['end_date']).date()
            ))

        # Create the single SchoolYear instance for the calendar
        school_year_instance = SchoolYear(
            start_date=start_date,
            end_date=end_date,
            holidays=holidays,
            special_periods=special_periods
        )
        
        # The key for the single school year can be a generated name
        year_name = f"{start_date.year}-{end_date.year}"
        calendar.school_years[year_name] = school_year_instance

        return calendar
    
    @classmethod
    def from_yaml(cls, yaml_path: Union[str, Path]) -> 'SchoolCalendar':
        """Load a SchoolCalendar from a YAML file."""
        with open(yaml_path, 'r') as f:
            config = yaml.safe_load(f)
        
        if not isinstance(config, dict):
            raise ValueError(f"Invalid calendar YAML format in {yaml_path}")
            
        return cls.from_dict(config)
    
    def find_school_year_for_date(self, d: date) -> Optional[SchoolYear]:
        """Find the school year that contains the given date."""
        for year in self.school_years.values():
            if year.start_date <= d <= year.end_date:
                return year
        return None
    
    def find_period_for_date(self, d: date) -> Optional[SpecialPeriod]:
        """Find the special period that contains the given date."""
        school_year = self.find_school_year_for_date(d)
        if not school_year:
            return None

        for period in school_year.special_periods:
            if period.contains_date(d):
                return period
                
        return None
    
    def get_period_name(self, d: date) -> str:
        """Get the period name for a specific date."""
        period = self.find_period_for_date(d)
        return period.name if period else "No Period"

    def get_all_periods(self) -> List[SpecialPeriod]:
        """Returns a flat list of all special periods from all school years."""
        all_periods = []
        for year in self.school_years.values():
            all_periods.extend(year.special_periods)
        return all_periods
    
    def is_collection_day(self, d: date) -> bool:
        """
        Determine if a given date is a collection day.
        Collection days are weekdays that are not holidays, PD days, or virtual days.
        """
        # Check if date is within any school year
        school_year = self.find_school_year_for_date(d)
        if not school_year:
            return False
            
        # Weekends are not collection days
        if d.weekday() >= 5:  # 5=Saturday, 6=Sunday
            return False
            
        # Check if it's a holiday
        for holiday in school_year.holidays:
            if holiday.contains_date(d):
                return False
            
        # If it's not a weekend or holiday, it's a collection day
        return True
    
    def count_collection_days(self, start_date: date, end_date: date, 
                             group_by: str = 'day') -> Dict[str, Any]:
        """
        Count collection days between start_date and end_date, grouped by the specified unit.
        Supported group_by values: 'day', 'week', 'month', 'period'
        """
        if start_date > end_date:
            logging.warning(f"Start date {start_date} is after end date {end_date}, swapping.")
            start_date, end_date = end_date, start_date
        
        results: Dict[str, Any] = {}
        
        if group_by == 'day':
            # Simply count each collection day
            count = sum(1 for d in self._date_range(start_date, end_date) if self.is_collection_day(d))
            results['total_days'] = count
            
        elif group_by == 'week':
            # Group by ISO week (week 1 starts with the first week of the year)
            results['week'] = {}
            
            for d in self._date_range(start_date, end_date):
                if self.is_collection_day(d):
                    year, week, _ = d.isocalendar()
                    week_key = f"{year}-W{week:02d}"
                    
                    if week_key not in results['week']:
                        results['week'][week_key] = 0
                    results['week'][week_key] += 1
                    
        elif group_by == 'month':
            # Group by month
            results['month'] = {}
            
            for d in self._date_range(start_date, end_date):
                if self.is_collection_day(d):
                    month_key = f"{d.year}-{d.month:02d}"
                    
                    if month_key not in results['month']:
                        results['month'][month_key] = 0
                    results['month'][month_key] += 1
                    
        elif group_by == 'period':
            # Group by collection period
            results['period'] = {}
            
            for d in self._date_range(start_date, end_date):
                if self.is_collection_day(d):
                    period = self.find_period_for_date(d)
                    if period:
                        if period.name not in results['period']:
                            results['period'][period.name] = 0
                        results['period'][period.name] += 1
        else:
            logging.error(f"Unsupported group_by value: {group_by}")
            
        return results
    
    def get_collection_day_density(self, start_date: date, end_date: date) -> float:
        """
        Calculate the density of collection days in the given date range.
        Returns a value between 0.0 (no collection days) and 1.0 (all days are collection days).
        """
        if start_date > end_date:
            return 0.0
            
        total_days = (end_date - start_date).days + 1
        if total_days == 0:
            return 0.0
            
        collection_days = sum(1 for d in self._date_range(start_date, end_date) 
                             if self.is_collection_day(d))
        
        return collection_days / total_days
    
    @staticmethod
    def _date_range(start_date: date, end_date: date) -> List[date]:
        """Generate a list of dates from start_date to end_date inclusive."""
        days = (end_date - start_date).days + 1
        return [start_date + timedelta(days=i) for i in range(days)]
