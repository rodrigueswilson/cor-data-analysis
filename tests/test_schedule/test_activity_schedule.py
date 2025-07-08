"""
Tests for the new ActivitySchedule implementation.

This test file uses pytest conventions and fixtures for testing the
core functionality of the ActivitySchedule class.
"""

import pytest
from datetime import date, datetime, time
from pathlib import Path
import yaml

from cor_data_analysis.data.schedule.activity_schedule import ActivitySchedule, Activity, SchedulePeriod


@pytest.fixture
def sample_schedule_data():
    """Return sample activity schedule data for testing."""
    return {
        "activities": [
            {"name": "Reading", "description": "Reading time"},
            {"name": "Math", "description": "Math exercises"}
        ],
        "periods": [
            {
                "name": "Morning Session", 
                "start_date": "2023-09-01", 
                "end_date": "2023-12-20"
            },
            {
                "name": "Afternoon Session", 
                "start_date": "2024-01-05", 
                "end_date": "2024-05-30",
                "activities": ["Math"]
            }
        ],
        "daily_schedule": {
            "2023-09-05": {
                "09:00": "Reading",
                "13:00": "Math"
            }
        }
    }


@pytest.fixture
def schedule_file(tmp_path, sample_schedule_data):
    """Create a temporary YAML file with sample schedule data."""
    schedule_path = tmp_path / "activity_schedule.yaml"
    
    with open(schedule_path, 'w') as f:
        yaml.dump(sample_schedule_data, f)
    
    return schedule_path


@pytest.fixture
def activity_schedule(schedule_file):
    """Create an ActivitySchedule instance for testing."""
    return ActivitySchedule.from_yaml(schedule_file)


def test_activity_initialization():
    """Test that Activity instances can be created correctly."""
    activity = Activity(name="Reading", description="Reading time")
    
    assert activity.name == "Reading"
    assert activity.description == "Reading time"
    assert str(activity) == "Reading"


def test_schedule_period_initialization():
    """Test that SchedulePeriod instances can be created correctly."""
    period = SchedulePeriod(
        name="Morning Session",
        start_date=date(2023, 9, 1),
        end_date=date(2023, 12, 20)
    )
    
    assert period.name == "Morning Session"
    assert period.start_date == date(2023, 9, 1)
    assert period.end_date == date(2023, 12, 20)
    assert period.contains_date(date(2023, 10, 15))
    assert not period.contains_date(date(2023, 8, 15))


def test_schedule_from_yaml(activity_schedule):
    """Test loading an ActivitySchedule from a YAML file."""
    # Check default activities
    assert len(activity_schedule.default_activities) == 2
    assert activity_schedule.default_activities[0].name == "Reading"
    assert activity_schedule.default_activities[1].name == "Math"
    
    # Check schedule periods
    assert len(activity_schedule.schedule_periods) == 2
    assert activity_schedule.schedule_periods[0].name == "Morning Session"
    assert activity_schedule.schedule_periods[1].name == "Afternoon Session"
    
    # Check period activities
    assert "Afternoon Session" in activity_schedule.period_activities
    assert len(activity_schedule.period_activities["Afternoon Session"]) == 1
    assert activity_schedule.period_activities["Afternoon Session"][0].name == "Math"
    
    # Check daily schedule
    test_date = date(2023, 9, 5)
    assert test_date in activity_schedule.activities_by_date
    assert time(9, 0) in activity_schedule.activities_by_date[test_date]
    assert time(13, 0) in activity_schedule.activities_by_date[test_date]


def test_get_activity_for_datetime(activity_schedule):
    """Test retrieving activities for specific datetimes."""
    # Test exact datetime match
    dt = datetime(2023, 9, 5, 9, 0)
    activity = activity_schedule.get_activity_for_datetime(dt)
    assert activity is not None
    assert activity.name == "Reading"
    
    # Test time-based matching (should get the previous activity)
    dt = datetime(2023, 9, 5, 11, 0)  # Between 9am and 1pm
    activity = activity_schedule.get_activity_for_datetime(dt)
    assert activity is not None
    assert activity.name == "Reading"
    
    # Test period-based matching
    dt = datetime(2024, 2, 15, 10, 0)  # In Afternoon Session
    activity = activity_schedule.get_activity_for_datetime(dt)
    assert activity is not None
    assert activity.name == "Math"
    
    # Test default activity
    dt = datetime(2023, 8, 1, 10, 0)  # No specific schedule
    activity = activity_schedule.get_activity_for_datetime(dt)
    assert activity is not None
    assert activity.name == "Reading"  # First default activity


def test_find_period_for_date(activity_schedule):
    """Test finding the schedule period for a specific date."""
    # Test date in first period
    d = date(2023, 10, 15)
    period = activity_schedule.find_period_for_date(d)
    assert period is not None
    assert period.name == "Morning Session"
    
    # Test date in second period
    d = date(2024, 2, 15)
    period = activity_schedule.find_period_for_date(d)
    assert period is not None
    assert period.name == "Afternoon Session"
    
    # Test date not in any period
    d = date(2023, 8, 1)
    period = activity_schedule.find_period_for_date(d)
    assert period is None
