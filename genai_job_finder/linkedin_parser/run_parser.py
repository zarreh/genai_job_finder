#!/usr/bin/env python3
"""
Simple script to run the LinkedIn job parser.
Usage: python -m genai_job_finder.linkedin_parser.run_parser
"""

from .parser import LinkedInJobParser
from .database import DatabaseManager


def main():
    """Run the LinkedIn job parser with default settings."""
    # Initialize database and parser
    db = DatabaseManager("data/jobs.db")
    parser = LinkedInJobParser(database=db)
    
    # Parse jobs with default search parameters
    print("Starting LinkedIn job parsing...")
    jobs = parser.parse_jobs(
        search_query="data scientist",
        location="San Antonio",
        total_jobs=50  # Parse fewer jobs for quick testing
    )
    
    print(f"✅ Successfully parsed {len(jobs)} jobs")
    
    # Export to CSV
    csv_file = db.export_jobs_to_csv("data/jobs_export.csv")
    if csv_file:
        print(f"📊 Jobs exported to: {csv_file}")
    else:
        print("📊 Jobs saved to database")


if __name__ == "__main__":
    main()
