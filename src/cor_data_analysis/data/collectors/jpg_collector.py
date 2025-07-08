"""
JPG collector for COR Data Analysis.

This module provides the JPGCollector class that handles scanning,
processing and metadata extraction from JPG/JPEG files.
"""
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from PIL import Image, ExifTags
from pydantic import BaseModel

from cor_data_analysis.config.settings import Settings
from cor_data_analysis.data.collectors.base import BaseCollector, CollectorOptions, FileInfo
from cor_data_analysis.utils.errors import capture_exception, try_except_with_default, safe_operation
from cor_data_analysis.utils.dt import format_date


class JPGCollectorOptions(CollectorOptions):
    """Configuration options specific to the JPG collector."""
    # Default extensions for JPG collector
    extensions: List[str] = ["jpg", "jpeg"]
    # Regex pattern for extracting date and time from filename
    filename_pattern: str = r"(\d{6})_(\d{4,6})(?:_\d{2})?\.(?:jpg|jpeg)$"
    # Whether to extract EXIF data
    extract_exif: bool = True
    # Whether to extract GPS data
    extract_gps: bool = True


class JPGCollector(BaseCollector):
    """
    Collector for JPG/JPEG files.
    
    This collector scans directories for JPG files, extracts metadata
    using the Pillow library, and processes file information including
    extracting date/time from filenames and EXIF data.
    """
    
    def __init__(self, settings: Settings, options: Optional[JPGCollectorOptions] = None):
        """
        Initialize the JPG collector with settings and options.
        
        Args:
            settings: Application settings
            options: JPG collector specific options
        """
        super().__init__(settings, options or JPGCollectorOptions())
        self.options: JPGCollectorOptions = self.options  # Type hint for IDE
    
    def extract_metadata(self, file_info: FileInfo) -> Optional[Dict[str, Any]]:
        """
        Extract raw metadata from a JPG file.
        
        Args:
            file_info: FileInfo object
            
        Returns:
            Dictionary with metadata or None if extraction failed
        """
        try:
            # Open the image
            img = Image.open(file_info.path)
            
            # Extract date and time from filename if possible
            date_str, time_str = self._extract_datetime_from_filename(file_info.name)
            
            # Basic metadata
            file_size_mb = file_info.size / (1024 * 1024)
            
            metadata = {
                'file_path': str(file_info.path),
                'file_name': file_info.name,
                'date': date_str,
                'time': time_str,
                'width': img.width,
                'height': img.height,
                'format': img.format,
                'mode': img.mode,
                'file_size_mb': round(file_size_mb, 2),
            }
            
            # Extract EXIF data if available and enabled
            if self.options.extract_exif and hasattr(img, '_getexif') and img._getexif():
                exif = {
                    ExifTags.TAGS[k]: v
                    for k, v in img._getexif().items()
                    if k in ExifTags.TAGS
                }
                
                # Add common EXIF fields
                exif_data = {}
                
                for tag in ['Make', 'Model', 'DateTime', 'ExposureTime', 
                          'FNumber', 'ISOSpeedRatings', 'FocalLength']:
                    if tag in exif:
                        exif_data[tag] = str(exif[tag])
                
                metadata.update({'exif': exif_data})
                
                # Extract GPS data if available and enabled
                if self.options.extract_gps:
                    # Get GPS data either from 'GPSInfo' key or tag 34853
                    if 'GPSInfo' in exif or 34853 in img._getexif():
                        # If the tag exists but wasn't mapped by EXIF tags, access it directly
                        if 'GPSInfo' not in exif and 34853 in img._getexif():
                            exif['GPSInfo'] = img._getexif()[34853]
                        
                        gps_data = self._extract_gps_data(exif)
                        if gps_data:
                            metadata.update(gps_data)
            
            return metadata
        except Exception as e:
            self.logger.warning(f"Failed to extract metadata from {file_info.path}: {e}")
            return None
    
    def _extract_datetime_from_filename(self, filename: str) -> Tuple[str, str]:
        """Extract date and time components from a filename.
        
        Parses filenames like 'YYMMDD_HHMMSS.jpg' using the regex pattern from options.
        Supports both 4-digit (HHMM) and 6-digit (HHMMSS) time formats.
        
        Args:
            filename: Name of the file (without path)
            
        Returns:
            Tuple of (date_string, time_string) or (None, None) if not found
        """
        match = re.match(self.options.filename_pattern, filename, re.IGNORECASE)
        if match:
            return match.groups()[:2]
        return None, None
    
    def _extract_gps_data(self, exif: Dict[Union[str, int], Any]) -> Optional[Dict[str, Any]]:
        """Extract GPS data from EXIF tags if available.
        
        Handles both string keys ('GPSInfo') and numeric tag IDs (34853) for GPS data.
        Converts GPS coordinates from degrees/minutes/seconds format to decimal degrees.
        Properly accounts for N/S and E/W references to set the correct sign.
        
        Args:
            exif: Dictionary of EXIF tags extracted from JPG file
            
        Returns:
            Dictionary with GPS data including decimal latitude and longitude, or None if unavailable
        """
        try:
            # First try to get GPSInfo from the EXIF dictionary
            gps_info = exif.get('GPSInfo', {})
            
            if not gps_info:
                # If not found, GPSInfo might be under the raw tag number 34853
                gps_info = exif.get(34853, {})
                
            if not gps_info:
                return None
                
            gps_data = {}
            
            # Extract GPS tags using their tag numbers
            gps_tags = {
                1: 'GPSLatitudeRef',  # N or S
                2: 'GPSLatitude',      # ((deg, 1), (min, 1), (sec, 1))
                3: 'GPSLongitudeRef',  # E or W
                4: 'GPSLongitude',     # ((deg, 1), (min, 1), (sec, 1))
                5: 'GPSAltitudeRef',   # 0 = above sea level
                6: 'GPSAltitude',      # (altitude, 1)
            }
            
            for key, name in gps_tags.items():
                if key in gps_info:
                    gps_data[name] = gps_info[key]
            
            # Calculate decimal latitude and longitude if possible
            if all(tag in gps_data for tag in ['GPSLatitudeRef', 'GPSLatitude', 'GPSLongitudeRef', 'GPSLongitude']):
                # Convert the degree/minute/second tuple to decimal degrees
                lat_tuple = tuple(float(x)/float(y) if isinstance(x, (int, float)) and isinstance(y, (int, float)) else x 
                              for x, y in gps_data['GPSLatitude'])
                lon_tuple = tuple(float(x)/float(y) if isinstance(x, (int, float)) and isinstance(y, (int, float)) else x 
                              for x, y in gps_data['GPSLongitude'])
                
                lat = self._convert_to_decimal_degrees(lat_tuple)
                lon = self._convert_to_decimal_degrees(lon_tuple)
                
                # Adjust for N/S and E/W
                if gps_data.get('GPSLatitudeRef') == 'S':
                    lat = -lat
                if gps_data.get('GPSLongitudeRef') == 'W':
                    lon = -lon
                    
                gps_data['latitude'] = lat
                gps_data['longitude'] = lon
            
            return {'gps': gps_data}
        except Exception as e:
            self.logger.warning(f"Failed to extract GPS data: {e}")
            return None
    
    def _convert_to_decimal_degrees(self, dms: tuple) -> float:
        """
        Convert GPS coordinates from degrees/minutes/seconds to decimal degrees.
        
        Args:
            dms: Tuple of (degrees, minutes, seconds)
            
        Returns:
            Decimal degrees as float
        """
        # Extract degrees, minutes, seconds
        degrees = float(dms[0]) if dms[0] else 0
        minutes = float(dms[1]) if dms[1] else 0
        seconds = float(dms[2]) if dms[2] else 0
        
        # Convert to decimal degrees
        return degrees + minutes/60 + seconds/3600
    
    def process_file(self, file_info: FileInfo) -> Optional[Dict[str, Any]]:
        """
        Process a JPG file, extracting metadata and additional information.
        
        Args:
            file_info: FileInfo object
            
        Returns:
            Dictionary with processed metadata or None if processing failed
        """
        meta = self.extract_metadata(file_info)
        if not meta:
            return None
            
        # Add processing timestamp
        meta['processed_at'] = datetime.now().isoformat()
        
        return meta
