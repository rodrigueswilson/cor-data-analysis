"""
Tests for the DataAggregator module.

These tests verify that the DataAggregator correctly aggregates file metadata
across multiple dimensions including time periods and classroom activities.
"""

import pytest
from datetime import datetime, date, time, timedelta
import os
from pathlib import Path
import tempfile
import pandas as pd
import numpy as np
import yaml

from cor_data_analysis.data.aggregation.aggregator import DataAggregator
from cor_data_analysis.data.calendar.school_calendar import SchoolCalendar
from cor_data_analysis.data.calendar.activity_schedule import ActivitySchedule


class TestDataAggregator:
    """Test the DataAggregator class functionality."""

    def setup_method(self, method):
        """Set up test fixtures."""
        self.calendar = self._create_test_calendar()
        self.schedule = self._create_test_schedule()
        self.mp3_df = self._create_sample_mp3_df()
        self.jpg_df = self._create_sample_jpg_df()
        self.aggregator = DataAggregator(
            calendar=self.calendar, activity_schedule=self.schedule
        )

    def _create_test_calendar(self):
        """Create a test calendar for the tests."""
        calendar_config = {
            "school_years": {
                "2022-2023": {
                    "start_date": "2022-08-29",
                    "end_date": "2023-06-15",
                    "periods": {
                        "P1 SY 22-23": {
                            "start_date": "2022-09-01",
                            "end_date": "2022-11-30",
                        },
                        "P2 SY 22-23": {
                            "start_date": "2022-12-01",
                            "end_date": "2023-02-28",
                        },
                        "P3 SY 22-23": {
                            "start_date": "2023-03-01",
                            "end_date": "2023-06-15",
                        },
                    },
                }
            }
        }
        return SchoolCalendar.from_dict(calendar_config)

    def _create_test_schedule(self):
        """Create a test activity schedule for the tests."""
        schedule_config = {
            "2022-09-01_2022-12-20": [
                {
                    "name": "Breakfast",
                    "start_time": "08:30",
                    "end_time": "09:00",
                    "category": "Meal",
                },
                {
                    "name": "Small Group",
                    "start_time": "09:15",
                    "end_time": "09:35",
                    "category": "Instruction",
                },
                {
                    "name": "Work Time",
                    "start_time": "09:45",
                    "end_time": "10:45",
                    "category": "Work",
                },
            ],
            "2022-12-21_2023-06-15": [
                {
                    "name": "Breakfast",
                    "start_time": "08:45",
                    "end_time": "09:15",
                    "category": "Meal",
                },
                {
                    "name": "Circle Time",
                    "start_time": "09:30",
                    "end_time": "09:50",
                    "category": "Instruction",
                },
                {
                    "name": "Centers",
                    "start_time": "10:00",
                    "end_time": "11:00",
                    "category": "Work",
                },
            ],
        }
        return ActivitySchedule.from_dict(schedule_config)

    def _create_sample_mp3_df(self):
        """Create a sample MP3 DataFrame for testing."""
        dates = [
            "2022-09-06", "2022-09-06", "2022-09-06", "2022-09-07", "2022-09-07", "2022-09-08",
            "2022-10-03", "2022-10-03", "2022-10-04", "2022-10-05",
            "2022-11-01", "2022-11-02",
            "2022-12-05", "2022-12-06", "2022-12-07",
            "2023-01-09", "2023-01-10",
            "2023-03-06", "2023-03-07",
        ]
        times = [
            "08:40", "09:25", "10:15",
            "08:45", "09:20",
            "10:00",
            "08:35", "10:00",
            "09:25",
            "10:15",
            "10:00", "10:30",
            "08:50", "09:40", "10:30",
            "08:55", "10:20",
            "09:00", "10:35",
        ]
        durations = [30, 45, 120, 25, 35, 60, 40, 90, 30, 120, 45, 60, 35, 40, 100, 45, 110, 50, 75]
        data = {
            'Date': dates,
            'Time': times,
            'Duration': durations,
            'FileSize': [i * 10240 for i in range(1, len(dates) + 1)],
        }
        return pd.DataFrame(data)

    def _create_sample_jpg_df(self):
        """Create a sample JPG DataFrame for testing."""
        dates = [
            "2022-09-06", "2022-09-06", "2022-09-07", "2022-09-08",
            "2022-10-03", "2022-10-04", "2022-10-04",
            "2022-12-05", "2022-12-05", "2022-12-06",
            "2023-01-09", "2023-01-10",
            "2023-03-06", "2023-03-07", "2023-03-07",
        ]
        times = [
            "08:35", "09:20",
            "09:30",
            "09:55",
            "08:40",
            "09:25", "10:15",
            "08:55", "09:45", "10:25",
            "09:00", "10:30",
            "09:50", "10:15", "10:40",
        ]
        data = {
            'Date': dates,
            'Time': times,
            'FileSize': [i * 51200 for i in range(1, len(dates) + 1)],
        }
        return pd.DataFrame(data)

    def test_format_duration(self):
        """Test the duration formatting helper method."""
        assert DataAggregator._format_duration(3661) == "1h 1m 1s"
        assert DataAggregator._format_duration(65) == "1m 5s"
        assert DataAggregator._format_duration(59) == "59s"
        assert DataAggregator._format_duration(0) == "0s"
        assert DataAggregator._format_duration(None) == "0s"

    def test_prepare_data(self):
        """Test the centralized prepare_data method."""
        prepared_df = self.aggregator.prepare_data(self.mp3_df)
        assert 'DateTime' in prepared_df.columns
        assert 'Activity' in prepared_df.columns
        assert 'ActivityCategory' in prepared_df.columns
        assert not prepared_df['DateTime'].isnull().any()
        specific_time = pd.Timestamp('2022-09-06 09:25:00')
        activity = prepared_df[prepared_df['DateTime'] == specific_time]['Activity'].iloc[0]
        assert activity == 'Small Group'

    def test_prepare_data_with_missing_datetime(self):
        """Test prepare_data with missing datetime information."""
        df_missing = self.mp3_df.copy()
        df_missing.loc[0, 'Date'] = pd.NaT
        prepared = self.aggregator.prepare_data(df_missing)
        assert pd.isna(prepared.loc[0, 'DateTime'])
        assert prepared.loc[0, 'Activity'] == 'Unknown'

    def test_aggregate_by_time_unit(self):
        """Test aggregation by time unit (day, week, month)."""
        daily_agg = self.aggregator.aggregate_by_time_unit(self.mp3_df, self.jpg_df, 'day')
        assert isinstance(daily_agg, pd.DataFrame)
        assert 'mp3_count' in daily_agg.columns
        assert daily_agg['mp3_count'].sum() > 0

        weekly_agg = self.aggregator.aggregate_by_time_unit(self.mp3_df, self.jpg_df, 'week')
        assert 'Week' in weekly_agg.columns

        monthly_agg = self.aggregator.aggregate_by_time_unit(self.mp3_df, self.jpg_df, 'month')
        assert 'Month' in monthly_agg.columns

    def test_aggregate_by_school_year(self):
        """Test the main aggregate_by_school_year integration method."""
        result = self.aggregator.aggregate_by_school_year(self.mp3_df, self.jpg_df)
        assert isinstance(result, dict)

        # Check for all expected summary keys
        expected_keys = [
            'daily_summary', 'weekly_summary', 'monthly_summary', 
            'period_summary', 'activity_distribution', 'category_distribution'
        ]
        for key in expected_keys:
            assert key in result

        # Validate period_summary structure and content
        period_summary_df = result['period_summary']
        assert isinstance(period_summary_df, pd.DataFrame)
        assert not period_summary_df.empty
        assert 'period_name' in period_summary_df.columns
        assert 'P1 SY 22-23' in period_summary_df['period_name'].tolist()

        # Validate distributions
        assert len(result['activity_distribution']) > 0

    def test_empty_data_handling(self):
        """Test that aggregation methods handle empty DataFrames gracefully."""
        empty_mp3 = pd.DataFrame(columns=self.mp3_df.columns)
        empty_jpg = pd.DataFrame(columns=self.jpg_df.columns)
        result = self.aggregator.aggregate_by_school_year(empty_mp3, empty_jpg)

        # Check that all summary DataFrames are empty
        assert result['daily_summary'].empty
        assert result['weekly_summary'].empty
        assert result['monthly_summary'].empty
        assert result['period_summary'].empty

        # Check that distributions are empty dictionaries
        assert len(result['activity_distribution']) == 0
        assert len(result['category_distribution']) == 0

    def test_no_calendar_handling(self):
        """Test that ValueError is raised when calendar or schedule are missing."""
        no_cal_agg = DataAggregator()
        with pytest.raises(ValueError, match="Calendar and activity schedule must be initialized"):
            no_cal_agg.aggregate_by_school_year(self.mp3_df, self.jpg_df)



