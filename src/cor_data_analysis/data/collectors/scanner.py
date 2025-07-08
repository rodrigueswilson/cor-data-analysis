"""
Scanner module for COR Data Analysis.

This module provides a unified Scanner class that uses both the MP3Collector and JPGCollector
to scan directories and collect metadata from both file types.
"""

import logging
from pathlib import Path
from typing import Dict, Any, Optional, Union

from cor_data_analysis.config.settings import Settings
from .mp3_collector import MP3Collector, MP3CollectorOptions
from .jpg_collector import JPGCollector, JPGCollectorOptions


class ScannerOptions:
    """Configuration options for the Scanner class."""

    def __init__(
        self,
        enable_mp3: bool = True,
        enable_jpg: bool = True,
        mp3_options: Optional[MP3CollectorOptions] = None,
        jpg_options: Optional[JPGCollectorOptions] = None,
    ):
        """
        Initialize scanner options.

        Args:
            enable_mp3: Whether to enable MP3 collection
            enable_jpg: Whether to enable JPG collection
            mp3_options: Options for the MP3 collector
            jpg_options: Options for the JPG collector
        """
        self.enable_mp3 = enable_mp3
        self.enable_jpg = enable_jpg
        self.mp3_options = mp3_options or MP3CollectorOptions()
        self.jpg_options = jpg_options or JPGCollectorOptions()


class Scanner:
    """
    Scanner class for COR Data Analysis.

    This class serves as a facade for the MP3Collector and JPGCollector,
    providing a unified interface for scanning directories and collecting metadata.
    """

    def __init__(self, settings: Settings, options: Optional[ScannerOptions] = None):
        """
        Initialize the Scanner.

        Args:
            settings: Application settings
            options: Scanner options
        """
        self.logger = logging.getLogger(__name__)
        self.settings = settings
        self.options = options or ScannerOptions()
        
        # Initialize collectors based on options
        self.mp3_collector = MP3Collector(settings, self.options.mp3_options) if self.options.enable_mp3 else None
        self.jpg_collector = JPGCollector(settings, self.options.jpg_options) if self.options.enable_jpg else None
    
    def scan_directory(self, directory: Union[str, Path]) -> Dict[str, Any]:
        """
        Scan a directory for MP3 and JPG files and collect their metadata.

        Args:
            directory: Directory path to scan

        Returns:
            Dictionary containing MP3 and JPG collection results
        """
        directory = Path(directory)
        self.logger.info(f"Scanning directory: {directory}")
        
        results = {
            "mp3_data": [],
            "mp3_outliers": [],
            "jpg_data": [],
            "jpg_outliers": [],
            "summary": {
                "total_mp3": 0,
                "total_jpg": 0,
                "total_files": 0,
                "total_outliers": 0,
            }
        }
        
        # Collect MP3 files if enabled
        if self.mp3_collector:
            self.logger.info("Collecting MP3 files...")
            mp3_results = self.mp3_collector.collect(directory)
            results["mp3_data"] = mp3_results["data"]
            results["mp3_outliers"] = mp3_results["outliers"]
            results["summary"]["total_mp3"] = len(mp3_results["data"]) + len(mp3_results["outliers"])
        
        # Collect JPG files if enabled
        if self.jpg_collector:
            self.logger.info("Collecting JPG files...")
            jpg_results = self.jpg_collector.collect(directory)
            results["jpg_data"] = jpg_results["data"]
            results["jpg_outliers"] = jpg_results["outliers"]
            results["summary"]["total_jpg"] = len(jpg_results["data"]) + len(jpg_results["outliers"])
        
        # Update summary
        results["summary"]["total_files"] = results["summary"]["total_mp3"] + results["summary"]["total_jpg"]
        results["summary"]["total_outliers"] = len(results["mp3_outliers"]) + len(results["jpg_outliers"])
        
        self.logger.info(f"Scan complete. Total files: {results['summary']['total_files']}")
        return results
    
    def process_directory(self, directory: Union[str, Path]) -> Dict[str, Any]:
        """
        Process a directory by scanning for files and collecting their metadata.

        This is an alias for scan_directory for backward compatibility with the original code.

        Args:
            directory: Directory path to process

        Returns:
            Dictionary containing MP3 and JPG collection results
        """
        return self.scan_directory(directory)
