"""
Configuration for the data cleaner module.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass
class CleanerConfig:
    """Configuration for the JobDataCleaner."""
    
    # Ollama configuration
    ollama_model: str = "llama3.2"
    ollama_base_url: str = "http://localhost:11434"
    ollama_temperature: float = 0.1
    ollama_max_tokens: int = 1000
    
    # Processing configuration
    batch_size: int = 10
    max_retries: int = 3
    timeout_seconds: int = 30
    
    # Experience extraction prompts
    experience_extraction_prompt: str = """
    Analyze the following job description and extract the minimum years of experience required.
    Look for phrases like:
    - "X+ years of experience"
    - "X to Y years experience"
    - "Minimum X years"
    - "At least X years"
    - "X years or more"
    - Entry level, Junior, Senior, etc.
    
    If no specific years are mentioned, infer from job level keywords:
    - Entry level: 0 years
    - Junior: 0-1 years
    - Associate/Early career: 1-3 years
    - Mid-level: 3-5 years
    - Senior: 5-8 years
    - Staff/Principal/Lead: 8-12 years
    - Director/VP/Executive: 12+ years
    
    Return only the minimum number of years as an integer. If unclear, return -1.
    
    Job Description:
    {content}
    
    Minimum years of experience required:
    """
    
    # Salary extraction prompt
    salary_extraction_prompt: str = """
    Analyze the following job description and extract salary information.
    Look for:
    - Salary ranges (e.g., "$80,000 - $120,000")
    - Hourly rates (e.g., "$25-35/hour")
    - Annual salaries (e.g., "$100K per year")
    - Benefits mentions that might include salary
    
    Return the information in this exact format:
    MIN_SALARY: [number or null]
    MAX_SALARY: [number or null]
    CURRENCY: [USD/EUR/etc or null]
    PERIOD: [yearly/monthly/hourly or null]
    
    If no salary information is found, return all fields as null.
    
    Job Description:
    {content}
    
    Salary Information:
    """
    
    # Work location type validation prompt
    location_type_validation_prompt: str = """
    Analyze the following job description and determine the work location type.
    The location type should be one of: Remote, Hybrid, On-site
    
    Look for keywords like:
    - Remote: "remote work", "work from home", "remote position", "100% remote"
    - Hybrid: "hybrid", "flexible work", "some remote", "office/remote mix"
    - On-site: "on-site", "in-office", "office-based", "no remote option"
    
    Current classification: {current_type}
    
    Job Description:
    {content}
    
    Based on the job description, is the current classification correct?
    Return only: Remote, Hybrid, or On-site
    
    Work location type:
    """
    
    # Employment type validation prompt
    employment_type_validation_prompt: str = """
    Analyze the following job description and determine the employment type.
    The employment type should be one of: Full-time, Part-time, Contract, Internship
    
    Look for keywords like:
    - Full-time: "full time", "40 hours", "permanent", "salaried"
    - Part-time: "part time", "20 hours", "flexible hours"
    - Contract: "contract", "contractor", "freelance", "consulting"
    - Internship: "intern", "internship", "student position"
    
    Current classification: {current_type}
    
    Job Description:
    {content}
    
    Based on the job description, is the current classification correct?
    Return only: Full-time, Part-time, Contract, or Internship
    
    Employment type:
    """
    
    # Keywords for experience level detection
    experience_keywords: Dict[str, List[str]] = None
    
    def __post_init__(self):
        """Set default experience keywords if not provided."""
        if self.experience_keywords is None:
            self.experience_keywords = {
                "intern": ["intern", "internship", "student", "trainee"],
                "entry": ["entry", "junior", "graduate", "new grad", "beginner"],
                "early_career": ["associate", "early career", "1-3 years"],
                "mid": ["mid-level", "mid level", "intermediate", "3-5 years"],
                "senior": ["senior", "sr.", "experienced", "5-8 years"],
                "staff": ["staff", "principal", "lead", "8-12 years"],
                "director": ["director", "vp", "executive", "manager", "12+ years"]
            }
