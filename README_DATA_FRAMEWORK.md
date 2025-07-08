# COR Data Analysis Framework

## Overview

The COR Data Analysis framework provides a comprehensive solution for aggregating and analyzing classroom data across multiple dimensions, with special emphasis on:

1. Multi-level periodization (days, weeks, months, collection periods)
2. Activity-based data collection and analysis
3. Flexible school calendar integration
4. Support for mid-year schedule changes

## Key Components

### School Calendar System

The `SchoolCalendar` module manages school years, collection periods, and special days:

```python
from cor_data_analysis.data.calendar import SchoolCalendar

# Load from configuration file
calendar = SchoolCalendar.from_yaml("path/to/school_calendar.yaml")

# Check if a date is a collection day
is_collection = calendar.is_collection_day(date(2022, 10, 15))

# Get the period name for a date
period_name = calendar.get_period_name(date(2022, 10, 15))

# Count collection days in a range
collection_days = calendar.count_collection_days(
    start_date=date(2022, 9, 1),
    end_date=date(2022, 11, 30),
    group_by='month'
)
```

### Activity Schedule System

The `ActivitySchedule` module handles classroom activities and mid-year schedule changes:

```python
from cor_data_analysis.data.calendar import ActivitySchedule

# Load from configuration file
schedule = ActivitySchedule.from_yaml("path/to/activity_schedules.yaml")

# Get activity for a specific datetime
activity = schedule.get_activity_for_datetime(datetime(2022, 10, 15, 8, 45))

# Get activity name for a specific datetime
activity_name = schedule.get_activity_name_for_datetime(datetime(2022, 10, 15, 8, 45))
```

### Data Aggregation System

The `DataAggregator` module provides flexible methods for analyzing file metadata:

```python
from cor_data_analysis.data.aggregation import DataAggregator

# Initialize with calendar and schedule
aggregator = DataAggregator(calendar=calendar, activity_schedule=schedule)

# Aggregate by school year (highest level)
school_year_metrics = aggregator.aggregate_by_school_year(mp3_df, jpg_df)

# Aggregate by collection period
period_metrics = aggregator.aggregate_by_period(mp3_df, jpg_df)

# Aggregate by time unit (day, week, month)
daily_metrics = aggregator.aggregate_by_time_unit(mp3_df, jpg_df, 'day')
weekly_metrics = aggregator.aggregate_by_time_unit(mp3_df, jpg_df, 'week')
monthly_metrics = aggregator.aggregate_by_time_unit(mp3_df, jpg_df, 'month')

# Aggregate by activity
activity_metrics = aggregator.aggregate_by_activity(mp3_df, jpg_df)

# Aggregate by activity category
category_metrics = aggregator.aggregate_by_activity_category(mp3_df, jpg_df)

# Aggregate by activity and period (combined analysis)
activity_period_metrics = aggregator.aggregate_by_activity_and_period(mp3_df, jpg_df)
```

## Configuration Files

### School Calendar Configuration (YAML)

```yaml
school_years:
  "2022-2023":
    start_date: "2022-08-29"
    end_date: "2023-06-15"
    periods:
      "P1 SY 22-23":
        start_date: "2022-09-01"
        end_date: "2022-11-30"
        color: "#4286f4"
      # Additional periods...
    holidays:
      - "2022-09-05"  # Labor Day
      # Additional holidays...
    professional_development_days:
      - "2022-10-14"
    virtual_days:
      - "2023-02-10"
```

### Activity Schedule Configuration (YAML)

```yaml
activity_schedules:
  # Default schedule
  default:
    - start_time: "08:00"
      end_time: "08:30"
      name: "Free Play"
      category: "Play"
    # Additional activities...

  # Fall 2022 Schedule
  "2022-09-01_2022-12-20":
    - start_time: "08:00"
      end_time: "08:30"
      name: "Free Play"
      category: "Play"
    # Additional activities...

  # Spring 2023 Schedule
  "2022-12-21_2023-06-15":
    - start_time: "08:15"  # 15 minutes later start
      end_time: "08:45"
      name: "Free Play"
      category: "Play"
    # Additional activities...
```

## Key Features

1. **Date-Range Based Activity Schedules**: Support for multiple classroom schedules within the same school year, enabling mid-year schedule changes.

2. **Flexible School Calendar**: Integration with school years, collection periods, holidays, and special non-collection days.

3. **Multi-Level Time Aggregation**: Analysis by day, ISO week, month, or custom collection periods.

4. **Activity-Based Analysis**: Grouping and metrics by classroom activities with support for schedule changes.

5. **Combined Dimensions**: Cross-analysis of activities by period and other flexible grouping options.

6. **Backward Compatibility**: Legacy support for existing interfaces like `get_activity_for_time(hour, minute)`.

## Next Steps

1. Integrate with existing data collection and processing pipelines
2. Create visualization modules for the aggregated data
3. Implement reporting modules using the multi-level metrics
