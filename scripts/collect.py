#!/usr/bin/env python
"""
Executable script for running the COR Data Analysis collector.

This script provides a convenient entry point for the collector CLI.
"""

import sys
from pathlib import Path

# Add the project root to the Python path to allow imports from src
project_root = Path(__file__).resolve().parents[1]
sys.path.append(str(project_root / 'src'))

from cor_data_analysis.data.cli import main

if __name__ == "__main__":
    sys.exit(main())
