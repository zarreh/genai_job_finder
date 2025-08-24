import re
import asyncio
from langchain.prompts import PromptTemplate
from langchain.schema import BaseOutputParser

from ..models import ExperienceLevel
from ..config import CleanerConfig
from ..llm import get_llm


EXPERIENCE_EXTRACTION_PROMPT = """
Analyze the following job description and extract the minimum years of experience required.
Look for phrases like:
- "X+ years of experience"
- "X to Y years experience"
- "Minimum X years"
- "At least X years"
- "X years or more"
- Entry level, Junior, Senior, etc.

If no specific years are mentioned, infer from job level keywords:
- Intern/Internship: 0 years
- Entry level/Junior: 0-1 years
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


class IntegerOutputParser(BaseOutputParser):
    """Parser to extract integer values from LLM responses."""
    
    def parse(self, text: str) -> int:
        """Parse integer from text, return -1 if not found."""
        numbers = re.findall(r'\b\d+\b', text.strip())
        if numbers:
            return int(numbers[0])
        return -1


class ExperienceExtractionChain:
    """Chain for extracting experience requirements from job descriptions."""
    
    def __init__(self, config: CleanerConfig = None):
        self.config = config or CleanerConfig()
        self.llm = get_llm(self.config)
        self.parser = IntegerOutputParser()
        self.prompt = PromptTemplate(
            template=EXPERIENCE_EXTRACTION_PROMPT,
            input_variables=["content"]
        )
        self.chain = self.prompt | self.llm | self.parser
    
    async def extract_experience_years(self, content: str) -> int:
        """Extract minimum years of experience from job content."""
        try:
            # First try keyword-based extraction
            years = self._extract_years_with_keywords(content)
            if years >= 0:
                return years
            
            # If keywords don't work, use LLM
            result = await asyncio.to_thread(self.chain.invoke, {"content": content})
            return max(0, result) if result >= 0 else 0
        
        except Exception as e:
            print(f"Warning: Failed to extract experience years: {e}")
            return 0
    
    def _extract_years_with_keywords(self, content: str) -> int:
        """Extract years using regex patterns and keywords."""
        content_lower = content.lower()
        
        # Pattern for explicit years
        year_patterns = [
            r'(\d+)\+\s*years?\s+(?:of\s+)?experience',
            r'minimum\s+(\d+)\s*years?',
            r'at\s+least\s+(\d+)\s*years?',
            r'(\d+)\s*-\s*\d+\s*years?\s+experience',
            r'(\d+)\+\s*years?',
            r'(\d+)\s*(?:to\s+\d+\s*)?years?\s+(?:of\s+)?experience'
        ]
        
        for pattern in year_patterns:
            matches = re.findall(pattern, content_lower)
            if matches:
                return int(matches[0])
        
        # Check for level-based keywords
        if any(keyword in content_lower for keyword in ["intern", "internship", "student", "trainee"]):
            return 0
        elif any(keyword in content_lower for keyword in ["entry", "junior", "graduate", "new grad", "beginner"]):
            return 0
        elif any(keyword in content_lower for keyword in ["associate", "early career", "1-3 years"]):
            return 2
        elif any(keyword in content_lower for keyword in ["mid-level", "mid level", "intermediate", "3-5 years"]):
            return 4
        elif any(keyword in content_lower for keyword in ["senior", "sr.", "experienced", "5-8 years"]):
            return 6
        elif any(keyword in content_lower for keyword in ["staff", "principal", "lead", "8-12 years"]):
            return 10
        elif any(keyword in content_lower for keyword in ["director", "vp", "executive", "manager", "12+ years"]):
            return 15
        
        return -1
    
    def get_experience_level(self, years: int) -> ExperienceLevel:
        """Get experience level from years."""
        return ExperienceLevel.from_years(years)


if __name__ == "__main__":
    async def test_experience_chain():
        """Test the experience extraction chain."""
        print("Testing Experience Extraction Chain")
        print("=" * 40)
        
        chain = ExperienceExtractionChain()
        
        test_cases = [
            "Looking for 5+ years of experience in software development",
            "Entry level position, perfect for new graduates",
            "Senior developer role requiring extensive experience",
            "Minimum 3 years experience in Python required",
            "Principal engineer position for technical leadership"
        ]
        
        for i, content in enumerate(test_cases, 1):
            years = await chain.extract_experience_years(content)
            level = chain.get_experience_level(years)
            
            print(f"\nTest {i}:")
            print(f"Content: {content}")
            print(f"Years: {years}")
            print(f"Level: {level.get_label()}")
        
        print("\n" + "=" * 40)
        print("Experience extraction test completed!")
    
    asyncio.run(test_experience_chain())
