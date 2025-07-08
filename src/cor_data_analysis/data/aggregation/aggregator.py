"""
Data Aggregation Framework

This module provides a flexible, multi-level data aggregation framework for analyzing
file metadata. It supports aggregation by various time periods (day, week, month)
and by activities, with support for mid-year schedule changes.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional, Any, Union
from datetime import datetime, date, time, timedelta
import logging
from pathlib import Path
from cor_data_analysis.data.calendar.school_calendar import SchoolCalendar
from cor_data_analysis.data.calendar.activity_schedule import ActivitySchedule

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class DataAggregator:
    """
    Main class for data aggregation operations. Clean, robust, and vectorized.
    """
    def __init__(
        self, 
        calendar: Optional[SchoolCalendar] = None,
        activity_schedule: Optional[ActivitySchedule] = None
    ):
        """Initializes the DataAggregator with optional calendar and activity schedules.

        Args:
            calendar (Optional[SchoolCalendar]): A SchoolCalendar instance for period-based aggregation.
            activity_schedule (Optional[ActivitySchedule]): An ActivitySchedule instance for activity-based aggregation.
        """
        self.calendar = calendar
        self.activity_schedule = activity_schedule

    def prepare_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Prepares a DataFrame for aggregation by ensuring necessary columns and assigning activities.

        This method standardizes the input DataFrame by:
        1. Ensuring a 'DateTime' column exists.
        2. Assigning 'Activity' and 'ActivityCategory' based on the activity schedule.
        3. Filling missing values with 'Unknown'.

        Args:
            df (pd.DataFrame): The input DataFrame to prepare.

        Returns:
            pd.DataFrame: The prepared DataFrame with added 'Activity' and 'ActivityCategory' columns.
        """
        """
        Central data preparation method. Ensures datetime columns and assigns activities.
        Uses a vectorized approach with pd.cut for performance and reliability.
        """
        if df is None or df.empty:
            return pd.DataFrame()

        df_copy = df.copy()
        df_copy = self._ensure_datetime_columns(df_copy)

        if self.activity_schedule and not df_copy.empty and 'DateTime' in df_copy.columns:
            def get_activity_details(dt):
                if pd.isna(dt):
                    return 'Unknown', 'Unknown'
                activity = self.activity_schedule.get_activity_for_datetime(dt)
                if activity:
                    return activity.name, activity.category
                return 'Unknown', 'Unknown'

            # Apply the function to each row to get activity details
            activity_details = df_copy['DateTime'].apply(get_activity_details)
            df_copy['Activity'] = [details[0] for details in activity_details]
            df_copy['ActivityCategory'] = [details[1] for details in activity_details]

        if 'Activity' not in df_copy.columns:
            df_copy['Activity'] = 'Unknown'
        else:
            if pd.api.types.is_categorical_dtype(df_copy['Activity'].dtype):
                if 'Unknown' not in df_copy['Activity'].cat.categories:
                    df_copy['Activity'] = df_copy['Activity'].cat.add_categories('Unknown')
            df_copy['Activity'] = df_copy['Activity'].fillna('Unknown')

        if 'ActivityCategory' not in df_copy.columns:
            df_copy['ActivityCategory'] = 'Unknown'
        else:
            df_copy['ActivityCategory'] = df_copy['ActivityCategory'].fillna('Unknown')

        return df_copy

    @staticmethod
    def _format_duration(seconds: float) -> str:
        """Formats a duration in seconds into a human-readable string (Hh Mm Ss)."""
        if not isinstance(seconds, (int, float)) or pd.isna(seconds):
            return "0s"
        seconds = int(seconds)
        hours, remainder = divmod(seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        parts = []
        if hours > 0:
            parts.append(f"{hours}h")
        if minutes > 0:
            parts.append(f"{minutes}m")
        if seconds > 0 or not parts:
            parts.append(f"{seconds}s")
        return " ".join(parts)

    def _ensure_datetime_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Ensures a consistent 'DateTime' column exists for aggregation.
        """
        if df is None or df.empty:
            return pd.DataFrame()

        df_copy = df.copy()
        if 'Date' in df_copy.columns and 'Time' in df_copy.columns:
            try:
                df_copy['Date'] = pd.to_datetime(df_copy['Date'], errors='coerce')
                df_copy['Time'] = df_copy['Time'].astype(str)
                df_copy['DateTime'] = pd.to_datetime(df_copy['Date'].dt.strftime('%Y-%m-%d') + ' ' + df_copy['Time'], errors='coerce')
            except Exception as e:
                logging.error(f"Error combining Date and Time columns: {e}")
                df_copy['DateTime'] = pd.NaT
        elif 'DateTime' in df_copy.columns:
            df_copy['DateTime'] = pd.to_datetime(df_copy['DateTime'], errors='coerce')
        else:
            df_copy['DateTime'] = pd.NaT

        return df_copy

    def _calculate_distributions(self, mp3_df: pd.DataFrame, jpg_df: pd.DataFrame) -> Dict[str, Any]:
        """Calculates activity and category distributions with consistent dictionary keys."""
        # Get activity and category counts if columns exist, otherwise empty dicts
        mp3_act_counts = mp3_df['Activity'].value_counts().to_dict() if 'Activity' in mp3_df.columns else {}
        jpg_act_counts = jpg_df['Activity'].value_counts().to_dict() if 'Activity' in jpg_df.columns else {}
        mp3_cat_counts = mp3_df['ActivityCategory'].value_counts().to_dict() if 'ActivityCategory' in mp3_df.columns else {}
        jpg_cat_counts = jpg_df['ActivityCategory'].value_counts().to_dict() if 'ActivityCategory' in jpg_df.columns else {}

        # Get a unique, sorted list of all activities and categories
        all_activities = sorted(list(set(mp3_act_counts.keys()) | set(jpg_act_counts.keys())))
        all_categories = sorted(list(set(mp3_cat_counts.keys()) | set(jpg_cat_counts.keys())))

        # Initialize distribution dictionaries
        act_dist = {act: {'mp3_count': 0, 'jpg_count': 0} for act in all_activities}
        cat_dist = {cat: {'mp3_count': 0, 'jpg_count': 0} for cat in all_categories}

        # Populate distributions
        for act, count in mp3_act_counts.items():
            act_dist[act]['mp3_count'] = count
        for act, count in jpg_act_counts.items():
            act_dist[act]['jpg_count'] = count
        for cat, count in mp3_cat_counts.items():
            cat_dist[cat]['mp3_count'] = count
        for cat, count in jpg_cat_counts.items():
            cat_dist[cat]['jpg_count'] = count

        return {
            'activity_distribution': act_dist, 
            'category_distribution': cat_dist
        }

    def aggregate_by_time_unit(self, mp3_df: pd.DataFrame, jpg_df: pd.DataFrame, unit: str) -> pd.DataFrame:
        """Aggregates MP3 and JPG data by a specified time unit (day, week, or month).

        Args:
            mp3_df (pd.DataFrame): DataFrame containing MP3 file data.
            jpg_df (pd.DataFrame): DataFrame containing JPG file data.
            unit (str): The time unit for aggregation ('day', 'week', or 'month').

        Returns:
            pd.DataFrame: A DataFrame with aggregated data for the specified time unit.
        """

        if unit not in ['day', 'week', 'month']:
            raise ValueError("Time unit must be one of 'day', 'week', or 'month'.")

        mp3_prepared = self.prepare_data(mp3_df)
        jpg_prepared = self.prepare_data(jpg_df)

        # Combine data for unified processing
        all_data = pd.concat([
            mp3_prepared[['DateTime', 'Duration', 'FileSize', 'Activity', 'ActivityCategory']].assign(type='mp3'),
            jpg_prepared[['DateTime', 'FileSize', 'Activity', 'ActivityCategory']].assign(type='jpg')
        ], ignore_index=True).dropna(subset=['DateTime'])

        if all_data.empty: return pd.DataFrame()

        if unit == 'day': all_data['group_key'] = all_data['DateTime'].dt.to_period('D')
        elif unit == 'week': all_data['group_key'] = all_data['DateTime'].dt.to_period('W')
        else: all_data['group_key'] = all_data['DateTime'].dt.to_period('M')
        
        def agg_func(group):
            mp3_mask = group['type'] == 'mp3'
            jpg_mask = group['type'] == 'jpg'
            collection_days = group['DateTime'].dt.date.nunique()
            total_duration = group.loc[mp3_mask, 'Duration'].sum()
            distributions = self._calculate_distributions(group[mp3_mask], group[jpg_mask])
            
            return pd.Series({
                'start_date': group['group_key'].min().start_time.date(),
                'end_date': group['group_key'].max().end_time.date(),
                'mp3_count': mp3_mask.sum(),
                'jpg_count': jpg_mask.sum(),
                'collection_days': collection_days,
                'total_duration_seconds': total_duration,
                'total_mp3_size_mb': group.loc[mp3_mask, 'FileSize'].sum() / (1024*1024),
                'total_jpg_size_mb': group.loc[jpg_mask, 'FileSize'].sum() / (1024*1024),
                'activity_distribution': distributions['activity_distribution'],
                'category_distribution': distributions['category_distribution']
            })

        aggregated_df = all_data.groupby('group_key').apply(agg_func).reset_index()

        # Rename the grouping column to the appropriate unit name for clarity
        rename_map = {'day': 'Day', 'week': 'Week', 'month': 'Month'}
        aggregated_df.rename(columns={'group_key': rename_map[unit]}, inplace=True)

        return aggregated_df

    def aggregate_by_school_year(self, mp3_df: pd.DataFrame, jpg_df: pd.DataFrame) -> Dict[str, Any]:
        """Performs a comprehensive aggregation of MP3 and JPG data over a full school year.

        This method aggregates data by day, week, month, and custom collection periods defined
        in the school calendar. It also calculates activity and category distributions.

        Args:
            mp3_df (pd.DataFrame): DataFrame containing MP3 file data.
            jpg_df (pd.DataFrame): DataFrame containing JPG file data.

        Returns:
            Dict[str, Any]: A dictionary containing:
                - 'daily_summary': DataFrame of daily aggregated data.
                - 'weekly_summary': DataFrame of weekly aggregated data.
                - 'monthly_summary': DataFrame of monthly aggregated data.
                - 'period_summary': DataFrame of period-based aggregated data.
                - 'activity_distribution': Dictionary of activity counts.
                - 'category_distribution': Dictionary of category counts.
        """

        if not self.calendar or not self.activity_schedule:
            raise ValueError("Calendar and activity schedule must be initialized.")

        mp3_prepared = self.prepare_data(mp3_df)
        jpg_prepared = self.prepare_data(jpg_df)

        # If both datasets are empty after preparation, return empty results
        if mp3_prepared.empty and jpg_prepared.empty:
            empty_distributions = self._calculate_distributions(mp3_prepared, jpg_prepared)
            return {
                'daily_summary': pd.DataFrame(),
                'weekly_summary': pd.DataFrame(),
                'monthly_summary': pd.DataFrame(),
                'period_summary': pd.DataFrame(),
                **empty_distributions
            }

        period_results = []
        for period in self.calendar.get_all_periods():
            start, end = pd.Timestamp(period.start_date), pd.Timestamp(period.end_date)
            
            mp3_period = mp3_prepared[mp3_prepared['DateTime'].between(start, end)]
            jpg_period = jpg_prepared[jpg_prepared['DateTime'].between(start, end)]
            
            if mp3_period.empty and jpg_period.empty:
                continue

            collection_days = pd.concat([mp3_period['DateTime'], jpg_period['DateTime']]).dt.date.nunique()
            total_duration = mp3_period['Duration'].sum()
            distributions = self._calculate_distributions(mp3_period, jpg_period)

            period_results.append({
                'period_name': period.name,
                'start_date': period.start_date,
                'end_date': period.end_date,
                'mp3_count': len(mp3_period),
                'jpg_count': len(jpg_period),
                'collection_days': collection_days,
                'total_duration_seconds': total_duration,
                **distributions
            })

        daily_summary = self.aggregate_by_time_unit(mp3_prepared, jpg_prepared, 'day')
        weekly_summary = self.aggregate_by_time_unit(mp3_prepared, jpg_prepared, 'week')
        monthly_summary = self.aggregate_by_time_unit(mp3_prepared, jpg_prepared, 'month')
        period_summary = pd.DataFrame(period_results)
        distributions = self._calculate_distributions(mp3_prepared, jpg_prepared)

        return {
            'daily_summary': daily_summary,
            'weekly_summary': weekly_summary,
            'monthly_summary': monthly_summary,
            'period_summary': period_summary,
            **distributions
        }

    def to_excel(self, data: Dict[str, pd.DataFrame], output_path: Union[str, Path]):
        """Exports aggregated data to an Excel file with multiple sheets.

        Each key-value pair in the data dictionary is written to a separate sheet.

        Args:
            data (Dict[str, pd.DataFrame]): A dictionary where keys are sheet names and values are DataFrames.
            output_path (Union[str, Path]): The path to the output Excel file.
        """

        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            for sheet_name, df in data.items():
                if isinstance(df, pd.DataFrame):
                    df.to_excel(writer, sheet_name=sheet_name, index=False)

    def to_json(self, data: Dict[str, pd.DataFrame], output_path: Union[str, Path]):
        """Exports aggregated data to a JSON file.

        The data is serialized to a JSON format where each key corresponds to a list of records from a DataFrame.

        Args:
            data (Dict[str, pd.DataFrame]): A dictionary of DataFrames to be exported.
            output_path (Union[str, Path]): The path to the output JSON file.
        """

        serializable_data = {}
        for key, df in data.items():
            if isinstance(df, pd.DataFrame):
                serializable_data[key] = df.to_dict(orient='records')
        
        with open(output_path, 'w') as f:
            import json
            json.dump(serializable_data, f, indent=4, default=str)
