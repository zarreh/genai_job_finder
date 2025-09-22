import asyncio
from langchain.prompts import PromptTemplate
from langchain.schema import BaseOutputParser

from ..models import WorkLocationType
from ..config import CleanerConfig
from ..llm import get_llm


LOCATION_VALIDATION_PROMPT = """
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


class LocationTypeOutputParser(BaseOutputParser):
    """Parser to extract work location type from LLM responses."""
    
    def parse(self, text: str) -> WorkLocationType:
        """Parse work location type from text."""
        text_lower = text.strip().lower()
        
        if "remote" in text_lower:
            return WorkLocationType.REMOTE
        elif "hybrid" in text_lower:
            return WorkLocationType.HYBRID
        elif "on-site" in text_lower or "onsite" in text_lower or "office" in text_lower:
            return WorkLocationType.ON_SITE
        else:
            return WorkLocationType.UNKNOWN


class LocationValidationChain:
    """Chain for validating work location type from job descriptions."""
    
    def __init__(self, config: CleanerConfig = None):
        self.config = config or CleanerConfig()
        self.llm = get_llm()
        self.parser = LocationTypeOutputParser()
        self.prompt = PromptTemplate(
            template=LOCATION_VALIDATION_PROMPT,
            input_variables=["content", "current_type"]
        )
        self.chain = self.prompt | self.llm | self.parser
    
    async def validate_location_type(self, content: str, current_type: str) -> WorkLocationType:
        """Validate and correct work location type."""
        try:
            # First try keyword-based validation
            detected_type = self._detect_location_type_with_keywords(content)
            if detected_type != WorkLocationType.UNKNOWN:
                return detected_type
            
            # If keywords are unclear, use LLM
            result = await asyncio.to_thread(
                self.chain.invoke, 
                {"content": content, "current_type": current_type}
            )
            return result
        
        except Exception as e:
            print(f"Warning: Failed to validate location type: {e}")
            return WorkLocationType.UNKNOWN
    
    def _detect_location_type_with_keywords(self, content: str) -> WorkLocationType:
        """Detect location type using keywords."""
        content_lower = content.lower()
        
        remote_keywords = ["remote", "work from home", "wfh", "100% remote", "fully remote"]
        hybrid_keywords = ["hybrid", "flexible", "office/remote", "remote/office"]
        onsite_keywords = ["on-site", "onsite", "in-office", "office-based"]
        
        remote_score = sum(1 for keyword in remote_keywords if keyword in content_lower)
        hybrid_score = sum(1 for keyword in hybrid_keywords if keyword in content_lower)
        onsite_score = sum(1 for keyword in onsite_keywords if keyword in content_lower)
        
        if remote_score > hybrid_score and remote_score > onsite_score:
            return WorkLocationType.REMOTE
        elif hybrid_score > onsite_score:
            return WorkLocationType.HYBRID
        elif onsite_score > 0:
            return WorkLocationType.ON_SITE
        else:
            return WorkLocationType.UNKNOWN


if __name__ == "__main__":
    async def test_location_chain():
        """Test the location validation chain."""
        print("Testing Location Validation Chain")
        print("=" * 40)
        
        chain = LocationValidationChain()
        
        test_cases = [
            ("This is a 100% remote position, work from anywhere", "On-site"),
            ("Hybrid role - 3 days in office, 2 days remote", "Remote"),
            ("Must be able to work on-site at our headquarters", "Hybrid"),
            ("Flexible work arrangement with remote options", "On-site"),
            ("Office-based position in downtown location", "Remote")
        ]
        
        for i, (content, current_type) in enumerate(test_cases, 1):
            validated_type = await chain.validate_location_type(content, current_type)
            
            print(f"\nTest {i}:")
            print(f"Content: {content}")
            print(f"Current: {current_type}")
            print(f"Validated: {validated_type.value}")
        
        print("\n" + "=" * 40)
        print("Location validation test completed!")
    
    asyncio.run(test_location_chain())
