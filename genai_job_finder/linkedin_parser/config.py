import os
from dataclasses import dataclass
from typing import Optional, List, Dict, Union


HEADERS: Dict[str, str] = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Cache-Control": "max-age=0",
}

# Time filter options:
# r86400: last 24 hours
# r604800: last 7 days  
# r2592000: last 30 days
TIME_FILTERS = {
    "24h": "r86400",
    "7d": "r604800", 
    "30d": "r2592000"
}

@dataclass
class SearchParams:
    """LinkedIn job search parameters"""
    keywords: str
    location: str
    time_filter: str = "r604800"  # Default to last 7 days
    remote: bool = False
    parttime: bool = False
    total_jobs: int = 50


# Default search configurations
# Edit the first entry below to set your default search parameters
LINKEDIN_JOB_SEARCH_PARAMS: List[SearchParams] = [
    # ACTIVE CONFIGURATION - Edit this to change your defaults
    # SearchParams(
    #     keywords="Data Analyst",           # 🔍 Change this to your target job
    #     location="San Antonio",           # 📍 Change this to your target location  
    #     time_filter="r604800",            # ⏰ r86400=24h, r604800=7d, r2592000=30d
    #     remote=False,                     # 🏠 True for remote jobs
    #     parttime=False,                   # ⏰ True for part-time jobs
    #     total_jobs=50                     # 📊 Number of jobs to parse
    # ),
    SearchParams(
        keywords="Data scientist",           # 🔍 Change this to your target job
        location="San Antonio",           # 📍 Change this to your target location  
        time_filter="r604800",            # ⏰ r86400=24h, r604800=7d, r2592000=30d
        remote=False,                     # 🏠 True for remote jobs
        parttime=False,                   # ⏰ True for part-time jobs
        total_jobs=50                     # 📊 Number of jobs to parse
    ),
    SearchParams(
        keywords="Data scientist",           # 🔍 Change this to your target job
        location="United States",           # 📍 Change this to your target location  
        time_filter="r86400",            # ⏰ r86400=24h, r604800=7d, r2592000=30d
        remote=True,                     # 🏠 True for remote jobs
        parttime=False,                   # ⏰ True for part-time jobs
        total_jobs=50                     # 📊 Number of jobs to parse
    ),
    
    # EXAMPLE CONFIGURATIONS (uncomment and modify as needed)
    # SearchParams(
    #     keywords="Software Engineer",
    #     location="Austin",
    #     time_filter="r604800",
    #     remote=False,
    #     parttime=False,
    #     total_jobs=100
    # ),
    # SearchParams(
    #     keywords="Machine Learning Engineer", 
    #     location="United States",
    #     time_filter="r604800",
    #     remote=True,
    #     parttime=False,
    #     total_jobs=150
    # ),
    # SearchParams(
    #     keywords="Product Manager",
    #     location="California",
    #     time_filter="r86400",
    #     remote=True,
    #     parttime=False,
    #     total_jobs=75
    # ),
    # ),
]


@dataclass
class ParserConfig:
    """Configuration for LinkedIn parser"""
    
    # Database settings
    database_path: str = os.environ.get("JOB_DB_PATH", "data/jobs.db")
    export_csv_path: str = os.environ.get("EXPORT_CSV_PATH", "data/jobs_export.csv")
    
    # Scraping settings
    headless_browser: bool = os.environ.get("HEADLESS_BROWSER", "true").lower() == "true"
    page_timeout: int = int(os.environ.get("PAGE_TIMEOUT", "10"))
    max_pages_per_search: int = int(os.environ.get("MAX_PAGES", "5"))
    delay_between_requests: float = float(os.environ.get("REQUEST_DELAY", "2.0"))
    
    # Search defaults (can be overridden by command line args)
    # NOTE: These are removed to force using LINKEDIN_JOB_SEARCH_PARAMS configuration
    # default_search_query: str = None  # Will use first entry from LINKEDIN_JOB_SEARCH_PARAMS
    # default_location: str = None      # Will use first entry from LINKEDIN_JOB_SEARCH_PARAMS  
    # default_total_jobs: int = None    # Will use first entry from LINKEDIN_JOB_SEARCH_PARAMS
    # default_time_filter: str = None   # Will use first entry from LINKEDIN_JOB_SEARCH_PARAMS
    # default_remote: bool = None       # Will use first entry from LINKEDIN_JOB_SEARCH_PARAMS
    # default_parttime: bool = None     # Will use first entry from LINKEDIN_JOB_SEARCH_PARAMS
    
    # Logging settings
    log_level: str = os.environ.get("LOG_LEVEL", "INFO")
    log_file: Optional[str] = os.environ.get("LOG_FILE")
    
    # Data processing settings
    combine_fields: List[str] = None
    metadata_fields: List[str] = None
    
    def __post_init__(self):
        """Set default field lists if not provided"""
        if self.combine_fields is None:
            self.combine_fields = [
                "title",
                "company", 
                "salary_range",
                "description",
                "job_function",
                "industries",
            ]
        
        if self.metadata_fields is None:
            self.metadata_fields = [
                "title",
                "company",
                "salary_range", 
                "job_function",
                "industries",
                "level",
                "employment_type",
                "posted_time",
                "applicants",
                "job_id",
                "parsing_link",
                "job_posting_link",
                "date",
            ]
    
    @classmethod
    def from_env(cls) -> "ParserConfig":
        """Create configuration from environment variables"""
        return cls()
    
    def get_search_params(self, **overrides) -> SearchParams:
        """Get search parameters from config with optional overrides"""
        if not LINKEDIN_JOB_SEARCH_PARAMS:
            raise ValueError("No search configurations found in LINKEDIN_JOB_SEARCH_PARAMS. Please add at least one SearchParams entry.")
        
        # Use the first configuration from the list as the base
        base_config = LINKEDIN_JOB_SEARCH_PARAMS[0]
        
        return SearchParams(
            keywords=overrides.get("search_query", base_config.keywords),
            location=overrides.get("location", base_config.location),
            time_filter=overrides.get("time_filter", base_config.time_filter),
            remote=overrides.get("remote", base_config.remote),
            parttime=overrides.get("parttime", base_config.parttime),
            total_jobs=overrides.get("total_jobs", base_config.total_jobs)
        )


# Backward compatibility with legacy config
PERSIST_PATH = os.environ.get("PERSIST_PATH", "data/job_data/vectorstore_faiss")
COMBINE_LIST = [
    "title",
    "company",
    "salary_range", 
    "description",
    "job_function",
    "industries",
]
METADATA_LIST = [
    "title",
    "company",
    "salary_range",
    "job_function", 
    "industries",
    "level",
    "employment_type",
    "posted_time",
    "applicants",
    "job_id",
    "parsing_link",
    "job_posting_link", 
    "date",
]
