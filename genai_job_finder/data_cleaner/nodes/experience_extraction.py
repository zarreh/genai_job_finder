import asyncio
from .state import JobCleaningState
from ..chains.experience_extraction import ExperienceExtractionChain
from ..config import CleanerConfig


async def extract_experience_node(state: JobCleaningState, config: CleanerConfig = None) -> JobCleaningState:
    """Node for extracting experience requirements."""
    try:
        config = config or CleanerConfig()
        chain = ExperienceExtractionChain(config)
        
        min_years = await chain.extract_experience_years(state["content"])
        experience_level = chain.get_experience_level(min_years)
        
        state["min_years_experience"] = min_years
        state["experience_level"] = experience_level
        state["experience_level_label"] = experience_level.get_label()
        
        print(f"✅ Experience extracted: {min_years} years → {experience_level.get_label()}")
        
    except Exception as e:
        error_msg = f"Failed to extract experience: {e}"
        state["processing_errors"].append(error_msg)
        state["min_years_experience"] = 0
        state["experience_level"] = None
        state["experience_level_label"] = "Unknown"
        print(f"❌ Experience extraction failed: {e}")
    
    return state


if __name__ == "__main__":
    async def test_experience_node():
        """Test the experience extraction node."""
        print("Testing Experience Extraction Node")
        print("=" * 40)
        
        test_state: JobCleaningState = {
            "job_id": "test-123",
            "company": "TechCorp",
            "title": "Senior Software Engineer",
            "location": "San Francisco, CA",
            "content": "We are looking for a Senior Software Engineer with 5+ years of experience in Python and web development.",
            "original_work_location_type": "Hybrid",
            "original_employment_type": "Full-time",
            "original_salary_range": "$120,000 - $160,000",
            "min_years_experience": None,
            "experience_level": None,
            "experience_level_label": None,
            "salary_range": None,
            "salary_corrected": False,
            "work_location_type": None,
            "location_corrected": False,
            "employment_type": None,
            "employment_corrected": False,
            "processing_errors": [],
            "processing_complete": False
        }
        
        result_state = await extract_experience_node(test_state)
        
        print(f"Job Title: {result_state['title']}")
        print(f"Experience Required: {result_state['min_years_experience']} years")
        print(f"Experience Level: {result_state['experience_level_label']}")
        print(f"Errors: {result_state['processing_errors']}")
        
        print("\n" + "=" * 40)
        print("Experience extraction node test completed!")
    
    asyncio.run(test_experience_node())
