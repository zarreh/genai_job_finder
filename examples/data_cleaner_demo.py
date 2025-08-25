"""
Example usage of the Job Data Cleaner module.

This script demonstrates how to use both the basic JobDataCleaner
and the LangGraph-based workflow cleaner.
"""

import asyncio
import pandas as pd
import logging
from pathlib import Path

from genai_job_finder.data_cleaner import JobDataCleaner, CleanerConfig
from genai_job_finder.data_cleaner.workflow import LangGraphJobCleaner


async def basic_cleaner_example():
    """Example using the basic JobDataCleaner."""
    print("=" * 60)
    print("BASIC JOB DATA CLEANER EXAMPLE")
    print("=" * 60)
    
    # Sample job data
    sample_job = {
        "id": "sample-123",
        "company": "TechCorp",
        "title": "Senior Software Engineer",
        "location": "San Francisco, CA",
        "work_location_type": "Hybrid",
        "employment_type": "Full-time",
        "salary_range": "$120,000 - $160,000",
        "content": """
        We are looking for a Senior Software Engineer with 5+ years of experience 
        in Python and web development. This is a full-time position offering 
        competitive salary between $120,000 - $160,000 annually. 
        
        The role offers hybrid work options - 3 days in office, 2 days remote.
        
        Requirements:
        - 5+ years of professional software development experience
        - Strong proficiency in Python, JavaScript, and React
        - Experience with cloud platforms (AWS, GCP)
        - Bachelor's degree in Computer Science or related field
        
        We offer excellent benefits including health insurance, 401k matching,
        and flexible PTO.
        """
    }
    
    # Initialize cleaner with custom config
    config = CleanerConfig(
        ollama_model="llama3.2",
        ollama_temperature=0.1,
        batch_size=5
    )
    
    cleaner = JobDataCleaner(config)
    
    # Clean the job data
    print("Processing sample job...")
    cleaned_job = await cleaner.clean_job_data(sample_job)
    
    # Display results
    print(f"\nCleaned Job Data:")
    print(f"Title: {cleaned_job.title}")
    print(f"Company: {cleaned_job.company}")
    print(f"Experience Required: {cleaned_job.min_years_experience} years")
    print(f"Experience Level: {cleaned_job.experience_level_label}")
    print(f"Work Location: {cleaned_job.work_location_type.value if cleaned_job.work_location_type else 'Unknown'}")
    print(f"Employment Type: {cleaned_job.employment_type.value if cleaned_job.employment_type else 'Unknown'}")
    
    if cleaned_job.salary_range:
        print(f"Salary Range: ${cleaned_job.salary_range.min_salary:,.0f} - ${cleaned_job.salary_range.max_salary:,.0f}")
        print(f"Mid Salary: ${cleaned_job.salary_range.mid_salary:,.0f}")
    
    print(f"\nCorrections Made:")
    print(f"  Location Type: {'Yes' if cleaned_job.work_location_type_corrected else 'No'}")
    print(f"  Employment Type: {'Yes' if cleaned_job.employment_type_corrected else 'No'}")
    print(f"  Salary Range: {'Yes' if cleaned_job.salary_range_corrected else 'No'}")


