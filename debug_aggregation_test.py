import pandas as pd
import logging
import traceback
import sys

from src.cor_data_analysis.data.aggregation.aggregator import DataAggregator
from tests.test_data.test_aggregator import TestDataAggregator

# Configure logging
logging.basicConfig(level=logging.DEBUG, 
                    format='%(asctime)s - %(levelname)s - %(message)s')

def debug_aggregate_by_school_year():
    """Debug the aggregate_by_school_year method with detailed output"""
    print("\n--- Starting Detailed Aggregation Debug ---")
    
    # Create a test instance
    test = TestDataAggregator()
    test.setUp()
    
    # Access the test data
    aggregator = test.aggregator
    mp3_df = test.mp3_df
    jpg_df = test.jpg_df
    
    # Debug dataframes
    print(f"MP3 DataFrame shape: {mp3_df.shape}")
    print(f"MP3 columns: {mp3_df.columns.tolist()}")
    print(f"JPG DataFrame shape: {jpg_df.shape}")
    print(f"JPG columns: {jpg_df.columns.tolist()}")
    
    # Patch the aggregate_by_school_year method to trace execution
    original_method = DataAggregator.aggregate_by_school_year
    
    def patched_method(self, mp3_df, jpg_df):
        print("\nExecuting patched aggregate_by_school_year method")
        try:
            # Step 1: Get school years
            print("Step 1: Getting school years")
            school_years = self.school_calendar.get_school_years() if self.school_calendar else []
            print(f"Found school years: {school_years}")
            
            # Initialize results dictionary
            result = {}
            
            # Step 2: Process each school year
            for school_year in school_years:
                print(f"\nProcessing school year: {school_year}")
                start_date, end_date = self.school_calendar.get_year_range(school_year)
                print(f"Date range: {start_date} to {end_date}")
                
                # Filter data for this school year
                print("Filtering MP3 data for school year")
                year_mp3 = mp3_df[(mp3_df['Date'] >= start_date) & (mp3_df['Date'] <= end_date)] if 'Date' in mp3_df.columns else pd.DataFrame()
                print(f"Filtered MP3 data shape: {year_mp3.shape}")
                
                print("Filtering JPG data for school year")
                year_jpg = jpg_df[(jpg_df['Date'] >= start_date) & (jpg_df['Date'] <= end_date)] if 'Date' in jpg_df.columns else pd.DataFrame()
                print(f"Filtered JPG data shape: {year_jpg.shape}")
                
                # Initialize metrics for this year
                year_metrics = {}
                
                # Add activity columns if needed
                print("Adding activity columns to MP3 data")
                if self.activity_schedule and not year_mp3.empty and 'Activity' not in year_mp3.columns:
                    year_mp3 = self._add_activity_columns(year_mp3)
                print(f"MP3 columns after adding activities: {year_mp3.columns.tolist()}")
                
                print("Adding activity columns to JPG data")
                if self.activity_schedule and not year_jpg.empty and 'Activity' not in year_jpg.columns:
                    year_jpg = self._add_activity_columns(year_jpg)
                print(f"JPG columns after adding activities: {year_jpg.columns.tolist()}")
                
                # Count metrics
                print("Calculating basic count metrics")
                year_metrics['mp3_count'] = len(year_mp3)
                year_metrics['jpg_count'] = len(year_jpg)
                
                # Calculate MP3 file size metrics
                print("Calculating file size metrics")
                
                # Activity distribution
                print("Processing activity distribution")
                activities = {}
                
                # Get unique activities from both dataframes
                unique_activities = set()
                if 'Activity' in year_mp3.columns and len(year_mp3) > 0:
                    unique_activities.update(act for act in year_mp3['Activity'].dropna().unique() if not pd.isna(act))
                if 'Activity' in year_jpg.columns and len(year_jpg) > 0:
                    unique_activities.update(act for act in year_jpg['Activity'].dropna().unique() if not pd.isna(act))
                
                print(f"Unique activities found: {unique_activities}")
                
                # Process each activity
                for activity in unique_activities:
                    print(f"Processing activity: {activity}")
                    # Create activity entry with default values
                    activity_data = {
                        'mp3_count': 0,
                        'mp3_percentage': 0.0,
                        'jpg_count': 0,
                        'jpg_percentage': 0.0
                    }
                    
                    # Calculate MP3 metrics if we have MP3 data with activity column
                    if 'Activity' in year_mp3.columns and len(year_mp3) > 0:
                        try:
                            activity_mp3 = year_mp3[year_mp3['Activity'] == activity]
                            activity_data['mp3_count'] = len(activity_mp3)
                            if len(year_mp3) > 0:
                                activity_data['mp3_percentage'] = float(len(activity_mp3) / len(year_mp3) * 100)
                        except Exception as e:
                            print(f"Error calculating MP3 metrics for activity {activity}: {e}")
                    
                    # Calculate JPG metrics if we have JPG data with activity column
                    if 'Activity' in year_jpg.columns and len(year_jpg) > 0:
                        try:
                            activity_jpg = year_jpg[year_jpg['Activity'] == activity]
                            activity_data['jpg_count'] = len(activity_jpg)
                            if len(year_jpg) > 0:
                                activity_data['jpg_percentage'] = float(len(activity_jpg) / len(year_jpg) * 100)
                        except Exception as e:
                            print(f"Error calculating JPG metrics for activity {activity}: {e}")
                    
                    # Store activity data
                    activities[activity] = activity_data
                
                print(f"Activity distribution: {activities}")
                year_metrics['activity_distribution'] = activities
                
                # Get category distributions within the school year
                print("Processing category distribution")
                categories = {}
                
                try:
                    unique_categories = set()
                    
                    # Extract categories from MP3 dataframe if available
                    if 'ActivityCategory' in year_mp3.columns and len(year_mp3) > 0:
                        # Filter out None/NaN values
                        valid_categories = [cat for cat in year_mp3['ActivityCategory'].dropna().unique() 
                                          if cat is not None and not pd.isna(cat)]
                        unique_categories.update(valid_categories)
                        print(f"Categories from MP3: {valid_categories}")
                    
                    # Extract categories from JPG dataframe if available
                    if 'ActivityCategory' in year_jpg.columns and len(year_jpg) > 0:
                        # Filter out None/NaN values
                        valid_categories = [cat for cat in year_jpg['ActivityCategory'].dropna().unique() 
                                          if cat is not None and not pd.isna(cat)]
                        unique_categories.update(valid_categories)
                        print(f"Categories from JPG: {valid_categories}")
                    
                    print(f"Unique categories found: {unique_categories}")
                    
                    # If we have no valid categories, add a default "Unknown" category
                    if not unique_categories:
                        unique_categories.add("Unknown")
                        print("No valid categories found, adding 'Unknown' category")
                    
                    # Process each category
                    for category in unique_categories:
                        print(f"Processing category: {category}")
                        # Create category entry with default values
                        category_data = {
                            'mp3_count': 0,
                            'mp3_percentage': 0.0,
                            'jpg_count': 0,
                            'jpg_percentage': 0.0,
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
                                print(f"Error calculating MP3 metrics for category {category}: {e}")
                        
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
                                print(f"Error calculating JPG metrics for category {category}: {e}")
                        
                        # Store category data
                        categories[category] = category_data
                    
                except Exception as e:
                    print(f"Error processing category distribution: {e}")
                    traceback.print_exc()
                
                print(f"Category distribution: {categories}")
                year_metrics['category_distribution'] = categories
                
                # Store all year metrics
                result[school_year] = year_metrics
            
            print(f"\nFinal result: {result}")
            # Important: Simply returning the result dictionary, not converting to DataFrame
            return result
            
        except Exception as e:
            print(f"Exception in aggregate_by_school_year: {e}")
            traceback.print_exc()
            return {}
    
    # Apply the patch
    DataAggregator.aggregate_by_school_year = patched_method
    
    # Execute the test method
    try:
        print("\nRunning test_aggregate_by_school_year...")
        year_agg = aggregator.aggregate_by_school_year(mp3_df, jpg_df)
        print("\nAggregation successful!")
        print(f"Result contains {len(year_agg)} school years")
        
        # Check the structure of what the test expects
        for school_year, metrics in year_agg.items():
            print(f"\nSchool year: {school_year}")
            print(f"Keys in metrics: {sorted(metrics.keys())}")
            
            if 'activity_distribution' in metrics:
                activities = metrics['activity_distribution']
                print(f"Activity distribution keys: {sorted(activities.keys())}")
                for activity, data in activities.items():
                    print(f"  {activity}: {data}")
            
            if 'category_distribution' in metrics:
                categories = metrics['category_distribution']
                print(f"Category distribution keys: {sorted(categories.keys())}")
                for category, data in categories.items():
                    print(f"  {category}: {data}")
    except Exception as e:
        print(f"Test execution failed: {e}")
        traceback.print_exc()
    
    # Restore the original method
    DataAggregator.aggregate_by_school_year = original_method

if __name__ == "__main__":
    debug_aggregate_by_school_year()
