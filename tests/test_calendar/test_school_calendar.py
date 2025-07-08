"""
Tests for the SchoolCalendar module.

These tests verify that the SchoolCalendar class correctly handles school years,
collection periods, and special days like holidays and professional development days.
"""

import unittest
from datetime import datetime, date, time
import os
from pathlib import Path
import tempfile
import yaml

from cor_data_analysis.data.calendar.school_calendar import SchoolCalendar, SchoolYear, CollectionPeriod


class TestCollectionPeriod(unittest.TestCase):
    """Test the CollectionPeriod class functionality."""
    
    def test_period_creation(self):
        """Test creating a CollectionPeriod instance."""
        period = CollectionPeriod(
            name="P1 SY 22-23",
            start_date=date(2022, 9, 1),
            end_date=date(2022, 11, 30),
            color="#4286f4"
        )
        self.assertEqual(period.name, "P1 SY 22-23")
        self.assertEqual(period.start_date, date(2022, 9, 1))
        self.assertEqual(period.end_date, date(2022, 11, 30))
        self.assertEqual(period.color, "#4286f4")
    
    def test_from_dict(self):
        """Test creating a CollectionPeriod from a dictionary."""
        data = {
            "start_date": "2022-09-01",
            "end_date": "2022-11-30",
            "color": "#4286f4"
        }
        period = CollectionPeriod.from_dict("P1 SY 22-23", data)
        self.assertEqual(period.name, "P1 SY 22-23")
        self.assertEqual(period.start_date, date(2022, 9, 1))
        self.assertEqual(period.end_date, date(2022, 11, 30))
        self.assertEqual(period.color, "#4286f4")
    
    def test_contains_date(self):
        """Test checking if a period contains a specific date."""
        period = CollectionPeriod(
            name="P1 SY 22-23",
            start_date=date(2022, 9, 1),
            end_date=date(2022, 11, 30)
        )
        self.assertTrue(period.contains_date(date(2022, 9, 1)))  # Start date
        self.assertTrue(period.contains_date(date(2022, 10, 15)))  # Middle date
        self.assertTrue(period.contains_date(date(2022, 11, 30)))  # End date
        self.assertFalse(period.contains_date(date(2022, 8, 31)))  # Before start
        self.assertFalse(period.contains_date(date(2022, 12, 1)))  # After end


class TestSchoolYear(unittest.TestCase):
    """Test the SchoolYear class functionality."""
    
    def test_year_creation(self):
        """Test creating a SchoolYear instance."""
        p1 = CollectionPeriod("P1", date(2022, 9, 1), date(2022, 11, 30))
        p2 = CollectionPeriod("P2", date(2022, 12, 1), date(2023, 2, 28))
        
        year = SchoolYear(
            name="2022-2023",
            start_date=date(2022, 8, 29),
            end_date=date(2023, 6, 15),
            periods={"P1": p1, "P2": p2},
            holidays={date(2022, 12, 25), date(2023, 1, 1)},
            professional_development_days={date(2022, 10, 14)},
            virtual_days={date(2023, 2, 10)}
        )
        
        self.assertEqual(year.name, "2022-2023")
        self.assertEqual(year.start_date, date(2022, 8, 29))
        self.assertEqual(year.end_date, date(2023, 6, 15))
        self.assertEqual(len(year.periods), 2)
        self.assertEqual(len(year.holidays), 2)
        self.assertEqual(len(year.professional_development_days), 1)
        self.assertEqual(len(year.virtual_days), 1)
    
    def test_from_dict(self):
        """Test creating a SchoolYear from a dictionary."""
        data = {
            "start_date": "2022-08-29",
            "end_date": "2023-06-15",
            "periods": {
                "P1 SY 22-23": {
                    "start_date": "2022-09-01",
                    "end_date": "2022-11-30",
                    "color": "#4286f4"
                },
                "P2 SY 22-23": {
                    "start_date": "2022-12-01",
                    "end_date": "2023-02-28",
                    "color": "#41f4a0"
                }
            },
            "holidays": [
                "2022-12-25",
                "2023-01-01"
            ],
            "professional_development_days": [
                "2022-10-14"
            ],
            "virtual_days": [
                "2023-02-10"
            ]
        }
        
        year = SchoolYear.from_dict("2022-2023", data)
        
        self.assertEqual(year.name, "2022-2023")
        self.assertEqual(year.start_date, date(2022, 8, 29))
        self.assertEqual(year.end_date, date(2023, 6, 15))
        self.assertEqual(len(year.periods), 2)
        self.assertEqual(len(year.holidays), 2)
        self.assertEqual(len(year.professional_development_days), 1)
        self.assertEqual(len(year.virtual_days), 1)
        
        # Check periods were created correctly
        self.assertIn("P1 SY 22-23", year.periods)
        self.assertEqual(year.periods["P1 SY 22-23"].start_date, date(2022, 9, 1))


