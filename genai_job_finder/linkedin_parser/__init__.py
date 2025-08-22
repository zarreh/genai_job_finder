"""LinkedIn Job Parser Module

This module provides functionality to scrape and parse job listings from LinkedIn,
storing them in a database with run date tracking.
"""

from .parser import LinkedInJobParser
from .models import Job, JobRun
from .database import DatabaseManager
from .run_parser import main as run_parser

__version__ = "0.1.0"
__all__ = ["LinkedInJobParser", "Job", "JobRun", "DatabaseManager", "run_parser"]
