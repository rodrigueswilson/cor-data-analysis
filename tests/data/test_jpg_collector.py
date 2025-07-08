"""
Tests for the JPG collector.

This module tests the functionality of the JPGCollector class, including
JPG metadata extraction, EXIF data handling, and GPS data extraction.
"""
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from unittest import mock

import pytest
from PIL import Image, ExifTags
from pydantic import BaseModel

from cor_data_analysis.config.settings import Settings
from cor_data_analysis.data.collectors.jpg_collector import JPGCollector, JPGCollectorOptions
from cor_data_analysis.data.collectors.base import FileInfo


class TestJPGCollector:
    """Test suite for JPGCollector functionality."""
    
    @pytest.fixture
    def jpg_collector(self, test_settings: Settings) -> JPGCollector:
        """Create a JPG collector with test settings."""
        options = JPGCollectorOptions(
            batch_size=5,
            enable_outlier_detection=True,
            outlier_dirs=['outliers'],
            extract_exif=True,
            extract_gps=True
        )
        return JPGCollector(test_settings, options)
    
    @pytest.fixture
    def mock_image(self):
        """Create a mock PIL Image."""
        mock_img = mock.MagicMock()
        mock_img.width = 1920
        mock_img.height = 1080
        mock_img.format = "JPEG"
        mock_img.mode = "RGB"
        
        # Mock EXIF data
        mock_exif = {
            271: 'Nikon',  # Make
            272: 'D750',   # Model
            306: '2023:05:01 08:30:00',  # DateTime
            33437: (4, 1),  # FNumber - f/4
            34855: 100,  # ISOSpeedRatings
            37386: (50, 1),  # FocalLength - 50mm
        }
        
        # Mock GPS data
        mock_gps_info = {
            1: 'N',  # GPSLatitudeRef
            2: ((40, 1), (45, 1), (31, 100)),  # GPSLatitude - 40°45'31.0"
            3: 'W',  # GPSLongitudeRef
            4: ((74, 1), (0, 1), (31, 100)),  # GPSLongitude - 74°0'31.0"
            5: 0,  # GPSAltitudeRef
            6: (100, 1),  # GPSAltitude - 100m
        }
        
        # Add GPSInfo to EXIF
        mock_exif[34853] = mock_gps_info
        
        # Setup the _getexif method
        mock_img._getexif = mock.MagicMock(return_value=mock_exif)
        
        return mock_img
    
    @pytest.fixture
    def test_jpg_file(self, temp_dir: Path) -> Path:
        """Create a test JPG file path (doesn't create actual file)."""
        return temp_dir / "230501_0830.jpg"
    
    def test_extract_datetime_from_filename(self, jpg_collector: JPGCollector):
        """Test extracting date and time from filename."""
        # Valid patterns
        assert jpg_collector._extract_datetime_from_filename("230501_0830.jpg") == ("230501", "0830")
        assert jpg_collector._extract_datetime_from_filename("230501_0830_01.jpg") == ("230501", "0830")
        assert jpg_collector._extract_datetime_from_filename("230501_0830.JPEG") == ("230501", "0830")
        
        # Invalid patterns
        assert jpg_collector._extract_datetime_from_filename("invalid.jpg") == (None, None)
        assert jpg_collector._extract_datetime_from_filename("230501_0830.png") == (None, None)
        
        # Test with custom pattern
        jpg_collector.options.filename_pattern = r"(\d{4})(\d{2})_\d+\.(?:jpg|jpeg)$"
        assert jpg_collector._extract_datetime_from_filename("202305_01.jpg") == ("2023", "05")
    
    def test_convert_to_decimal_degrees(self, jpg_collector: JPGCollector):
        """Test converting degrees/minutes/seconds to decimal degrees."""
        # Test exact values
        assert jpg_collector._convert_to_decimal_degrees((40, 45, 31)) == pytest.approx(40.75861, 0.00001)
        assert jpg_collector._convert_to_decimal_degrees((0, 0, 0)) == 0
        
        # Test with different values
        assert jpg_collector._convert_to_decimal_degrees((10, 30, 0)) == 10.5
        
        # Test with None values (should default to 0)
        assert jpg_collector._convert_to_decimal_degrees((40, None, 31)) == pytest.approx(40.00861, 0.00001)
    
    @mock.patch('cor_data_analysis.data.collectors.jpg_collector.Image')
    def test_extract_metadata(self, mock_image_module, jpg_collector: JPGCollector, 
                           mock_image, test_jpg_file: Path):
        """Test extracting metadata from JPG file."""
        # Setup mock Image.open to return our mock image
        mock_image_module.open.return_value = mock_image
        
        # Create a FileInfo object for the test file
        file_info = FileInfo(
            path=test_jpg_file,
            size=2048000,  # ~2MB
            mtime=datetime.now().timestamp(),
            root=test_jpg_file.parent,
            name=test_jpg_file.name
        )
        
        # Extract metadata
        metadata = jpg_collector.extract_metadata(file_info)
        
        # Verify basic metadata
        assert metadata is not None
        assert metadata['file_path'] == str(test_jpg_file)
        assert metadata['file_name'] == test_jpg_file.name
        assert metadata['date'] == "230501"
        assert metadata['time'] == "0830"
        assert metadata['width'] == 1920
        assert metadata['height'] == 1080
        assert metadata['format'] == "JPEG"
        assert metadata['mode'] == "RGB"
        assert metadata['file_size_mb'] == 1.95
        
        # Verify EXIF data
        assert 'exif' in metadata
        assert metadata['exif']['Make'] == 'Nikon'
        assert metadata['exif']['Model'] == 'D750'
        assert metadata['exif']['DateTime'] == '2023:05:01 08:30:00'
        
        # Verify GPS data
        assert 'gps' in metadata
        assert 'latitude' in metadata['gps']
        assert 'longitude' in metadata['gps']
        assert metadata['gps']['latitude'] == pytest.approx(40.750086, 0.00001)
        assert metadata['gps']['longitude'] == pytest.approx(-74.000086, 0.00001)
        
        # Test with EXIF extraction disabled
        jpg_collector.options.extract_exif = False
        metadata = jpg_collector.extract_metadata(file_info)
        assert 'exif' not in metadata
        assert 'gps' not in metadata
        
        # Test with GPS extraction disabled
        jpg_collector.options.extract_exif = True
        jpg_collector.options.extract_gps = False
        metadata = jpg_collector.extract_metadata(file_info)
        assert 'exif' in metadata
        assert 'gps' not in metadata
    
    @mock.patch('cor_data_analysis.data.collectors.jpg_collector.Image')
    def test_process_file(self, mock_image_module, jpg_collector: JPGCollector, 
                       mock_image, test_jpg_file: Path):
        """Test processing a JPG file."""
        # Setup mock Image.open
        mock_image_module.open.return_value = mock_image
        
        # Create a FileInfo object for the test file
        file_info = FileInfo(
            path=test_jpg_file,
            size=2048000,  # ~2MB
            mtime=datetime.now().timestamp(),
            root=test_jpg_file.parent,
            name=test_jpg_file.name
        )
        
        # Process the file
        result = jpg_collector.process_file(file_info)
        
        # Verify the result
        assert result is not None
        assert result['file_path'] == str(test_jpg_file)
        assert 'processed_at' in result
        
        # Verify processed_at is a valid ISO format datetime
        try:
            datetime.fromisoformat(result['processed_at'])
            valid_datetime = True
        except ValueError:
            valid_datetime = False
        assert valid_datetime is True
    
    @mock.patch('cor_data_analysis.data.collectors.jpg_collector.Image')
    def test_process_file_with_error(self, mock_image_module, jpg_collector: JPGCollector, test_jpg_file: Path):
        """Test processing a JPG file that causes an error."""
        # Make Image.open raise an exception
        mock_image_module.open.side_effect = Exception("Test error")
        
        # Create a FileInfo object for the test file
        file_info = FileInfo(
            path=test_jpg_file,
            size=2048000,
            mtime=datetime.now().timestamp(),
            root=test_jpg_file.parent,
            name=test_jpg_file.name
        )
        
        # Process should return None on error
        result = jpg_collector.process_file(file_info)
        assert result is None
