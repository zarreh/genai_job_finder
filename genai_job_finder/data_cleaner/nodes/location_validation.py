import asyncio
from .state import JobCleaningState
from ..chains.location_validation import LocationValidationChain
from ..models import WorkLocationType
from ..config import CleanerConfig


def map_to_location_type(type_str: str) -> WorkLocationType:
    """Map string to WorkLocationType enum."""
    if not type_str:
        return WorkLocationType.UNKNOWN
    
    type_lower = type_str.lower().strip()
    if "remote" in type_lower:
        return WorkLocationType.REMOTE
    elif "hybrid" in type_lower:
        return WorkLocationType.HYBRID
    elif "on-site" in type_lower or "onsite" in type_lower:
        return WorkLocationType.ON_SITE
    else:
        return WorkLocationType.UNKNOWN


async def validate_location_node(state: JobCleaningState, config: CleanerConfig = None) -> JobCleaningState:
    """Node for validating work location type."""
    try:
        config = config or CleanerConfig()
        chain = LocationValidationChain(config)
        
        original_type = state.get("original_work_location_type", "")
        
        if not original_type or original_type.strip() == "":
            # No original type, extract from content
            detected_type = await chain.validate_location_type(state["content"], "")
            state["work_location_type"] = detected_type
            state["location_corrected"] = detected_type != WorkLocationType.UNKNOWN
            print(f"✅ Location detected: {detected_type.value}")
        else:
            # Validate existing type
            validated_type = await chain.validate_location_type(state["content"], original_type)
            original_enum = map_to_location_type(original_type)
            
            # If validation returns Unknown, keep the original type
            if validated_type == WorkLocationType.UNKNOWN:
                state["work_location_type"] = original_enum
                state["location_corrected"] = False
                print(f"✅ Location kept original: {original_enum.value}")
            else:
                state["work_location_type"] = validated_type
                state["location_corrected"] = original_enum != validated_type
                
                if state["location_corrected"]:
                    print(f"✅ Location corrected: {original_type} → {validated_type.value}")
                else:
                    print(f"✅ Location validated: {validated_type.value}")
        
    except Exception as e:
        error_msg = f"Failed to validate location type: {e}"
        state["processing_errors"].append(error_msg)
        # Keep original if available, otherwise set to Unknown
        original_type = state.get("original_work_location_type", "")
        if original_type:
            state["work_location_type"] = map_to_location_type(original_type)
        else:
            state["work_location_type"] = WorkLocationType.UNKNOWN
        state["location_corrected"] = False
        print(f"❌ Location validation failed: {e}")
    
    return state


if __name__ == "__main__":
    async def test_location_node():
        """Test the location validation node."""
        print("Testing Location Validation Node")
        print("=" * 40)
        
        test_state: JobCleaningState = {
            "job_id": "test-123",
            "company": "RemoteCorp",
            "title": "Remote Developer",
            "location": "Anywhere",
            "content": "This is a 100% remote position. Work from anywhere in the US with flexible hours.",
            "original_work_location_type": "On-site",  # Incorrect
            "original_employment_type": "Full-time",
            "original_salary_range": "$80,000 - $120,000",
            "min_years_experience": 2,
            "experience_level": None,
            "experience_level_label": "Early-career",
            "salary_range": None,
            "salary_corrected": False,
            "work_location_type": None,
            "location_corrected": False,
            "employment_type": None,
            "employment_corrected": False,
            "processing_errors": [],
            "processing_complete": False
        }
        
        result_state = await validate_location_node(test_state)
        
        print(f"Job Title: {result_state['title']}")
        print(f"Original Location Type: {result_state['original_work_location_type']}")
        print(f"Validated Location Type: {result_state['work_location_type'].value if result_state['work_location_type'] else 'None'}")
        print(f"Location Corrected: {result_state['location_corrected']}")
        print(f"Errors: {result_state['processing_errors']}")
        
        print("\n" + "=" * 40)
        print("Location validation node test completed!")
    
    asyncio.run(test_location_node())
