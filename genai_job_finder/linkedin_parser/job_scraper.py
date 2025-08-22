"""
LinkedIn Job Scraper - Updated version that matches legacy output format
"""
import logging
from typing import List, Dict, Any
from .parser import LinkedInJobParser
from .database import DatabaseManager

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def linkedin_job_search(
    search_params: List[Dict[str, Any]],
    total_jobs_per_search: int = 500,
    output_file: str = "job_data.csv"
) -> None:
    """
    Main function to scrape LinkedIn jobs - matches legacy interface
    
    Args:
        search_params: List of search parameter dictionaries
        total_jobs_per_search: Number of jobs to scrape per search
        output_file: Output CSV filename
    """
    
    # Initialize parser and database
    database = DatabaseManager()
    parser = LinkedInJobParser(database)
    
    all_jobs = []
    
    for params in search_params:
        logger.info(f"Starting search: {params}")
        
        # Extract parameters
        keywords = params.get("keywords", "")
        location = params.get("location", "")
        time_filter = params.get("f_TPR", "r86400")  # default: last 24 hours
        remote = params.get("remote", False)
        parttime = params.get("parttime", False)
        
        try:
            # Parse jobs
            jobs = parser.parse_jobs(
                search_query=keywords,
                location=location,
                total_jobs=total_jobs_per_search,
                time_filter=time_filter,
                remote=remote,
                parttime=parttime
            )
            
            all_jobs.extend(jobs)
            logger.info(f"Successfully scraped {len(jobs)} jobs for: {keywords}")
            
        except Exception as e:
            logger.error(f"Error scraping jobs for {keywords}: {e}")
            continue
    
    # Export to CSV
    if all_jobs:
        database.export_jobs_to_csv(output_file)
        logger.info(f"Exported {len(all_jobs)} total jobs to {output_file}")
    else:
        logger.warning("No jobs were scraped")


# Example usage matching the legacy code structure
if __name__ == "__main__":
    # Define search parameters (matches legacy LINKEDIN_JOB_SEARCH_PARAMS)
    SEARCH_PARAMS = [
        {
            "keywords": "senior data scientist",
            "location": "San Antonio",
            "f_TPR": "r86400",  # last 24 hours
            "remote": False,
            "parttime": False,  # full-time
        },
        # Add more search parameters as needed
        # {
        #     "keywords": "Machine Learning Engineer",
        #     "location": "united states",
        #     "f_TPR": "r604800",  # last 7 days
        #     "remote": True,
        #     "parttime": False,
        # },
    ]
    
    # Run the job search
    linkedin_job_search(
        search_params=SEARCH_PARAMS,
        total_jobs_per_search=500,
        output_file="data/senior_data_scientist.csv"
    )
