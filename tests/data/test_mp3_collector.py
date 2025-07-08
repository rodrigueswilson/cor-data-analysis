"""
Tests for the MP3 collector.

This module tests the functionality of the MP3Collector class, including
MP3 metadata extraction, activity determination, and file processing.
"""
import os
import re
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from unittest import mock

import pytest
from mutagen.mp3 import MP3
from pydantic import BaseModel

from cor_data_analysis.config.settings import Settings
from cor_data_analysis.data.collectors.mp3_collector import MP3Collector, MP3CollectorOptions
from cor_data_analysis.data.collectors.base import FileInfo


class TestMP3Collector:
    """Test suite for MP3Collector functionality."""
    
    @pytest.fixture
    def mp3_collector(self, test_settings: Settings) -> MP3Collector:
        """Create an MP3 collector with test settings."""
        options = MP3CollectorOptions(
            batch_size=5,
            enable_outlier_detection=True,
            outlier_dirs=['outliers'],
            extract_id3_tags=True,
            determine_activity=True
        )
        return MP3Collector(test_settings, options)
    
    @pytest.fixture
    def mp3_metadata_mock(self):
        """Create a mock MP3 metadata object."""
        mock_mp3 = mock.MagicMock()
        mock_mp3.info.length = 180.5  # 3 minutes and 0.5 seconds
        # Create a dictionary-like mock for tags that correctly returns single string values
        mock_tags = mock.MagicMock()
        # Set up get method to return properly formatted values
        mock_tags.get.side_effect = lambda key, default: ['Test Artist'] if key == 'TPE1' else \
                                                  ['Test Album'] if key == 'TALB' else \
                                                  ['Test Title'] if key == 'TIT2' else default
        # Set up __contains__ to simulate 'in' operator
        mock_tags.__contains__.side_effect = lambda key: key in ['TPE1', 'TALB', 'TIT2']
        mock_mp3.tags = mock_tags
        return mock_mp3
    
    @pytest.fixture
    def test_mp3_file(self, temp_dir: Path) -> Path:
        """Create a test MP3 file path (doesn't create actual file)."""
        return temp_dir / "230501_0830.mp3"
    
    def test_extract_datetime_from_filename(self, mp3_collector: MP3Collector):
        """Test extracting date and time from filename."""
        # Valid patterns
        assert mp3_collector._extract_datetime_from_filename("230501_0830.mp3") == ("230501", "0830")
        assert mp3_collector._extract_datetime_from_filename("230501_0830_01.mp3") == ("230501", "0830")
        
        # Invalid patterns
        assert mp3_collector._extract_datetime_from_filename("invalid.mp3") == (None, None)
        assert mp3_collector._extract_datetime_from_filename("230501_0830.wav") == (None, None)
        
        # Test with custom pattern
        mp3_collector.options.filename_pattern = r"(\d{4})(\d{2})_\d+\.mp3$"
        assert mp3_collector._extract_datetime_from_filename("202305_01.mp3") == ("2023", "05")
    
    def test_format_duration(self, mp3_collector: MP3Collector):
        """Test formatting duration from seconds to HH:MM:SS."""
        assert mp3_collector._format_duration(3661.2) == "01:01:01"  # 1 hour, 1 minute, 1 second
        assert mp3_collector._format_duration(60) == "00:01:00"  # 1 minute
        assert mp3_collector._format_duration(30) == "00:00:30"  # 30 seconds
        assert mp3_collector._format_duration(0) == "00:00:00"  # 0 seconds
        assert mp3_collector._format_duration(None) == ""  # None duration
    
    def test_determine_activity(self, mp3_collector: MP3Collector):
        """Test determining activity based on time string."""
        # Test various times
        assert mp3_collector._determine_activity("0815") == "Free Play"
        assert mp3_collector._determine_activity("0845") == "Breakfast"
        assert mp3_collector._determine_activity("0910") == "Greeting Time"
        assert mp3_collector._determine_activity("0920") == "Small Group"
        assert mp3_collector._determine_activity("0940") == "Planning Time"
        assert mp3_collector._determine_activity("1000") == "Work Time I"
        assert mp3_collector._determine_activity("1050") == "Clean Up"
        assert mp3_collector._determine_activity("1100") == "Recall"
        assert mp3_collector._determine_activity("1110") == "Large Group"
        assert mp3_collector._determine_activity("1130") == "Lunch Time"
        assert mp3_collector._determine_activity("1300") == "Other"
        
        # Test None and invalid
        assert mp3_collector._determine_activity(None) is None
        assert mp3_collector._determine_activity("invalid") is None
        
        # Test with activity determination disabled
        mp3_collector.options.determine_activity = False
        assert mp3_collector._determine_activity("0830") is None
    
    @mock.patch('cor_data_analysis.data.collectors.mp3_collector.MP3')
    def test_extract_metadata(self, mock_mp3_class, mp3_collector: MP3Collector, 
                           mp3_metadata_mock, test_mp3_file: Path):
        """Test extracting metadata from MP3 file."""
        # Setup mock MP3 instance
        mock_mp3_class.return_value = mp3_metadata_mock
        
        # Create a FileInfo object for the test file
        file_info = FileInfo(
            path=test_mp3_file,
            size=1024000,  # ~1MB
            mtime=datetime.now().timestamp(),
            root=test_mp3_file.parent,
            name=test_mp3_file.name
        )
        
        # Extract metadata
        metadata = mp3_collector.extract_metadata(file_info)
        
        # Verify the metadata
        assert metadata is not None
        assert metadata['file_path'] == str(test_mp3_file)
        assert metadata['file_name'] == test_mp3_file.name
        assert metadata['date'] == "230501"
        assert metadata['time'] == "0830"
        assert metadata['duration_seconds'] == 180.5
        assert metadata['duration_hms'] == "00:03:00"
        assert metadata['file_size_mb'] == 0.98
        assert metadata['artist'] == "Test Artist"
        assert metadata['album'] == "Test Album"
        assert metadata['title'] == "Test Title"
        
        # Test without ID3 tags
        mp3_collector.options.extract_id3_tags = False
        metadata = mp3_collector.extract_metadata(file_info)
        assert 'artist' not in metadata
        assert 'album' not in metadata
        assert 'title' not in metadata
    
    @mock.patch('cor_data_analysis.data.collectors.mp3_collector.MP3')
    def test_process_file(self, mock_mp3_class, mp3_collector: MP3Collector, 
                       mp3_metadata_mock, test_mp3_file: Path):
        """Test processing an MP3 file."""
        # Setup mock MP3 instance
        mock_mp3_class.return_value = mp3_metadata_mock
        
        # Create a FileInfo object for the test file
        file_info = FileInfo(
            path=test_mp3_file,
            size=1024000,  # ~1MB
            mtime=datetime.now().timestamp(),
            root=test_mp3_file.parent,
            name=test_mp3_file.name
        )
        
        # Process the file
        result = mp3_collector.process_file(file_info)
        
        # Verify the result
        assert result is not None
        assert result['file_path'] == str(test_mp3_file)
        assert result['activity'] == "Breakfast"  # Based on time 0830
        assert 'processed_at' in result
        
        # Verify processed_at is a valid ISO format datetime
        try:
            datetime.fromisoformat(result['processed_at'])
            valid_datetime = True
        except ValueError:
            valid_datetime = False
        assert valid_datetime is True
    
    @mock.patch('cor_data_analysis.data.collectors.mp3_collector.MP3')
    def test_process_file_with_error(self, mock_mp3_class, mp3_collector: MP3Collector, test_mp3_file: Path):
        """Test processing an MP3 file that causes an error."""
        # Make MP3 constructor raise an exception
        mock_mp3_class.side_effect = Exception("Test error")
        
        # Create a FileInfo object for the test file
        file_info = FileInfo(
            path=test_mp3_file,
            size=1024000,
            mtime=datetime.now().timestamp(),
            root=test_mp3_file.parent,
            name=test_mp3_file.name
        )
        
        # Process should return None on error
        result = mp3_collector.process_file(file_info)
        assert result is None
