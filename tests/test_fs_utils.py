"""Tests for file system utilities."""

import os
import tempfile
from pathlib import Path
import shutil
import unittest
from unittest import mock

import pytest

from cor_data_analysis.utils.fs import (
    ensure_directory, safe_filename, list_files, safe_delete, safe_copy,
    batch_process_files, create_temp_directory, file_size_format
)


class TestFileSystemUtils(unittest.TestCase):
    """Test file system utility functions."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a temporary directory for testing
        self.test_dir = Path(tempfile.mkdtemp())
        
        # Create some test files and directories
        self.file1 = self.test_dir / "file1.txt"
        self.file1.write_text("Test file 1")
        
        self.file2 = self.test_dir / "file2.csv"
        self.file2.write_text("Test file 2")
        
        self.subdir = self.test_dir / "subdir"
        self.subdir.mkdir()
        
        self.file3 = self.subdir / "file3.txt"
        self.file3.write_text("Test file 3")
    
    def tearDown(self):
        """Tear down test fixtures."""
        # Clean up the temporary directory
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_ensure_directory(self):
        """Test ensuring a directory exists."""
        # Test existing directory
        path = ensure_directory(self.test_dir)
        assert path.exists()
        assert path.is_dir()
        
        # Test creating new directory
        new_dir = self.test_dir / "new_dir"
        path = ensure_directory(new_dir)
        assert path.exists()
        assert path.is_dir()
        
        # Test with a file path
        with pytest.raises(OSError):
            ensure_directory(self.file1)
    
    def test_safe_filename(self):
        """Test converting strings to safe filenames."""
        assert safe_filename("file.txt") == "file.txt"
        assert safe_filename("file?.txt") == "file_.txt"
        assert safe_filename('file"with:chars</\\>') == "file_with_chars____"
    
    def test_list_files(self):
        """Test listing files in a directory."""
        # Test basic listing
        files = list_files(self.test_dir)
        assert len(files) == 2  # file1.txt and file2.csv
        assert self.file1 in files
        assert self.file2 in files
        
        # Test with extension filter
        files = list_files(self.test_dir, extensions={"txt"})
        assert len(files) == 1
        assert self.file1 in files
        
        # Test recursive listing
        files = list_files(self.test_dir, recursive=True)
        assert len(files) == 3  # file1.txt, file2.csv, and subdir/file3.txt
        assert self.file1 in files
        assert self.file2 in files
        assert self.file3 in files
        
        # Test including directories
        files = list_files(self.test_dir, include_dirs=True)
        assert len(files) == 3  # file1.txt, file2.csv, and subdir
        assert self.file1 in files
        assert self.file2 in files
        assert self.subdir in files
        
        # Test non-existent directory
        with pytest.raises(FileNotFoundError):
            list_files(self.test_dir / "nonexistent")
    
    def test_safe_delete(self):
        """Test safely deleting files and directories."""
        # Test deleting a file
        assert safe_delete(self.file1)
        assert not self.file1.exists()
        
        # Test deleting a directory
        assert safe_delete(self.subdir)
        assert not self.subdir.exists()
        
        # Test deleting a non-existent path
        assert not safe_delete(self.test_dir / "nonexistent")
    
    def test_safe_copy(self):
        """Test safely copying files and directories."""
        # Test copying a file
        dest_file = self.test_dir / "file1_copy.txt"
        assert safe_copy(self.file1, dest_file)
        assert dest_file.exists()
        assert dest_file.read_text() == "Test file 1"
        
        # Test not overwriting existing files
        assert not safe_copy(self.file2, dest_file, overwrite=False)
        assert dest_file.read_text() == "Test file 1"  # Content unchanged
        
        # Test overwriting existing files
        assert safe_copy(self.file2, dest_file, overwrite=True)
        assert dest_file.read_text() == "Test file 2"  # Content changed
        
        # Test copying a directory
        dest_dir = self.test_dir / "subdir_copy"
        assert safe_copy(self.subdir, dest_dir)
        assert dest_dir.exists()
        assert (dest_dir / "file3.txt").exists()
        
        # Test copying non-existent source
        assert not safe_copy(self.test_dir / "nonexistent", dest_file)
    
    def test_batch_process_files(self):
        """Test batch processing of files."""
        # Mock process function
        process_func = mock.Mock()
        
        # Test processing all files
        count = batch_process_files(self.test_dir, process_func)
        assert count == 2
        assert process_func.call_count == 2
        
        # Test processing with extension filter
        process_func.reset_mock()
        count = batch_process_files(self.test_dir, process_func, extensions={"csv"})
        assert count == 1
        assert process_func.call_count == 1
        assert process_func.call_args[0][0] == self.file2
        
        # Test with recursive processing
        process_func.reset_mock()
        count = batch_process_files(self.test_dir, process_func, recursive=True)
        assert count == 3
        assert process_func.call_count == 3
    
    def test_create_temp_directory(self):
        """Test creating a temporary directory."""
        temp_dir = create_temp_directory()
        assert temp_dir.exists()
        assert temp_dir.is_dir()
        
        # Clean up
        shutil.rmtree(temp_dir)
    
    def test_file_size_format(self):
        """Test formatting file sizes."""
        assert file_size_format(0) == "0B"
        assert file_size_format(1024) == "1.00 KB"
        assert file_size_format(1024 * 1024) == "1.00 MB"
        assert file_size_format(1024 * 1024 * 1024) == "1.00 GB"
        assert file_size_format(1500) == "1.46 KB"
