import re
from langchain.schema import BaseOutputParser
from .models import JobSearchQueries


class JobQueryOutputParser(BaseOutputParser):
    """Parser to extract structured job queries from LLM responses."""

    def parse(self, text: str) -> JobSearchQueries:
        """Parse job search queries from text response."""
        # Initialize lists and variables
        primary_titles = []
        secondary_titles = []
        skill_based_queries = []
        industry_focus = ""
        seniority_level = ""

        lines = [line.strip() for line in text.split("\n") if line.strip()]
        current_section = None

        for line in lines:
            line_lower = line.lower()

            # Section headers
            if "primary" in line_lower and "title" in line_lower:
                current_section = "primary"
                continue
            elif "secondary" in line_lower and "title" in line_lower:
                current_section = "secondary"
                continue
            elif "skill" in line_lower and (
                "query" in line_lower or "queries" in line_lower
            ):
                current_section = "skills"
                continue
            elif "industry" in line_lower and "focus" in line_lower:
                current_section = "industry"
                # Extract industry from same line if present
                if ":" in line:
                    industry_focus = line.split(":", 1)[1].strip()
                continue
            elif "seniority" in line_lower and "level" in line_lower:
                current_section = "seniority"
                # Extract seniority from same line if present
                if ":" in line:
                    seniority_level = line.split(":", 1)[1].strip()
                continue

            # Extract list items
            if line.startswith(
                (
                    "- ",
                    "• ",
                    "* ",
                    "1. ",
                    "2. ",
                    "3. ",
                    "4. ",
                    "5. ",
                    "6. ",
                    "7. ",
                    "8. ",
                )
            ):
                # Remove list markers
                item = re.sub(r"^[-•*]?\s*\d*\.?\s*", "", line).strip()
                if item:
                    if current_section == "primary":
                        primary_titles.append(item)
                    elif current_section == "secondary":
                        secondary_titles.append(item)
                    elif current_section == "skills":
                        skill_based_queries.append(item)

            # Extract key-value pairs
            elif ":" in line and current_section in ["industry", "seniority"]:
                key, value = line.split(":", 1)
                value = value.strip()
                if "industry" in key.lower() or current_section == "industry":
                    industry_focus = value
                elif (
                    "seniority" in key.lower()
                    or "level" in key.lower()
                    or current_section == "seniority"
                ):
                    seniority_level = value

        # Validate that we have the required data
        if not primary_titles:
            raise ValueError("Failed to extract primary job titles from LLM response")
        if not secondary_titles:
            raise ValueError("Failed to extract secondary job titles from LLM response")
        
        # Provide defaults for optional fields that might be missing
        if not skill_based_queries:
            # Generate default skill queries from primary titles
            skill_based_queries = [f"{primary_titles[0]} skills", f"{primary_titles[1]} experience"] if len(primary_titles) >= 2 else ["relevant skills"]
        
        if not industry_focus:
            industry_focus = "Technology"  # Default industry
        
        if not seniority_level:
            seniority_level = "Mid"  # Default seniority

        return JobSearchQueries(
            primary_titles=primary_titles[:5],
            secondary_titles=secondary_titles[:8],  # Allow 8 secondary titles
            skill_based_queries=skill_based_queries[:3],
            industry_focus=industry_focus,
            seniority_level=seniority_level,
        )

    @property
    def _type(self) -> str:
        """Return the type of parser."""
        return "job_query_output_parser"