class TestSchoolCalendar(unittest.TestCase):
    """Test the SchoolCalendar class functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a sample calendar with multiple school years
        self.calendar = SchoolCalendar()
        
        # 2022-2023 School Year
        p1_22_23 = CollectionPeriod("P1 SY 22-23", date(2022, 9, 1), date(2022, 11, 30))
        p2_22_23 = CollectionPeriod("P2 SY 22-23", date(2022, 12, 1), date(2023, 2, 28))
        p3_22_23 = CollectionPeriod("P3 SY 22-23", date(2023, 3, 1), date(2023, 6, 15))
        
        year_22_23 = SchoolYear(
            name="2022-2023",
            start_date=date(2022, 8, 29),
            end_date=date(2023, 6, 15),
            periods={"P1 SY 22-23": p1_22_23, "P2 SY 22-23": p2_22_23, "P3 SY 22-23": p3_22_23},
            holidays={date(2022, 12, 25), date(2023, 1, 1)},
            professional_development_days={date(2022, 10, 14)},
            virtual_days={date(2023, 2, 10)}
        )
        
        # 2023-2024 School Year
        p1_23_24 = CollectionPeriod("P1 SY 23-24", date(2023, 9, 1), date(2023, 11, 30))
        p2_23_24 = CollectionPeriod("P2 SY 23-24", date(2023, 12, 1), date(2024, 2, 28))
        
        year_23_24 = SchoolYear(
            name="2023-2024",
            start_date=date(2023, 8, 28),
            end_date=date(2024, 6, 14),
            periods={"P1 SY 23-24": p1_23_24, "P2 SY 23-24": p2_23_24},
            holidays={date(2023, 12, 25), date(2024, 1, 1)},
            professional_development_days={date(2023, 10, 13)},
            virtual_days={}
        )
        
        self.calendar.school_years = {
            "2022-2023": year_22_23,
            "2023-2024": year_23_24
        }
    
    def test_find_school_year_for_date(self):
        """Test finding the school year for a specific date."""
        # 2022-2023 School Year
        year = self.calendar.find_school_year_for_date(date(2022, 10, 15))
        self.assertIsNotNone(year)
        self.assertEqual(year.name, "2022-2023")
        
        # 2023-2024 School Year
        year = self.calendar.find_school_year_for_date(date(2023, 10, 15))
        self.assertIsNotNone(year)
        self.assertEqual(year.name, "2023-2024")
        
        # Date outside any school year
        year = self.calendar.find_school_year_for_date(date(2025, 1, 1))
        self.assertIsNone(year)
    
    def test_find_period_for_date(self):
        """Test finding the collection period for a specific date."""
        # P1 SY 22-23
        period = self.calendar.find_period_for_date(date(2022, 10, 15))
        self.assertIsNotNone(period)
        self.assertEqual(period.name, "P1 SY 22-23")
        
        # P2 SY 22-23
        period = self.calendar.find_period_for_date(date(2023, 1, 15))
        self.assertIsNotNone(period)
        self.assertEqual(period.name, "P2 SY 22-23")
        
        # P1 SY 23-24
        period = self.calendar.find_period_for_date(date(2023, 10, 15))
        self.assertIsNotNone(period)
        self.assertEqual(period.name, "P1 SY 23-24")
        
        # Date within school year but not in any period
        period = self.calendar.find_period_for_date(date(2022, 8, 30))
        self.assertIsNone(period)
        
        # Date outside any school year
        period = self.calendar.find_period_for_date(date(2025, 1, 1))
        self.assertIsNone(period)
    
    def test_get_period_name(self):
        """Test getting the period name for a specific date."""
        self.assertEqual(self.calendar.get_period_name(date(2022, 10, 15)), "P1 SY 22-23")
        self.assertEqual(self.calendar.get_period_name(date(2023, 1, 15)), "P2 SY 22-23")
        self.assertEqual(self.calendar.get_period_name(date(2025, 1, 1)), "No Period")
    
    def test_is_collection_day(self):
        """Test determining if a date is a collection day."""
        # Regular weekday within a period
        self.assertTrue(self.calendar.is_collection_day(date(2022, 10, 17)))  # Monday
        
        # Weekend
        self.assertFalse(self.calendar.is_collection_day(date(2022, 10, 15)))  # Saturday
        self.assertFalse(self.calendar.is_collection_day(date(2022, 10, 16)))  # Sunday
        
        # Holiday
        self.assertFalse(self.calendar.is_collection_day(date(2022, 12, 25)))  # Christmas
        
        # Professional development day
        self.assertFalse(self.calendar.is_collection_day(date(2022, 10, 14)))
        
        # Virtual day
        self.assertFalse(self.calendar.is_collection_day(date(2023, 2, 10)))
        
        # Day within school year but not in any period
        self.assertFalse(self.calendar.is_collection_day(date(2022, 8, 30)))
        
        # Day outside any school year
        self.assertFalse(self.calendar.is_collection_day(date(2025, 1, 1)))
    
    def test_count_collection_days(self):
        """Test counting collection days between dates."""
        # Test total days count
        result = self.calendar.count_collection_days(date(2022, 10, 1), date(2022, 10, 31), group_by='day')
        self.assertIn('total_days', result)
        # 31 days in October, minus weekends (8-9, 15-16, 22-23, 29-30) = 21 days
        # Minus professional development day (10/14) = 20 days
        self.assertEqual(result['total_days'], 20)
        
        # Test weekly grouping
        result = self.calendar.count_collection_days(date(2022, 10, 1), date(2022, 10, 31), group_by='week')
        self.assertIn('week', result)
        self.assertEqual(len(result['week']), 5)  # 5 weeks in October 2022
        
        # Test monthly grouping
        result = self.calendar.count_collection_days(date(2022, 9, 1), date(2022, 11, 30), group_by='month')
        self.assertIn('month', result)
        self.assertEqual(len(result['month']), 3)  # September, October, November
        
        # Test period grouping
        result = self.calendar.count_collection_days(date(2022, 9, 1), date(2022, 11, 30), group_by='period')
        self.assertIn('period', result)
        self.assertIn('P1 SY 22-23', result['period'])
    
    def test_get_collection_day_density(self):
        """Test calculating the density of collection days in a range."""
        # October 2022: 31 days total, 20 collection days
        density = self.calendar.get_collection_day_density(date(2022, 10, 1), date(2022, 10, 31))
        self.assertAlmostEqual(density, 20/31, places=2)
        
        # Weekend: no collection days
        density = self.calendar.get_collection_day_density(date(2022, 10, 15), date(2022, 10, 16))
        self.assertEqual(density, 0.0)


class TestSchoolCalendarFromConfig(unittest.TestCase):
    """Test loading SchoolCalendar from configuration."""
    
    def test_from_dict(self):
        """Test creating a SchoolCalendar from a dictionary configuration."""
        config = {
            "school_years": {
                "2022-2023": {
                    "start_date": "2022-08-29",
                    "end_date": "2023-06-15",
                    "periods": {
                        "P1 SY 22-23": {
                            "start_date": "2022-09-01",
                            "end_date": "2022-11-30",
                            "color": "#4286f4"
                        },
                        "P2 SY 22-23": {
                            "start_date": "2022-12-01",
                            "end_date": "2023-02-28",
                            "color": "#41f4a0"
                        }
                    },
                    "holidays": [
                        "2022-12-25",
                        "2023-01-01"
                    ],
                    "professional_development_days": [
                        "2022-10-14"
                    ],
                    "virtual_days": [
                        "2023-02-10"
                    ]
                }
            }
        }
        
        calendar = SchoolCalendar.from_dict(config)
        
        # Verify the school year was loaded
        self.assertEqual(len(calendar.school_years), 1)
        self.assertIn("2022-2023", calendar.school_years)
        
        # Verify periods were loaded
        year = calendar.school_years["2022-2023"]
        self.assertEqual(len(year.periods), 2)
        self.assertIn("P1 SY 22-23", year.periods)
        self.assertIn("P2 SY 22-23", year.periods)
        
        # Verify special days were loaded
        self.assertEqual(len(year.holidays), 2)
        self.assertEqual(len(year.professional_development_days), 1)
        self.assertEqual(len(year.virtual_days), 1)
    
    def test_from_yaml(self):
        """Test loading a SchoolCalendar from a YAML file."""
        # Create a temporary YAML file
        config = {
            "school_years": {
                "2022-2023": {
                    "start_date": "2022-08-29",
                    "end_date": "2023-06-15",
                    "periods": {
                        "P1 SY 22-23": {
                            "start_date": "2022-09-01",
                            "end_date": "2022-11-30",
                            "color": "#4286f4"
                        }
                    },
                    "holidays": ["2022-12-25"]
                }
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.yaml') as tmp:
            yaml.dump(config, tmp)
            tmp_path = tmp.name
            
        try:
            # Load from the temporary file
            calendar = SchoolCalendar.from_yaml(tmp_path)
            
            # Verify it loaded correctly
            self.assertEqual(len(calendar.school_years), 1)
            self.assertIn("2022-2023", calendar.school_years)
            
            # Verify period was loaded
            year = calendar.school_years["2022-2023"]
            self.assertEqual(len(year.periods), 1)
            self.assertIn("P1 SY 22-23", year.periods)
            
            # Verify holiday was loaded
            self.assertEqual(len(year.holidays), 1)
            self.assertIn(date(2022, 12, 25), year.holidays)
        finally:
            # Clean up
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)


if __name__ == '__main__':
    unittest.main()
