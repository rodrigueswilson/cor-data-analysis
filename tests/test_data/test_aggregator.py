"""
Tests for the DataAggregator class.
"""

import pandas as pd
import numpy as np
import pytest
from datetime import datetime, timedelta
from pathlib import Path
import yaml
import tempfile

from cor_data_analysis.data.aggregation.aggregator import DataAggregator
from cor_data_analysis.data.schedule.activity_schedule import ActivitySchedule
from cor_data_analysis.data.calendar.school_calendar import SchoolCalendar

@pytest.fixture
def sample_schedule_yaml():
    """Create a sample schedule YAML for testing."""
    schedule_yaml = """
    activities:
      - name: Morning Class
        category: Academic
        description: Academic morning activities
      - name: Recess
        category: Break
        description: Morning break
      - name: Math Class
        category: Academic
        description: Mathematics learning
      - name: Lunch
        category: Break
        description: Lunch break
      - name: Science Class
        category: Academic
        description: Science activities
      - name: Afternoon Break
        category: Break
        description: Short afternoon break
      - name: Reading Time
        category: Academic
        description: Reading and literacy
      - name: After School
        category: Other
        description: After school activities
    
    periods:
      - name: Fall Semester
        start_date: 2023-09-01
        end_date: 2023-12-20
        activities:
          - Morning Class
          - Recess
          - Math Class
      - name: Spring Semester
        start_date: 2024-01-08
        end_date: 2024-06-15
        activities:
          - Science Class
          - Afternoon Break
          - Reading Time
    
    daily_schedule:
      "2023-09-15":
        "09:15:00": "Morning Class"
        "13:30:00": "Science Class"
      "2023-09-16":
        "11:00:00": "Math Class"
      "2023-10-01":
        "14:45:00": "Reading Time"
    """
    return schedule_yaml

@pytest.fixture
def sample_calendar_yaml():
    """Create a sample calendar YAML for testing."""
    calendar_yaml = """
    school_year:
      start_date: 2023-09-01
      end_date: 2024-06-15
    special_periods:
      - name: Fall Semester
        start_date: 2023-09-01
        end_date: 2023-12-20
      - name: Spring Semester
        start_date: 2024-01-08
        end_date: 2024-06-15
    holidays:
      - name: Thanksgiving
        start_date: 2023-11-23
        end_date: 2023-11-24
      - name: Winter Break
        start_date: 2023-12-21
        end_date: 2024-01-07
      - name: Spring Break
        start_date: 2024-03-25
        end_date: 2024-03-29
    """
    return calendar_yaml

@pytest.fixture
def sample_schedule(tmp_path, sample_schedule_yaml):
    """Create a sample ActivitySchedule for testing."""
    schedule_file = tmp_path / "schedule.yaml"
    schedule_file.write_text(sample_schedule_yaml)
    schedule = ActivitySchedule.from_yaml(schedule_file)
    print("\nSchedule periods:")
    for period in schedule.schedule_periods:
        print(f"  {period.name}: {period.start_date} - {period.end_date}")
    return schedule

@pytest.fixture
def sample_calendar(tmp_path, sample_calendar_yaml):
    """Create a sample SchoolCalendar for testing."""
    calendar_file = tmp_path / "calendar.yaml"
    calendar_file.write_text(sample_calendar_yaml)
    return SchoolCalendar.from_yaml(calendar_file)

@pytest.fixture
def sample_data_aggregator(sample_schedule, sample_calendar):
    """Create a sample DataAggregator for testing."""
    return DataAggregator(calendar=sample_calendar, activity_schedule=sample_schedule)

@pytest.fixture
def sample_mp3_df():
    """Create a sample DataFrame for MP3 files."""
    data = {
        'Date': pd.to_datetime(['2023-09-15', '2023-09-15', '2023-09-16', '2023-10-01']),
        'Time': ['09:15:00', '13:30:00', '11:00:00', '14:45:00'],
        'Duration': [120.5, 300.2, 180.0, 200.5],
        'FileSize': [2048000, 3072000, 1536000, 2560000],  # in bytes
    }
    return pd.DataFrame(data)

@pytest.fixture
def sample_jpg_df():
    """Create a sample DataFrame for JPG files."""
    data = {
        'Date': pd.to_datetime(['2023-09-15', '2023-09-15', '2023-09-16', '2023-10-01']),
        'Time': ['09:20:00', '13:35:00', '11:05:00', '14:50:00'],
        'FileSize': [1024000, 1536000, 768000, 1280000],  # in bytes
    }
    return pd.DataFrame(data)

