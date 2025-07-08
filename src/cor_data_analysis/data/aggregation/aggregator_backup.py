"""
Data Aggregation Framework

This module provides a flexible, multi-level data aggregation framework for analyzing
file metadata. It supports aggregation by various time periods (day, week, month)
and by activities, with support for mid-year schedule changes.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional, Any, Union, Set
from datetime import datetime, date, time, timedelta
import logging
from pathlib import Path
from ...calendar import SchoolCalendar, ActivitySchedule


class DataAggregator:
    """
    Main class for data aggregation operations across multiple dimensions.
    Supports time-based and activity-based aggregation with flexible grouping.
    """
    def __init__(
        self, 
        calendar: Optional[SchoolCalendar] = None,
        activity_schedule: Optional[ActivitySchedule] = None
    ):
        self.calendar = calendar
        self.activity_schedule = activity_schedule
        
    def aggregate_by_period(
        self, 
        mp3_df: pd.DataFrame, 
        jpg_df: pd.DataFrame
    ) -> pd.DataFrame:
        """
        Aggregate data by collection periods defined in the school calendar.
        Similar to the original calculate_period_metrics function.
        """
        if self.calendar is None:
            logging.warning("No calendar provided. Cannot aggregate by period.")
            return pd.DataFrame()
            
        period_data = []
        
        # Get a list of all periods across all school years
        all_periods = []
        for school_year in self.calendar.school_years.values():
            all_periods.extend(school_year.periods.values())
            
        for period in all_periods:
            # Create empty dataframes with correct columns if inputs are empty
            mp3_period_df = pd.DataFrame(columns=mp3_df.columns) if not mp3_df.empty else None
            jpg_period_df = pd.DataFrame(columns=jpg_df.columns) if not jpg_df.empty else None
            
            # Filter data for this period
            if not mp3_df.empty and 'Date' in mp3_df.columns:
                mp3_period_df = mp3_df[
                    (mp3_df['Date'] >= period.start_date) & 
                    (mp3_df['Date'] <= period.end_date)
                ]
                
            if not jpg_df.empty and 'Date' in jpg_df.columns:
                jpg_period_df = jpg_df[
                    (jpg_df['Date'] >= period.start_date) & 
                    (jpg_df['Date'] <= period.end_date)
                ]
                
            # Skip periods with no data
            if (mp3_period_df is None or mp3_period_df.empty) and (jpg_period_df is None or jpg_period_df.empty):
                logging.debug(f"No data found for period {period.name}, skipping")
                continue
                
            # Calculate metrics
            collection_days = self.calendar.count_collection_days(
                period.start_date, 
                period.end_date,
                group_by='period'
            )
            num_days = collection_days.get('period', {}).get(period.name, 0)
            
            # Calculate MP3 metrics
            mp3_count = len(mp3_period_df) if mp3_period_df is not None else 0
            mp3_total_size_mb = mp3_period_df['File Size (MB)'].sum() if mp3_period_df is not None and 'File Size (MB)' in mp3_period_df else 0
            mp3_unique_days = mp3_period_df['Date'].nunique() if mp3_period_df is not None and 'Date' in mp3_period_df else 0
            
            # Calculate duration metrics safely
            mp3_duration_metrics = self._calculate_duration_metrics(mp3_period_df)
            
            # Calculate JPG metrics
            jpg_count = len(jpg_period_df) if jpg_period_df is not None else 0
            jpg_total_size_mb = jpg_period_df['File Size (MB)'].sum() if jpg_period_df is not None and 'File Size (MB)' in jpg_period_df else 0
            jpg_unique_days = jpg_period_df['Date'].nunique() if jpg_period_df is not None and 'Date' in jpg_period_df else 0
            
            # Add to results
            period_data.append({
                'Collection Period': period.name,
                'Start Date': period.start_date,
                'End Date': period.end_date,
                'Collection Days': num_days,
                'JPG Count': jpg_count,
                'JPG Total Size (MB)': round(jpg_total_size_mb, 2),
                'JPG Unique Days': jpg_unique_days,
                'JPG Daily Average': round(jpg_count / num_days, 2) if num_days > 0 else 0,
                'MP3 Count': mp3_count,
                'MP3 Total Size (MB)': round(mp3_total_size_mb, 2),
                'MP3 Unique Days': mp3_unique_days,
                'MP3 Daily Average': round(mp3_count / num_days, 2) if num_days > 0 else 0,
                'Total Duration (seconds)': mp3_duration_metrics['total_seconds'],
                'Total Duration (HH:MM:SS)': self._format_seconds(mp3_duration_metrics['total_seconds']),
                'Avg Duration (HH:MM:SS)': self._format_seconds(mp3_duration_metrics['avg_seconds']),
                'Min Duration (HH:MM:SS)': self._format_seconds(mp3_duration_metrics['min_seconds']),
                'Max Duration (HH:MM:SS)': self._format_seconds(mp3_duration_metrics['max_seconds']),
                'Daily Avg Duration (HH:MM:SS)': self._format_seconds(
                    mp3_duration_metrics['total_seconds'] / num_days if num_days > 0 else 0
                ),
                'Total Count (JPG + MP3)': jpg_count + mp3_count,
                'Daily Avg (JPG + MP3)': round((jpg_count + mp3_count) / num_days, 2) if num_days > 0 else 0,
            })
            
        # Convert to DataFrame
        return pd.DataFrame(period_data) if period_data else pd.DataFrame()
        
    def aggregate_by_time(
        self, 
        mp3_df: pd.DataFrame, 
        jpg_df: pd.DataFrame,
        time_unit: str = 'month'
    ) -> pd.DataFrame:
        """
        Aggregate data by time units (day, week, month).
        Supports ISO week numbering for weekly aggregation.
        """
        valid_units = ['day', 'week', 'month']
        if time_unit not in valid_units:
            logging.error(f"Invalid time unit: {time_unit}. Must be one of {valid_units}")
            return pd.DataFrame()
        
        # Ensure Date column is datetime
        mp3_df_with_date = self._ensure_datetime(mp3_df, 'Date') if not mp3_df.empty else pd.DataFrame()
        jpg_df_with_date = self._ensure_datetime(jpg_df, 'Date') if not jpg_df.empty else pd.DataFrame()
        
        # Group by the specified time unit
        if time_unit == 'day':
            mp3_grouped = mp3_df_with_date.groupby(mp3_df_with_date['Date'].dt.date) if not mp3_df_with_date.empty else None
            jpg_grouped = jpg_df_with_date.groupby(jpg_df_with_date['Date'].dt.date) if not jpg_df_with_date.empty else None
            date_format = '%Y-%m-%d'
        elif time_unit == 'week':
            # Use ISO week numbering (week 1 starts first week of year)
            if not mp3_df_with_date.empty:
                mp3_df_with_date['Year_Week'] = mp3_df_with_date['Date'].dt.strftime('%G-W%V')  # ISO year and week
                mp3_grouped = mp3_df_with_date.groupby('Year_Week')
            else:
                mp3_grouped = None
                
            if not jpg_df_with_date.empty:
                jpg_df_with_date['Year_Week'] = jpg_df_with_date['Date'].dt.strftime('%G-W%V')  # ISO year and week
                jpg_grouped = jpg_df_with_date.groupby('Year_Week')
            else:
                jpg_grouped = None
                
            date_format = 'ISO Week'  # Special case for display
        else:  # month
            if not mp3_df_with_date.empty:
                mp3_df_with_date['Year_Month'] = mp3_df_with_date['Date'].dt.strftime('%Y-%m')
                mp3_grouped = mp3_df_with_date.groupby('Year_Month')
            else:
                mp3_grouped = None
                
            if not jpg_df_with_date.empty:
                jpg_df_with_date['Year_Month'] = jpg_df_with_date['Date'].dt.strftime('%Y-%m')
                jpg_grouped = jpg_df_with_date.groupby('Year_Month')
            else:
                jpg_grouped = None
                
            date_format = '%Y-%m'
            
        # Calculate metrics for each group
        time_data = []
        
        # Get all time periods from both datasets
        all_periods = set()
        if mp3_grouped is not None:
            all_periods.update(mp3_grouped.groups.keys())
        if jpg_grouped is not None:
            all_periods.update(jpg_grouped.groups.keys())
            
        for period in sorted(all_periods):
            # Get data for this period
            mp3_period = mp3_grouped.get_group(period) if mp3_grouped is not None and period in mp3_grouped.groups else pd.DataFrame()
            jpg_period = jpg_grouped.get_group(period) if jpg_grouped is not None and period in jpg_grouped.groups else pd.DataFrame()
            
            # Calculate collection days
            if time_unit == 'day':
                # For day level, it's either 1 or 0
                collection_day = 1 if self.calendar and self.calendar.is_collection_day(period) else 0
                active_days = collection_day
            else:
                # For week/month, we need to determine the date range
                start_date, end_date = self._get_date_range_for_period(period, time_unit)
                collection_days_dict = (
                    self.calendar.count_collection_days(start_date, end_date, group_by=time_unit)
                    if self.calendar and start_date and end_date else {}
                )
                
                if time_unit == 'week':
                    active_days = collection_days_dict.get('week', {}).get(period, 0)
                else:  # month
                    active_days = collection_days_dict.get('month', {}).get(period, 0)
            
            # Calculate metrics
            mp3_count = len(mp3_period)
            mp3_unique_days = mp3_period['Date'].dt.date.nunique() if not mp3_period.empty else 0
            
            jpg_count = len(jpg_period)
            jpg_unique_days = jpg_period['Date'].dt.date.nunique() if not jpg_period.empty else 0
            
            # Calculate duration metrics
            mp3_duration_metrics = self._calculate_duration_metrics(mp3_period)
            
            # Add to results with the correct period name formatting
            period_name = period if date_format == 'ISO Week' else period
            
            time_data.append({
                f'{time_unit.capitalize()}': period_name,
                'Collection Days': active_days,
                'MP3 Count': mp3_count,
                'MP3 Unique Days': mp3_unique_days,
                'MP3 Daily Average': round(mp3_count / active_days, 2) if active_days > 0 else 0,
                'Total Duration (seconds)': mp3_duration_metrics['total_seconds'],
                'Avg Duration (HH:MM:SS)': self._format_seconds(mp3_duration_metrics['avg_seconds']),
                'JPG Count': jpg_count,
                'JPG Unique Days': jpg_unique_days,
                'JPG Daily Average': round(jpg_count / active_days, 2) if active_days > 0 else 0,
                'Total Count (JPG + MP3)': mp3_count + jpg_count,
                'Daily Avg (JPG + MP3)': round((mp3_count + jpg_count) / active_days, 2) if active_days > 0 else 0,
            })
            
        # Convert to DataFrame and sort by period
        result_df = pd.DataFrame(time_data) if time_data else pd.DataFrame()
        if not result_df.empty:
            period_col = f'{time_unit.capitalize()}'
            result_df = result_df.sort_values(by=period_col)
            
        return result_df

    def aggregate_by_activity(
        self, 
        mp3_df: pd.DataFrame, 
        jpg_df: pd.DataFrame,
        include_periods: bool = True
    ) -> pd.DataFrame:
        """
        Aggregate data by classroom activities, optionally breaking down by collection periods.
        Handles mid-year schedule changes by using the appropriate schedule for each date.
        """
        if self.activity_schedule is None:
            logging.warning("No activity schedule provided. Cannot aggregate by activity.")
            return pd.DataFrame()
        
        # Ensure we have the needed columns
        mp3_with_datetime = self._ensure_datetime_columns(mp3_df) if not mp3_df.empty else pd.DataFrame()
        jpg_with_datetime = self._ensure_datetime_columns(jpg_df) if not jpg_df.empty else pd.DataFrame()
        
        # Get all activities across all schedule periods
        all_activities = set()
        for period in self.activity_schedule.schedule_periods:
            for activity in period.activities:
                all_activities.add(activity.name)
                
        # Add activities from the default schedule if any
        for activity in self.activity_schedule.default_activities:
            all_activities.add(activity.name)
            
        # Sort activities by typical daily order
        all_activities = sorted(all_activities)
        
        # Map timestamps to activities using the appropriate schedule for each date
        if not mp3_with_datetime.empty:
            mp3_with_datetime['Activity'] = mp3_with_datetime.apply(
                lambda row: self.activity_schedule.get_activity_name_for_datetime(
                    row['DateTime']
                ),
                axis=1
            )
            
        if not jpg_with_datetime.empty:
            jpg_with_datetime['Activity'] = jpg_with_datetime.apply(
                lambda row: self.activity_schedule.get_activity_name_for_datetime(
                    row['DateTime']
                ),
                axis=1
            )
        
        # Group by activity (and optionally by period)
        activity_data = []
        
        if include_periods and self.calendar:
            # Get periods to include
            all_periods = []
            for school_year in self.calendar.school_years.values():
                all_periods.extend(list(school_year.periods.values()))
                
            # Limit to 3 periods for compatibility with original code
            all_periods = all_periods[:3]
            
            # For each activity, calculate metrics across periods
            for activity_name in all_activities:
                row = {'Activity': activity_name}
                
                for i, period in enumerate(all_periods, 1):
                    # Filter data for this activity and period
                    if not mp3_with_datetime.empty:
                        mp3_activity_period = mp3_with_datetime[
                            (mp3_with_datetime['Activity'] == activity_name) & 
                            (mp3_with_datetime['Date'] >= period.start_date) &
                            (mp3_with_datetime['Date'] <= period.end_date)
                        ]
                    else:
                        mp3_activity_period = pd.DataFrame()
                        
                    if not jpg_with_datetime.empty:
                        jpg_activity_period = jpg_with_datetime[
                            (jpg_with_datetime['Activity'] == activity_name) & 
                            (jpg_with_datetime['Date'] >= period.start_date) &
                            (jpg_with_datetime['Date'] <= period.end_date)
                        ]
                    else:
                        jpg_activity_period = pd.DataFrame()
                    
                    # Count collection days in this period
                    collection_days = self.calendar.count_collection_days(
                        period.start_date, period.end_date, group_by='period'
                    )
                    num_days = collection_days.get('period', {}).get(period.name, 0)
                    
                    # Calculate metrics
                    mp3_count = len(mp3_activity_period)
                    jpg_count = len(jpg_activity_period)
                    
                    # Add metrics to row
                    row[f'JPG Count P{i}'] = jpg_count
                    row[f'JPG Daily Avg P{i}'] = round(jpg_count / num_days, 2) if num_days > 0 else 0
                    row[f'MP3 Count P{i}'] = mp3_count
                    row[f'MP3 Daily Avg P{i}'] = round(mp3_count / num_days, 2) if num_days > 0 else 0
                
                activity_data.append(row)
        else:
            # Simple activity aggregation without periods
            for activity_name in all_activities:
                if not mp3_with_datetime.empty:
                    mp3_activity = mp3_with_datetime[mp3_with_datetime['Activity'] == activity_name]
                else:
                    mp3_activity = pd.DataFrame()
                    
                if not jpg_with_datetime.empty:
                    jpg_activity = jpg_with_datetime[jpg_with_datetime['Activity'] == activity_name]
                else:
                    jpg_activity = pd.DataFrame()
                
                # Calculate metrics
                mp3_count = len(mp3_activity)
                jpg_count = len(jpg_activity)
                
                # Calculate duration metrics for this activity
                mp3_duration_metrics = self._calculate_duration_metrics(mp3_activity)
                
                activity_data.append({
                    'Activity': activity_name,
                    'MP3 Count': mp3_count,
                    'MP3 Total Duration (HH:MM:SS)': self._format_seconds(mp3_duration_metrics['total_seconds']),
                    'MP3 Avg Duration (HH:MM:SS)': self._format_seconds(mp3_duration_metrics['avg_seconds']),
                    'JPG Count': jpg_count,
                    'Total Count': mp3_count + jpg_count
                })
                
        # Convert to DataFrame
        return pd.DataFrame(activity_data)
    
    def _calculate_duration_metrics(self, df: pd.DataFrame) -> Dict[str, float]:
        """Calculate duration metrics from a DataFrame containing Duration (seconds) column."""
        metrics = {
            'total_seconds': 0,
            'avg_seconds': 0,
            'min_seconds': 0,
            'max_seconds': 0
        }
        
        if df is None or df.empty or 'Duration (seconds)' not in df.columns:
            return metrics
            
        duration_col = df['Duration (seconds)']
        if not pd.api.types.is_numeric_dtype(duration_col):
            return metrics
            
        metrics['total_seconds'] = duration_col.sum()
        metrics['avg_seconds'] = duration_col.mean() if len(df) > 0 else 0
        metrics['min_seconds'] = duration_col.min() if len(df) > 0 else 0
        metrics['max_seconds'] = duration_col.max() if len(df) > 0 else 0
        
        return metrics
    
    def _format_seconds(self, seconds: float) -> str:
        """Format seconds as HH:MM:SS."""
        if pd.isna(seconds) or seconds < 0:
            return "00:00:00"
            
        try:
            hours, remainder = divmod(int(seconds), 3600)
            minutes, seconds = divmod(remainder, 60)
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        except Exception as e:
            logging.error(f"Error formatting seconds {seconds}: {e}")
            return "00:00:00"
    
    def _ensure_datetime(self, df: pd.DataFrame, date_col: str) -> pd.DataFrame:
        """Ensure the Date column is datetime type."""
        if df.empty or date_col not in df.columns:
            return df
            
        result = df.copy()
        if not pd.api.types.is_datetime64_dtype(result[date_col]):
            result[date_col] = pd.to_datetime(result[date_col])
            
        return result
    
    def _ensure_datetime_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Ensure Date is datetime and add DateTime column combining Date and Time.
        Used for activity mapping.
        """
        if df.empty or 'Date' not in df.columns or 'Time' not in df.columns:
            return df
            
        result = df.copy()
        
        # Ensure Date is datetime
        if not pd.api.types.is_datetime64_dtype(result['Date']):
            result['Date'] = pd.to_datetime(result['Date'])
            
        # Create DateTime column by combining Date and Time
        result['DateTime'] = result.apply(
            lambda row: self._combine_date_time(row['Date'], row['Time']),
            axis=1
        )
        
        return result
    
    @staticmethod
    def _combine_date_time(d: pd.Timestamp, t: str) -> datetime:
        """Combine a date and time string into a datetime object."""
        try:
            hours, minutes = map(int, t.split(':'))
            return datetime.combine(
                d.date(),
                time(hour=hours, minute=minutes)
            )
        except Exception as e:
            logging.error(f"Error combining date {d} and time {t}: {e}")
            return d  # Fall back to just the date with time at midnight
    
    def aggregate_by_activity_category(self, mp3_df, jpg_df):
        """
        Aggregate data by activity category.
        
        Group activities by their categories (e.g., Meal, Instruction) and
        aggregate metrics within each category.
        
        Args:
            mp3_df (pd.DataFrame): DataFrame containing MP3 metadata.
            jpg_df (pd.DataFrame): DataFrame containing JPG metadata.
            
        Returns:
            dict: Dictionary with category keys, each containing aggregated metrics.
        """
        if self.activity_schedule is None:
            logging.warning("No activity schedule provided. Cannot aggregate by activity category.")
            return {}
            
        # Add activity information for aggregation
        mp3_df_with_activity = self._add_activity_columns(mp3_df.copy())
        jpg_df_with_activity = self._add_activity_columns(jpg_df.copy())
        
        categories = {}
        
        # Get unique categories
        all_categories = set()
        for mp3_category in mp3_df_with_activity['ActivityCategory'].dropna().unique():
            all_categories.add(mp3_category)
        for jpg_category in jpg_df_with_activity['ActivityCategory'].dropna().unique():
            all_categories.add(jpg_category)
        
        # For each category, calculate metrics
        for category in sorted(all_categories):
            if pd.isna(category):
                continue
                
            # Filter data for this category
            category_mp3 = mp3_df_with_activity[mp3_df_with_activity['ActivityCategory'] == category]
            category_jpg = jpg_df_with_activity[jpg_df_with_activity['ActivityCategory'] == category]
            
            # Calculate basic metrics
            category_metrics = {
                'mp3_count': len(category_mp3),
                'jpg_count': len(category_jpg)
            }
            
            # Calculate MP3 size metrics
            if len(category_mp3) > 0:
                if 'FileSize' in category_mp3.columns:
                    category_metrics['mp3_size_bytes'] = category_mp3['FileSize'].sum()
                    category_metrics['mp3_size_mb'] = category_mp3['FileSize'].sum() / (1024 * 1024)
                elif 'File Size (MB)' in category_mp3.columns:
                    category_metrics['mp3_size_mb'] = category_mp3['File Size (MB)'].sum()
                    category_metrics['mp3_size_bytes'] = category_mp3['File Size (MB)'].sum() * (1024 * 1024)  # Approximate
            else:
                category_metrics['mp3_size_bytes'] = 0
                category_metrics['mp3_size_mb'] = 0
                
            # Calculate JPG size metrics
            if len(category_jpg) > 0:
                if 'FileSize' in category_jpg.columns:
                    category_metrics['jpg_size_bytes'] = category_jpg['FileSize'].sum()
                    category_metrics['jpg_size_mb'] = category_jpg['FileSize'].sum() / (1024 * 1024)
                elif 'File Size (MB)' in category_jpg.columns:
                    category_metrics['jpg_size_mb'] = category_jpg['File Size (MB)'].sum()
                    category_metrics['jpg_size_bytes'] = category_jpg['File Size (MB)'].sum() * (1024 * 1024)  # Approximate
            else:
                category_metrics['jpg_size_bytes'] = 0
                category_metrics['jpg_size_mb'] = 0
            
            # Get activities in this category
            category_activities = set(category_mp3['Activity'].dropna().unique()) | set(category_jpg['Activity'].dropna().unique())
            category_metrics['activities'] = sorted(list(category_activities))
            
            # Calculate duration metrics if available
            if 'Duration' in category_mp3.columns and len(category_mp3) > 0:
                category_metrics.update({
                    'total_duration_seconds': category_mp3['Duration'].sum(),
                    'total_duration_formatted': self._format_duration(category_mp3['Duration'].sum()),
                    'average_duration_seconds': category_mp3['Duration'].mean(),
                    'average_duration_formatted': self._format_duration(category_mp3['Duration'].mean()),
                })
                
            categories[category] = category_metrics
            
        return categories
    
    def aggregate_by_activity_and_period(self, mp3_df, jpg_df):
        """
        Aggregate data by activity and collection period.
        
        This combines the activity and period dimensions to provide a detailed view
        of how each activity is performing across different collection periods.
        
        Args:
            mp3_df (pd.DataFrame): DataFrame containing MP3 metadata.
            jpg_df (pd.DataFrame): DataFrame containing JPG metadata.
            
        Returns:
            dict: Dictionary with period keys, each containing a nested dictionary of 
                  activity metrics.
        """
        # Add activity information
        mp3_df_with_activity = self._add_activity_columns(mp3_df.copy())
        jpg_df_with_activity = self._add_activity_columns(jpg_df.copy())
        
        # Get periods
        periods = {}
        for year_name, year in self.calendar.school_years.items():
            for period_name, period in year.periods.items():
                periods[period_name] = (period.start_date, period.end_date)
        
        results = {}
        
        # For each period
        for period_name, (start_date, end_date) in periods.items():
            # Filter for this period
            period_mp3 = mp3_df_with_activity[
                (mp3_df_with_activity['Date'] >= pd.Timestamp(start_date)) & 
                (mp3_df_with_activity['Date'] <= pd.Timestamp(end_date))
            ]
            
            period_jpg = jpg_df_with_activity[
                (jpg_df_with_activity['Date'] >= pd.Timestamp(start_date)) & 
                (jpg_df_with_activity['Date'] <= pd.Timestamp(end_date))
            ]
            
            # Skip if no data
            if len(period_mp3) == 0 and len(period_jpg) == 0:
                continue
            
            # Group by activity
            results[period_name] = {}
            
            # Get unique activities in this period
            activities = set(period_mp3['Activity'].dropna().unique()) | set(period_jpg['Activity'].dropna().unique())
            
            for activity in activities:
                if pd.isna(activity):
                    continue
                    
                # Filter for this activity
                activity_mp3 = period_mp3[period_mp3['Activity'] == activity]
                activity_jpg = period_jpg[period_jpg['Activity'] == activity]
                
                # Calculate metrics
                activity_metrics = {
                    'mp3_count': len(activity_mp3),
                    'mp3_files': activity_mp3.to_dict('records') if len(activity_mp3) > 0 else [],
                    'jpg_count': len(activity_jpg),
                    'jpg_files': activity_jpg.to_dict('records') if len(activity_jpg) > 0 else [],
                }
                
                # Calculate MP3 size metrics
                if len(activity_mp3) > 0:
                    if 'FileSize' in activity_mp3.columns:
                        activity_metrics['mp3_size_bytes'] = activity_mp3['FileSize'].sum()
                        activity_metrics['mp3_size_mb'] = activity_mp3['FileSize'].sum() / (1024 * 1024)
                    elif 'File Size (MB)' in activity_mp3.columns:
                        activity_metrics['mp3_size_mb'] = activity_mp3['File Size (MB)'].sum()
                        activity_metrics['mp3_size_bytes'] = activity_mp3['File Size (MB)'].sum() * (1024 * 1024)  # Approximate
                else:
                    activity_metrics['mp3_size_bytes'] = 0
                    activity_metrics['mp3_size_mb'] = 0
                    
                # Calculate JPG size metrics
                if len(activity_jpg) > 0:
                    if 'FileSize' in activity_jpg.columns:
                        activity_metrics['jpg_size_bytes'] = activity_jpg['FileSize'].sum()
                        activity_metrics['jpg_size_mb'] = activity_jpg['FileSize'].sum() / (1024 * 1024)
                    elif 'File Size (MB)' in activity_jpg.columns:
                        activity_metrics['jpg_size_mb'] = activity_jpg['File Size (MB)'].sum()
                        activity_metrics['jpg_size_bytes'] = activity_jpg['File Size (MB)'].sum() * (1024 * 1024)  # Approximate
                else:
                    activity_metrics['jpg_size_bytes'] = 0
                    activity_metrics['jpg_size_mb'] = 0
                
                # Calculate duration metrics if available
                if 'Duration' in activity_mp3.columns and len(activity_mp3) > 0:
                    activity_metrics.update({
                        'total_duration_seconds': activity_mp3['Duration'].sum(),
                        'total_duration_formatted': self._format_duration(activity_mp3['Duration'].sum()),
                        'average_duration_seconds': activity_mp3['Duration'].mean(),
                        'average_duration_formatted': self._format_duration(activity_mp3['Duration'].mean()),
                    })
                
                results[period_name][activity] = activity_metrics
                
        return results
        
    def aggregate_by_school_year(self, mp3_df, jpg_df):
        """
        Aggregates MP3 and JPG file metadata by school year.

        This method calculates key metrics for each school year defined in the calendar,
        including file counts, sizes, durations, and distributions by activity
        and category. It is designed to be robust against missing data and
        inconsistent dictionary structures, which resolves the "ValueError: All arrays
        must be of the same length" error.

        Args:
            mp3_df (pd.DataFrame): DataFrame containing MP3 metadata.
            jpg_df (pd.DataFrame): DataFrame containing JPG metadata.

        Returns:
            dict: A dictionary where keys are school year names and values are
                  nested dictionaries of aggregated metrics for that year.
        """
        results = {}
        if self.calendar is None:
            logging.warning("No SchoolCalendar provided; cannot aggregate by school year.")
            return results

        # --- 1. Data Preparation ---
        # Create copies to avoid side effects on the original DataFrames.
        # If a dataframe is None or empty, initialize it as an empty DataFrame to prevent errors.
        mp3_df_processed = mp3_df.copy() if mp3_df is not None and not mp3_df.empty else pd.DataFrame()
        jpg_df_processed = jpg_df.copy() if jpg_df is not None and not jpg_df.empty else pd.DataFrame()

        # Add necessary helper columns. These methods should handle empty DataFrames gracefully.
        if not mp3_df_processed.empty:
            mp3_df_processed = self._ensure_datetime_columns(mp3_df_processed)
            mp3_df_processed = self._add_activity_columns(mp3_df_processed)
            # Standardize missing activity/category data to 'Unknown' for consistent grouping.
            if 'Activity' in mp3_df_processed.columns:
                mp3_df_processed['Activity'].fillna('Unknown', inplace=True)
            if 'ActivityCategory' in mp3_df_processed.columns:
                mp3_df_processed['ActivityCategory'].fillna('Unknown', inplace=True)

        if not jpg_df_processed.empty:
            jpg_df_processed = self._ensure_datetime_columns(jpg_df_processed)
            jpg_df_processed = self._add_activity_columns(jpg_df_processed)
            if 'Activity' in jpg_df_processed.columns:
                jpg_df_processed['Activity'].fillna('Unknown', inplace=True)
            if 'ActivityCategory' in jpg_df_processed.columns:
                jpg_df_processed['ActivityCategory'].fillna('Unknown', inplace=True)

        # --- 2. Iterate Through School Years ---
        try:
            school_years = self.calendar.get_years()
        except Exception as e:
            logging.error(f"Could not retrieve school years from calendar: {e}")
            return {}

        for year_name, (start_date, end_date) in school_years.items():
            logging.info(f"Processing school year: {year_name} ({start_date} to {end_date})")

            # Filter data for the current school year.
            try:
                year_mp3 = mp3_df_processed[
                    (mp3_df_processed['Date'] >= pd.Timestamp(start_date)) & 
                    (mp3_df_processed['Date'] <= pd.Timestamp(end_date))
                ] if not mp3_df_processed.empty else pd.DataFrame()
                
                year_jpg = jpg_df_processed[
                    (jpg_df_processed['Date'] >= pd.Timestamp(start_date)) & 
                    (jpg_df_processed['Date'] <= pd.Timestamp(end_date))
                ] if not jpg_df_processed.empty else pd.DataFrame()
            except Exception as e:
                logging.error(f"Error filtering data for year {year_name}: {e}")
                year_mp3 = pd.DataFrame()
                year_jpg = pd.DataFrame()

            if year_mp3.empty and year_jpg.empty:
                logging.info(f"No data for school year {year_name}, skipping.")
                continue

            # --- 3. Calculate Base Metrics ---
            total_mp3_count = len(year_mp3)
            total_jpg_count = len(year_jpg)

            # Calculate unique collection days based on the presence of any file.
            try:
                mp3_dates = set(year_mp3['Date'].dt.date) if not year_mp3.empty and 'Date' in year_mp3.columns else set()
                jpg_dates = set(year_jpg['Date'].dt.date) if not year_jpg.empty and 'Date' in year_jpg.columns else set()
                collection_days = len(mp3_dates.union(jpg_dates))
            except Exception as e:
                logging.error(f"Error calculating collection days: {e}")
                collection_days = 0

            # --- 4. Activity & Category Distribution (Core Fix) ---
            # This section ensures dictionary keys are consistent, preventing the ValueError.
            def get_distribution(df, total_count, col_name):
                """Helper to calculate distribution for activities or categories."""
                distribution = {}
                if df.empty or col_name not in df.columns:
                    return distribution
                
                try:
                    # Group by the column and count occurrences.
                    counts = df.groupby(col_name).size()
                    
                    for item_name, count in counts.items():
                        distribution[item_name] = {
                            'count': count,
                            'percentage': (count / total_count * 100) if total_count > 0 else 0.0,
                        }
                    return distribution
                except Exception as e:
                    logging.error(f"Error calculating distribution for {col_name}: {e}")
                    return {}

            # Calculate distributions
            mp3_activity_dist = get_distribution(year_mp3, total_mp3_count, 'Activity')
            jpg_activity_dist = get_distribution(year_jpg, total_jpg_count, 'Activity')
            
            mp3_category_dist = get_distribution(year_mp3, total_mp3_count, 'ActivityCategory')
            jpg_category_dist = get_distribution(year_jpg, total_jpg_count, 'ActivityCategory')

            # Combine distributions, ensuring all activities/categories are present
            all_activities = sorted(list(set(mp3_activity_dist.keys()).union(set(jpg_activity_dist.keys()))))
            all_categories = sorted(list(set(mp3_category_dist.keys()).union(set(jpg_category_dist.keys()))))

            # Ensure we always have at least one entry (Unknown) if everything is empty
            if not all_activities:
                all_activities = ['Unknown']
            if not all_categories:
                all_categories = ['Unknown']
                
            # Create consistent activity distribution dictionaries
            final_activity_dist = {}
            for activity in all_activities:
                final_activity_dist[activity] = {
                    'mp3_count': mp3_activity_dist.get(activity, {}).get('count', 0),
                    'mp3_percentage': mp3_activity_dist.get(activity, {}).get('percentage', 0.0),
                    'jpg_count': jpg_activity_dist.get(activity, {}).get('count', 0),
                    'jpg_percentage': jpg_activity_dist.get(activity, {}).get('percentage', 0.0),
                }

            # Create consistent category distribution dictionaries
            final_category_dist = {}
            for category in all_categories:
                final_category_dist[category] = {
                    'mp3_count': mp3_category_dist.get(category, {}).get('count', 0),
                    'mp3_percentage': mp3_category_dist.get(category, {}).get('percentage', 0.0),
                    'jpg_count': jpg_category_dist.get(category, {}).get('count', 0),
                    'jpg_percentage': jpg_category_dist.get(category, {}).get('percentage', 0.0),
                }

            # --- 5. Calculate Duration Metrics ---
            total_duration_seconds = 0
            if not year_mp3.empty:
                try:
                    # Check for both possible duration column names
                    if 'Duration (seconds)' in year_mp3.columns:
                        total_duration_seconds = year_mp3['Duration (seconds)'].sum()
                    elif 'Duration' in year_mp3.columns:
                        total_duration_seconds = year_mp3['Duration'].sum()
                except Exception as e:
                    logging.error(f"Error calculating total duration: {e}")
                    total_duration_seconds = 0

            # Calculate average duration per day
            avg_duration_per_day = 0
            if collection_days > 0 and total_duration_seconds > 0:
                avg_duration_per_day = total_duration_seconds / collection_days

            # --- 6. Get periods for this school year ---
            periods_list = []
            try:
                periods = self.calendar.get_periods_in_year(year_name)
                if periods is not None:
                    # Convert period info to serializable format
                    periods_list = [
                        {
                            'name': period_name,
                            'start_date': period_start_date.isoformat() if hasattr(period_start_date, 'isoformat') else str(period_start_date),
                            'end_date': period_end_date.isoformat() if hasattr(period_end_date, 'isoformat') else str(period_end_date)
                        }
                        for period_name, (period_start_date, period_end_date) in periods.items()
                    ]
            except Exception as e:
                logging.error(f"Error getting periods for year {year_name}: {e}")

            # --- 7. Assemble Final Metrics for the Year ---
            # Initialize all metrics with default values to ensure consistent structure
            year_metrics = {
                'start_date': start_date.isoformat() if hasattr(start_date, 'isoformat') else str(start_date),
                'end_date': end_date.isoformat() if hasattr(end_date, 'isoformat') else str(end_date),
                'mp3_count': total_mp3_count,
                'jpg_count': total_jpg_count,
                'mp3_size_bytes': 0,
                'mp3_size_mb': 0.0,
                'jpg_size_bytes': 0,
                'jpg_size_mb': 0.0,
                'mp3_unique_dates': 0,
                'jpg_unique_dates': 0,
                'collection_days': collection_days,
                'average_mp3_per_day': (total_mp3_count / collection_days) if collection_days > 0 else 0.0,
                'average_jpg_per_day': (total_jpg_count / collection_days) if collection_days > 0 else 0.0,
                'total_duration_seconds': total_duration_seconds,
                'total_duration_formatted': self._format_duration(total_duration_seconds),
                'average_duration_per_day_seconds': avg_duration_per_day,
                'average_duration_per_day_formatted': self._format_duration(avg_duration_per_day),
                'periods': periods_list,
                'activity_distribution': final_activity_dist,
                'category_distribution': final_category_dist
            }

            # Calculate unique dates
            if not year_mp3.empty and 'Date' in year_mp3.columns:
                try:
                    year_metrics['mp3_unique_dates'] = len(year_mp3['Date'].dt.date.unique())
                except Exception as e:
                    logging.error(f"Error calculating MP3 unique dates: {e}")
            
            if not year_jpg.empty and 'Date' in year_jpg.columns:
                try:
                    year_metrics['jpg_unique_dates'] = len(year_jpg['Date'].dt.date.unique())
                except Exception as e:
                    logging.error(f"Error calculating JPG unique dates: {e}")

            # Calculate file size metrics
            if not year_mp3.empty:
                try:
                    if 'File Size' in year_mp3.columns:
                        year_metrics['mp3_size_bytes'] = int(year_mp3['File Size'].sum())
                        year_metrics['mp3_size_mb'] = round(year_metrics['mp3_size_bytes'] / (1024 * 1024), 2)
                    elif 'File Size (MB)' in year_mp3.columns:
                        year_metrics['mp3_size_mb'] = round(year_mp3['File Size (MB)'].sum(), 2)
                        year_metrics['mp3_size_bytes'] = int(year_metrics['mp3_size_mb'] * 1024 * 1024)
                except Exception as e:
                    logging.error(f"Error calculating MP3 size metrics: {e}")
            
            if not year_jpg.empty:
                try:
                    if 'File Size' in year_jpg.columns:
                        year_metrics['jpg_size_bytes'] = int(year_jpg['File Size'].sum())
                        year_metrics['jpg_size_mb'] = round(year_metrics['jpg_size_bytes'] / (1024 * 1024), 2)
                    elif 'File Size (MB)' in year_jpg.columns:
                        year_metrics['jpg_size_mb'] = round(year_jpg['File Size (MB)'].sum(), 2)
                        year_metrics['jpg_size_bytes'] = int(year_metrics['jpg_size_mb'] * 1024 * 1024)
                except Exception as e:
                    logging.error(f"Error calculating JPG size metrics: {e}")

            # Add year metrics to results
            results[year_name] = year_metrics
            
        return results
        results = {}
        if self.calendar is None:
            logging.warning("No SchoolCalendar provided; cannot aggregate by school year.")
            return results

        # --- 1. Data Preparation ---
        # Create copies to avoid side effects on the original DataFrames.
        # If a dataframe is None or empty, initialize it as an empty DataFrame to prevent errors.
        mp3_df_processed = mp3_df.copy() if mp3_df is not None and not mp3_df.empty else pd.DataFrame()
        jpg_df_processed = jpg_df.copy() if jpg_df is not None and not jpg_df.empty else pd.DataFrame()

        # Add necessary helper columns. This logic assumes these helper methods exist in your class.
        # These methods should handle empty DataFrames gracefully.
        if not mp3_df_processed.empty:
            mp3_df_processed = self._ensure_datetime_columns(mp3_df_processed)
            mp3_df_processed = self._add_activity_columns(mp3_df_processed)
            # Standardize missing activity/category data to 'Unknown' for consistent grouping.
            if 'Activity' in mp3_df_processed.columns:
                mp3_df_processed['Activity'].fillna('Unknown', inplace=True)
            if 'ActivityCategory' in mp3_df_processed.columns:
                mp3_df_processed['ActivityCategory'].fillna('Unknown', inplace=True)

        if not jpg_df_processed.empty:
            jpg_df_processed = self._ensure_datetime_columns(jpg_df_processed)
            jpg_df_processed = self._add_activity_columns(jpg_df_processed)
            if 'Activity' in jpg_df_processed.columns:
                jpg_df_processed['Activity'].fillna('Unknown', inplace=True)
            if 'ActivityCategory' in jpg_df_processed.columns:
                jpg_df_processed['ActivityCategory'].fillna('Unknown', inplace=True)
        
        # --- 2. Iterate Through School Years ---
        try:
            school_years = self.calendar.get_years()
        except Exception as e:
            logging.error(f"Could not retrieve school years from calendar: {e}")
            return {}

        for year_name, (start_date, end_date) in school_years.items():
            logging.info(f"Processing school year: {year_name} ({start_date} to {end_date})")

            # Filter data for the current school year
            try:
                year_mp3 = mp3_df_processed[
                    (mp3_df_processed['Date'] >= pd.Timestamp(start_date)) & 
                    (mp3_df_processed['Date'] <= pd.Timestamp(end_date))
                ] if not mp3_df_processed.empty else pd.DataFrame()
                
                year_jpg = jpg_df_processed[
                    (jpg_df_processed['Date'] >= pd.Timestamp(start_date)) & 
                    (jpg_df_processed['Date'] <= pd.Timestamp(end_date))
                ] if not jpg_df_processed.empty else pd.DataFrame()
            except Exception as e:
                logging.error(f"Error filtering data for year {year_name}: {e}")
                year_mp3 = pd.DataFrame()
                year_jpg = pd.DataFrame()

            if year_mp3.empty and year_jpg.empty:
                logging.info(f"No data for school year {year_name}, skipping.")
                continue

            # --- 3. Calculate Base Metrics ---
            total_mp3_count = len(year_mp3)
            total_jpg_count = len(year_jpg)

            # Calculate unique collection days based on the presence of any file
            try:
                mp3_dates = set(year_mp3['Date'].dt.date) if not year_mp3.empty and 'Date' in year_mp3.columns else set()
                jpg_dates = set(year_jpg['Date'].dt.date) if not year_jpg.empty and 'Date' in year_jpg.columns else set()
                collection_days = len(mp3_dates.union(jpg_dates))
            except Exception as e:
                logging.error(f"Error calculating collection days: {e}")
                collection_days = 0
            
            # --- 4. Activity & Category Distribution (Core Fix) ---
            # This section ensures dictionary keys are consistent, preventing the ValueError.
            def get_distribution(df, total_count, col_name):
                """Helper to calculate distribution for activities or categories."""
                distribution = {}
                if df.empty or col_name not in df.columns:
                    return distribution
                
                try:
                    # Group by the column and count occurrences
                    counts = df.groupby(col_name).size()
                    
                    for item_name, count in counts.items():
                        distribution[item_name] = {
                            'count': count,
                            'percentage': (count / total_count * 100) if total_count > 0 else 0.0,
                        }
                    return distribution
                except Exception as e:
                    logging.error(f"Error calculating distribution for {col_name}: {e}")
                    return {}

            # Calculate distributions
            mp3_activity_dist = get_distribution(year_mp3, total_mp3_count, 'Activity')
            jpg_activity_dist = get_distribution(year_jpg, total_jpg_count, 'Activity')
            
            mp3_category_dist = get_distribution(year_mp3, total_mp3_count, 'ActivityCategory')
            jpg_category_dist = get_distribution(year_jpg, total_jpg_count, 'ActivityCategory')

            # Combine distributions, ensuring all activities/categories are present
            all_activities = sorted(list(set(mp3_activity_dist.keys()).union(set(jpg_activity_dist.keys()))))
            all_categories = sorted(list(set(mp3_category_dist.keys()).union(set(jpg_category_dist.keys()))))

            # Ensure we always have at least one entry (Unknown) if everything is empty
            if not all_activities:
                all_activities = ['Unknown']
            if not all_categories:
                all_categories = ['Unknown']
                
            # Create consistent activity distribution dictionaries
            final_activity_dist = {}
            for activity in all_activities:
                final_activity_dist[activity] = {
                    'mp3_count': mp3_activity_dist.get(activity, {}).get('count', 0),
                    'mp3_percentage': mp3_activity_dist.get(activity, {}).get('percentage', 0.0),
                    'jpg_count': jpg_activity_dist.get(activity, {}).get('count', 0),
                    'jpg_percentage': jpg_activity_dist.get(activity, {}).get('percentage', 0.0),
                }

            # Create consistent category distribution dictionaries
            final_category_dist = {}
            for category in all_categories:
                final_category_dist[category] = {
                    'mp3_count': mp3_category_dist.get(category, {}).get('count', 0),
            
            try:
                # Group by the column and count occurrences
                counts = df.groupby(col_name).size()
                
                for item_name, count in counts.items():
                    distribution[item_name] = {
                        'count': count,
                        'percentage': (count / total_count * 100) if total_count > 0 else 0.0,
                    }
                return distribution
            except Exception as e:
                logging.error(f"Error calculating distribution for {col_name}: {e}")
                return {}

        # Calculate distributions
        mp3_activity_dist = get_distribution(year_mp3, total_mp3_count, 'Activity')
        jpg_activity_dist = get_distribution(year_jpg, total_jpg_count, 'Activity')
        
        mp3_category_dist = get_distribution(year_mp3, total_mp3_count, 'ActivityCategory')
        jpg_category_dist = get_distribution(year_jpg, total_jpg_count, 'ActivityCategory')

        # Combine distributions, ensuring all activities/categories are present
        all_activities = sorted(list(set(mp3_activity_dist.keys()).union(set(jpg_activity_dist.keys()))))
        all_categories = sorted(list(set(mp3_category_dist.keys()).union(set(jpg_category_dist.keys()))))

        # Ensure we always have at least one entry (Unknown) if everything is empty
        if not all_activities:
            all_activities = ['Unknown']
        if not all_categories:
            all_categories = ['Unknown']
        
        # Create consistent activity distribution dictionaries
        final_activity_dist = {}
        for activity in all_activities:
            final_activity_dist[activity] = {
                'mp3_count': mp3_activity_dist.get(activity, {}).get('count', 0),
                'mp3_percentage': mp3_activity_dist.get(activity, {}).get('percentage', 0.0),
                'jpg_count': jpg_activity_dist.get(activity, {}).get('count', 0),
                'jpg_percentage': jpg_activity_dist.get(activity, {}).get('percentage', 0.0),
            }

        # Create consistent category distribution dictionaries
        final_category_dist = {}
        for category in all_categories:
            final_category_dist[category] = {
                'mp3_count': mp3_category_dist.get(category, {}).get('count', 0),
                'mp3_percentage': mp3_category_dist.get(category, {}).get('percentage', 0.0),
                'jpg_count': jpg_category_dist.get(category, {}).get('count', 0),
                'jpg_percentage': jpg_category_dist.get(category, {}).get('percentage', 0.0),
            }

        # Store distributions in year metrics
        year_metrics['activity_distribution'] = final_activity_dist
        year_metrics['category_distribution'] = final_category_dist

        # Calculate size metrics for MP3 files
        if len(year_mp3) > 0:
            try:
                if 'FileSize' in year_mp3.columns:
                    year_metrics['mp3_size_bytes'] = int(year_mp3['FileSize'].sum())
                    year_metrics['mp3_size_mb'] = float(year_mp3['FileSize'].sum() / (1024 * 1024))
                elif 'File Size (MB)' in year_mp3.columns:
                    year_metrics['mp3_size_mb'] = float(year_mp3['File Size (MB)'].sum())
                    year_metrics['mp3_size_bytes'] = int(year_mp3['File Size (MB)'].sum() * (1024 * 1024))  # Approximate
            except Exception as e:
                logging.error(f"Error calculating MP3 file sizes: {e}")
        
        # Calculate size metrics for JPG files
        if len(year_jpg) > 0:
            try:
                if 'FileSize' in year_jpg.columns:
                    year_metrics['jpg_size_bytes'] = int(year_jpg['FileSize'].sum())
                    year_metrics['jpg_size_mb'] = float(year_jpg['FileSize'].sum() / (1024 * 1024))
                elif 'File Size (MB)' in year_jpg.columns:
                    year_metrics['jpg_size_mb'] = float(year_jpg['File Size (MB)'].sum())
                    year_metrics['jpg_size_bytes'] = int(year_jpg['File Size (MB)'].sum() * (1024 * 1024))  # Approximate
            except Exception as e:
                logging.error(f"Error calculating JPG file sizes: {e}")
        
        # Calculate unique dates
        try:
            if len(year_mp3) > 0 and 'Date' in year_mp3.columns:
                year_metrics['mp3_unique_dates'] = len(year_mp3['Date'].unique())
            if len(year_jpg) > 0 and 'Date' in year_jpg.columns:
                year_metrics['jpg_unique_dates'] = len(year_jpg['Date'].unique())
        except Exception as e:
            logging.error(f"Error calculating unique dates: {e}")
        
        # Calculate collection days
        try:
            all_dates = set()
            if len(year_mp3) > 0 and 'Date' in year_mp3.columns:
                all_dates.update(year_mp3['Date'].unique())
            if len(year_jpg) > 0 and 'Date' in year_jpg.columns:
                all_dates.update(year_jpg['Date'].unique())
            year_metrics['collection_days'] = len(all_dates)
        except Exception as e:
            logging.error(f"Error calculating collection days: {e}")
        
        # Calculate average per day
        try:
            if year_metrics['collection_days'] > 0:
                year_metrics['average_mp3_per_day'] = float(year_metrics['mp3_count'] / year_metrics['collection_days'])
                year_metrics['average_jpg_per_day'] = float(year_metrics['jpg_count'] / year_metrics['collection_days'])
        except Exception as e:
            logging.error(f"Error calculating averages per day: {e}")
        
        # Calculate duration metrics
        try:
            if len(year_mp3) > 0 and 'Duration' in year_mp3.columns:
                total_duration = year_mp3['Duration'].sum()
                year_metrics['total_duration_seconds'] = int(total_duration)
                year_metrics['total_duration_formatted'] = self._format_duration(total_duration)
                if year_metrics['collection_days'] > 0:
                    avg_duration = total_duration / year_metrics['collection_days']
                    year_metrics['average_duration_per_day_seconds'] = float(avg_duration)
                    year_metrics['average_duration_per_day_formatted'] = self._format_duration(avg_duration)
        except Exception as e:
            logging.error(f"Error calculating duration metrics: {e}")
        
        # Process activity distributions
        activities = {}
        try:
            # Get unique activities from both dataframes
            unique_activities = set()
            if 'Activity' in year_mp3.columns and len(year_mp3) > 0:
                valid_activities = [act for act in year_mp3['Activity'].dropna().unique() 
                                  if act is not None and not pd.isna(act)]
                unique_activities.update(valid_activities)
                logging.error(f"Error calculating averages per day: {e}")
            
            # Calculate duration metrics
            try:
                if len(year_mp3) > 0 and 'Duration' in year_mp3.columns:
                    total_duration = year_mp3['Duration'].sum()
                    year_metrics['total_duration_seconds'] = int(total_duration)
                    year_metrics['total_duration_formatted'] = self._format_duration(total_duration)
                    if year_metrics['collection_days'] > 0:
                        avg_duration = total_duration / year_metrics['collection_days']
                        year_metrics['average_duration_per_day_seconds'] = float(avg_duration)
                        year_metrics['average_duration_per_day_formatted'] = self._format_duration(avg_duration)
            except Exception as e:
                logging.error(f"Error calculating duration metrics: {e}")
            
            # Process activity distributions
            activities = {}
            try:
                # Get unique activities from both dataframes
                unique_activities = set()
                if 'Activity' in year_mp3.columns and len(year_mp3) > 0:
                    valid_activities = [act for act in year_mp3['Activity'].dropna().unique() 
                                      if act is not None and not pd.isna(act)]
                    unique_activities.update(valid_activities)
                    
                if 'Activity' in year_jpg.columns and len(year_jpg) > 0:
                    valid_activities = [act for act in year_jpg['Activity'].dropna().unique() 
                                      if act is not None and not pd.isna(act)]
                    unique_activities.update(valid_activities)
                
                # If we have no valid activities, add a default "Unknown" activity
                if not unique_activities:
                    unique_activities.add("Unknown")
                
                # Process each activity
                for activity in unique_activities:
                    activity_data = {
                        'mp3_count': 0,
                        'mp3_percentage': 0.0,  
                        'jpg_count': 0,
                        'jpg_percentage': 0.0    
                    }
                    
                    # Calculate MP3 metrics if we have MP3 data with activity column
                    if 'Activity' in year_mp3.columns and len(year_mp3) > 0:
                    })
                    duration_metrics_added = True
                except Exception as e:
                    logging.error(f"Error calculating duration metrics: {e}")
            
            if not duration_metrics_added:
                year_metrics.update({
                    'total_duration_seconds': 0,
                    'total_duration_formatted': '0:00:00',
                    'average_duration_per_file_seconds': 0,
                    'average_duration_per_file_formatted': '0:00:00',
                    'average_duration_per_day_seconds': 0,
                    'average_duration_per_day_formatted': '0:00:00',
                })
            
            # Initialize activity and category distributions
            activities = {}
            
            try:
                # Get unique activities from both dataframes
                unique_activities = set()
                if 'Activity' in year_mp3.columns and len(year_mp3) > 0:
                    # Filter out None/NaN values for consistent handling
                    valid_activities = [act for act in year_mp3['Activity'].dropna().unique() 
                                      if act is not None and not pd.isna(act)]
                    unique_activities.update(valid_activities)
                if 'Activity' in year_jpg.columns and len(year_jpg) > 0:
                    valid_activities = [act for act in year_jpg['Activity'].dropna().unique() 
                                      if act is not None and not pd.isna(act)]
                    unique_activities.update(valid_activities)
                
                # Add Unknown activity if no valid activities found
                if not unique_activities:
                    unique_activities.add("Unknown")
                
                # Process each activity
                for activity in unique_activities:
                    # Initialize activity data with consistent structure and types
                    activity_data = {
                        'mp3_count': 0,
                        'mp3_percentage': 0.0,  # Ensure consistent float type
                        'jpg_count': 0,
                        'jpg_percentage': 0.0    # Ensure consistent float type
                    }
                    
                    # Calculate MP3 metrics if we have MP3 data with activity column
                    if 'Activity' in year_mp3.columns and len(year_mp3) > 0:
                        try:
                            if activity == "Unknown":
                                # For "Unknown" activity, include records with None/NaN activity
                                activity_mp3 = year_mp3[year_mp3['Activity'].isna()]
                            else:
                                activity_mp3 = year_mp3[year_mp3['Activity'] == activity]
                            
                            activity_data['mp3_count'] = len(activity_mp3)
                            if len(year_mp3) > 0:
                                activity_data['mp3_percentage'] = float(len(activity_mp3) / len(year_mp3) * 100)
                        except Exception as e:
                            logging.error(f"Error calculating MP3 metrics for activity {activity}: {e}")
                    
                    # Calculate JPG metrics if we have JPG data with activity column
                    if 'Activity' in year_jpg.columns and len(year_jpg) > 0:
                        try:
                            if activity == "Unknown":
                                # For "Unknown" activity, include records with None/NaN activity
                                activity_jpg = year_jpg[year_jpg['Activity'].isna()]
                            else:
                                activity_jpg = year_jpg[year_jpg['Activity'] == activity]
                            
                            activity_data['jpg_count'] = len(activity_jpg)
                            if len(year_jpg) > 0:
                                activity_data['jpg_percentage'] = float(len(activity_jpg) / len(year_jpg) * 100)
                        except Exception as e:
                            logging.error(f"Error calculating JPG metrics for activity {activity}: {e}")
                    
                    # Store activity data
                    activities[activity] = activity_data
            except Exception as e:
                logging.error(f"Error processing activity distributions: {e}")
                # Ensure we at least have an empty dictionary
                activities = {}
            
            # Store activity distribution in year metrics
            year_metrics['activity_distribution'] = activities
            
            # Get category distributions within the school year
            categories = {}
            
            # Extract and process category distribution
            try:
                unique_categories = set()
                
                # Extract categories from MP3 dataframe if available
                if 'ActivityCategory' in year_mp3.columns and len(year_mp3) > 0:
                    # Filter out None/NaN values
                    valid_categories = [cat for cat in year_mp3['ActivityCategory'].dropna().unique() 
                                      if cat is not None and not pd.isna(cat)]
                    unique_categories.update(valid_categories)
                
                # Extract categories from JPG dataframe if available
                if 'ActivityCategory' in year_jpg.columns and len(year_jpg) > 0:
                    # Filter out None/NaN values
                    valid_categories = [cat for cat in year_jpg['ActivityCategory'].dropna().unique() 
                                      if cat is not None and not pd.isna(cat)]
                    unique_categories.update(valid_categories)
                    
                # If we have no valid categories, add a default "Unknown" category
                if not unique_categories:
                    unique_categories.add("Unknown")
                
                # Process each category
                for category in unique_categories:
                    # Initialize category data with consistent structure
                    category_data = {
                        'mp3_count': 0,
                        'mp3_percentage': 0.0,  # Use float for consistent types
                        'jpg_count': 0,
                        'jpg_percentage': 0.0    # Use float for consistent types
                    }
                    
                    # Calculate MP3 metrics if we have MP3 data with category column
                    if 'ActivityCategory' in year_mp3.columns and len(year_mp3) > 0:
                        try:
                            if category == "Unknown":
                                # For "Unknown" category, include records with None/NaN category
                                category_mp3 = year_mp3[year_mp3['ActivityCategory'].isna()]
                            else:
                                category_mp3 = year_mp3[year_mp3['ActivityCategory'] == category]
                            
                            category_data['mp3_count'] = len(category_mp3)
                            if len(year_mp3) > 0:
                                category_data['mp3_percentage'] = float(len(category_mp3) / len(year_mp3) * 100)
                        except Exception as e:
                            logging.error(f"Error calculating MP3 metrics for category {category}: {e}")
                    
                    # Calculate JPG metrics if we have JPG data with category column
                    if 'ActivityCategory' in year_jpg.columns and len(year_jpg) > 0:
                        try:
                            if category == "Unknown":
                                # For "Unknown" category, include records with None/NaN category
                                category_jpg = year_jpg[year_jpg['ActivityCategory'].isna()]
                            else:
                                category_jpg = year_jpg[year_jpg['ActivityCategory'] == category]
                            
                            category_data['jpg_count'] = len(category_jpg)
                            if len(year_jpg) > 0:
                                category_data['jpg_percentage'] = float(len(category_jpg) / len(year_jpg) * 100)
                        except Exception as e:
                            logging.error(f"Error calculating JPG metrics for category {category}: {e}")
                    
                    # Store category data
                    categories[category] = category_data
                
                # Store category distribution in year metrics
                year_metrics['category_distribution'] = categories
                
            except Exception as e:
                logging.error(f"Error processing category distributions: {e}")
                # Ensure we at least have an empty dictionary
                year_metrics['category_distribution'] = {}
            
            # Add year metrics to results
            results[year_name] = year_metrics
            
        return results
        
    def _add_activity_columns(self, df):
        """
        Add activity and activity category columns to a DataFrame based on timestamps.
        
        Args:
            df (pd.DataFrame): DataFrame with Date and Time columns.
            
        Returns:
            pd.DataFrame: DataFrame with Activity and ActivityCategory columns added.
        """
        if df.empty or 'Date' not in df.columns or 'Time' not in df.columns:
            return df
            
        # Ensure datetime columns
        df_with_dt = self._ensure_datetime_columns(df)
        
        # Add activity name
        df_with_dt['Activity'] = df_with_dt.apply(
            lambda row: self.activity_schedule.get_activity_name_for_datetime(row['DateTime']) 
                if self.activity_schedule else None,
            axis=1
        )
        
        # Add activity category
        def get_category(row):
            if not self.activity_schedule:
                return None
            activity = self.activity_schedule.get_activity_for_datetime(row['DateTime'])
            return activity.category if activity else None
        
        df_with_dt['ActivityCategory'] = df_with_dt.apply(get_category, axis=1)
        
        return df_with_dt
        
    def _format_duration(self, seconds):
        """
        Format duration in seconds as HH:MM:SS.
        This is an alias for _format_seconds for backward compatibility.
        
        Args:
            seconds (float): Duration in seconds.
            
        Returns:
            str: Formatted duration string.
        """
        return self._format_seconds(seconds)
    
    @staticmethod
    def _get_date_range_for_period(period: str, time_unit: str) -> Tuple[Optional[date], Optional[date]]:
        """Get the start and end dates for a period string based on the time unit."""
        if time_unit == 'week':
            # Parse ISO week format like '2023-W01'
            try:
                year_str, week_str = period.split('-W')
                year = int(year_str)
                week = int(week_str)
                
                # Get the first day of this ISO week
                start_date = datetime.strptime(f'{year}-{week}-1', '%G-%V-%u').date()
                # Add 6 days to get the end of the week
                end_date = start_date + timedelta(days=6)
                
                return start_date, end_date
            except Exception as e:
                logging.error(f"Error parsing week period {period}: {e}")
                return None, None
        elif time_unit == 'month':
            # Parse month format like '2023-01'
            try:
                year_str, month_str = period.split('-')
                year = int(year_str)
                month = int(month_str)
                
                # First day of month
                start_date = date(year, month, 1)
                
                # Last day of month
                if month == 12:
                    end_date = date(year + 1, 1, 1) - timedelta(days=1)
                else:
                    end_date = date(year, month + 1, 1) - timedelta(days=1)
                    
                return start_date, end_date
            except Exception as e:
                logging.error(f"Error parsing month period {period}: {e}")
                return None, None
        else:
            # For day unit, the period is already a date
            return None, None
