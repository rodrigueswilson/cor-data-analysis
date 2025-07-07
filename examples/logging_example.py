"""Example script demonstrating the logging infrastructure.

This example shows how to:
1. Get a configured logger
2. Use different log levels
3. Use context logging
4. Change log levels dynamically
"""

import sys
import time
from pathlib import Path

# Add the project root to the path so we can import the package
sys.path.insert(0, str(Path(__file__).parent.parent))

from cor_data_analysis.utils.logging import get_logger, LoggingContext
from cor_data_analysis.config import get_settings


def main():
    """Run the logging demonstration."""
    # Get a logger with the default configuration
    logger = get_logger("example")
    
    logger.info("Starting logging example")
    
    # Demonstrate different log levels
    logger.debug("This is a debug message")
    logger.info("This is an info message")
    logger.warning("This is a warning message")
    logger.error("This is an error message")
    logger.critical("This is a critical message")
    
    # Demonstrate using context
    logger.info("Log message without context")
    
    with LoggingContext(logger, user="example_user", operation="demo"):
        logger.info("Log message with user and operation context")
        
        # Nested context
        with LoggingContext(logger, subsystem="authentication"):
            logger.info("Log message with nested context")
            
    logger.info("Context is removed after the with block")
    
    # Demonstrate changing log level
    logger.info("Changing log level to DEBUG")
    settings = get_settings()
    settings.logging.level = "DEBUG"
    
    # Re-configure logger with new settings
    logger = get_logger("example")
    
    logger.debug("Now debug messages are visible")
    
    logger.info("Logging example completed")


if __name__ == "__main__":
    main()
