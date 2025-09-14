from typing import List
from pydantic import BaseModel, Field


class JobSearchQueries(BaseModel):
    """Structured output for job search queries based on resume analysis."""
    
    primary_titles: List[str] = Field(
        description="Realistic next-step job titles with best chance of getting hired (5 titles)"
    )
    secondary_titles: List[str] = Field(
        description="Opportunistic and futuristic job titles leveraging domain/technical knowledge (8 titles)"
    )
    skill_based_queries: List[str] = Field(
        description="Skill-focused search queries (2-3 queries)"
    )
    industry_focus: str = Field(
        description="Primary industry or sector based on experience"
    )
    seniority_level: str = Field(
        description="Experience level: Entry, Mid, Senior, or Executive"
    )

    def to_dict(self) -> dict:
        """Convert to dictionary for easy serialization."""
        return {
            "primary_titles": self.primary_titles,
            "secondary_titles": self.secondary_titles,
            "skill_based_queries": self.skill_based_queries,
            "industry_focus": self.industry_focus,
            "seniority_level": self.seniority_level
        }

    def get_all_titles(self) -> List[str]:
        """Get all job titles (primary + secondary) as a single list."""
        return self.primary_titles + self.secondary_titles

    def display_summary(self) -> str:
        """Get a formatted summary for display purposes."""
        return f"""
📍 Primary Job Titles ({len(self.primary_titles)}):
{chr(10).join([f"  • {title}" for title in self.primary_titles])}

🔍 Secondary Job Titles ({len(self.secondary_titles)}):
{chr(10).join([f"  • {title}" for title in self.secondary_titles])}

🛠️ Skill-Based Queries:
{chr(10).join([f"  • {query}" for query in self.skill_based_queries])}

🏭 Industry Focus: {self.industry_focus}
📈 Seniority Level: {self.seniority_level}
"""