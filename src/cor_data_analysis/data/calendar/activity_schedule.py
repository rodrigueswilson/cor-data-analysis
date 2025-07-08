"""
Activity Schedule Module

This module provides classes for managing classroom activity schedules with support
for mid-year schedule changes. It allows mapping timestamps to appropriate activities
based on configurable date ranges.
"""

from datetime import datetime, date, time
from typing import Dict, List, Tuple, Optional, Any, Union
import logging
import yaml
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Activity:
    """Represents a scheduled classroom activity."""
    name: str
    start_time: time
    end_time: time
    category: str = "General"
    description: str = ""
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Activity':
        """Create an Activity from a dictionary representation."""
        # Parse time strings in format "HH:MM" to time objects
        start_time_str = data.get('start_time', '00:00')
        end_time_str = data.get('end_time', '00:00')
        
        start_time = datetime.strptime(start_time_str, "%H:%M").time()
        end_time = datetime.strptime(end_time_str, "%H:%M").time()
        
        return cls(
            name=data.get('name', 'Unknown Activity'),
            start_time=start_time,
            end_time=end_time,
            category=data.get('category', 'General'),
            description=data.get('description', '')
        )
    
    def contains_time(self, t: time) -> bool:
        """Check if this activity's time range contains the given time."""
        return self.start_time <= t < self.end_time


class SchedulePeriod:
    """
    Represents a period with a specific activity schedule.
    This allows for different schedules during different parts of the school year.
    """
    def __init__(self, start_date: date, end_date: date, activities: List[Activity]):
        self.start_date = start_date
        self.end_date = end_date
        self.activities = activities
    
    @classmethod
    def from_dict(cls, date_range_key: str, activities_data: List[Dict[str, Any]]) -> 'SchedulePeriod':
        """Create a SchedulePeriod from a date range key and list of activity dictionaries."""
        start_date_str, end_date_str = date_range_key.split('_')
        start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
        end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
        
        activities = [Activity.from_dict(act) for act in activities_data]
        return cls(start_date, end_date, activities)
    
    def contains_date(self, d: date) -> bool:
        """Check if this schedule period contains the given date."""
        return self.start_date <= d <= self.end_date
    
    def get_activity_for_time(self, t: time) -> Optional[Activity]:
        """Find the activity that contains the given time."""
        for activity in self.activities:
            if activity.contains_time(t):
                return activity
        return None


class ActivitySchedule:
    """
    Manages different activity schedules that can vary by date ranges.
    Supports mid-year schedule changes and efficiently maps timestamps to activities.
    """
    def __init__(self):
        self.schedule_periods: List[SchedulePeriod] = []
        self.default_activities: List[Activity] = []
    
    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> 'ActivitySchedule':
        """Create an ActivitySchedule from a configuration dictionary."""
        schedule = cls()
        
        # Load default activities if present
        if 'default' in config_dict:
            schedule.default_activities = [
                Activity.from_dict(act) for act in config_dict['default']
            ]
        
        # Load date-specific schedules
        for date_range_key, activities_data in config_dict.items():
            if date_range_key == 'default':
                continue
                
            try:
                schedule_period = SchedulePeriod.from_dict(date_range_key, activities_data)
                schedule.schedule_periods.append(schedule_period)
            except ValueError as e:
                logging.error(f"Error parsing schedule for date range {date_range_key}: {e}")
                continue
                
        return schedule
    
    @classmethod
    def from_yaml(cls, yaml_path: Union[str, Path]) -> 'ActivitySchedule':
        """Load an ActivitySchedule from a YAML file."""
        with open(yaml_path, 'r') as f:
            config = yaml.safe_load(f)
        
        if not isinstance(config, dict) or 'activity_schedules' not in config:
            raise ValueError(f"Invalid schedule YAML format in {yaml_path}")
            
        return cls.from_dict(config['activity_schedules'])
    
    def find_schedule_for_date(self, d: date) -> List[Activity]:
        """Find the appropriate activity schedule for the given date."""
        for period in self.schedule_periods:
            if period.contains_date(d):
                return period.activities
        
        # Fall back to default schedule if no specific period matches
        if self.default_activities:
            return self.default_activities
            
        # If no default either, return empty list
        logging.warning(f"No schedule found for date {d}")
        return []
    
    def get_activity_for_datetime(self, dt: datetime) -> Optional[Activity]:
        """Get the activity for a specific datetime."""
        activities = self.find_schedule_for_date(dt.date())
        
        for activity in activities:
            if activity.contains_time(dt.time()):
                return activity
                
        return None
    
    def get_activity_name_for_datetime(self, dt: datetime) -> str:
        """Get the activity name for a specific datetime."""
        activity = self.get_activity_for_datetime(dt)
        return activity.name if activity else "No Activity Scheduled"
    
    def get_activity_for_time(self, hour: int, minute: int, d: Optional[date] = None) -> Optional[str]:
        """
        Legacy compatibility method to get activity name for a specific time.
        If date is not provided, uses the default activities.
        """
        t = time(hour=hour, minute=minute)
        
        if d is None:
            # Use default activities if no date provided
            activities = self.default_activities
        else:
            activities = self.find_schedule_for_date(d)
            
        for activity in activities:
            if activity.contains_time(t):
                return activity.name
                
        return None
