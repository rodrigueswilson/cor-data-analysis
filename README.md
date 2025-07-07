# COR Data Analysis

## Project Overview
Modern, modular system for MP3 and JPG metadata collection, aggregation, reporting, and visualization.

## Features
- MP3 metadata extraction and analysis
  - Duration in seconds and human-readable format (HH:MM:SS)
  - ID3 tags (artist, album, title)
  - Date and time extraction from filenames (YYMMDD_HHMM format)
  - Activity classification based on metadata
- JPG metadata collection and processing
  - Date and time extraction from filenames (YYMMDD_HHMMSS format with configurable regex)
  - EXIF data extraction (make, model, timestamp, exposure settings)
  - GPS coordinates extraction with decimal degree conversion
- Data aggregation across collection periods
- Excel report generation with advanced formatting
- Automated chart and visualization creation
- Period-based metrics calculation

## Collector Framework
The project includes a robust collector framework for scanning directories and extracting metadata from MP3 and JPG files.

### Framework Components
- **BaseCollector**: Abstract base class providing common functionality
- **MP3Collector**: Extracts metadata from MP3 files including duration, ID3 tags, and activity classification
- **JPGCollector**: Extracts metadata from JPG files including dimensions, EXIF data, and GPS coordinates
- **Scanner**: Unified interface for using both collectors together

## Architecture
This project follows a layered architecture with clear separation of concerns:
- Configuration layer (settings, feature flags)
- Data collection layer (file scanning, metadata extraction)
- Processing layer (aggregation, period calculations)
- Reporting layer (Excel generation, chart creation)
- Utility layer (shared functionality)

## Development
This project is under active development.

### Requirements
- Python 3.9+
- Poetry for dependency management

### Installation
```bash
# Clone the repository
git clone https://github.com/your-username/cor-data-analysis.git

# Install dependencies with Poetry
cd cor-data-analysis
poetry install
```

### Using the Collector CLI
The project provides a convenient command-line interface for collecting metadata from MP3 and JPG files:

```bash
# Activate the poetry environment
poetry shell

# Scan a directory and print results to console
python -m cor_data_analysis.collect /path/to/directory

# Save results to a JSON file
python -m cor_data_analysis.collect /path/to/directory --output results.json

# Only collect MP3 files
python -m cor_data_analysis.collect /path/to/directory --mp3-only

# Only collect JPG files
python -m cor_data_analysis.collect /path/to/directory --jpg-only

# Disable outlier detection
python -m cor_data_analysis.collect /path/to/directory --no-outliers

# Don't extract EXIF data from JPG files
python -m cor_data_analysis.collect /path/to/directory --no-exif

# Enable verbose logging
python -m cor_data_analysis.collect /path/to/directory --verbose
```

## License
Private - Copyright © 2025
