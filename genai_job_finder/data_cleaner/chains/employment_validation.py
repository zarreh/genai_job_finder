import asyncio
from langchain.prompts import PromptTemplate
from langchain.schema import BaseOutputParser

from ..models import EmploymentType
from ..config import CleanerConfig
from ..llm import get_llm


EMPLOYMENT_VALIDATION_PROMPT = """
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


class EmploymentTypeOutputParser(BaseOutputParser):
    """Parser to extract employment type from LLM responses."""
    
    def parse(self, text: str) -> EmploymentType:
        """Parse employment type from text."""
        text_lower = text.strip().lower()
        
        if "full-time" in text_lower or "full time" in text_lower:
            return EmploymentType.FULL_TIME
        elif "part-time" in text_lower or "part time" in text_lower:
            return EmploymentType.PART_TIME
        elif "contract" in text_lower:
            return EmploymentType.CONTRACT
        elif "internship" in text_lower or "intern" in text_lower:
            return EmploymentType.INTERNSHIP
        else:
            return EmploymentType.UNKNOWN


class EmploymentValidationChain:
    """Chain for validating employment type from job descriptions."""
    
    def __init__(self, config: CleanerConfig = None):
        self.config = config or CleanerConfig()
        self.llm = get_llm()
        self.parser = EmploymentTypeOutputParser()
        self.prompt = PromptTemplate(
            template=EMPLOYMENT_VALIDATION_PROMPT,
            input_variables=["content", "current_type"]
        )
        self.chain = self.prompt | self.llm | self.parser
    
    async def validate_employment_type(self, content: str, current_type: str) -> EmploymentType:
        """Validate and correct employment type."""
        try:
            # First try keyword-based validation
            detected_type = self._detect_employment_type_with_keywords(content)
            if detected_type != EmploymentType.UNKNOWN:
                return detected_type
            
            # If keywords are unclear, use LLM
            result = await asyncio.to_thread(
                self.chain.invoke,
                {"content": content, "current_type": current_type}
            )
            return result
        
        except Exception as e:
            print(f"Warning: Failed to validate employment type: {e}")
            return EmploymentType.UNKNOWN
    
    def _detect_employment_type_with_keywords(self, content: str) -> EmploymentType:
        """Detect employment type using keywords."""
        content_lower = content.lower()
        
        if any(keyword in content_lower for keyword in ["full-time", "full time", "40 hours", "permanent"]):
            return EmploymentType.FULL_TIME
        elif any(keyword in content_lower for keyword in ["part-time", "part time", "20 hours"]):
            return EmploymentType.PART_TIME
        elif any(keyword in content_lower for keyword in ["contract", "contractor", "freelance"]):
            return EmploymentType.CONTRACT
        elif any(keyword in content_lower for keyword in ["intern", "internship", "student"]):
            return EmploymentType.INTERNSHIP
        else:
            return EmploymentType.UNKNOWN


if __name__ == "__main__":
    async def test_employment_chain():
        """Test the employment validation chain."""
        print("Testing Employment Validation Chain")
        print("=" * 40)
        
        chain = EmploymentValidationChain()
        
        test_cases = [
            ("This is a full-time permanent position", "Part-time"),
            ("Looking for part-time help, 20 hours per week", "Full-time"),
            ("Contract role for 6 months", "Full-time"),
            ("Summer internship program for students", "Full-time")
        ]
        
        for i, (content, current_type) in enumerate(test_cases, 1):
            validated_type = await chain.validate_employment_type(content, current_type)
            
            print(f"\nTest {i}:")
            print(f"Content: {content}")
            print(f"Current: {current_type}")
            print(f"Validated: {validated_type.value}")
        
        print("\n" + "=" * 40)
        print("Employment validation test completed!")
    
    asyncio.run(test_employment_chain())
