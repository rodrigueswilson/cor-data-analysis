"""
Tests for the ActivitySchedule module.

These tests verify that the ActivitySchedule class correctly handles mid-year
schedule changes and properly maps timestamps to activities.
"""

import unittest
from datetime import datetime, date, time
import os
from pathlib import Path
import tempfile
import yaml

from cor_data_analysis.data.calendar.activity_schedule import ActivitySchedule, Activity, SchedulePeriod


class TestActivity(unittest.TestCase):
    """Test the Activity class functionality."""
    
    def test_activity_creation(self):
        """Test creating an Activity instance."""
        activity = Activity(
            name="Breakfast",
            start_time=time(8, 30),
            end_time=time(9, 0),
            category="Meal"
        )
        self.assertEqual(activity.name, "Breakfast")
        self.assertEqual(activity.start_time, time(8, 30))
        self.assertEqual(activity.end_time, time(9, 0))
        self.assertEqual(activity.category, "Meal")
    
    def test_from_dict(self):
        """Test creating an Activity from a dictionary."""
        data = {
            "name": "Small Group",
            "start_time": "09:15",
            "end_time": "09:35",
            "category": "Instruction",
            "description": "Teacher-led small group activity"
        }
        activity = Activity.from_dict(data)
        self.assertEqual(activity.name, "Small Group")
        self.assertEqual(activity.start_time, time(9, 15))
        self.assertEqual(activity.end_time, time(9, 35))
        self.assertEqual(activity.category, "Instruction")
        self.assertEqual(activity.description, "Teacher-led small group activity")
    
    def test_contains_time(self):
        """Test checking if an activity contains a specific time."""
        activity = Activity(
            name="Breakfast",
            start_time=time(8, 30),
            end_time=time(9, 0)
        )
        self.assertTrue(activity.contains_time(time(8, 30)))  # Start time is included
        self.assertTrue(activity.contains_time(time(8, 45)))  # Middle time is included
        self.assertFalse(activity.contains_time(time(9, 0)))  # End time is excluded
        self.assertFalse(activity.contains_time(time(8, 0)))  # Before start time
        self.assertFalse(activity.contains_time(time(10, 0)))  # After end time


