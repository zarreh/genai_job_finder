import asyncio
from .state import JobCleaningState
from ..chains.employment_validation import EmploymentValidationChain
from ..models import EmploymentType
from ..config import CleanerConfig


def map_to_employment_type(type_str: str) -> EmploymentType:
    """Map string to EmploymentType enum."""
    if not type_str:
        return EmploymentType.UNKNOWN
    
    type_lower = type_str.lower().strip()
    if "full" in type_lower:
        return EmploymentType.FULL_TIME
    elif "part" in type_lower:
        return EmploymentType.PART_TIME
    elif "contract" in type_lower:
        return EmploymentType.CONTRACT
    elif "intern" in type_lower:
        return EmploymentType.INTERNSHIP
    elif "temp" in type_lower:
        return EmploymentType.TEMPORARY
    else:
        return EmploymentType.UNKNOWN


async def validate_employment_node(state: JobCleaningState, config: CleanerConfig = None) -> JobCleaningState:
    """Node for validating employment type."""
    try:
        config = config or CleanerConfig()
        chain = EmploymentValidationChain(config)
        
        original_type = state.get("original_employment_type", "")
        
        if not original_type or original_type.strip() == "":
            # No original type, extract from content
            detected_type = await chain.validate_employment_type(state["content"], "")
            state["employment_type"] = detected_type
            state["employment_corrected"] = detected_type != EmploymentType.UNKNOWN
            print(f"✅ Employment detected: {detected_type.value}")
        else:
            # Validate existing type
            validated_type = await chain.validate_employment_type(state["content"], original_type)
            original_enum = map_to_employment_type(original_type)
            
            # If validation returns Unknown, keep the original type
            if validated_type == EmploymentType.UNKNOWN:
                state["employment_type"] = original_enum
                state["employment_corrected"] = False
                print(f"✅ Employment kept original: {original_enum.value}")
            else:
                state["employment_type"] = validated_type
                state["employment_corrected"] = original_enum != validated_type
                
                if state["employment_corrected"]:
                    print(f"✅ Employment corrected: {original_type} → {validated_type.value}")
                else:
                    print(f"✅ Employment validated: {validated_type.value}")
        
    except Exception as e:
        error_msg = f"Failed to validate employment type: {e}"
        state["processing_errors"].append(error_msg)
        # Keep original if available, otherwise set to Unknown
        original_type = state.get("original_employment_type", "")
        if original_type:
            state["employment_type"] = map_to_employment_type(original_type)
        else:
            state["employment_type"] = EmploymentType.UNKNOWN
        state["employment_corrected"] = False
        print(f"❌ Employment validation failed: {e}")
    
    return state


if __name__ == "__main__":
    async def test_employment_node():
        """Test the employment validation node."""
        print("Testing Employment Validation Node")
        print("=" * 40)
        
        test_state: JobCleaningState = {
            "job_id": "test-123",
            "company": "StartupInc",
            "title": "Data Scientist",
            "location": "Remote",
            "content": "This is a full-time permanent position with excellent benefits and growth opportunities.",
            "original_work_location_type": "Remote",
            "original_employment_type": "Part-time",  # Incorrect
            "original_salary_range": "$90,000 - $130,000",
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
        
        result_state = await validate_employment_node(test_state)
        
        print(f"Job Title: {result_state['title']}")
        print(f"Original Employment Type: {result_state['original_employment_type']}")
        print(f"Validated Employment Type: {result_state['employment_type'].value if result_state['employment_type'] else 'None'}")
        print(f"Employment Corrected: {result_state['employment_corrected']}")
        print(f"Errors: {result_state['processing_errors']}")
        
        print("\n" + "=" * 40)
        print("Employment validation node test completed!")
    
    asyncio.run(test_employment_node())
