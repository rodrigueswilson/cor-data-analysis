"""
Integrated Data Analysis Example

This script demonstrates how to integrate the new data aggregation framework
with existing data collection and processing functions to enable enhanced
analysis with mid-year schedule changes and multi-level periodization.
"""

import os
import sys
import pandas as pd
import numpy as np
from datetime import datetime, date
import matplotlib.pyplot as plt
import yaml

# Add the project root to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import the new framework components
from cor_data_analysis.data.calendar import SchoolCalendar, ActivitySchedule
from cor_data_analysis.data.aggregation import DataAggregator


def load_mp3_and_jpg_data(data_dir):
    """
    Load MP3 and JPG metadata from existing CSV files or create from raw data.
    
    This is a placeholder that would integrate with your existing data loading logic.
    """
    # In a real implementation, this would use your existing data loading functions
    # For demonstration, we'll create some sample data
    
    print(f"Loading data from {data_dir}...")
    
    # Check if the processed data already exists
    mp3_path = os.path.join(data_dir, 'mp3_metadata.csv')
    jpg_path = os.path.join(data_dir, 'jpg_metadata.csv')
    
    if os.path.exists(mp3_path) and os.path.exists(jpg_path):
        print("Loading from existing metadata files...")
        mp3_df = pd.read_csv(mp3_path, parse_dates=['Date', 'DateTime'])
        jpg_df = pd.read_csv(jpg_path, parse_dates=['Date', 'DateTime'])
        return mp3_df, jpg_df
    
    # Otherwise, create sample data (this would be your existing extraction logic)
    print("Creating sample metadata...")
    
    # Sample date range covering the school year
    start_date = '2022-09-01'
    end_date = '2023-06-15'
    date_range = pd.date_range(start=start_date, end=end_date, freq='B')  # Business days
    
    # Filter out weekends
    date_range = date_range[date_range.dayofweek < 5]
    
    # Create MP3 data (multiple recordings per day)
    mp3_dates = []
    mp3_times = []
    mp3_durations = []
    mp3_sizes = []
    mp3_filenames = []
    
    # Create 2-3 recordings for each 5th day
    for i, day in enumerate(date_range):
        if i % 5 == 0:
            num_recordings = np.random.randint(2, 4)
            for j in range(num_recordings):
                mp3_dates.append(day)
                # Create times during typical activities
                hour = np.random.choice([8, 9, 10, 11, 14])
                minute = np.random.randint(0, 60)
                mp3_times.append(f"{hour:02d}:{minute:02d}")
                # Random duration 30-300 seconds
                mp3_durations.append(np.random.randint(30, 301))
                # Random size 1-10 MB (in bytes)
                mp3_sizes.append(np.random.randint(1024*1024, 10*1024*1024))
                # Create filename
                mp3_filenames.append(f"rec_{day.strftime('%Y%m%d')}_{j+1}.mp3")
    
    # Create JPG data (multiple photos per day)
    jpg_dates = []
    jpg_times = []
    jpg_sizes = []
    jpg_filenames = []
    
    # Create 1-4 photos for each 3rd day
    for i, day in enumerate(date_range):
        if i % 3 == 0:
            num_photos = np.random.randint(1, 5)
            for j in range(num_photos):
                jpg_dates.append(day)
                # Create times during typical activities
                hour = np.random.choice([8, 9, 10, 11, 14])
                minute = np.random.randint(0, 60)
                jpg_times.append(f"{hour:02d}:{minute:02d}")
                # Random size 2-5 MB (in bytes)
                jpg_sizes.append(np.random.randint(2*1024*1024, 5*1024*1024))
                # Create filename
                jpg_filenames.append(f"img_{day.strftime('%Y%m%d')}_{j+1}.jpg")
    
    # Create the DataFrames
    mp3_df = pd.DataFrame({
        'Filename': mp3_filenames,
        'Date': pd.to_datetime(mp3_dates),
        'Time': mp3_times,
        'Duration': mp3_durations,
        'FileSize': mp3_sizes
    })
    
    jpg_df = pd.DataFrame({
        'Filename': jpg_filenames,
        'Date': pd.to_datetime(jpg_dates),
        'Time': jpg_times,
        'FileSize': jpg_sizes
    })
    
    # Add DateTime columns combining Date and Time
    mp3_df['DateTime'] = pd.to_datetime(mp3_df['Date'].dt.strftime('%Y-%m-%d') + ' ' + mp3_df['Time'])
    jpg_df['DateTime'] = pd.to_datetime(jpg_df['Date'].dt.strftime('%Y-%m-%d') + ' ' + jpg_df['Time'])
    
    # Save to CSV for future use
    os.makedirs(data_dir, exist_ok=True)
    mp3_df.to_csv(mp3_path, index=False)
    jpg_df.to_csv(jpg_path, index=False)
    
    print(f"Created {len(mp3_df)} MP3 records and {len(jpg_df)} JPG records")
    return mp3_df, jpg_df