class TestSchedulePeriod(unittest.TestCase):
    """Test the SchedulePeriod class functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.activity1 = Activity("Breakfast", time(8, 30), time(9, 0), "Meal")
        self.activity2 = Activity("Small Group", time(9, 15), time(9, 35), "Instruction")
        self.period = SchedulePeriod(
            start_date=date(2022, 9, 1),
            end_date=date(2022, 12, 20),
            activities=[self.activity1, self.activity2]
        )
    
    def test_period_creation(self):
        """Test creating a SchedulePeriod instance."""
        self.assertEqual(self.period.start_date, date(2022, 9, 1))
        self.assertEqual(self.period.end_date, date(2022, 12, 20))
        self.assertEqual(len(self.period.activities), 2)
    
    def test_from_dict(self):
        """Test creating a SchedulePeriod from a dictionary."""
        data = [
            {
                "name": "Breakfast",
                "start_time": "08:30",
                "end_time": "09:00",
                "category": "Meal"
            },
            {
                "name": "Small Group",
                "start_time": "09:15",
                "end_time": "09:35",
                "category": "Instruction"
            }
        ]
        period = SchedulePeriod.from_dict("2022-09-01_2022-12-20", data)
        self.assertEqual(period.start_date, date(2022, 9, 1))
        self.assertEqual(period.end_date, date(2022, 12, 20))
        self.assertEqual(len(period.activities), 2)
        self.assertEqual(period.activities[0].name, "Breakfast")
    
    def test_contains_date(self):
        """Test checking if a period contains a specific date."""
        self.assertTrue(self.period.contains_date(date(2022, 9, 1)))  # Start date
        self.assertTrue(self.period.contains_date(date(2022, 10, 15)))  # Middle date
        self.assertTrue(self.period.contains_date(date(2022, 12, 20)))  # End date
        self.assertFalse(self.period.contains_date(date(2022, 8, 31)))  # Before start
        self.assertFalse(self.period.contains_date(date(2022, 12, 21)))  # After end
    
    def test_get_activity_for_time(self):
        """Test getting the activity for a specific time."""
        self.assertEqual(self.period.get_activity_for_time(time(8, 45)), self.activity1)
        self.assertEqual(self.period.get_activity_for_time(time(9, 25)), self.activity2)
        self.assertIsNone(self.period.get_activity_for_time(time(10, 0)))  # No activity at this time


class TestActivitySchedule(unittest.TestCase):
    """Test the ActivitySchedule class functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a sample schedule with two periods
        self.schedule = ActivitySchedule()
        
        # Fall schedule
        fall_activities = [
            Activity("Breakfast", time(8, 30), time(9, 0), "Meal"),
            Activity("Small Group", time(9, 15), time(9, 35), "Instruction")
        ]
        fall_period = SchedulePeriod(date(2022, 9, 1), date(2022, 12, 20), fall_activities)
        
        # Spring schedule with different times
        spring_activities = [
            Activity("Breakfast", time(8, 45), time(9, 15), "Meal"),  # 15 min later
            Activity("Small Group", time(9, 35), time(10, 0), "Instruction")  # 20 min later
        ]
        spring_period = SchedulePeriod(date(2022, 12, 21), date(2023, 6, 15), spring_activities)
        
        # Default activities
        default_activities = [
            Activity("Default Activity", time(9, 0), time(10, 0), "General")
        ]
        
        self.schedule.schedule_periods = [fall_period, spring_period]
        self.schedule.default_activities = default_activities
    
    def test_find_schedule_for_date(self):
        """Test finding the appropriate schedule for a specific date."""
        # Fall schedule
        fall_activities = self.schedule.find_schedule_for_date(date(2022, 10, 15))
        self.assertEqual(len(fall_activities), 2)
        self.assertEqual(fall_activities[0].name, "Breakfast")
        self.assertEqual(fall_activities[0].start_time, time(8, 30))
        
        # Spring schedule
        spring_activities = self.schedule.find_schedule_for_date(date(2023, 2, 15))
        self.assertEqual(len(spring_activities), 2)
        self.assertEqual(spring_activities[0].name, "Breakfast")
        self.assertEqual(spring_activities[0].start_time, time(8, 45))  # 15 min later
        
        # Date outside any period - should get default
        outside_activities = self.schedule.find_schedule_for_date(date(2023, 8, 1))
        self.assertEqual(len(outside_activities), 1)
        self.assertEqual(outside_activities[0].name, "Default Activity")
    
    def test_get_activity_for_datetime(self):
        """Test getting the activity for a specific datetime."""
        # Fall schedule - Breakfast time
        fall_breakfast = datetime(2022, 10, 15, 8, 45)
        activity = self.schedule.get_activity_for_datetime(fall_breakfast)
        self.assertIsNotNone(activity)
        self.assertEqual(activity.name, "Breakfast")
        
        # Spring schedule - Breakfast time (15 min later)
        spring_breakfast = datetime(2023, 2, 15, 8, 45)
        activity = self.schedule.get_activity_for_datetime(spring_breakfast)
        self.assertIsNotNone(activity)
        self.assertEqual(activity.name, "Breakfast")
        
        # This would be breakfast in fall but not in spring
        early_spring = datetime(2023, 2, 15, 8, 35)
        activity = self.schedule.get_activity_for_datetime(early_spring)
        self.assertIsNone(activity)  # No activity at this time in spring
    
    def test_get_activity_name_for_datetime(self):
        """Test getting the activity name for a specific datetime."""
        dt = datetime(2022, 10, 15, 8, 45)
        self.assertEqual(self.schedule.get_activity_name_for_datetime(dt), "Breakfast")
        
        no_activity_dt = datetime(2022, 10, 15, 10, 0)
        self.assertEqual(self.schedule.get_activity_name_for_datetime(no_activity_dt), 
                        "No Activity Scheduled")
    
    def test_get_activity_for_time(self):
        """Test legacy method to get activity for hour/minute."""
        # With date specified - should use correct schedule
        fall_date = date(2022, 10, 15)
        self.assertEqual(self.schedule.get_activity_for_time(8, 45, fall_date), "Breakfast")
        
        spring_date = date(2023, 2, 15)
        self.assertEqual(self.schedule.get_activity_for_time(8, 45, spring_date), "Breakfast")
        self.assertIsNone(self.schedule.get_activity_for_time(8, 35, spring_date))
        
        # Without date - should use default schedule
        self.assertEqual(self.schedule.get_activity_for_time(9, 30), "Default Activity")


