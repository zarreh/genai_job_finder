from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, Any
from enum import Enum


class JobType(Enum):
    FULL_TIME = "full_time"
    PART_TIME = "part_time"
    CONTRACT = "contract"
    INTERNSHIP = "internship"
    TEMPORARY = "temporary"
    OTHER = "other"


class ExperienceLevel(Enum):
    ENTRY = "entry"
    MID = "mid"
    SENIOR = "senior"
    DIRECTOR = "director"
    EXECUTIVE = "executive"
    NOT_SPECIFIED = "not_specified"


@dataclass
class Job:
    """Represents a job listing from LinkedIn"""
    job_id: str
    title: str
    company: str
    location: str
    description: str
    posted_date: Optional[datetime] = None
    salary_range: Optional[str] = None
    job_type: Optional[JobType] = None
    experience_level: Optional[ExperienceLevel] = None
    skills: Optional[list[str]] = None
    benefits: Optional[list[str]] = None
    applicants_count: Optional[int] = None
    remote_option: bool = False
    easy_apply: bool = False
    linkedin_url: Optional[str] = None
    company_linkedin_url: Optional[str] = None
    run_id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert job to dictionary for database storage"""
        return {
            'job_id': self.job_id,
            'title': self.title,
            'company': self.company,
            'location': self.location,
            'description': self.description,
            'posted_date': self.posted_date.isoformat() if self.posted_date else None,
            'salary_range': self.salary_range,
            'job_type': self.job_type.value if self.job_type else None,
            'experience_level': self.experience_level.value if self.experience_level else None,
            'skills': ','.join(self.skills) if self.skills else None,
            'benefits': ','.join(self.benefits) if self.benefits else None,
            'applicants_count': self.applicants_count,
            'remote_option': self.remote_option,
            'easy_apply': self.easy_apply,
            'linkedin_url': self.linkedin_url,
            'company_linkedin_url': self.company_linkedin_url,
            'run_id': self.run_id
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