def plot_activity_metrics(activity_period_metrics, output_dir):
    """
    Plot metrics by activity and period.
    """
    print("Generating activity metrics plots...")
    os.makedirs(output_dir, exist_ok=True)
    
    # Extract periods and activities
    periods = list(activity_period_metrics.keys())
    
    # Prepare data for plotting
    for period in periods:
        activities = list(activity_period_metrics[period].keys())
        mp3_counts = [activity_period_metrics[period][act]['mp3_count'] for act in activities]
        jpg_counts = [activity_period_metrics[period][act]['jpg_count'] for act in activities]
        
        # Create a bar plot
        plt.figure(figsize=(12, 6))
        x = np.arange(len(activities))
        width = 0.35
        
        plt.bar(x - width/2, mp3_counts, width, label='MP3 Files')
        plt.bar(x + width/2, jpg_counts, width, label='JPG Files')
        
        plt.xlabel('Activity')
        plt.ylabel('Count')
        plt.title(f'File Counts by Activity for {period}')
        plt.xticks(x, activities, rotation=45, ha='right')
        plt.legend()
        plt.tight_layout()
        
        # Save the plot
        plt.savefig(os.path.join(output_dir, f'activity_metrics_{period.replace(" ", "_")}.png'))
        plt.close()


def plot_period_metrics(period_metrics, output_dir):
    """
    Plot metrics by period.
    """
    print("Generating period metrics plots...")
    os.makedirs(output_dir, exist_ok=True)
    
    # Extract data for plotting
    periods = list(period_metrics.keys())
    mp3_counts = [period_metrics[p]['mp3_count'] for p in periods]
    jpg_counts = [period_metrics[p]['jpg_count'] for p in periods]
    
    # Create a bar plot
    plt.figure(figsize=(10, 6))
    x = np.arange(len(periods))
    width = 0.35
    
    plt.bar(x - width/2, mp3_counts, width, label='MP3 Files')
    plt.bar(x + width/2, jpg_counts, width, label='JPG Files')
    
    plt.xlabel('Period')
    plt.ylabel('Count')
    plt.title('File Counts by Collection Period')
    plt.xticks(x, periods)
    plt.legend()
    
    # Save the plot
    plt.savefig(os.path.join(output_dir, 'period_metrics.png'))
    plt.close()


