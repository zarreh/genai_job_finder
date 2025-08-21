"""GenAI Job Finder Package

A comprehensive job finder using AI and web scraping technologies.
"""

from .linkedin_parser import LinkedInJobParser, Job, JobRun, DatabaseManager

__version__ = "0.1.0"
__all__ = ["LinkedInJobParser", "Job", "JobRun", "DatabaseManager"]