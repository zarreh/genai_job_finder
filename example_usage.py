"""Example usage of the LinkedIn parser module"""

import logging
import sys
from linkedin_parser import LinkedInJobParser, DatabaseManager
from genai_job_finder.legacy.config import LINKEDIN_JOB_SEARCH_PARAMS


def setup_logging():
    """Configure logging"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


def parse_jobs_from_config(max_pages: int = 3):
    """Parse jobs using the search parameters from legacy config"""
    setup_logging()
    
    # Initialize database
    db = DatabaseManager("data/jobs.db")
    
    # Parse jobs for each search configuration
    total_jobs = 0
    
    # Use requests-based parser
    parser = LinkedInJobParser(database=db)
    
    for idx, search_params in enumerate(LINKEDIN_JOB_SEARCH_PARAMS):
        print(f"\n{'='*80}")
        print(f"Search {idx + 1}/{len(LINKEDIN_JOB_SEARCH_PARAMS)}")
        print(f"Keywords: {search_params['keywords']}")
        print(f"Location: {search_params['location']}")
        print(f"Remote: {search_params.get('remote', False)}")
        print(f"Time Period: {search_params.get('f_TPR', 'Not specified')}")
        print('='*80)
        
        try:
            # Build location string (add 'remote' if specified)
            location = search_params['location']
            if search_params.get('remote', False):
                # LinkedIn often uses specific formatting for remote jobs
                location = f"{location} (Remote)"
            
            # Parse jobs
            jobs = parser.parse_jobs(
                search_query=search_params['keywords'],
                location=location,
                max_pages=max_pages
            )
            
            print(f"\nFound {len(jobs)} jobs for this search")
            total_jobs += len(jobs)
            
            # Display first 3 jobs from this search
            for job in jobs[:3]:
                print(f"\n  • {job.title} at {job.company}")
                print(f"    Location: {job.location}")
                if job.salary_range:
                    print(f"    Salary: {job.salary_range}")
                
        except Exception as e:
            logging.error(f"Error parsing jobs for search {idx + 1}: {e}")
            print(f"\n❌ Failed to parse jobs for this search: {e}")
    
    print(f"\n{'='*80}")
    print(f"Total jobs parsed across all searches: {total_jobs}")
    
    # Show summary of recent runs
    recent_runs = db.get_recent_runs(10)
    print(f"\n\nRecent parsing runs:")
    for run in recent_runs:
        print(f"Run {run['id']}: {run['run_date']} - "
              f"Query: {run['search_query']} - "
              f"Status: {run['status']}, Jobs: {run['job_count']}")


def main():
    """Main function with menu options"""
    print("LinkedIn Job Parser")
    print("==================")
    
    print("\nOptions:")
    print("1. Parse jobs from legacy config (3 different searches)")
    print("2. Parse a single custom search")
    print("3. View recent parsing runs")
    
    choice = input("\nEnter your choice (1-3): ").strip()
    
    if choice == "1":
        # Parse from config
        pages = input("How many pages per search? (default: 3): ").strip()
        max_pages = int(pages) if pages.isdigit() else 3
        parse_jobs_from_config(max_pages)
        
    elif choice == "2":
        # Custom search
        keywords = input("Enter search keywords: ").strip()
        location = input("Enter location: ").strip()
        pages = input("How many pages? (default: 3): ").strip()
        max_pages = int(pages) if pages.isdigit() else 3
        
        setup_logging()
        db = DatabaseManager("data/jobs.db")
        
        parser = LinkedInJobParser(database=db)
        jobs = parser.parse_jobs(
            search_query=keywords,
            location=location,
            max_pages=max_pages
        )
        
        print(f"\nFound {len(jobs)} jobs")
        for job in jobs[:5]:
            print(f"\n{'='*60}")
            print(f"Title: {job.title}")
            print(f"Company: {job.company}")
            print(f"Location: {job.location}")
            print(f"Posted: {job.posted_date}")
            print(f"Easy Apply: {job.easy_apply}")
            if job.salary_range:
                print(f"Salary: {job.salary_range}")

    elif choice == "3":
        # View recent runs
        setup_logging()
        db = DatabaseManager("data/jobs.db")
        recent_runs = db.get_recent_runs(20)
        
        print("\nRecent parsing runs:")
        print("="*100)
        for run in recent_runs:
            print(f"Run {run['id']}: {run['run_date']} | "
                  f"Query: {run['search_query'][:30]}... | "
                  f"Location: {run['location_filter'][:20]}... | "
                  f"Status: {run['status']} | Jobs: {run['job_count']}")
    
    else:
        print("Invalid choice")


if __name__ == "__main__":
    main()