async def langgraph_cleaner_example():
    """Example using the LangGraph workflow cleaner."""
    print("\n" + "=" * 60)
    print("LANGGRAPH WORKFLOW CLEANER EXAMPLE")
    print("=" * 60)
    
    # Sample job with problematic data
    sample_job = {
        "id": "sample-456",
        "company": "StartupInc",
        "title": "Data Scientist",
        "location": "Remote",
        "work_location_type": "On-site",  # Incorrect - should be Remote
        "employment_type": "Part-time",   # Incorrect - should be Full-time
        "salary_range": "",               # Missing
        "content": """
        Join our team as a Data Scientist! This is a full-time remote position
        perfect for someone with 2-4 years of experience in machine learning.
        
        We're offering a competitive salary of $90K to $130K per year, plus equity.
        
        This role is 100% remote - work from anywhere in the US!
        
        Requirements:
        - 2-4 years of experience in data science or machine learning
        - PhD or Masters in Statistics, Computer Science, or related field
        - Experience with Python, R, SQL
        - Strong communication skills
        
        This is a full-time position with excellent benefits.
        """
    }
    
    # Initialize LangGraph cleaner
    config = CleanerConfig(
        ollama_model="llama3.2",
        ollama_temperature=0.1
    )
    
    cleaner = LangGraphJobCleaner(config)
    
    # Clean the job data
    print("Processing sample job with LangGraph workflow...")
    cleaned_job = await cleaner.clean_job_data(sample_job)
    
    # Display results
    print(f"\nCleaned Job Data (LangGraph):")
    print(f"Title: {cleaned_job.title}")
    print(f"Company: {cleaned_job.company}")
    print(f"Experience Required: {cleaned_job.min_years_experience} years")
    print(f"Experience Level: {cleaned_job.experience_level_label}")
    
    print(f"\nLocation Type:")
    print(f"  Original: {cleaned_job.original_work_location_type}")
    print(f"  Corrected: {cleaned_job.work_location_type.value if cleaned_job.work_location_type else 'Unknown'}")
    print(f"  Was Corrected: {'Yes' if cleaned_job.work_location_type_corrected else 'No'}")
    
    print(f"\nEmployment Type:")
    print(f"  Original: {cleaned_job.original_employment_type}")
    print(f"  Corrected: {cleaned_job.employment_type.value if cleaned_job.employment_type else 'Unknown'}")
    print(f"  Was Corrected: {'Yes' if cleaned_job.employment_type_corrected else 'No'}")
    
    if cleaned_job.salary_range:
        print(f"\nSalary Information:")
        print(f"  Range: ${cleaned_job.salary_range.min_salary:,.0f} - ${cleaned_job.salary_range.max_salary:,.0f}")
        print(f"  Mid Salary: ${cleaned_job.salary_range.mid_salary:,.0f}")
        print(f"  Was Extracted: {'Yes' if cleaned_job.salary_range_corrected else 'No'}")


async def csv_processing_example():
    """Example of processing a CSV file."""
    print("\n" + "=" * 60)
    print("CSV FILE PROCESSING EXAMPLE")
    print("=" * 60)
    
    # Check if the sample CSV exists
    csv_path = Path("data/jobs_export.csv")
    
    if not csv_path.exists():
        print(f"Sample CSV file not found: {csv_path}")
        print("Please ensure the file exists to run this example.")
        return
    
    # Read a small sample from the CSV
    df = pd.read_csv(csv_path)
    sample_df = df.head(3)  # Process only first 3 records for demo
    
    print(f"Processing {len(sample_df)} records from CSV...")
    
    # Initialize cleaner
    config = CleanerConfig(
        ollama_model="llama3.2",
        batch_size=3
    )
    
    cleaner = JobDataCleaner(config)
    
    # Process the sample
    cleaned_df = await cleaner.clean_dataframe(sample_df)
    
    # Display summary
    print(f"\nProcessing Summary:")
    print(f"Records processed: {len(cleaned_df)}")
    
    if 'experience_level_label' in cleaned_df.columns:
        exp_levels = cleaned_df['experience_level_label'].value_counts()
        print(f"Experience levels found: {dict(exp_levels)}")
    
    # Show salary statistics
    if 'mid_salary' in cleaned_df.columns:
        valid_salaries = cleaned_df['mid_salary'].dropna()
        if len(valid_salaries) > 0:
            print(f"Salary ranges extracted: {len(valid_salaries)} out of {len(cleaned_df)}")
            print(f"Average mid salary: ${valid_salaries.mean():,.0f}")


async def main():
    """Run all examples."""
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("Job Data Cleaner Examples")
    print("This demo requires Ollama to be running with llama3.2 model")
    print("Make sure you have: ollama pull llama3.2")
    print()
    
    try:
        # Run examples
        await basic_cleaner_example()
        await langgraph_cleaner_example()
        await csv_processing_example()
        
        print("\n" + "=" * 60)
        print("ALL EXAMPLES COMPLETED!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\nError running examples: {e}")
        print("Make sure Ollama is running and llama3.2 model is available")


if __name__ == "__main__":
    asyncio.run(main())