def test_data_aggregator_init(sample_schedule, sample_calendar):
    """Test DataAggregator initialization."""
    aggregator = DataAggregator(calendar=sample_calendar, activity_schedule=sample_schedule)
    
    assert aggregator.calendar is sample_calendar
    assert aggregator.activity_schedule is sample_schedule

def test_prepare_data(sample_data_aggregator, sample_mp3_df):
    """Test prepare_data method."""
    prepared_df = sample_data_aggregator.prepare_data(sample_mp3_df)
    
    assert 'DateTime' in prepared_df.columns
    assert 'Activity' in prepared_df.columns
    assert 'ActivityCategory' in prepared_df.columns
    
    # Debug prints
    print("\nDateTime values:")
    for dt in prepared_df['DateTime']:
        print(f"  {dt}")
    
    print("\nActivity values:")
    print(prepared_df['Activity'].tolist())
    
    print("\nActivityCategory values:")
    print(prepared_df['ActivityCategory'].tolist())
    
    # First record should be 9:15 AM which falls in "Morning Class"
    assert prepared_df.iloc[0]['Activity'] == 'Morning Class'
    assert prepared_df.iloc[0]['ActivityCategory'] == 'Academic'
    
    # Second record should be 1:30 PM which falls in "Science Class"
    assert prepared_df.iloc[1]['Activity'] == 'Science Class'
    assert prepared_df.iloc[1]['ActivityCategory'] == 'Academic'

def test_ensure_datetime_columns(sample_data_aggregator, sample_mp3_df):
    """Test _ensure_datetime_columns method."""
    df_with_datetime = sample_data_aggregator._ensure_datetime_columns(sample_mp3_df)
    
    assert 'DateTime' in df_with_datetime.columns
    assert df_with_datetime['DateTime'].dtype == 'datetime64[ns]'
    
    # Check if Date and Time were combined correctly
    expected_datetime = pd.to_datetime('2023-09-15 09:15:00')
    assert df_with_datetime.iloc[0]['DateTime'] == expected_datetime

def test_calculate_distributions(sample_data_aggregator, sample_mp3_df, sample_jpg_df):
    """Test _calculate_distributions method."""
    # First, prepare the data to add Activity and ActivityCategory columns
    mp3_prepared = sample_data_aggregator.prepare_data(sample_mp3_df)
    jpg_prepared = sample_data_aggregator.prepare_data(sample_jpg_df)
    
    # Calculate distributions
    distributions = sample_data_aggregator._calculate_distributions(mp3_prepared, jpg_prepared)
    
    assert 'activity_distribution' in distributions
    assert 'category_distribution' in distributions
    
    # Check if distribution calculations are correct
    activity_dist = distributions['activity_distribution']
    assert 'Morning Class' in activity_dist
    assert 'Science Class' in activity_dist
    
    category_dist = distributions['category_distribution']
    assert 'Academic' in category_dist
    
    # Morning Class should have 1 MP3 and 1 JPG
    assert activity_dist['Morning Class']['mp3_count'] == 1
    assert activity_dist['Morning Class']['jpg_count'] == 1

def test_aggregate_by_time_unit(sample_data_aggregator, sample_mp3_df, sample_jpg_df):
    """Test aggregate_by_time_unit method."""
    # Test daily aggregation
    daily_agg = sample_data_aggregator.aggregate_by_time_unit(sample_mp3_df, sample_jpg_df, 'day')
    
    assert 'Day' in daily_agg.columns
    assert len(daily_agg) == 3  # 3 unique days in the sample data
    
    # First day should have 2 MP3s and 2 JPGs
    first_day = daily_agg.iloc[0]
    assert first_day['mp3_count'] == 2
    assert first_day['jpg_count'] == 2

def test_aggregate_by_school_year(sample_data_aggregator, sample_mp3_df, sample_jpg_df):
    """Test aggregate_by_school_year method."""
    results = sample_data_aggregator.aggregate_by_school_year(sample_mp3_df, sample_jpg_df)
    
    assert 'daily_summary' in results
    assert 'weekly_summary' in results
    assert 'monthly_summary' in results
    assert 'period_summary' in results
    assert 'activity_distribution' in results
    assert 'category_distribution' in results
