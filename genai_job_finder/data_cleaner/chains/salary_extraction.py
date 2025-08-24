import re
import asyncio
from typing import Optional
from langchain.prompts import PromptTemplate
from langchain.schema import BaseOutputParser

from ..models import SalaryRange
from ..config import CleanerConfig
from ..llm import get_llm


SALARY_EXTRACTION_PROMPT = """
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


class SalaryOutputParser(BaseOutputParser):
    """Parser to extract salary information from LLM responses."""
    
    def parse(self, text: str) -> Optional[SalaryRange]:
        """Parse salary range from formatted text."""
        try:
            lines = [line.strip() for line in text.strip().split('\n') if line.strip()]
            
            min_salary = None
            max_salary = None
            currency = "USD"
            period = "yearly"
            
            for line in lines:
                if line.startswith("MIN_SALARY:"):
                    value = line.split(":", 1)[1].strip()
                    if value.lower() not in ["null", "none", ""]:
                        min_salary = float(re.sub(r'[^\d.]', '', value))
                
                elif line.startswith("MAX_SALARY:"):
                    value = line.split(":", 1)[1].strip()
                    if value.lower() not in ["null", "none", ""]:
                        max_salary = float(re.sub(r'[^\d.]', '', value))
                
                elif line.startswith("CURRENCY:"):
                    value = line.split(":", 1)[1].strip()
                    if value.lower() not in ["null", "none", ""]:
                        currency = value.upper()
                
                elif line.startswith("PERIOD:"):
                    value = line.split(":", 1)[1].strip()
                    if value.lower() not in ["null", "none", ""]:
                        period = value.lower()
            
            if min_salary is not None or max_salary is not None:
                return SalaryRange(
                    min_salary=min_salary,
                    max_salary=max_salary,
                    currency=currency,
                    period=period
                )
            
            return None
        
        except Exception:
            return None


class SalaryExtractionChain:
    """Chain for extracting salary information from job descriptions."""
    
    def __init__(self, config: CleanerConfig = None):
        self.config = config or CleanerConfig()
        self.llm = get_llm(self.config)
        self.parser = SalaryOutputParser()
        self.prompt = PromptTemplate(
            template=SALARY_EXTRACTION_PROMPT,
            input_variables=["content"]
        )
        self.chain = self.prompt | self.llm | self.parser
    
    async def extract_salary_range(self, content: str) -> Optional[SalaryRange]:
        """Extract salary range from job content."""
        try:
            # First try regex-based extraction
            salary_range = self._extract_salary_with_regex(content)
            if salary_range:
                return salary_range
            
            # If regex doesn't work, use LLM
            result = await asyncio.to_thread(self.chain.invoke, {"content": content})
            return result
        
        except Exception as e:
            print(f"Warning: Failed to extract salary range: {e}")
            return None
    
    def _extract_salary_with_regex(self, content: str) -> Optional[SalaryRange]:
        """Extract salary using regex patterns."""
        patterns = [
            r'\$(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\s*-\s*\$(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
            r'\$(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\s*to\s*\$(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
            r'\$(\d{1,3}(?:,\d{3})*)\s*k?\s*to\s*\$(\d{1,3}(?:,\d{3})*)\s*k?\s*(?:per\s+year|annually|/year)?',
            r'(\d{1,3}(?:,\d{3})*)\s*k\s*-\s*(\d{1,3}(?:,\d{3})*)\s*k\s*(?:per\s+year|annually|/year)?',
            r'(\d{1,3}(?:,\d{3})*)\s*k\s*to\s*(\d{1,3}(?:,\d{3})*)\s*k\s*(?:per\s+year|annually|/year)?',
            r'\$(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)/yr\s*-\s*\$(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)/yr'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            if matches:
                min_str, max_str = matches[0]
                try:
                    min_salary = float(min_str.replace(',', ''))
                    max_salary = float(max_str.replace(',', ''))
                    
                    # Handle K suffix (thousands)
                    if 'k' in content.lower() and min_salary < 1000:
                        min_salary *= 1000
                        max_salary *= 1000
                    
                    return SalaryRange(
                        min_salary=min_salary,
                        max_salary=max_salary,
                        currency="USD",
                        period="yearly"
                    )
                except ValueError:
                    continue
        
        return None


if __name__ == "__main__":
    async def test_salary_chain():
        """Test the salary extraction chain."""
        print("Testing Salary Extraction Chain")
        print("=" * 40)
        
        chain = SalaryExtractionChain()
        
        test_cases = [
            "Competitive salary range: $80,000 - $120,000 annually",
            "We offer $90K to $130K per year plus benefits",
            "Salary: $95,000.00/yr - $140,000.00/yr",
            "Great opportunity with competitive compensation",
            "Hourly rate: $25-35/hour depending on experience"
        ]
        
        for i, content in enumerate(test_cases, 1):
            salary_range = await chain.extract_salary_range(content)
            
            print(f"\nTest {i}:")
            print(f"Content: {content}")
            if salary_range:
                print(f"Salary Range: ${salary_range.min_salary:,.0f} - ${salary_range.max_salary:,.0f}")
                print(f"Mid Salary: ${salary_range.mid_salary:,.0f}")
                print(f"Currency: {salary_range.currency}")
                print(f"Period: {salary_range.period}")
            else:
                print("No salary information found")
        
        print("\n" + "=" * 40)
        print("Salary extraction test completed!")
    
    asyncio.run(test_salary_chain())
