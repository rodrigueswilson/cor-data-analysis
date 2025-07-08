"""
Sample script to generate aggregation reports.

This script demonstrates how to use the DataAggregator to perform a full analysis
and export the results to Excel and JSON formats.
"""

import pandas as pd
from pathlib import Path
import sys

# Add the project root to the Python path
project_root = Path(__file__).resolve().parents[1]
sys.path.append(str(project_root / 'src'))

from cor_data_analysis.data.aggregation.aggregator import DataAggregator
from cor_data_analysis.data.calendar.school_calendar import SchoolCalendar
from cor_data_analysis.data.calendar.activity_schedule import ActivitySchedule

def _create_test_calendar():
    """Creates a sample SchoolCalendar for the report generation."""
    calendar_config = {
        "school_years": {
            "2022-2023": {
                "start_date": "2022-08-29",
                "end_date": "2023-06-15",
                "periods": {
                    "P1 SY 22-23": {"start_date": "2022-09-01", "end_date": "2022-11-30"},
                    "P2 SY 22-23": {"start_date": "2022-12-01", "end_date": "2023-02-28"},
                    "P3 SY 22-23": {"start_date": "2023-03-01", "end_date": "2023-06-15"},
                },
            }
        }
    }
    return SchoolCalendar.from_dict(calendar_config)

def _create_test_schedule():
    """Creates a sample ActivitySchedule for the report generation."""
    schedule_config = {
        "2022-09-01_2022-12-20": [
            {"name": "Breakfast", "start_time": "08:30", "end_time": "09:00", "category": "Meal"},
            {"name": "Small Group", "start_time": "09:15", "end_time": "09:35", "category": "Instruction"},
            {"name": "Work Time", "start_time": "09:45", "end_time": "10:45", "category": "Work"},
        ],
        "2022-12-21_2023-06-15": [
            {"name": "Breakfast", "start_time": "08:45", "end_time": "09:15", "category": "Meal"},
            {"name": "Circle Time", "start_time": "09:30", "end_time": "09:50", "category": "Instruction"},
            {"name": "Centers", "start_time": "10:00", "end_time": "11:00", "category": "Work"},
        ],
    }
    return ActivitySchedule.from_dict(schedule_config)

def _create_sample_mp3_df():
    """Creates a sample MP3 DataFrame."""
    data = {
        'Date': ["2022-09-06", "2022-09-06", "2022-09-06", "2022-09-07", "2022-09-07", "2022-09-08",
                 "2022-10-03", "2022-10-03", "2022-10-04", "2022-10-05", "2022-11-01", "2022-11-02",
                 "2022-12-05", "2022-12-06", "2022-12-07", "2023-01-09", "2023-01-10", "2023-03-06", "2023-03-07"],
        'Time': ["08:40", "09:25", "10:15", "08:50", "09:30", "10:00", "08:35", "09:20", "10:10", "09:00",
                 "09:40", "10:30", "08:55", "09:45", "10:20", "09:05", "09:55", "10:15", "09:10"],
        'Duration': [30, 45, 120, 25, 50, 90, 35, 40, 110, 20, 55, 80, 28, 48, 100, 22, 52, 130, 18],
        'FileSize': [1024*500, 1024*700, 1024*1200, 1024*400, 1024*800, 1024*1000, 1024*600, 1024*650, 1024*1150, 1024*300,
                     1024*850, 1024*950, 1024*450, 1024*750, 1024*1050, 1024*350, 1024*820, 1024*1250, 1024*280]
    }
    return pd.DataFrame(data)

def _create_sample_jpg_df():
    """Creates a sample JPG DataFrame."""
    data = {
        'Date': ["2022-09-06", "2022-09-07", "2022-10-03", "2022-11-01", "2022-12-05", "2023-01-09", "2023-03-06"],
        'Time': ["09:00", "09:45", "09:00", "10:00", "09:15", "09:30", "10:00"],
        'FileSize': [1024*100, 1024*150, 1024*120, 1024*180, 1024*110, 1024*130, 1024*160]
    }
    return pd.DataFrame(data)

def main():
    """Main function to generate and export reports."""
    print("Initializing calendar and schedule...")
    calendar = _create_test_calendar()
    schedule = _create_test_schedule()

    print("Creating sample DataFrames...")
    mp3_df = _create_sample_mp3_df()
    jpg_df = _create_sample_jpg_df()

    print("Initializing DataAggregator...")
    aggregator = DataAggregator(calendar=calendar, activity_schedule=schedule)

    print("Running aggregation...")
    aggregated_data = aggregator.aggregate_by_school_year(mp3_df, jpg_df)

    # Define output paths
    reports_dir = project_root / 'reports'
    excel_path = reports_dir / 'sample_aggregation_report.xlsx'
    json_path = reports_dir / 'sample_aggregation_report.json'

    print(f"Exporting to Excel: {excel_path}")
    aggregator.to_excel(aggregated_data, excel_path)

    print(f"Exporting to JSON: {json_path}")
    aggregator.to_json(aggregated_data, json_path)

    print("\nSample reports generated successfully!")

if __name__ == "__main__":
    main()
