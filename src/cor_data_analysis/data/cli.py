"""
Command-line interface for COR Data Analysis collectors.

This module provides a CLI for the COR Data Analysis collectors,
allowing users to scan directories and collect metadata from both MP3 and JPG files.
"""

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Dict, Any, Optional

from cor_data_analysis.config.settings import Settings
from cor_data_analysis.data.scanner import Scanner, ScannerOptions
from cor_data_analysis.data.collectors.mp3_collector import MP3CollectorOptions
from cor_data_analysis.data.collectors.jpg_collector import JPGCollectorOptions


def setup_logging(verbose: bool = False):
    """
    Set up logging configuration.

    Args:
        verbose: Whether to enable verbose logging
    """
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)]
    )


def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="COR Data Analysis Collector CLI")
    
    parser.add_argument(
        "directory",
        type=str,
        help="Directory to scan for MP3 and JPG files",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=str,
        help="Output file path (JSON format)",
        default=None,
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose logging",
        default=False,
    )
    parser.add_argument(
        "--mp3-only",
        action="store_true",
        help="Only collect MP3 files",
        default=False,
    )
    parser.add_argument(
        "--jpg-only",
        action="store_true",
        help="Only collect JPG files",
        default=False,
    )
    parser.add_argument(
        "--no-outliers",
        action="store_true",
        help="Disable outlier detection",
        default=False,
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        help="Batch size for processing files",
        default=10,
    )
    parser.add_argument(
        "--no-exif",
        action="store_true",
        help="Don't extract EXIF data from JPG files",
        default=False,
    )
    parser.add_argument(
        "--no-gps",
        action="store_true",
        help="Don't extract GPS data from JPG files",
        default=False,
    )

    return parser.parse_args()


def save_results(results: Dict[str, Any], output_path: Optional[str] = None):
    """
    Save collection results to a JSON file or print to console.

    Args:
        results: Collection results
        output_path: Path to output file (if None, print to console)
    """
    # Convert Path objects to strings for JSON serialization
    def path_to_str(obj):
        if isinstance(obj, Path):
            return str(obj)
        return obj
    
    json_results = json.dumps(results, default=path_to_str, indent=2)
    
    if output_path:
        with open(output_path, "w") as f:
            f.write(json_results)
        print(f"Results saved to {output_path}")
    else:
        print(json_results)


def main():
    """Main entry point for the CLI."""
    args = parse_args()
    setup_logging(args.verbose)
    
    logger = logging.getLogger(__name__)
    logger.info(f"Scanning directory: {args.directory}")
    
    # Create settings (in a real application, this would be loaded from a config file)
    settings = Settings()
    
    # Configure collector options based on command-line arguments
    mp3_options = MP3CollectorOptions(
        batch_size=args.batch_size,
        enable_outlier_detection=not args.no_outliers,
    )
    
    jpg_options = JPGCollectorOptions(
        batch_size=args.batch_size,
        enable_outlier_detection=not args.no_outliers,
        extract_exif=not args.no_exif,
        extract_gps=not args.no_gps,
    )
    
    # Configure scanner options
    scanner_options = ScannerOptions(
        enable_mp3=not args.jpg_only,
        enable_jpg=not args.mp3_only,
        mp3_options=mp3_options,
        jpg_options=jpg_options,
    )
    
    # Create scanner and scan directory
    scanner = Scanner(settings, scanner_options)
    results = scanner.scan_directory(args.directory)
    
    # Save or print results
    save_results(results, args.output)
    
    # Print summary
    summary = results["summary"]
    print(f"\nScan complete!")
    print(f"- Total files: {summary['total_files']}")
    print(f"- MP3 files: {summary['total_mp3']} ({len(results['mp3_outliers'])} outliers)")
    print(f"- JPG files: {summary['total_jpg']} ({len(results['jpg_outliers'])} outliers)")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
