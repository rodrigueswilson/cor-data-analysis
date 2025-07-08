"""
Tests for the new ActivitySchedule module implementation.

This test file uses pytest conventions and fixtures for testing the
core functionality of the ActivitySchedule class.
"""

import pytest
from datetime import date, datetime
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
            }
        ]
    }


@pytest.fixture
def schedule_file(tmp_path, sample_schedule_data):
    """Create a temporary YAML file with sample schedule data."""
    schedule_path = tmp_path / "activity_schedule.yaml"
    
    with open(schedule_path, 'w') as f:
        yaml.dump(sample_schedule_data, f)
    
    return schedule_path


def test_activity_initialization():
    """Test that Activity instances can be created correctly."""
    activity = Activity(name="Reading", description="Reading time")
    
    assert activity.name == "Reading"
    assert activity.description == "Reading time"


# This test will fail with the current stub implementation
# but provides a framework for the final implementation
@pytest.mark.xfail(reason="Stub implementation doesn't fully support YAML loading yet")
def test_schedule_from_yaml(schedule_file):
    """Test loading an ActivitySchedule from a YAML file."""
    schedule = ActivitySchedule.from_yaml(schedule_file)
    
    # These assertions will need to be updated as we implement the full class
    assert len(schedule.default_activities) > 0
    assert len(schedule.schedule_periods) > 0
