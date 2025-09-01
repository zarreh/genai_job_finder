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
    # Get the project root directory by finding the directory containing pyproject.toml
    current_dir = os.path.dirname(__file__)
    project_root = current_dir
    
    # Traverse up until we find pyproject.toml
    while project_root != os.path.dirname(project_root):  # Not at filesystem root
        if os.path.exists(os.path.join(project_root, "pyproject.toml")):
            break
        project_root = os.path.dirname(project_root)
    
    return os.path.join(project_root, "data", "jobs.db")

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