def main():
    """
    Main function to run the integrated data analysis.
    """
    # Set up paths
    base_dir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
    data_dir = os.path.join(base_dir, 'data')
    config_dir = os.path.join(base_dir, 'sample_configs')
    output_dir = os.path.join(base_dir, 'output')
    
    os.makedirs(data_dir, exist_ok=True)
    os.makedirs(output_dir, exist_ok=True)
    
    # Load configurations
    print("Loading configurations...")
    calendar_path = os.path.join(config_dir, 'school_calendar.yaml')
    schedule_path = os.path.join(config_dir, 'activity_schedules.yaml')
    
    calendar = SchoolCalendar.from_yaml(calendar_path)
    activity_schedule = ActivitySchedule.from_yaml(schedule_path)
    
    # Initialize the data aggregator
    print("Initializing data aggregator...")
    aggregator = DataAggregator(calendar=calendar, activity_schedule=activity_schedule)
    
    # Load data
    mp3_df, jpg_df = load_mp3_and_jpg_data(data_dir)
    
    print(f"MP3 files: {len(mp3_df)}")
    print(f"JPG files: {len(jpg_df)}")
    
    # Perform aggregation
    print("Aggregating by school year...")
    school_year_metrics = aggregator.aggregate_by_school_year(mp3_df, jpg_df)
    
    print("Aggregating by period...")
    period_metrics = aggregator.aggregate_by_period(mp3_df, jpg_df)
    
    print("Aggregating by activity and period...")
    activity_period_metrics = aggregator.aggregate_by_activity_and_period(mp3_df, jpg_df)
    
    print("Aggregating by activity...")
    activity_metrics = aggregator.aggregate_by_activity(mp3_df, jpg_df)
    
    print("Aggregating by time unit (month)...")
    monthly_metrics = aggregator.aggregate_by_time_unit(mp3_df, jpg_df, 'month')
    
    # Generate plots
    plot_period_metrics(period_metrics, output_dir)
    plot_activity_metrics(activity_period_metrics, output_dir)
    
    # Save aggregated data to CSV
    print("Saving aggregated data...")
    monthly_metrics.to_csv(os.path.join(output_dir, 'monthly_metrics.csv'), index=False)
    
    print("Analysis complete. Results saved to", output_dir)
    
    # Visualize school year metrics
    if school_year_metrics:
        plt.figure(figsize=(12, 6))
        plt.title('School Year Data Collection Metrics')
        
        years = list(school_year_metrics.keys())
        mp3_counts = [school_year_metrics[year]['mp3_count'] for year in years]
        jpg_counts = [school_year_metrics[year]['jpg_count'] for year in years]
        
        x = np.arange(len(years))
        width = 0.35
        
        plt.bar(x - width/2, mp3_counts, width, label='MP3 Files')
        plt.bar(x + width/2, jpg_counts, width, label='JPG Files')
        
        plt.xlabel('School Year')
        plt.ylabel('File Count')
        plt.xticks(x, years)
        plt.legend()
        plt.tight_layout()
        
        # Save the figure
        figures_dir = os.path.join(os.path.dirname(__file__), 'figures')
        os.makedirs(figures_dir, exist_ok=True)
        plt.savefig(os.path.join(figures_dir, 'school_year_metrics.png'))
        print(f"\nSaved school year metrics chart to {os.path.join(figures_dir, 'school_year_metrics.png')}")

    # Save results
    results_dir = os.path.join(os.path.dirname(__file__), 'results')
    os.makedirs(results_dir, exist_ok=True)
    
    # Save school year metrics
    school_year_df = pd.DataFrame([{
        'school_year': year,
        'mp3_count': metrics['mp3_count'],
        'jpg_count': metrics['jpg_count'],
        'mp3_size_mb': metrics['mp3_size_mb'],
        'jpg_size_mb': metrics['jpg_size_mb'],
        'collection_days': metrics['collection_days'],
        'avg_mp3_per_day': metrics['average_mp3_per_day'],
        'avg_jpg_per_day': metrics['average_jpg_per_day'],
        'periods': ', '.join(metrics['periods'])
    } for year, metrics in school_year_metrics.items()])
    
    school_year_df.to_csv(os.path.join(results_dir, 'school_year_metrics.csv'), index=False)
    print(f"Saved school year metrics to {os.path.join(results_dir, 'school_year_metrics.csv')}")
    
    # Save period metrics
    period_df = pd.DataFrame([{
        'period': period,
        'mp3_count': metrics['mp3_count'],
        'jpg_count': metrics['jpg_count'],
        'mp3_size_mb': metrics['mp3_size_mb'],
        'jpg_size_mb': metrics['jpg_size_mb'],
        'collection_days': metrics['collection_days'],
        'avg_mp3_per_day': metrics['average_mp3_per_day'],
        'avg_jpg_per_day': metrics['average_jpg_per_day']
    } for period, metrics in period_metrics.items()])
    
    period_df.to_csv(os.path.join(results_dir, 'period_metrics.csv'), index=False)
    print(f"Saved period metrics to {os.path.join(results_dir, 'period_metrics.csv')}")
    
    # Save activity distribution by school year
    for year, metrics in school_year_metrics.items():
        if 'activity_distribution' in metrics:
            activity_dist_df = pd.DataFrame([{
                'activity': activity,
                'mp3_count': dist['mp3_count'],
                'mp3_percentage': dist['mp3_percentage'],
                'jpg_count': dist['jpg_count'],
                'jpg_percentage': dist['jpg_percentage']
            } for activity, dist in metrics['activity_distribution'].items()])
            
            file_path = os.path.join(results_dir, f'{year}_activity_distribution.csv')
            activity_dist_df.to_csv(file_path, index=False)
            print(f"Saved {year} activity distribution to {file_path}")

    # Print summary
    print("\nSummary of metrics by period:")
    for period, metrics in period_metrics.items():
        print(f"\n{period}:")
        print(f"  MP3 Files: {metrics['mp3_count']} ({metrics['mp3_size_mb']:.2f} MB)")
        print(f"  JPG Files: {metrics['jpg_count']} ({metrics['jpg_size_mb']:.2f} MB)")
        print(f"  Collection Days: {metrics['collection_days']}")
        print(f"  Avg MP3/Day: {metrics['average_mp3_per_day']:.2f}")
        print(f"  Avg JPG/Day: {metrics['average_jpg_per_day']:.2f}")
        
        # Show top activities in this period
        if period in activity_period_metrics:
            activities = activity_period_metrics[period]
            sorted_activities = sorted(activities.items(), 
                                       key=lambda x: x[1]['mp3_count'] + x[1]['jpg_count'], 
                                       reverse=True)
            
            print("  Top activities:")
            for i, (activity, act_metrics) in enumerate(sorted_activities[:3], 1):
                total = act_metrics['mp3_count'] + act_metrics['jpg_count']
                print(f"    {i}. {activity}: {total} files ({act_metrics['mp3_count']} MP3, {act_metrics['jpg_count']} JPG)")


if __name__ == "__main__":
    main()
