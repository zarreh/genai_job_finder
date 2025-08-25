"""
Data models and enums for the data cleaner module.
"""

from enum import Enum
from dataclasses import dataclass
from typing import Optional, Dict, Any


class ExperienceLevel(Enum):
    """Classification of job experience levels based on years of experience."""
    ENTRY_LEVEL = 0  # 0 years (entry level)
    JUNIOR = 1  # 1 year (junior)
    ASSOCIATE = 2  # 2-3 years
    MID = 3  # 4-5 years
    SENIOR = 4  # 6-8 years
    STAFF_PRINCIPAL = 5  # 9-12 years
    DIRECTOR_EXECUTIVE = 6  # 13+ years
    
    @classmethod
    def from_years(cls, years: int) -> 'ExperienceLevel':
        """Classify experience level based on years of experience."""
        if years == 0:
            return cls.ENTRY_LEVEL
        elif years == 1:
            return cls.JUNIOR
        elif years <= 3:
            return cls.ASSOCIATE
        elif years <= 5:
            return cls.MID
        elif years <= 8:
            return cls.SENIOR
        elif years <= 12:
            return cls.STAFF_PRINCIPAL
        else:
            return cls.DIRECTOR_EXECUTIVE
    
    def get_label(self) -> str:
        """Get human-readable label for the experience level."""
        labels = {
            self.ENTRY_LEVEL: "Entry level",
            self.JUNIOR: "Junior",
            self.ASSOCIATE: "Associate/Early career", 
            self.MID: "Mid-level",
            self.SENIOR: "Senior",
            self.STAFF_PRINCIPAL: "Staff/Principal/Lead",
            self.DIRECTOR_EXECUTIVE: "Director/VP/Executive"
        }
        return labels[self]


class WorkLocationType(Enum):
    """Work location types."""
    REMOTE = "Remote"
    HYBRID = "Hybrid"
    ON_SITE = "On-site"
    UNKNOWN = "Unknown"


class EmploymentType(Enum):
    """Employment types."""
    FULL_TIME = "Full-time"
    PART_TIME = "Part-time"
    CONTRACT = "Contract"
    INTERNSHIP = "Internship"
    UNKNOWN = "Unknown"


@dataclass
class SalaryRange:
    """Represents a salary range with min, max, and mid values."""
    min_salary: Optional[float] = None
    max_salary: Optional[float] = None
    mid_salary: Optional[float] = None
    currency: str = "USD"
    period: str = "yearly"  # yearly, monthly, hourly
    
    def __post_init__(self):
        """Calculate mid salary if both min and max are provided."""
        if self.min_salary is not None and self.max_salary is not None:
            self.mid_salary = (self.min_salary + self.max_salary) / 2


@dataclass
class CleanedJobData:
    """Represents cleaned and enhanced job data."""
    # Original fields
    id: str
    company: str
    title: str
    location: Optional[str]
    content: str
    
    # Enhanced fields
    min_years_experience: Optional[int] = None
    experience_level: Optional[ExperienceLevel] = None
    experience_level_label: Optional[str] = None
    
    # Cleaned location type
    work_location_type: Optional[WorkLocationType] = None
    work_location_type_corrected: bool = False
    
    # Cleaned employment type
    employment_type: Optional[EmploymentType] = None
    employment_type_corrected: bool = False
    
    # Salary information
    salary_range: Optional[SalaryRange] = None
    salary_range_corrected: bool = False
    
    # Original fields preserved
    original_work_location_type: Optional[str] = None
    original_employment_type: Optional[str] = None
    original_salary_range: Optional[str] = None
    
    def __post_init__(self):
        """Set experience level label from experience level enum."""
        if self.experience_level:
            self.experience_level_label = self.experience_level.get_label()
