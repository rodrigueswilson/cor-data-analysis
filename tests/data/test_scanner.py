"""
Tests for the Scanner class.

This module tests the Scanner class that provides a unified interface
for scanning directories and collecting metadata from both MP3 and JPG files.
"""

import os
from pathlib import Path
from typing import Dict

import pytest
from unittest import mock

from cor_data_analysis.config.settings import Settings
from cor_data_analysis.data.collectors.scanner import Scanner, ScannerOptions
from cor_data_analysis.data.collectors.mp3_collector import MP3CollectorOptions
from cor_data_analysis.data.collectors.jpg_collector import JPGCollectorOptions


class TestScanner:
    """Test suite for the Scanner class."""

    @pytest.fixture
    def scanner(self, test_settings: Settings) -> Scanner:
        """Create a Scanner with test settings."""
        return Scanner(test_settings)

    @pytest.fixture
    def scanner_mp3_only(self, test_settings: Settings) -> Scanner:
        """Create a Scanner with MP3 collection only."""
        options = ScannerOptions(
            enable_mp3=True,
            enable_jpg=False,
        )
        return Scanner(test_settings, options)

    @pytest.fixture
    def scanner_jpg_only(self, test_settings: Settings) -> Scanner:
        """Create a Scanner with JPG collection only."""
        options = ScannerOptions(
            enable_mp3=False,
            enable_jpg=True,
        )
        return Scanner(test_settings, options)

    @pytest.fixture
    def mixed_files_structure(self, temp_dir: Path) -> Dict[str, Path]:
        """Create a test directory structure with both MP3 and JPG files."""
        # Create main directories
        main_dir = temp_dir / "data"
        outlier_dir = temp_dir / "outliers"
        
        dirs = {
            'main': main_dir,
            'outliers': outlier_dir,
            'root': temp_dir
        }
        
        # Create directories
        for dir_path in dirs.values():
            dir_path.mkdir(exist_ok=True)
        
        # Create test MP3 files in main directory
        for i in range(3):
            file_path = main_dir / f"230501_08{i}0.mp3"
            with open(file_path, 'w') as f:
                pass
        
        # Create test JPG files in main directory
        for i in range(3):
            file_path = main_dir / f"230501_09{i}0.jpg"
            with open(file_path, 'w') as f:
                pass
        
        # Create outlier MP3 files
        for i in range(2):
            file_path = outlier_dir / f"230501_10{i}0.mp3"
            with open(file_path, 'w') as f:
                pass
        
        # Create outlier JPG files
        for i in range(2):
            file_path = outlier_dir / f"230501_11{i}0.jpg"
            with open(file_path, 'w') as f:
                pass
        
        return dirs

    def test_scanner_initialization(self, test_settings: Settings):
        """Test that Scanner is initialized correctly with various options."""
        # Test default initialization
        scanner = Scanner(test_settings)
        assert scanner.mp3_collector is not None
        assert scanner.jpg_collector is not None

        # Test MP3-only initialization
        options = ScannerOptions(enable_mp3=True, enable_jpg=False)
        scanner = Scanner(test_settings, options)
        assert scanner.mp3_collector is not None
        assert scanner.jpg_collector is None

        # Test JPG-only initialization
        options = ScannerOptions(enable_mp3=False, enable_jpg=True)
        scanner = Scanner(test_settings, options)
        assert scanner.mp3_collector is None
        assert scanner.jpg_collector is not None

        # Test custom collector options
        mp3_options = MP3CollectorOptions(batch_size=10, enable_outlier_detection=False)
        jpg_options = JPGCollectorOptions(batch_size=20, extract_exif=False)
        options = ScannerOptions(
            mp3_options=mp3_options,
            jpg_options=jpg_options,
        )
        scanner = Scanner(test_settings, options)
        assert scanner.mp3_collector is not None
        assert scanner.jpg_collector is not None
        assert scanner.options.mp3_options.batch_size == 10
        assert scanner.options.mp3_options.enable_outlier_detection is False
        assert scanner.options.jpg_options.batch_size == 20
        assert scanner.options.jpg_options.extract_exif is False

    @mock.patch('cor_data_analysis.data.collectors.mp3_collector.MP3')
    @mock.patch('cor_data_analysis.data.collectors.jpg_collector.Image')
    def test_scan_directory(self, mock_image_module, mock_mp3_module, 
                           scanner: Scanner, mixed_files_structure: Dict[str, Path]):
        """Test scanning a directory with both MP3 and JPG files."""
        # Setup mocks
        mock_mp3 = mock.MagicMock()
        mock_mp3.info.length = 180.0
        mock_mp3.tags = {}
        mock_mp3_module.return_value = mock_mp3
        
        mock_image = mock.MagicMock()
        mock_image.width = 1920
        mock_image.height = 1080
        mock_image.format = "JPEG"
        mock_image.mode = "RGB"
        mock_image._getexif.return_value = {}
        mock_image_module.open.return_value = mock_image
        
        # Scan directory
        results = scanner.scan_directory(mixed_files_structure['root'])
        
        # Verify results
        assert len(results['mp3_data']) == 3
        assert len(results['mp3_outliers']) == 2
        assert len(results['jpg_data']) == 3
        assert len(results['jpg_outliers']) == 2
        
        # Verify summary
        assert results['summary']['total_mp3'] == 5
        assert results['summary']['total_jpg'] == 5
        assert results['summary']['total_files'] == 10
        assert results['summary']['total_outliers'] == 4
        
    @mock.patch('cor_data_analysis.data.collectors.mp3_collector.MP3')
    def test_scan_directory_mp3_only(self, mock_mp3_module, 
                                    scanner_mp3_only: Scanner, 
                                    mixed_files_structure: Dict[str, Path]):
        """Test scanning a directory with MP3 files only."""
        # Setup mocks
        mock_mp3 = mock.MagicMock()
        mock_mp3.info.length = 180.0
        mock_mp3.tags = {}
        mock_mp3_module.return_value = mock_mp3
        
        # Scan directory
        results = scanner_mp3_only.scan_directory(mixed_files_structure['root'])
        
        # Verify results
        assert len(results['mp3_data']) == 3
        assert len(results['mp3_outliers']) == 2
        assert len(results['jpg_data']) == 0
        assert len(results['jpg_outliers']) == 0
        
        # Verify summary
        assert results['summary']['total_mp3'] == 5
        assert results['summary']['total_jpg'] == 0
        assert results['summary']['total_files'] == 5
        assert results['summary']['total_outliers'] == 2
        
    @mock.patch('cor_data_analysis.data.collectors.jpg_collector.Image')
    def test_scan_directory_jpg_only(self, mock_image_module,
                                   scanner_jpg_only: Scanner,
                                   mixed_files_structure: Dict[str, Path]):
        """Test scanning a directory with JPG files only."""
        # Setup mocks
        mock_image = mock.MagicMock()
        mock_image.width = 1920
        mock_image.height = 1080
        mock_image.format = "JPEG"
        mock_image.mode = "RGB"
        mock_image._getexif.return_value = {}
        mock_image_module.open.return_value = mock_image
        
        # Scan directory
        results = scanner_jpg_only.scan_directory(mixed_files_structure['root'])
        
        # Verify results
        assert len(results['mp3_data']) == 0
        assert len(results['mp3_outliers']) == 0
        assert len(results['jpg_data']) == 3
        assert len(results['jpg_outliers']) == 2
        
        # Verify summary
        assert results['summary']['total_mp3'] == 0
        assert results['summary']['total_jpg'] == 5
        assert results['summary']['total_files'] == 5
        assert results['summary']['total_outliers'] == 2
        
    @mock.patch('cor_data_analysis.data.collectors.mp3_collector.MP3')
    @mock.patch('cor_data_analysis.data.collectors.jpg_collector.Image')
    def test_process_directory_alias(self, mock_image_module, mock_mp3_module,
                                    scanner: Scanner, mixed_files_structure: Dict[str, Path]):
        """Test that process_directory is an alias for scan_directory."""
        # Setup mocks
        mock_mp3 = mock.MagicMock()
        mock_mp3.info.length = 180.0
        mock_mp3.tags = {}
        mock_mp3_module.return_value = mock_mp3
        
        mock_image = mock.MagicMock()
        mock_image.width = 1920
        mock_image.height = 1080
        mock_image.format = "JPEG"
        mock_image.mode = "RGB"
        mock_image._getexif.return_value = {}
        mock_image_module.open.return_value = mock_image
        
        # Mock scan_directory to verify it's called by process_directory
        scanner.scan_directory = mock.MagicMock(return_value={"mock_result": True})
        
        # Call process_directory
        result = scanner.process_directory(mixed_files_structure['root'])
        
        # Verify scan_directory was called with the same arguments
        scanner.scan_directory.assert_called_once_with(mixed_files_structure['root'])
        
        # Verify result is the same as scan_directory's return value
        assert result == {"mock_result": True}
