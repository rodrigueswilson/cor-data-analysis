"""
Activity Schedule Module

This module provides classes for managing activity schedules, periods,
and mapping date/time values to appropriate activities.

This is a new implementation designed to address pytest compatibility issues.
"""

from dataclasses import dataclass, field
from datetime import date, datetime, time
from typing import Dict, List, Optional, Any, Union
import yaml
from pathlib import Path
import pandas as pd
import logging


@dataclass
class Activity:
    """
    Represents a scheduled activity.
    
    Activities are the core building blocks of the schedule and can be
    assigned to specific time periods or used as defaults.
    """
    name: str
    category: str = "Unknown"
    description: str = ""
    
    def __str__(self) -> str:
        return self.name


@dataclass
class SchedulePeriod:
    """
    Represents a period in the activity schedule.
    
    Periods define date ranges that can have specific activities associated with them.
    """
    name: str
    start_date: date
    end_date: date
    
    def contains_date(self, d: date) -> bool:
        """Check if this period contains the given date."""
        return self.start_date <= d <= self.end_date
    
    def __str__(self) -> str:
        return f"{self.name} ({self.start_date} to {self.end_date})"


class ActivitySchedule:
    """
    Manages activities scheduled on specific dates.
    
    This class provides functionality to:
    1. Load activity schedules from YAML configuration
    2. Map datetime objects to specific activities
    3. Handle period-based activity assignments
    """
    
    def __init__(self):
        """Initialize an empty activity schedule."""
        self.schedule_periods: List[SchedulePeriod] = []
        self.default_activities: List[Activity] = []
        self.period_activities: Dict[str, List[Activity]] = {}
        self.activities_by_date: Dict[date, Dict[time, Activity]] = {}
        
    @classmethod
    def from_dict(cls, config: Dict[str, Any]) -> 'ActivitySchedule':
        """Create an ActivitySchedule from a configuration dictionary."""
        schedule = cls()
        
        # Load defined activities
        activities = {}
        for act_data in config.get('activities', []):
            activity = Activity(
                name=act_data['name'],
                category=act_data.get('category', 'Academic'),  # Default to Academic if not specified
                description=act_data.get('description', '')
            )
            activities[activity.name] = activity
            schedule.default_activities.append(activity)
        
        # Load schedule periods
        for period_data in config.get('periods', []):
            period = SchedulePeriod(
                name=period_data['name'],
                start_date=pd.to_datetime(period_data['start_date']).date(),
                end_date=pd.to_datetime(period_data['end_date']).date()
            )
            schedule.schedule_periods.append(period)
            
            # Associate activities with periods if specified
            if 'activities' in period_data:
                period_activities = []
                for act_name in period_data['activities']:
                    if act_name in activities:
                        period_activities.append(activities[act_name])
                    else:
                        logging.warning(f"Activity '{act_name}' referenced in period '{period.name}' but not defined")
                schedule.period_activities[period.name] = period_activities
        
        # Load date-specific activities if present
        for date_str, daily_acts in config.get('daily_schedule', {}).items():
            try:
                schedule_date = pd.to_datetime(date_str).date()
                daily_dict = {}
                
                for time_str, act_name in daily_acts.items():
                    try:
                        schedule_time = pd.to_datetime(time_str).time()
                        if act_name in activities:
                            daily_dict[schedule_time] = activities[act_name]
                    except Exception as e:
                        logging.error(f"Error parsing time '{time_str}': {e}")
                
                schedule.activities_by_date[schedule_date] = daily_dict
                
            except Exception as e:
                logging.error(f"Error parsing date '{date_str}': {e}")
        
        return schedule
        
    @classmethod
    def from_yaml(cls, yaml_path: Union[str, Path]) -> 'ActivitySchedule':
        """Load an ActivitySchedule from a YAML file."""
        with open(yaml_path, 'r') as f:
            config = yaml.safe_load(f)
        
        if not isinstance(config, dict):
            raise ValueError(f"Invalid schedule YAML format in {yaml_path}")
            
        return cls.from_dict(config)
        
    def get_activity_for_datetime(self, dt: datetime) -> Optional[Activity]:
        """
        Get the activity scheduled for the given datetime.
        
        This method checks:
        1. If there's a specific activity for this exact date and time
        2. If there's an activity for the period containing this date
        3. Returns the default activity if no specific one is found
        """
        if not dt:
            return None
            
        # Check for date-specific activity
        d = dt.date()
        t = dt.time()
        
        if d in self.activities_by_date:
            # Find the closest time that's earlier than the target time
            time_dict = self.activities_by_date[d]
            closest_time = None
            
            for schedule_time in sorted(time_dict.keys()):
                if schedule_time <= t:
                    closest_time = schedule_time
                else:
                    break
                    
            if closest_time is not None:
                return time_dict[closest_time]
        
        # Check for period-specific activity
        for period in self.schedule_periods:
            if period.contains_date(d) and period.name in self.period_activities:
                period_acts = self.period_activities[period.name]
                if period_acts:
                    return period_acts[0]  # Return first activity for this period
        
        # Return default activity if available
        return self.default_activities[0] if self.default_activities else None
        
    def get_activity_name_for_datetime(self, dt: datetime) -> Optional[str]:
        """Get the name of the activity scheduled for the given datetime."""
        activity = self.get_activity_for_datetime(dt)
        return activity.name if activity else None
        
    def find_period_for_date(self, d: date) -> Optional[SchedulePeriod]:
        """Find the schedule period that contains the given date."""
        for period in self.schedule_periods:
            if period.contains_date(d):
                return period
        return None
