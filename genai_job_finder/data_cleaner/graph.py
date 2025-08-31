import asyncio
import sqlite3
import pandas as pd
from typing import Dict, Any
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from tqdm import tqdm
import time

from .nodes import (
    JobCleaningState,
    extract_experience_node,
    extract_salary_node,
    validate_location_node,
    validate_employment_node
)
from .config import CleanerConfig
from .models import ExperienceLevel, WorkLocationType, EmploymentType


def initialize_state_node(state: JobCleaningState) -> JobCleaningState:
    """Initialize the cleaning state."""
    state["processing_errors"] = state.get("processing_errors", [])
    state["processing_complete"] = False
    state["salary_corrected"] = False
    state["location_corrected"] = False
    state["employment_corrected"] = False
    return state


def finalize_state_node(state: JobCleaningState) -> JobCleaningState:
    """Finalize the cleaning results."""
    state["processing_complete"] = True
    return state


class JobCleaningGraph:
    """LangGraph-based job cleaning workflow."""
    
    def __init__(self, config: CleanerConfig = None):
        self.config = config or CleanerConfig()
        self.workflow = self._build_workflow()
    
    def _build_workflow(self) -> StateGraph:
        """Build the LangGraph workflow for job cleaning."""
        workflow = StateGraph(JobCleaningState)
        
        # Add nodes
        workflow.add_node("initialize", initialize_state_node)
        workflow.add_node("extract_experience", self._experience_wrapper)
        workflow.add_node("extract_salary", self._salary_wrapper)
        workflow.add_node("validate_location", self._location_wrapper)
        workflow.add_node("validate_employment", self._employment_wrapper)
        workflow.add_node("finalize", finalize_state_node)
        
        # Define the flow
        workflow.set_entry_point("initialize")
        workflow.add_edge("initialize", "extract_experience")
        workflow.add_edge("extract_experience", "extract_salary")
        workflow.add_edge("extract_salary", "validate_location")
        workflow.add_edge("validate_location", "validate_employment")
        workflow.add_edge("validate_employment", "finalize")
        workflow.add_edge("finalize", END)
        
        # Compile with memory for state persistence
        memory = MemorySaver()
        return workflow.compile(checkpointer=memory)
    
    async def _experience_wrapper(self, state: JobCleaningState) -> JobCleaningState:
        """Wrapper for experience extraction node."""
        return await extract_experience_node(state, self.config)
    
    async def _salary_wrapper(self, state: JobCleaningState) -> JobCleaningState:
        """Wrapper for salary extraction node."""
        return await extract_salary_node(state, self.config)
    
    async def _location_wrapper(self, state: JobCleaningState) -> JobCleaningState:
        """Wrapper for location validation node."""
        return await validate_location_node(state, self.config)
    
    async def _employment_wrapper(self, state: JobCleaningState) -> JobCleaningState:
        """Wrapper for employment validation node."""
        return await validate_employment_node(state, self.config)
    
    async def process_job(self, job_data: Dict[str, Any]) -> JobCleaningState:
        """Process a single job through the workflow."""
        # Create initial state
        initial_state: JobCleaningState = {
            "job_id": str(job_data.get("id", "")),
            "company": str(job_data.get("company", "")),
            "title": str(job_data.get("title", "")),
            "location": job_data.get("location"),
            "content": str(job_data.get("content", "")),
            "original_work_location_type": job_data.get("work_location_type"),
            "original_employment_type": job_data.get("employment_type"),
            "original_salary_range": job_data.get("salary_range"),
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
        
        # Run the workflow
        config = {"configurable": {"thread_id": job_data.get("id", "default")}}
        final_state = await self.workflow.ainvoke(initial_state, config)
        
        return final_state
    
    async def process_dataframe(self, df: pd.DataFrame, progress_callback=None) -> pd.DataFrame:
        """Process an entire DataFrame of job data."""
        print(f"Starting to process {len(df)} job records")
        start_time = time.time()
        
        results = []
        
        # Process jobs with progress bar
        for idx, row in tqdm(df.iterrows(), total=len(df), desc="Processing jobs"):
            try:
                job_data = row.to_dict()
                result_state = await self.process_job(job_data)
                
                # Convert result to dictionary
                result_dict = self._state_to_dict(result_state, job_data)
                results.append(result_dict)
                
                # Call progress callback with detailed AI enhancement progress
                if progress_callback:
                    progress_callback(f"🤖 AI enhancement: processing job details ({idx + 1}/{len(df)})", 7)
                
            except Exception as e:
                print(f"Error processing job {idx}: {e}")
                # Add original data with error flag
                error_dict = job_data.copy()
                error_dict["processing_error"] = str(e)
                results.append(error_dict)
                
                # Still call progress callback for failed jobs
                if progress_callback:
                    progress_callback(f"🤖 AI enhancement: processing job details ({idx + 1}/{len(df)})", 7)
        
        end_time = time.time()
        print(f"Processing completed in {end_time - start_time:.2f} seconds")
        
        return pd.DataFrame(results)
    
    def _state_to_dict(self, state: JobCleaningState, original_data: Dict[str, Any]) -> Dict[str, Any]:
        """Convert JobCleaningState to dictionary for DataFrame."""
        result = original_data.copy()
        
        # Add cleaned fields
        result["min_years_experience"] = state["min_years_experience"]
        result["experience_level"] = state["experience_level"].value if state["experience_level"] else None
        result["experience_level_label"] = state["experience_level_label"]
        
        # Salary fields
        if state["salary_range"]:
            result["min_salary"] = state["salary_range"].min_salary
            result["max_salary"] = state["salary_range"].max_salary
            result["mid_salary"] = state["salary_range"].mid_salary
            result["salary_currency"] = state["salary_range"].currency
            result["salary_period"] = state["salary_range"].period
        else:
            result["min_salary"] = None
            result["max_salary"] = None
            result["mid_salary"] = None
            result["salary_currency"] = None
            result["salary_period"] = None
        
        result["salary_corrected"] = state["salary_corrected"]
        
        # Location fields
        result["work_location_type"] = state["work_location_type"].value if state["work_location_type"] else None
        result["location_corrected"] = state["location_corrected"]
        
        # Employment fields
        result["employment_type"] = state["employment_type"].value if state["employment_type"] else None
        result["employment_corrected"] = state["employment_corrected"]
        
        # Processing info
        result["processing_errors"] = "; ".join(state["processing_errors"]) if state["processing_errors"] else None
        result["processing_complete"] = state["processing_complete"]
        
        return result
    
    def save_workflow_diagram(self, output_file_path: str = "job_cleaning_workflow.png") -> str:
        """Save the workflow diagram as PNG using LangGraph's built-in method."""
        try:
            # Use LangGraph's built-in method to generate PNG
            self.workflow.get_graph().draw_mermaid_png(output_file_path=output_file_path)
            print(f"✅ Workflow diagram saved as PNG: {output_file_path}")
            return output_file_path
        except Exception as e:
            print(f"⚠️ Could not generate PNG diagram: {e}")
            print("💡 Make sure you have the required dependencies for mermaid PNG generation")
            return None
    
    def load_from_database(self, db_path: str, table_name: str = "jobs") -> pd.DataFrame:
        """Load job data from SQLite database."""
        conn = sqlite3.connect(db_path)
        try:
            df = pd.read_sql_query(f"SELECT * FROM {table_name}", conn)
            print(f"Loaded {len(df)} records from {db_path}:{table_name}")
            return df
        finally:
            conn.close()
    
    def save_to_database(self, df: pd.DataFrame, db_path: str, table_name: str = "cleaned_jobs"):
        """Save cleaned data to SQLite database."""
        conn = sqlite3.connect(db_path)
        try:
            df.to_sql(table_name, conn, if_exists="replace", index=False)
            print(f"Saved {len(df)} records to {db_path}:{table_name}")
        finally:
            conn.close()
    
    async def process_database_table(self, db_path: str, source_table: str = "jobs", target_table: str = "cleaned_jobs", progress_callback=None):
        """Process jobs from database table and save results."""
        print(f"Processing database: {db_path}")
        print(f"Source table: {source_table}")
        print(f"Target table: {target_table}")
        
        # Load data
        df = self.load_from_database(db_path, source_table)
        
        # Process data with progress callback
        cleaned_df = await self.process_dataframe(df, progress_callback)
        
        # Save results
        self.save_to_database(cleaned_df, db_path, target_table)
        
        # Print summary
        self._print_summary(cleaned_df)
    
    def _print_summary(self, df: pd.DataFrame):
        """Print processing summary."""
        print("\n" + "="*60)
        print("PROCESSING SUMMARY")
        print("="*60)
        
        print(f"Total records processed: {len(df)}")
        
        # Experience level distribution
        if 'experience_level_label' in df.columns:
            exp_dist = df['experience_level_label'].value_counts()
            print(f"\nExperience Level Distribution:")
            for level, count in exp_dist.items():
                print(f"  {level}: {count}")
        
        # Corrections made
        corrections = {
            'Location Type': df['location_corrected'].sum() if 'location_corrected' in df.columns else 0,
            'Employment Type': df['employment_corrected'].sum() if 'employment_corrected' in df.columns else 0,
            'Salary Range': df['salary_corrected'].sum() if 'salary_corrected' in df.columns else 0,
        }
        
        print(f"\nCorrections Made:")
        for field, count in corrections.items():
            print(f"  {field}: {count} records")
        
        # Salary statistics
        if 'mid_salary' in df.columns:
            salary_stats = df['mid_salary'].describe()
            print(f"\nSalary Statistics (Mid-range):")
            print(f"  Count: {salary_stats['count']:.0f}")
            if salary_stats['count'] > 0:
                print(f"  Mean: ${salary_stats['mean']:,.0f}")
                print(f"  Median: ${salary_stats['50%']:,.0f}")
                print(f"  Min: ${salary_stats['min']:,.0f}")
                print(f"  Max: ${salary_stats['max']:,.0f}")
        
        print("="*60)


if __name__ == "__main__":
    async def test_graph():
        """Test the job cleaning graph."""
        print("Testing Job Cleaning Graph")
        print("=" * 40)
        
        # Create sample job data
        sample_job = {
            "id": "test-123",
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
            """
        }
        
        # Initialize graph
        config = CleanerConfig()
        graph = JobCleaningGraph(config)
        
        # Process single job
        print("Processing sample job...")
        result = await graph.process_job(sample_job)
        
        # Display results
        print(f"\nProcessing Results:")
        print(f"Title: {result['title']}")
        print(f"Experience: {result['min_years_experience']} years → {result['experience_level_label']}")
        print(f"Location: {result['original_work_location_type']} → {result['work_location_type'].value if result['work_location_type'] else 'None'}")
        print(f"Employment: {result['original_employment_type']} → {result['employment_type'].value if result['employment_type'] else 'None'}")
        if result['salary_range']:
            print(f"Salary: ${result['salary_range'].min_salary:,.0f} - ${result['salary_range'].max_salary:,.0f}")
        
        print(f"Errors: {result['processing_errors']}")
        
        print("\n" + "=" * 40)
        print("Graph test completed!")
    
    asyncio.run(test_graph())