class TestActivityScheduleFromConfig(unittest.TestCase):
    """Test loading ActivitySchedule from configuration."""
    
    def test_from_dict(self):
        """Test creating an ActivitySchedule from a dictionary configuration."""
        config = {
            "default": [
                {
                    "name": "Default Activity",
                    "start_time": "09:00",
                    "end_time": "10:00",
                    "category": "General"
                }
            ],
            "2022-09-01_2022-12-20": [
                {
                    "name": "Breakfast",
                    "start_time": "08:30",
                    "end_time": "09:00",
                    "category": "Meal"
                },
                {
                    "name": "Small Group",
                    "start_time": "09:15",
                    "end_time": "09:35",
                    "category": "Instruction"
                }
            ],
            "2022-12-21_2023-06-15": [
                {
                    "name": "Breakfast",
                    "start_time": "08:45",
                    "end_time": "09:15",
                    "category": "Meal"
                },
                {
                    "name": "Small Group",
                    "start_time": "09:35",
                    "end_time": "10:00",
                    "category": "Instruction"
                }
            ]
        }
        
        schedule = ActivitySchedule.from_dict(config)
        
        # Verify periods were loaded correctly
        self.assertEqual(len(schedule.schedule_periods), 2)
        self.assertEqual(len(schedule.default_activities), 1)
        
        # Verify default activity
        self.assertEqual(schedule.default_activities[0].name, "Default Activity")
        
        # Test schedule selection
        fall_activities = schedule.find_schedule_for_date(date(2022, 10, 15))
        self.assertEqual(fall_activities[0].name, "Breakfast")
        self.assertEqual(fall_activities[0].start_time, time(8, 30))
        
        spring_activities = schedule.find_schedule_for_date(date(2023, 2, 15))
        self.assertEqual(spring_activities[0].name, "Breakfast")
        self.assertEqual(spring_activities[0].start_time, time(8, 45))
    
    def test_from_yaml(self):
        """Test loading an ActivitySchedule from a YAML file."""
        # Create a temporary YAML file
        config = {
            "activity_schedules": {
                "default": [
                    {
                        "name": "Default Activity",
                        "start_time": "09:00",
                        "end_time": "10:00",
                        "category": "General"
                    }
                ],
                "2022-09-01_2022-12-20": [
                    {
                        "name": "Breakfast",
                        "start_time": "08:30",
                        "end_time": "09:00",
                        "category": "Meal"
                    }
                ]
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.yaml') as tmp:
            yaml.dump(config, tmp)
            tmp_path = tmp.name
            
        try:
            # Load from the temporary file
            schedule = ActivitySchedule.from_yaml(tmp_path)
            
            # Verify it loaded correctly
            self.assertEqual(len(schedule.schedule_periods), 1)
            self.assertEqual(len(schedule.default_activities), 1)
            self.assertEqual(schedule.default_activities[0].name, "Default Activity")
            
            # Test fall schedule
            fall_activities = schedule.find_schedule_for_date(date(2022, 10, 15))
            self.assertEqual(fall_activities[0].name, "Breakfast")
        finally:
            # Clean up
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)


if __name__ == '__main__':
    unittest.main()
