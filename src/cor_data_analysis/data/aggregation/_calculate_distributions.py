"""
Temporary file to develop the _calculate_distributions method
This will be moved into aggregator.py once it's working correctly
"""

def _calculate_distributions(self, year_mp3, year_jpg, total_mp3_count, total_jpg_count):
    """
    Calculate activity and category distributions from MP3 and JPG data.
    
    This method ensures that all dictionary entries have a consistent structure
    to prevent the "ValueError: All arrays must be of the same length" error
    when converting to DataFrames.
    
    Args:
        year_mp3: DataFrame with MP3 metadata for the current period
        year_jpg: DataFrame with JPG metadata for the current period
        total_mp3_count: Total count of MP3 files
        total_jpg_count: Total count of JPG files
        
    Returns:
        Dictionary with 'activity_distribution' and 'category_distribution' keys,
        each containing nested dictionaries with consistent structure
    """
    # Initialize return structure
    distributions = {
        'activity_distribution': {},
        'category_distribution': {}
    }
    
    # Handle empty dataframes
    if (year_mp3.empty and year_jpg.empty) or (total_mp3_count == 0 and total_jpg_count == 0):
        return distributions
    
    # ------ Activity Distribution ------
    # Get all unique activities from both dataframes
    mp3_activities = set() if year_mp3.empty or 'Activity' not in year_mp3.columns else set(year_mp3['Activity'].dropna())
    jpg_activities = set() if year_jpg.empty or 'Activity' not in year_jpg.columns else set(year_jpg['Activity'].dropna())
    all_activities = sorted(mp3_activities.union(jpg_activities))
    
    if not all_activities:
        all_activities = ['Unknown']
    
    # Initialize activity distribution with consistent structure
    # This is key to avoiding the "All arrays must be of the same length" error
    activity_distribution = {}
    for activity in all_activities:
        # Pre-initialize with all possible keys, setting defaults to 0/0.0
        activity_distribution[activity] = {
            'mp3_count': 0,
            'mp3_percentage': 0.0,
            'jpg_count': 0,
            'jpg_percentage': 0.0
        }
    
    # Calculate MP3 counts and percentages
    if not year_mp3.empty and 'Activity' in year_mp3.columns and total_mp3_count > 0:
        mp3_counts = year_mp3['Activity'].value_counts()
        for activity, count in mp3_counts.items():
            if activity in activity_distribution:
                activity_distribution[activity]['mp3_count'] = count
                activity_distribution[activity]['mp3_percentage'] = (count / total_mp3_count) * 100.0
    
    # Calculate JPG counts and percentages
    if not year_jpg.empty and 'Activity' in year_jpg.columns and total_jpg_count > 0:
        jpg_counts = year_jpg['Activity'].value_counts()
        for activity, count in jpg_counts.items():
            if activity in activity_distribution:
                activity_distribution[activity]['jpg_count'] = count
                activity_distribution[activity]['jpg_percentage'] = (count / total_jpg_count) * 100.0
    
    distributions['activity_distribution'] = activity_distribution
    
    # ------ Category Distribution ------
    # Get all unique categories from both dataframes
    mp3_categories = set() if year_mp3.empty or 'ActivityCategory' not in year_mp3.columns else set(year_mp3['ActivityCategory'].dropna())
    jpg_categories = set() if year_jpg.empty or 'ActivityCategory' not in year_jpg.columns else set(year_jpg['ActivityCategory'].dropna())
    all_categories = sorted(mp3_categories.union(jpg_categories))
    
    if not all_categories:
        all_categories = ['Unknown']
    
    # Initialize category distribution with consistent structure
    category_distribution = {}
    for category in all_categories:
        # Pre-initialize with all possible keys, setting defaults to 0/0.0
        category_distribution[category] = {
            'mp3_count': 0,
            'mp3_percentage': 0.0,
            'jpg_count': 0,
            'jpg_percentage': 0.0
        }
    
    # Calculate MP3 counts and percentages by category
    if not year_mp3.empty and 'ActivityCategory' in year_mp3.columns and total_mp3_count > 0:
        mp3_category_counts = year_mp3['ActivityCategory'].value_counts()
        for category, count in mp3_category_counts.items():
            if category in category_distribution:
                category_distribution[category]['mp3_count'] = count
                category_distribution[category]['mp3_percentage'] = (count / total_mp3_count) * 100.0
    
    # Calculate JPG counts and percentages by category
    if not year_jpg.empty and 'ActivityCategory' in year_jpg.columns and total_jpg_count > 0:
        jpg_category_counts = year_jpg['ActivityCategory'].value_counts()
        for category, count in jpg_category_counts.items():
            if category in category_distribution:
                category_distribution[category]['jpg_count'] = count
                category_distribution[category]['jpg_percentage'] = (count / total_jpg_count) * 100.0
    
    distributions['category_distribution'] = category_distribution
    
    return distributions
