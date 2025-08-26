"""
Common utility functions and constants for the frontend
"""
import os
import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)

def get_time_filter_options() -> Dict[str, Optional[str]]:
    """Get time filter options for job posting dates"""
    return {
        "Any time": None,
        "Past hour": "r3600",      # 1 hour in seconds
        "Past 24 hours": "r86400", # 24 hours in seconds
        "Past week": "r604800",    # 7 days in seconds
        "Past month": "r2592000"   # 30 days in seconds
    }

def get_database_path() -> str:
    """Get the path to the main database"""
    return os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), 
        "data", 
        "jobs.db"
    )

def setup_logging():
    """Setup logging configuration"""
    import sys
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),  # This will show logs in terminal
            logging.FileHandler('frontend.log')  # Also save to file
        ]
    )
