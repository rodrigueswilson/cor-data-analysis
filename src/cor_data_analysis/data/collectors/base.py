"""
Base collector functionality for COR Data Analysis.

This module provides the base collector class that implements common
scanning and collection functionality used across different collectors.
"""
from abc import ABC, abstractmethod
import logging
import os
import re
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Pattern, Set, Tuple, Union

from pydantic import BaseModel

from cor_data_analysis.config.settings import Settings
from cor_data_analysis.utils.errors import capture_exception, try_except_with_default, safe_operation


class FileInfo(BaseModel):
    """Represents basic information about a file."""
    path: Path
    size: int
    mtime: float
    root: Path
    name: str


class CollectorOptions(BaseModel):
    """Configuration options for collectors."""
    extensions: List[str] = []
    batch_size: int = 100
    enable_outlier_detection: bool = True
    outlier_dirs: List[str] = ["outliers"]


class BaseCollector(ABC):
    """
    Base class for all collectors.
    
    This class provides common functionality for scanning directories,
    filtering files, and detecting outliers. Specific collectors (MP3, JPG)
    should inherit from this class and implement their specific methods.
    """
    
    def __init__(self, settings: Settings, options: Optional[CollectorOptions] = None):
        """
        Initialize the collector with settings and options.
        
        Args:
            settings: Application settings
            options: Collector-specific options
        """
        self.settings = settings
        self.options = options or CollectorOptions()
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
    def scan_directory(self, directory_path: Union[str, Path]) -> List[FileInfo]:
        """
        Recursively scan a directory for files with specified extensions.
        
        Args:
            directory_path: Root directory to scan.
            
        Returns:
            List of FileInfo objects with file information.
        """
        directory_path = Path(directory_path)
        file_info_list = []
        
        if not directory_path.is_dir():
            self.logger.error(f"Invalid directory: {directory_path}")
            return file_info_list
        
        for root, _, files in os.walk(directory_path):
            root_path = Path(root)
            for file in files:
                if self.options.extensions:
                    if not any(file.lower().endswith(f'.{ext.lower()}') for ext in self.options.extensions):
                        continue
                
                file_path = root_path / file
                try:
                    stat = file_path.stat()
                    file_info = FileInfo(
                        path=file_path,
                        size=stat.st_size,
                        mtime=stat.st_mtime,
                        root=root_path,
                        name=file
                    )
                    file_info_list.append(file_info)
                except Exception as e:
                    self.logger.warning(f"Error accessing file {file_path}: {e}")
        
        return file_info_list
    
    def filter_files(self, files: List[FileInfo], 
                    filter_criteria: Optional[Callable[[FileInfo], bool]] = None) -> List[FileInfo]:
        """
        Filter files based on a provided filter criteria function.
        
        Args:
            files: List of FileInfo objects
            filter_criteria: Function returning True for files to keep
            
        Returns:
            Filtered list of FileInfo objects
        """
        if filter_criteria is None:
            return files
        return [f for f in files if filter_criteria(f)]
    
    def identify_outliers(self, files: List[FileInfo]) -> Tuple[List[FileInfo], List[FileInfo]]:
        """
        Identify files that are outliers based on directory names.
        
        Args:
            files: List of FileInfo objects
            
        Returns:
            Tuple of (normal_files, outlier_files)
        """
        if not self.options.enable_outlier_detection:
            return files, []
            
        outliers = []
        normal_files = []
        
        for file in files:
            parts = file.root.parts
            if any(outlier_dir in parts for outlier_dir in self.options.outlier_dirs):
                outliers.append(file)
            else:
                normal_files.append(file)
                
        return normal_files, outliers
    
    def batch_process(self, files: List[FileInfo], 
                     processor: Callable[[FileInfo], Optional[Dict[str, Any]]]) -> List[Dict[str, Any]]:
        """
        Process a list of files in batches.
        
        Args:
            files: List of FileInfo objects to process
            processor: Function to process each file
            
        Returns:
            List of processed results (excluding None results)
        """
        results = []
        batch_size = self.options.batch_size
        
        for i in range(0, len(files), batch_size):
            batch = files[i:i + batch_size]
            self.logger.info(f"Processing batch {i//batch_size + 1}/{(len(files) + batch_size - 1)//batch_size}")
            
            for file in batch:
                try:
                    result = processor(file)
                    if result is not None:
                        results.append(result)
                except Exception as e:
                    self.logger.error(f"Error processing file {file.path}: {e}")
        
        return results
    
    @abstractmethod
    def extract_metadata(self, file_info: FileInfo) -> Optional[Dict[str, Any]]:
        """
        Extract metadata from a file.
        
        Args:
            file_info: FileInfo object
            
        Returns:
            Dictionary with metadata or None if extraction failed
        """
        pass
    
    @abstractmethod
    def process_file(self, file_info: FileInfo) -> Optional[Dict[str, Any]]:
        """
        Process a file, extracting and transforming metadata.
        
        Args:
            file_info: FileInfo object
            
        Returns:
            Dictionary with processed metadata or None if processing failed
        """
        pass
    
    def collect(self, directory_path: Union[str, Path]) -> Dict[str, List[Dict[str, Any]]]:
        """
        Main collection method that scans a directory and processes files.
        
        Args:
            directory_path: Directory to scan
            
        Returns:
            Dictionary with 'data' and 'outliers' keys containing lists of processed files
        """
        self.logger.info(f"Starting collection in {directory_path}")
        
        # Scan directory
        all_files = self.scan_directory(directory_path)
        self.logger.info(f"Found {len(all_files)} files with extensions {self.options.extensions}")
        
        # Separate outliers
        normal_files, outlier_files = self.identify_outliers(all_files)
        self.logger.info(f"Identified {len(outlier_files)} outlier files")
        
        # Process normal files
        data = self.batch_process(normal_files, self.process_file)
        self.logger.info(f"Processed {len(data)} regular files")
        
        # Process outlier files
        outliers = self.batch_process(outlier_files, self.process_file)
        self.logger.info(f"Processed {len(outliers)} outlier files")
        
        return {
            "data": data,
            "outliers": outliers
        }
