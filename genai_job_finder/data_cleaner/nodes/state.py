from typing import TypedDict, Optional, List
from ..models import ExperienceLevel, WorkLocationType, EmploymentType, SalaryRange


class JobCleaningState(TypedDict):
    """State for the job cleaning workflow."""
    # Input data
    job_id: str
    company: str
    title: str
    location: Optional[str]
    content: str
    original_work_location_type: Optional[str]
    original_employment_type: Optional[str]
    original_salary_range: Optional[str]
    
    # Processing results
    min_years_experience: Optional[int]
    experience_level: Optional[ExperienceLevel]
    experience_level_label: Optional[str]
    
    salary_range: Optional[SalaryRange]
    salary_corrected: bool
    
    work_location_type: Optional[WorkLocationType]
    location_corrected: bool
    
    employment_type: Optional[EmploymentType]
    employment_corrected: bool
    
    # Processing status
    processing_errors: List[str]
    processing_complete: bool
