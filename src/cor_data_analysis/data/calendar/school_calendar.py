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
class CollectionPeriod:
    """Represents a data collection period within a school year."""
    name: str
    start_date: date
    end_date: date
    color: str = "#FFFFFF"  # Display color for visualizations
    
    @classmethod
    def from_dict(cls, name: str, data: Dict[str, Any]) -> 'CollectionPeriod':
        """Create a CollectionPeriod from a name and dictionary."""
        return cls(
            name=name,
            start_date=pd.to_datetime(data['start_date']).date(),
            end_date=pd.to_datetime(data['end_date']).date(),
            color=data.get('color', "#FFFFFF")
        )
    
    def contains_date(self, d: date) -> bool:
        """Check if this period contains the given date."""
        return self.start_date <= d <= self.end_date


@dataclass
class SchoolYear:
    """Represents a school year with collection periods and special days."""
    name: str
    start_date: date
    end_date: date
    periods: Dict[str, CollectionPeriod]
    holidays: Set[date]
    professional_development_days: Set[date]
    virtual_days: Set[date]
    
    @classmethod
    def from_dict(cls, name: str, data: Dict[str, Any]) -> 'SchoolYear':
        """Create a SchoolYear from a name and dictionary."""
        # Parse basic year info
        start_date = pd.to_datetime(data['start_date']).date()
        end_date = pd.to_datetime(data['end_date']).date()
        
        # Parse collection periods
        periods = {}
        for period_name, period_data in data.get('periods', {}).items():
            periods[period_name] = CollectionPeriod.from_dict(period_name, period_data)
        
        # Parse special days
        holidays = {pd.to_datetime(d).date() for d in data.get('holidays', [])}
        pd_days = {pd.to_datetime(d).date() for d in data.get('professional_development_days', [])}
        virtual_days = {pd.to_datetime(d).date() for d in data.get('virtual_days', [])}
        
        return cls(
            name=name,
            start_date=start_date,
            end_date=end_date,
            periods=periods,
            holidays=holidays,
            professional_development_days=pd_days,
            virtual_days=virtual_days
        )


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
        
        for year_name, year_data in config_dict.get('school_years', {}).items():
            try:
                school_year = SchoolYear.from_dict(year_name, year_data)
                calendar.school_years[year_name] = school_year
            except Exception as e:
                logging.error(f"Error parsing school year {year_name}: {e}")
                continue
                
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
    
    def find_period_for_date(self, d: date) -> Optional[CollectionPeriod]:
        """Find the collection period that contains the given date."""
        school_year = self.find_school_year_for_date(d)
        if not school_year:
            return None
            
        for period in school_year.periods.values():
            if period.contains_date(d):
                return period
                
        return None
    
    def get_period_name(self, d: date) -> str:
        """Get the period name for a specific date."""
        period = self.find_period_for_date(d)
        return period.name if period else "No Period"

    def get_all_periods(self) -> List[CollectionPeriod]:
        """Returns a flat list of all collection periods from all school years."""
        all_periods = []
        for year in self.school_years.values():
            all_periods.extend(year.periods.values())
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
            
        # Check if it's a special non-collection day
        if (d in school_year.holidays or 
            d in school_year.professional_development_days or
            d in school_year.virtual_days):
            return False
            
        # Check if it's within a defined collection period
        period = self.find_period_for_date(d)
        return period is not None
    
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
