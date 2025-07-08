"""
Pytest configuration and shared fixtures.

This module provides common fixtures for testing the COR data analysis collectors.
"""
import os
import shutil
import tempfile
from pathlib import Path
from typing import Dict, Generator

import pytest

from cor_data_analysis.config.settings import Settings


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for test files."""
    temp_dir = Path(tempfile.mkdtemp(prefix="cor_test_"))
    yield temp_dir
    # Cleanup after tests
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def test_settings() -> Settings:
    """Create test settings for collectors."""
    return Settings(
        log_level="INFO",
        output_dir=Path(os.path.join(tempfile.gettempdir(), "cor_test_output")),
        # Add any other settings needed for testing
    )
