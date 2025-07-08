"""
Tests for the base collector class.

This module tests the functionality of the BaseCollector class, including
directory scanning, file filtering, and outlier detection.
"""
import os
import shutil
import tempfile
from pathlib import Path
from typing import Dict, List, Optional

import pytest
from pydantic import BaseModel

from cor_data_analysis.config.settings import Settings
from cor_data_analysis.data.collectors.base import BaseCollector, CollectorOptions, FileInfo


class _TestCollector(BaseCollector):
    """Test implementation of the BaseCollector for testing."""
    
    def extract_metadata(self, file_info: FileInfo) -> Optional[Dict]:
        """Simple implementation that returns basic file info as metadata."""
        return {
            'filename': file_info.name,
            'size': file_info.size,
            'path': str(file_info.path)
        }
    
    def process_file(self, file_info: FileInfo) -> Optional[Dict]:
        """Process a test file."""
        metadata = self.extract_metadata(file_info)
        if metadata:
            metadata['processed'] = True
        return metadata


class TestBaseCollector:
    """Test suite for BaseCollector functionality."""

    @pytest.fixture
    def test_collector(self, test_settings: Settings) -> _TestCollector:
        """Create a test collector with settings."""
        options = CollectorOptions(
            extensions=['txt', 'dat'],
            batch_size=10,
            enable_outlier_detection=True,
            outlier_dirs=['outliers', 'excluded']
        )
        return _TestCollector(test_settings, options)

    @pytest.fixture
    def test_files_structure(self, temp_dir: Path) -> Dict[str, Path]:
        """Create a test directory structure with files."""
        # Create main directories
        main_dir = temp_dir / "data"
        outlier_dir = temp_dir / "outliers"

        dirs = {
            'main': main_dir,
            'outliers': outlier_dir,
        }

        # Create directories
        for dir_path in dirs.values():
            dir_path.mkdir(exist_ok=True)

        # Create test files in main directory
        for i in range(5):
            file_path = main_dir / f"test_{i}.txt"
            with open(file_path, 'w') as f:
                f.write(f"Test file {i}")

            file_path = main_dir / f"test_{i}.dat"
            with open(file_path, 'w') as f:
                f.write(f"Test data file {i}")

            file_path = main_dir / f"test_{i}.bin"  # Should be ignored
            with open(file_path, 'w') as f:
                f.write(f"Test binary file {i}")

        # Create test files in outlier directory
        for i in range(3):
            file_path = outlier_dir / f"outlier_{i}.txt"
            with open(file_path, 'w') as f:
                f.write(f"Outlier file {i}")

            file_path = outlier_dir / f"outlier_{i}.dat"
            with open(file_path, 'w') as f:
                f.write(f"Outlier data file {i}")

        return dirs

    def test_scan_directory(self, test_collector: _TestCollector, test_files_structure: Dict[str, Path]):
        """Test scanning directories for files with specific extensions."""
        # Test scanning main directory
        files = test_collector.scan_directory(test_files_structure['main'])

        # Should only find .txt and .dat files (10 total)
        assert len(files) == 10
        assert all(f.name.endswith('.txt') or f.name.endswith('.dat') for f in files)
        assert not any(f.name.endswith('.bin') for f in files)

        # Check file info structure
        for f in files:
            assert isinstance(f, FileInfo)
            assert f.path.exists()
            assert f.size > 0
            assert f.mtime > 0

    def test_identify_outliers(self, test_collector: _TestCollector, test_files_structure: Dict[str, Path]):
        """Test identifying outlier files based on directory."""
        # Scan all files including outliers
        all_files = test_collector.scan_directory(test_files_structure['main'].parent)

        # Identify outliers
        normal_files, outlier_files = test_collector.identify_outliers(all_files)

        # Verify correct separation
        assert len(normal_files) == 10  # Files in main directory
        assert len(outlier_files) == 6   # Files in outliers directory

        # Verify normal files are in main directory
        for f in normal_files:
            assert 'outliers' not in f.root.parts

        # Verify outlier files are in outliers directory
        for f in outlier_files:
            assert 'outliers' in f.root.parts

        # Test with outlier detection disabled
        test_collector.options.enable_outlier_detection = False
        normal_files, outlier_files = test_collector.identify_outliers(all_files)
        assert len(normal_files) == len(all_files)
        assert len(outlier_files) == 0

    def test_batch_processing(self, test_collector: _TestCollector, test_files_structure: Dict[str, Path]):
        """Test processing files in batches."""
        # Set batch size to a small number to test multiple batches
        test_collector.options.batch_size = 3

        # Get files to process
        all_files = test_collector.scan_directory(test_files_structure['main'])
        assert len(all_files) == 10

        # Process files
        results = test_collector.batch_process(all_files, test_collector.process_file)

        # Verify all files were processed
        assert len(results) == 10
        for result in results:
            assert result['processed'] is True
            assert result['filename'].endswith(('.txt', '.dat'))

    def test_collect(self, test_collector: _TestCollector, test_files_structure: Dict[str, Path]):
        """Test the entire collection process."""
        # Run collection on the parent directory that includes both normal and outlier files
        collection_results = test_collector.collect(test_files_structure['main'].parent)

        # Verify the structure of the results
        assert 'data' in collection_results
        assert 'outliers' in collection_results

        # Verify counts
        assert len(collection_results['data']) == 10  # Files in main directory
        assert len(collection_results['outliers']) == 6  # Files in outliers directory

        # Verify the data is properly processed
        for item in collection_results['data'] + collection_results['outliers']:
            assert 'filename' in item
            assert 'size' in item
            assert 'path' in item
            assert 'processed' in item
            assert item['processed'] is True
