#!/usr/bin/env python3
"""
Quick demo of the data cleaner with real data (keyword-based processing only).
This demo does not require Ollama to be running.
"""

import pandas as pd
import asyncio
from pathlib import Path

from genai_job_finder.data_cleaner import JobDataCleaner, CleanerConfig
from genai_job_finder.data_cleaner.models import ExperienceLevel


async def demo_with_real_data():
    """Demonstrate the cleaner with real job data using keyword-based processing."""
    print("=" * 60)
    print("DATA CLEANER DEMO - Real Data (Keyword Processing)")
    print("=" * 60)
    
    # Load a small sample of real data
    csv_path = Path("data/jobs_export.csv")
    
    if not csv_path.exists():
        print(f"Sample data file not found: {csv_path}")
        print("Please ensure the file exists.")
        return
    
    # Read only first 3 records for quick demo
    df = pd.read_csv(csv_path, nrows=3)
    print(f"Loaded {len(df)} sample records")
    
    # Show original data
    print("\nOriginal Data Sample:")
    for idx, row in df.iterrows():
        print(f"\n{idx + 1}. {row['title']} at {row['company']}")
        print(f"   Location Type: {row['work_location_type']}")
        print(f"   Employment: {row['employment_type']}")
        print(f"   Salary: {row['salary_range']}")
        
        # Show a snippet of content
        content_snippet = row['content'][:200] + "..." if len(row['content']) > 200 else row['content']
        print(f"   Content: {content_snippet}")
    
    # Initialize cleaner with mock LLM (we'll only use keyword processing)
    config = CleanerConfig()
    
    # Process jobs using keyword-based extraction only
    print("\n" + "=" * 60)
    print("PROCESSING RESULTS (Keyword-based)")
    print("=" * 60)
    
    for idx, row in df.iterrows():
        job_data = row.to_dict()
        
        print(f"\n{idx + 1}. Processing: {row['title']}")
        
        # Use keyword-based processors directly (no LLM calls)
        from genai_job_finder.data_cleaner.processors import ExperienceProcessor, SalaryProcessor
        
        exp_processor = ExperienceProcessor(config)
        salary_processor = SalaryProcessor(config)
        
        # Extract experience using keywords
        content = job_data['content']
        min_years = exp_processor._extract_years_with_keywords(content)
        
        if min_years >= 0:
            experience_level = ExperienceLevel.from_years(min_years)
            print(f"   ✅ Experience: {min_years} years → {experience_level.get_label()}")
        else:
            print(f"   ⚠️ Experience: Could not determine from keywords")
        
        # Extract salary using regex
        salary_range_str = job_data.get('salary_range', '')
        # Handle NaN values
        if pd.isna(salary_range_str):
            salary_range_str = ''
        
        existing_salary = salary_processor._extract_salary_with_regex(str(salary_range_str))
        if existing_salary:
            print(f"   ✅ Salary: ${existing_salary.min_salary:,.0f} - ${existing_salary.max_salary:,.0f}")
            print(f"      Mid-range: ${existing_salary.mid_salary:,.0f}")
        else:
            # Try extracting from content
            content_salary = salary_processor._extract_salary_with_regex(content)
            if content_salary:
                print(f"   ✅ Salary (from content): ${content_salary.min_salary:,.0f} - ${content_salary.max_salary:,.0f}")
            else:
                print(f"   ⚠️ Salary: No salary information found")
        
        # Check location type keywords
        from genai_job_finder.data_cleaner.processors import LocationTypeProcessor
        from genai_job_finder.data_cleaner.models import WorkLocationType
        location_processor = LocationTypeProcessor(config)
        detected_location = location_processor._detect_location_type_with_keywords(content)
        
        original_location = job_data.get('work_location_type', '')
        # If detection is Unknown, keep original
        final_location = detected_location if detected_location != WorkLocationType.UNKNOWN else original_location
        final_location_str = final_location.value if isinstance(final_location, WorkLocationType) else final_location
        print(f"   📍 Location: '{original_location}' → {final_location_str}")
        
        # Check employment type keywords  
        from genai_job_finder.data_cleaner.processors import EmploymentTypeProcessor
        from genai_job_finder.data_cleaner.models import EmploymentType
        emp_processor = EmploymentTypeProcessor(config)
        detected_employment = emp_processor._detect_employment_type_with_keywords(content)
        
        original_employment = job_data.get('employment_type', '')
        # If detection is Unknown, keep original
        final_employment = detected_employment if detected_employment != EmploymentType.UNKNOWN else original_employment
        final_employment_str = final_employment.value if isinstance(final_employment, EmploymentType) else final_employment
        print(f"   💼 Employment: '{original_employment}' → {final_employment_str}")
    
    print("\n" + "=" * 60)
    print("DEMO COMPLETE!")
    print("=" * 60)
    print("\nThis demo used keyword-based processing only.")
    print("For full AI-powered processing with Ollama:")
    print("1. Start Ollama: ollama serve")
    print("2. Pull model: ollama pull llama3.2") 
    print("3. Run: python examples/data_cleaner_demo.py")
    print("\nOr use the CLI:")
    print("python -m genai_job_finder.data_cleaner.run_cleaner input.csv output.csv")


if __name__ == "__main__":
    asyncio.run(demo_with_real_data())
