"""
MP3 collector for COR Data Analysis.

This module provides the MP3Collector class that handles scanning,
processing and metadata extraction from MP3 files.
"""
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from mutagen.mp3 import MP3
from mutagen.id3 import ID3NoHeaderError
from pydantic import BaseModel

from cor_data_analysis.config.settings import Settings
from cor_data_analysis.data.collectors.base import BaseCollector, CollectorOptions, FileInfo
from cor_data_analysis.utils.errors import capture_exception, try_except_with_default, safe_operation
from cor_data_analysis.utils.dt import format_date


class MP3CollectorOptions(CollectorOptions):
    """Configuration options specific to the MP3 collector."""
    # Default extensions for MP3 collector
    extensions: List[str] = ["mp3"]
    # Regex pattern for extracting date and time from filename
    filename_pattern: str = r"(\d{6})_(\d{4})(?:_\d{2})?\.mp3$"
    # Whether to extract ID3 tags
    extract_id3_tags: bool = True
    # Whether to determine activities based on time
    determine_activity: bool = True


class MP3Collector(BaseCollector):
    """
    Collector for MP3 files.
    
    This collector scans directories for MP3 files, extracts metadata
    using the mutagen library, and processes file information including
    extracting date/time from filenames and determining activity.
    """
    
    def __init__(self, settings: Settings, options: Optional[MP3CollectorOptions] = None):
        """
        Initialize the MP3 collector with settings and options.
        
        Args:
            settings: Application settings
            options: MP3 collector specific options
        """
        super().__init__(settings, options or MP3CollectorOptions())
        self.options: MP3CollectorOptions = self.options  # Type hint for IDE
    
    def extract_metadata(self, file_info: FileInfo) -> Optional[Dict[str, Any]]:
        """
        Extract raw metadata from an MP3 file.
        
        Args:
            file_info: FileInfo object
            
        Returns:
            Dictionary with metadata or None if extraction failed
        """
        try:
            audio = MP3(str(file_info.path))
            tags = audio.tags if audio.tags else {}
            
            # Extract date and time from filename if possible
            date_str, time_str = self._extract_datetime_from_filename(file_info.name)
            
            duration = audio.info.length if audio.info else None
            file_size_mb = file_info.size / (1024 * 1024)
            
            metadata = {
                'file_path': str(file_info.path),
                'file_name': file_info.name,
                'date': date_str,
                'time': time_str,
                'duration_seconds': duration,
                'duration_hms': self._format_duration(duration) if duration else None,
                'file_size_mb': round(file_size_mb, 2),
            }
            
            # Add ID3 tags if extraction is enabled
            if self.options.extract_id3_tags and tags:
                metadata.update({
                    'artist': str(tags.get('TPE1', [''])[0]) if 'TPE1' in tags else None,
                    'album': str(tags.get('TALB', [''])[0]) if 'TALB' in tags else None,
                    'title': str(tags.get('TIT2', [''])[0]) if 'TIT2' in tags else None,
                })
            
            return metadata
        except ID3NoHeaderError:
            self.logger.warning(f"No ID3 header found in {file_info.path}")
            return None
        except Exception as e:
            self.logger.warning(f"Failed to extract metadata from {file_info.path}: {e}")
            return None
    
    def _extract_datetime_from_filename(self, filename: str) -> tuple[Optional[str], Optional[str]]:
        """
        Extract date and time from filename based on the configured pattern.
        
        Args:
            filename: Name of the file
            
        Returns:
            Tuple of (date_string, time_string) or (None, None) if not found
        """
        match = re.match(self.options.filename_pattern, filename, re.IGNORECASE)
        if match:
            return match.groups()[:2]
        return None, None
    
    def _format_duration(self, seconds: Optional[float]) -> str:
        """
        Format duration in seconds to HH:MM:SS format.
        
        Args:
            seconds: Duration in seconds
            
        Returns:
            Formatted duration string
        """
        if seconds is None:
            return ''
        seconds = int(seconds)
        return f"{seconds//3600:02}:{(seconds%3600)//60:02}:{seconds%60:02}"
    
    def _determine_activity(self, time_str: Optional[str]) -> Optional[str]:
        """
        Classify activity based on time string (e.g. 0830 = Breakfast).
        
        Args:
            time_str: Time string in HHMM format
            
        Returns:
            Activity name or None if time_str is None or no matching activity found
        """
        if not time_str or not self.options.determine_activity:
            return None
            
        # Activity mapping from the original code
        try:
            time_int = int(time_str)
            if 800 <= time_int < 830:
                return "Free Play"
            elif 830 <= time_int < 900:
                return "Breakfast"
            elif 900 <= time_int < 915:
                return "Greeting Time"
            elif 915 <= time_int < 935:
                return "Small Group"
            elif 935 <= time_int < 945:
                return "Planning Time"
            elif 945 <= time_int < 1045:
                return "Work Time I"
            elif 1045 <= time_int < 1055:
                return "Clean Up"
            elif 1055 <= time_int < 1105:
                return "Recall"
            elif 1105 <= time_int < 1125:
                return "Large Group"
            elif 1125 <= time_int < 1200:
                return "Lunch Time"
            else:
                return "Other"
        except ValueError:
            self.logger.warning(f"Could not convert time string '{time_str}' to integer")
            return None
    
    def process_file(self, file_info: FileInfo) -> Optional[Dict[str, Any]]:
        """
        Process an MP3 file, extracting metadata and additional information.
        
        Args:
            file_info: FileInfo object
            
        Returns:
            Dictionary with processed metadata or None if processing failed
        """
        meta = self.extract_metadata(file_info)
        if not meta:
            return None
            
        # Add activity classification if enabled
        meta['activity'] = self._determine_activity(meta['time'])
        
        # Add processing timestamp
        meta['processed_at'] = datetime.now().isoformat()
        
        return meta
