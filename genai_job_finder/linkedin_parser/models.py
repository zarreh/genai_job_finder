from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, Any
from enum import Enum
import uuid


class JobType(Enum):
    FULL_TIME = "Full-time"
    PART_TIME = "Part-time"
    CONTRACT = "Contract"
    INTERNSHIP = "Internship"
    OTHER = "Other"


class ExperienceLevel(Enum):
    ENTRY = "Entry level"
    MID = "Mid-Senior level"
    SENIOR = "Senior level"
    DIRECTOR = "Director"
    EXECUTIVE = "Executive"
    NOT_SPECIFIED = "Not Applicable"


@dataclass
class Job:
    """Represents a job listing from LinkedIn - matches legacy output structure"""
    job_id: str
    title: str
    company: str
    content: str  # Full job description content
    location: Optional[str] = None  # Job location
    work_location_type: Optional[str] = None  # Remote/Hybrid/On-site
    level: Optional[str] = None  # Seniority level
    salary_range: Optional[str] = None
    employment_type: Optional[str] = None  # Full-time, Part-time, etc.
    job_function: Optional[str] = None  # Job function category
    industries: Optional[str] = None  # Industry category
    posted_time: Optional[str] = None  # When job was posted (text format)
    applicants: Optional[str] = None  # Number of applicants
    date: Optional[str] = None  # Date when parsed
    parsing_link: Optional[str] = None  # URL used to parse the job
    job_posting_link: Optional[str] = None  # Main LinkedIn job posting URL
    id: Optional[str] = None  # UUID for each record
    run_id: Optional[int] = None
    company_id: Optional[str] = None  # Link to company information
    # Company information fields (denormalized for easier access)
    company_size: Optional[str] = None  # Number of employees (e.g., "1,000-5,000 employees")
    company_followers: Optional[str] = None  # Number of followers (e.g., "150,000 followers")
    company_industry: Optional[str] = None  # Company industry
    company_info_link: Optional[str] = None  # LinkedIn company page URL used for extraction
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def __post_init__(self):
        """Generate UUID if not provided"""
        if self.id is None:
            self.id = str(uuid.uuid4())
        if self.date is None:
            self.date = datetime.now().date().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert job to dictionary for database storage - matches legacy format"""
        return {
            'id': self.id,
            'company': self.company,
            'title': self.title,
            'location': self.location,
            'work_location_type': self.work_location_type,
            'level': self.level,
            'salary_range': self.salary_range,
            'content': self.content,
            'employment_type': self.employment_type,
            'job_function': self.job_function,
            'industries': self.industries,
            'posted_time': self.posted_time,
            'applicants': self.applicants,
            'job_id': self.job_id,
            'date': self.date,
            'parsing_link': self.parsing_link,
            'job_posting_link': self.job_posting_link,
            'run_id': self.run_id,
            'company_id': self.company_id,
            'company_size': self.company_size,
            'company_followers': self.company_followers,
            'company_industry': self.company_industry,
            'company_info_link': self.company_info_link
        }


@dataclass
class Company:
    """Represents company information extracted from LinkedIn"""
    company_name: str
    company_size: Optional[str] = None  # Number of employees (e.g., "1,000-5,000 employees")
    followers: Optional[str] = None  # Number of followers (e.g., "150,000 followers")
    industry: Optional[str] = None  # Company industry
    company_url: Optional[str] = None  # LinkedIn company page URL
    id: Optional[str] = None  # UUID for each record
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def __post_init__(self):
        """Generate UUID if not provided"""
        if self.id is None:
            self.id = str(uuid.uuid4())
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert company to dictionary for database storage"""
        return {
            'id': self.id,
            'company_name': self.company_name,
            'company_size': self.company_size,
            'followers': self.followers,
            'industry': self.industry,
            'company_url': self.company_url,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }


@dataclass
class JobRun:
    """Represents a parsing run session"""
    id: Optional[int] = None
    run_date: datetime = None
    search_query: Optional[str] = None
    location_filter: Optional[str] = None
    job_count: int = 0
    status: str = "pending"
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    def __post_init__(self):
        if self.run_date is None:
            self.run_date = datetime.now()
        if self.started_at is None:
            self.started_at = datetime.now()
