import asyncio
from .state import JobCleaningState
from ..chains.salary_extraction import SalaryExtractionChain
from ..config import CleanerConfig


async def extract_salary_node(state: JobCleaningState, config: CleanerConfig = None) -> JobCleaningState:
    """Node for extracting salary information."""
    try:
        config = config or CleanerConfig()
        chain = SalaryExtractionChain(config)
        
        original_salary = state.get("original_salary_range", "")
        
        # Check if we already have valid salary data
        if original_salary and original_salary.strip():
            existing_salary = chain._extract_salary_with_regex(original_salary)
            if existing_salary:
                state["salary_range"] = existing_salary
                state["salary_corrected"] = False
                print(f"✅ Using existing salary: ${existing_salary.min_salary:,.0f} - ${existing_salary.max_salary:,.0f}")
                return state
        
        # Extract from content
        extracted_salary = await chain.extract_salary_range(state["content"])
        
        if extracted_salary:
            state["salary_range"] = extracted_salary
            state["salary_corrected"] = True
            print(f"✅ Salary extracted: ${extracted_salary.min_salary:,.0f} - ${extracted_salary.max_salary:,.0f}")
        else:
            state["salary_range"] = None
            state["salary_corrected"] = False
            print("⚠️ No salary information found")
        
    except Exception as e:
        error_msg = f"Failed to extract salary: {e}"
        state["processing_errors"].append(error_msg)
        state["salary_range"] = None
        state["salary_corrected"] = False
        print(f"❌ Salary extraction failed: {e}")
    
    return state


if __name__ == "__main__":
    async def test_salary_node():
        """Test the salary extraction node."""
        print("Testing Salary Extraction Node")
        print("=" * 40)
        
        test_state: JobCleaningState = {
            "job_id": "test-123",
            "company": "TechCorp",
            "title": "Software Engineer",
            "location": "San Francisco, CA",
            "content": "Competitive salary of $90,000 - $130,000 per year plus benefits and equity.",
            "original_work_location_type": "Remote",
            "original_employment_type": "Full-time",
            "original_salary_range": "",
            "min_years_experience": 3,
            "experience_level": None,
            "experience_level_label": "Mid",
            "salary_range": None,
            "salary_corrected": False,
            "work_location_type": None,
            "location_corrected": False,
            "employment_type": None,
            "employment_corrected": False,
            "processing_errors": [],
            "processing_complete": False
        }
        
        result_state = await extract_salary_node(test_state)
        
        print(f"Job Title: {result_state['title']}")
        if result_state['salary_range']:
            print(f"Salary Range: ${result_state['salary_range'].min_salary:,.0f} - ${result_state['salary_range'].max_salary:,.0f}")
            print(f"Mid Salary: ${result_state['salary_range'].mid_salary:,.0f}")
        print(f"Salary Corrected: {result_state['salary_corrected']}")
        print(f"Errors: {result_state['processing_errors']}")
        
        print("\n" + "=" * 40)
        print("Salary extraction node test completed!")
    
    asyncio.run(test_salary_node())
