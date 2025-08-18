import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class ParserConfig:
    """Configuration for LinkedIn parser"""
    
    # Database settings
    database_path: str = os.environ.get("JOB_DB_PATH", "data/jobs.db")
    
    # Scraping settings
    headless_browser: bool = os.environ.get("HEADLESS_BROWSER", "true").lower() == "true"
    page_timeout: int = int(os.environ.get("PAGE_TIMEOUT", "10"))
    max_pages_per_search: int = int(os.environ.get("MAX_PAGES", "5"))
    delay_between_requests: float = float(os.environ.get("REQUEST_DELAY", "2.0"))
    
    # Logging settings
    log_level: str = os.environ.get("LOG_LEVEL", "INFO")
    log_file: Optional[str] = os.environ.get("LOG_FILE")
    
    # Search defaults
    default_location: str = os.environ.get("DEFAULT_LOCATION", "United States")
    
    @classmethod
    def from_env(cls) -> "ParserConfig":
        """Create configuration from environment variables"""
        return cls()
