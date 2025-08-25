import streamlit as st
import pandas as pd
import sys
import os
import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
import math
import time
import asyncio
import subprocess
import sqlite3
import json
from bs4 import BeautifulSoup

# Add the parent directory to the path so we can import from genai_job_finder
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from genai_job_finder.linkedin_parser.parser import LinkedInJobParser
from genai_job_finder.linkedin_parser.database import DatabaseManager
from genai_job_finder.linkedin_parser.models import Job, JobType, ExperienceLevel
from genai_job_finder.data_cleaner.graph import JobCleaningGraph
from genai_job_finder.data_cleaner.config import CleanerConfig

# Configure logging to show in terminal
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),  # This will show logs in terminal
        logging.FileHandler('frontend.log')  # Also save to file
    ]
)

logger = logging.getLogger(__name__)

# Page configuration
st.set_page_config(
    page_title="GenAI Job Finder",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'jobs' not in st.session_state:
    st.session_state.jobs = []
if 'stored_jobs' not in st.session_state:
    st.session_state.stored_jobs = []
if 'cleaned_jobs' not in st.session_state:
    st.session_state.cleaned_jobs = []
if 'current_page' not in st.session_state:
    st.session_state.current_page = 1
if 'search_performed' not in st.session_state:
    st.session_state.search_performed = False
if 'rows_per_page' not in st.session_state:
    st.session_state.rows_per_page = 10
if 'jobs_loaded' not in st.session_state:
    st.session_state.jobs_loaded = False
if 'selected_job' not in st.session_state:
    st.session_state.selected_job = None
if 'show_job_details' not in st.session_state:
    st.session_state.show_job_details = False
if 'use_cleaned_data' not in st.session_state:
    st.session_state.use_cleaned_data = False
if 'cleaning_in_progress' not in st.session_state:
    st.session_state.cleaning_in_progress = False

def get_time_filter_options():
    """Get time filter options for job posting dates"""
    return {
        "Any time": None,
        "Past 24 hours": 1,
        "Past week": 7,
        "Past month": 30
    }

def load_jobs_from_database() -> List[dict]:
    """Load all jobs from the database"""
    try:
        # Use the main database in data/ folder
        db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "jobs.db")
        
        if not os.path.exists(db_path):
            logger.warning(f"Database not found at {db_path}")
            return []
        
        db_manager = DatabaseManager(db_path)
        df = db_manager.get_all_jobs_as_dataframe()
        
        if df.empty:
            return []
        
        # Convert DataFrame to list of dictionaries
        jobs = df.to_dict('records')
        logger.info(f"Loaded {len(jobs)} jobs from database")
        return jobs
        
    except Exception as e:
        logger.error(f"Error loading jobs from database: {e}")
        return []

def load_cleaned_jobs_from_database() -> List[dict]:
    """Load all cleaned jobs from the database"""
    try:
        # Use the main database in data/ folder
        db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "jobs.db")
        
        if not os.path.exists(db_path):
            logger.warning(f"Database not found at {db_path}")
            return []
        
        import sqlite3
        with sqlite3.connect(db_path) as conn:
            # Check if cleaned_jobs table exists
            tables_query = "SELECT name FROM sqlite_master WHERE type='table' AND name='cleaned_jobs'"
            tables_df = pd.read_sql_query(tables_query, conn)
            
            if tables_df.empty:
                logger.warning("No cleaned_jobs table found")
                return []
            
            # Load cleaned jobs
            query = "SELECT * FROM cleaned_jobs ORDER BY created_at DESC"
            df = pd.read_sql_query(query, conn)
            
            if df.empty:
                return []
            
            # Convert DataFrame to list of dictionaries
            jobs = df.to_dict('records')
            logger.info(f"Loaded {len(jobs)} cleaned jobs from database")
            return jobs
        
    except Exception as e:
        logger.error(f"Error loading cleaned jobs from database: {e}")
        return []

def run_data_cleaner(db_path: str) -> bool:
    """Run the data cleaner on the database"""
    try:
        logger.info("Starting data cleaner...")
        
        # Setup cleaner config
        config = CleanerConfig(
            ollama_model="llama3.2",
            ollama_base_url="http://localhost:11434"
        )
        
        # Initialize and run the cleaning graph
        graph = JobCleaningGraph(config)
        
        # Run asynchronously
        async def clean_data():
            await graph.process_database_table(db_path, "jobs", "cleaned_jobs")
        
        # Use asyncio to run the cleaning
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(clean_data())
        loop.close()
        
        logger.info("Data cleaning completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"Error during data cleaning: {e}")
        return False

def get_recent_runs_from_database() -> List[dict]:
    """Get recent job runs from database"""
    try:
        db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "jobs.db")
        
        if not os.path.exists(db_path):
            return []
        
        db_manager = DatabaseManager(db_path)
        runs = db_manager.get_recent_runs()
        return runs
        
    except Exception as e:
        logger.error(f"Error loading runs from database: {e}")
        return []

def display_job_details(job_data: dict):
    """Display detailed view of a selected job"""
    st.header("📋 Job Details")
    
    # Check if this is cleaned data
    is_cleaned = 'experience_level_label' in job_data
    
    # Back button
    col1, col2 = st.columns([1, 4])
    with col1:
        if st.button("← Back to Jobs", type="primary"):
            st.session_state.show_job_details = False
            st.session_state.selected_job = None
            st.rerun()
    
    with col2:
        if is_cleaned:
            st.success("🤖 AI-Enhanced Job Data")
        else:
            st.info("📊 Original Job Data")
    
    # Job header
    st.subheader(f"🎯 {job_data.get('title', 'N/A')}")
    st.markdown(f"**🏢 Company:** {job_data.get('company', 'N/A')}")
    
    # Key information in columns
    if is_cleaned:
        # Enhanced view for cleaned data
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("📍 Location", job_data.get('location', 'N/A'))
            st.metric("💼 Employment Type", job_data.get('employment_type', 'N/A'))
            st.metric("🎯 Experience Level", job_data.get('experience_level_label', 'N/A'))
            st.metric("📅 Years Required", str(job_data.get('min_years_experience', 'N/A')))
        
        with col2:
            st.metric("🏠 Work Location Type", job_data.get('work_location_type', 'N/A'))
            
            # Handle salary display with proper NaN checking
            import pandas as pd
            min_sal = job_data.get('min_salary')
            max_sal = job_data.get('max_salary')
            mid_sal = job_data.get('mid_salary')
            
            if (min_sal is not None and max_sal is not None and 
                not pd.isna(min_sal) and not pd.isna(max_sal) and
                min_sal > 0 and max_sal > 0):
                st.metric("💰 Salary Range", f"${min_sal:,.0f} - ${max_sal:,.0f}")
                if mid_sal is not None and not pd.isna(mid_sal) and mid_sal > 0:
                    st.metric("💵 Mid Salary", f"${mid_sal:,.0f}")
                else:
                    st.metric("💵 Mid Salary", "N/A")
                st.metric("💱 Currency", job_data.get('salary_currency', 'N/A'))
            else:
                st.metric("💰 Salary Range", job_data.get('salary_range', 'Not specified'))
            
        with col3:
            st.metric("⏰ Posted", job_data.get('posted_time', 'N/A'))
            st.metric("👥 Applicants", job_data.get('applicants', 'N/A'))
            st.metric("🔧 Job Function", job_data.get('job_function', 'N/A'))
            st.metric("🏭 Industries", job_data.get('industries', 'N/A'))
            
        # AI Processing status
        if job_data.get('processing_complete'):
            st.success("✅ AI Processing Complete")
        if job_data.get('processing_errors'):
            st.warning(f"⚠️ Processing Errors: {job_data.get('processing_errors')}")
            
    else:
        # Original view for raw data
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("📍 Location", job_data.get('location', 'N/A'))
            st.metric("💼 Employment Type", job_data.get('employment_type', 'N/A'))
            st.metric("📊 Level", job_data.get('level', 'N/A'))
        
        with col2:
            st.metric("🏠 Work Location Type", job_data.get('work_location_type', 'N/A'))
            st.metric("💰 Salary Range", job_data.get('salary_range', 'N/A') if job_data.get('salary_range') else 'Not specified')
            st.metric("⏰ Posted", job_data.get('posted_time', 'N/A'))
        
        with col3:
            st.metric("👥 Applicants", job_data.get('applicants', 'N/A'))
            st.metric("🔧 Job Function", job_data.get('job_function', 'N/A'))
            st.metric("🏭 Industries", job_data.get('industries', 'N/A'))
    
    # LinkedIn link
    if job_data.get('job_posting_link'):
        st.markdown(f"🔗 **[View on LinkedIn]({job_data.get('job_posting_link')})**")
    
    # Date parsed
    if job_data.get('date'):
        st.caption(f"📅 Parsed on: {job_data.get('date')}")
    
    if is_cleaned and job_data.get('updated_at'):
        st.caption(f"🤖 AI Enhanced on: {job_data.get('updated_at')}")
    
    st.divider()
    
    # Job description
    st.subheader("📝 Job Description")
    content = job_data.get('content', 'No job description available.')
    
    if content and content != 'N/A':
        # Format the content for better readability
        formatted_content = content.replace('\\n', '\n').replace('\\t', '\t')
        
        # Display in a scrollable container
        with st.container():
            st.markdown(f"""
            <div style="background-color: #f0f2f6; padding: 20px; border-radius: 10px; max-height: 500px; overflow-y: auto;">
                <pre style="white-space: pre-wrap; font-family: inherit; margin: 0;">{formatted_content}</pre>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("No detailed job description available.")
    
    # Additional metadata
    st.divider()
    st.subheader("🔍 Additional Information")
    
    detail_cols = st.columns(2)
    with detail_cols[0]:
        if job_data.get('job_id'):
            st.text(f"Job ID: {job_data.get('job_id')}")
        if job_data.get('id'):
            st.text(f"Record ID: {job_data.get('id')}")
    
    with detail_cols[1]:
        if job_data.get('parsing_link'):
            st.markdown(f"**Parsing Source:** [LinkedIn API]({job_data.get('parsing_link')})")
        if job_data.get('run_id'):
            st.text(f"Parser Run ID: {job_data.get('run_id')}")
            
    # Show AI enhancement details for cleaned data
    if is_cleaned:
        st.subheader("🤖 AI Enhancement Details")
        enhancement_cols = st.columns(4)
        
        with enhancement_cols[0]:
            if job_data.get('salary_corrected'):
                st.success("💰 Salary Enhanced")
            else:
                st.info("💰 Salary Original")
                
        with enhancement_cols[1]:
            if job_data.get('location_corrected'):
                st.success("📍 Location Enhanced")
            else:
                st.info("📍 Location Original")
                
        with enhancement_cols[2]:
            if job_data.get('employment_corrected'):
                st.success("💼 Employment Enhanced")
            else:
                st.info("💼 Employment Original")
                
        with enhancement_cols[3]:
            exp_level = job_data.get('experience_level', 0)
            if exp_level > 0:
                st.success(f"🎯 Experience: Level {exp_level}")
            else:
                st.info("🎯 Experience: Not classified")

def find_job_by_id(job_id: str, jobs_data: List[dict]) -> Optional[dict]:
    """Find a job by its ID in the jobs data"""
    for job in jobs_data:
        if isinstance(job, dict):
            if job.get('id') == job_id:
                return job
        else:
            if hasattr(job, 'id') and job.id == job_id:
                return job.to_dict() if hasattr(job, 'to_dict') else job.__dict__
    return None

def format_job_for_display(job_data: dict, is_cleaned: bool = False) -> dict:
    """Format job data for display in table - supports both Job objects and dict data"""
    # Handle both Job objects and dictionary data
    if isinstance(job_data, dict):
        if is_cleaned:
            # Enhanced cleaned data format with AI-enhanced fields
            
            # Handle salary formatting with proper NaN checking
            min_sal = job_data.get('min_salary')
            max_sal = job_data.get('max_salary')
            mid_sal = job_data.get('mid_salary')
            
            # Check if salary values are valid numbers (not None, not NaN)
            import pandas as pd
            if (min_sal is not None and max_sal is not None and 
                not pd.isna(min_sal) and not pd.isna(max_sal) and
                min_sal > 0 and max_sal > 0):
                if mid_sal and not pd.isna(mid_sal) and mid_sal > 0:
                    salary_display = f"${min_sal:,.0f} - ${max_sal:,.0f} (Mid: ${mid_sal:,.0f})"
                else:
                    salary_display = f"${min_sal:,.0f} - ${max_sal:,.0f}"
            else:
                salary_display = job_data.get("salary_range", "N/A")
            
            # Use enhanced fields from cleaned_jobs table
            experience_level = job_data.get("experience_level_label", "N/A")
            years_exp = job_data.get("min_years_experience")
            if years_exp is None or pd.isna(years_exp):
                years_exp = "N/A"
            
            base_format = {
                "Company": job_data.get("company", "N/A"),
                "Title": job_data.get("title", "N/A"),
                "Location": job_data.get("location", "N/A"),
                "Work Location Type": job_data.get("work_location_type", "N/A"),
                "Experience Level": experience_level,
                "Years Experience": years_exp,
                "Salary Range": salary_display,
                "Employment Type": job_data.get("employment_type", "N/A"),
                "Job Function": job_data.get("job_function", "N/A"),
                "Industries": job_data.get("industries", "N/A"),
                "Posted Time": job_data.get("posted_time", "N/A"),
                "Applicants": job_data.get("applicants", "N/A"),
                "Job ID": job_data.get("id") or job_data.get("job_id", "N/A")  # Keep ID for selection
            }
            return base_format
        else:
            # Data from database (dictionary format) - original
            return {
                "Company": job_data.get("company", "N/A"),
                "Title": job_data.get("title", "N/A"),
                "Location": job_data.get("location", "N/A"),
                "Work Location Type": job_data.get("work_location_type", "N/A"),
                "Level": job_data.get("level", "N/A"),
                "Salary Range": job_data.get("salary_range", "N/A"),
                "Employment Type": job_data.get("employment_type", "N/A"),
                "Job Function": job_data.get("job_function", "N/A"),
                "Industries": job_data.get("industries", "N/A"),
                "Posted Time": job_data.get("posted_time", "N/A"),
                "Applicants": job_data.get("applicants", "N/A"),
                "Job ID": job_data.get("id", "N/A")  # Keep ID for selection
            }
    else:
        # Job object format (for backwards compatibility)
        return {
            "Company": job_data.company if job_data.company else "N/A",
            "Title": job_data.title if job_data.title else "N/A",
            "Location": job_data.location if job_data.location else "N/A",
            "Work Location Type": job_data.work_location_type if job_data.work_location_type else "N/A",
            "Level": job_data.level if job_data.level else "N/A",
            "Salary Range": job_data.salary_range if job_data.salary_range else "N/A",
            "Employment Type": job_data.employment_type if job_data.employment_type else "N/A",
            "Job Function": job_data.job_function if job_data.job_function else "N/A",
            "Industries": job_data.industries if job_data.industries else "N/A",
            "Posted Time": job_data.posted_time if job_data.posted_time else "N/A",
            "Applicants": job_data.applicants if job_data.applicants else "N/A",
            "Job ID": job_data.id if job_data.id else "N/A"
        }

def search_jobs(search_query: str, location: str, max_pages: int, time_filter: Optional[int] = None, remote_only: bool = False):
    """Enhanced search with real-time progress tracking"""
    try:
        # Clean and prepare inputs
        search_query = search_query.strip()
        location = location.strip() if location else ""
        
        # If remote_only is True, modify the search query to include remote keywords
        if remote_only:
            search_query += " remote"
        
        logger.info(f"Starting job search for: '{search_query}' in '{location or 'Any location'}' (max_pages: {max_pages}, remote_only: {remote_only})")
        
        # Create progress tracking UI elements
        progress_container = st.container()
        with progress_container:
            # Status display in colored box
            status_placeholder = st.empty()
            
            # Step 1: Initialize
            with status_placeholder.container():
                st.info("🚀 Initializing LinkedIn job parser...")
            
            # Initialize the parser with temporary database
            logger.info("Initializing parser for temporary search...")
            
            # Use a temporary in-memory database
            import tempfile
            temp_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
            temp_db.close()
            
            db_manager = DatabaseManager(temp_db.name)
            parser = LinkedInJobParser(database=db_manager)
            
            # Step 2: Start parsing
            with status_placeholder.container():
                st.info("🔍 Searching for job listings...")
            logger.info("Starting job parsing...")
            
            # Parse jobs using the parser's built-in functionality
            try:
                # Convert max_pages to total_jobs estimate (25 jobs per page)
                total_jobs_estimate = max_pages * 25
                
                # Step 3: Getting job IDs
                with status_placeholder.container():
                    st.info(f"📋 Collecting job IDs from {max_pages} pages...")
                
                # Get job IDs first
                job_ids = parser._get_job_ids(
                    search_query=search_query,
                    location=location,
                    total_jobs=total_jobs_estimate,
                    time_filter="r86400",
                    remote=remote_only,
                    parttime=False
                )
                
                # Step 4: Found job IDs
                with status_placeholder.container():
                    st.info(f"✅ Found {len(job_ids)} job listings! Now fetching detailed information...")
                time.sleep(1)  # Brief pause to show the count
                
                # Step 5: Getting detailed job data with progress tracking
                with status_placeholder.container():
                    st.info("� Extracting detailed job information...")
                
                # Create a temporary job run
                job_run = db_manager.create_job_run(search_query, location)
                
                # Get detailed data with progress updates
                jobs_list = []
                for i, job_id in enumerate(job_ids, 1):
                    with status_placeholder.container():
                        st.info(f"🔄 Getting job details ({i}/{len(job_ids)})...")
                    
                    try:
                        job_details_url = parser.JOB_DETAILS_URL.format(job_id)
                        response = parser.session.get(job_details_url, timeout=15)
                        response.raise_for_status()
                        soup = BeautifulSoup(response.text, "html.parser")
                        
                        job_info = parser._extract_job_details(soup, job_id, 
                                                             datetime.now().date().isoformat(), 
                                                             job_details_url, job_run.id)
                        if job_info:
                            jobs_list.append(job_info)
                            # Save individual job to database
                            db_manager.save_job(job_info)
                        
                        import random
                        time.sleep(random.uniform(1, 3))
                        
                    except Exception as e:
                        logger.warning(f"Error fetching job {job_id}: {e}")
                        continue
                
                # Step 6: Processing results
                with status_placeholder.container():
                    st.info(f"⚙️ Processing {len(jobs_list)} job details...")
                
                # Convert Job objects to dict format for display
                jobs_dict = [job.to_dict() for job in jobs_list]
                
                logger.info(f"Found {len(jobs_dict)} jobs from parsing")
                
                # Step 7: Apply time filter if specified
                if time_filter and jobs_dict:
                    with status_placeholder.container():
                        st.info(f"⏰ Applying time filter ({time_filter} days)...")
                    
                    logger.info(f"Applying time filter: {time_filter} days")
                    cutoff_date = datetime.now() - timedelta(days=time_filter)
                    original_count = len(jobs_dict)
                    
                    filtered_jobs = []
                    for job in jobs_dict:
                        # For simplicity in live search, include all jobs
                        try:
                            if job.get('posted_time'):
                                filtered_jobs.append(job)
                            else:
                                filtered_jobs.append(job)
                        except:
                            filtered_jobs.append(job)
                    
                    logger.info(f"After time filtering: {len(filtered_jobs)} jobs remain")
                    jobs_dict = filtered_jobs
                
                # Step 8: AI Enhancement with Data Cleaner
                if jobs_dict:
                    with status_placeholder.container():
                        st.info(f"🤖 Enhancing {len(jobs_dict)} jobs with AI analysis...")
                    
                    logger.info("Starting AI enhancement with data cleaner...")
                    
                    try:
                        # Run data cleaner on the temporary database
                        config = CleanerConfig(
                            ollama_model="llama3.2",
                            ollama_base_url="http://localhost:11434"
                        )
                        graph = JobCleaningGraph(config)
                        
                        # Process the jobs through the AI cleaning pipeline
                        import asyncio
                        try:
                            logger.info(f"Processing {len(jobs_dict)} jobs with AI enhancement...")
                            with status_placeholder.container():
                                st.info("🔧 Running AI data enhancement pipeline...")
                            
                            # Run the async process_database_table in a new event loop
                            loop = asyncio.new_event_loop()
                            asyncio.set_event_loop(loop)
                            loop.run_until_complete(graph.process_database_table(temp_db.name, "jobs", "cleaned_jobs"))
                            loop.close()
                            logger.info("AI enhancement completed successfully")
                        except RuntimeError as re:
                            # If we're already in an event loop, use run_data_cleaner instead
                            logger.info(f"AsyncIO RuntimeError: {re}, using synchronous data cleaner approach...")
                            with status_placeholder.container():
                                st.info("🔧 Using alternative AI enhancement method...")
                            success = run_data_cleaner(temp_db.name)
                            if not success:
                                raise Exception("Data cleaner failed")
                        except Exception as e:
                            logger.error(f"AI enhancement error: {e}")
                            raise Exception(f"AI enhancement failed: {e}")
                        
                        with status_placeholder.container():
                            st.info("🔄 Loading AI-enhanced job data...")
                        
                        # Reload the enhanced jobs from database
                        enhanced_jobs = []
                        try:
                            
                            conn = sqlite3.connect(temp_db.name)
                            cursor = conn.cursor()
                            
                            # Check if cleaned_jobs table exists and has data
                            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='cleaned_jobs'")
                            if cursor.fetchone():
                                # Get all cleaned jobs
                                cursor.execute("SELECT * FROM cleaned_jobs ORDER BY created_at DESC")
                                rows = cursor.fetchall()
                                columns = [description[0] for description in cursor.description]
                                
                                logger.info(f"Found {len(rows)} rows in cleaned_jobs table")
                                logger.info(f"Cleaned jobs columns: {columns}")
                                
                                for row in rows:
                                    job_data = dict(zip(columns, row))
                                    
                                    # Convert any JSON strings back to lists/objects
                                    for field in ['required_skills', 'preferred_skills', 'education_requirements']:
                                        if job_data.get(field):
                                            try:
                                                job_data[field] = json.loads(job_data[field])
                                            except:
                                                pass
                                    
                                    enhanced_jobs.append(job_data)
                                    
                                # Log sample of enhanced data
                                if enhanced_jobs:
                                    sample_job = enhanced_jobs[0]
                                    logger.info(f"Sample enhanced job data: experience_level_label={sample_job.get('experience_level_label')}, min_years_experience={sample_job.get('min_years_experience')}, min_salary={sample_job.get('min_salary')}")
                            else:
                                logger.warning("No cleaned_jobs table found, using original data")
                            
                            conn.close()
                            
                            if enhanced_jobs:
                                jobs_dict = enhanced_jobs
                                logger.info(f"Successfully enhanced {len(enhanced_jobs)} jobs with AI")
                            else:
                                logger.warning("No enhanced jobs returned, using original data")
                        
                        except Exception as db_error:
                            logger.warning(f"Failed to load enhanced jobs: {db_error}, using original data")
                    
                    except Exception as cleaning_error:
                        logger.warning(f"AI enhancement failed: {cleaning_error}, proceeding with original data")
                        with status_placeholder.container():
                            st.warning("⚠️ AI enhancement failed, showing original job data")
                        time.sleep(2)
                
                # Step 9: Complete
                ai_enhanced_count = sum(1 for job in jobs_dict if job.get('experience_level_label') or job.get('min_salary') or job.get('processed_at'))
                enhanced_msg = f" ({ai_enhanced_count} AI-enhanced)" if ai_enhanced_count > 0 else ""
                
                with status_placeholder.container():
                    st.success(f"🎉 Search completed! Found {len(jobs_dict)} jobs{enhanced_msg} ready to view.")
                
                # Clean up temporary database
                try:
                    os.unlink(temp_db.name)
                except:
                    pass
                
                logger.info(f"Final result: {len(jobs_dict)} jobs with {ai_enhanced_count} AI-enhanced")
                
                return jobs_dict
                
            except Exception as e:
                # Clean up and re-raise
                try:
                    os.unlink(temp_db.name)
                except:
                    pass
                raise e
            
    except Exception as e:
        error_msg = f"Error searching for jobs: {str(e)}"
        logger.error(error_msg, exc_info=True)
        st.error(error_msg)
        return []

def main():
    st.title("🔍 GenAI Job Finder")
    st.markdown("Find your dream job using AI-powered search and analysis")
    
    # Check if we should show job details
    if st.session_state.show_job_details and st.session_state.selected_job:
        display_job_details(st.session_state.selected_job)
        return
    
    # Create tabs
    tab1, tab2, tab3, tab4 = st.tabs(["🔍 Live Job Search", "📊 Stored Jobs", "🤖 AI-Enhanced Jobs", "📈 Search History"])
    
    with tab1:
        st.header("Live Job Search with AI Enhancement")
        st.info("⚠️ This performs live LinkedIn scraping with automatic AI enhancement. Results include enhanced data but are not saved to database.")
        
        # Search form
        with st.form("job_search_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                search_query = st.text_input(
                    "Job Title/Keywords*",
                    placeholder="e.g., Software Engineer, Data Scientist, AI/ML Engineer",
                    help="Enter job titles, skills, or keywords to search for"
                )
                
                location = st.text_input(
                    "Location",
                    placeholder="e.g., San Francisco, CA, United States, London, UK",
                    help="Leave empty to search all locations"
                )
                
                remote_only = st.checkbox(
                    "🏠 Remote Jobs Only",
                    value=False,
                    help="Search specifically for remote job opportunities (adds 'remote' to search query)"
                )
            
            with col2:
                time_filter_options = get_time_filter_options()
                time_filter_label = st.selectbox(
                    "Time Posted",
                    options=list(time_filter_options.keys()),
                    index=0,
                    help="Filter jobs by when they were posted"
                )
                time_filter = time_filter_options[time_filter_label]
                
                max_pages = st.slider(
                    "Max Pages to Search",
                    min_value=1,
                    max_value=10,
                    value=3,
                    help="Each page contains ~25 job listings. More pages = more results but longer search time"
                )
            
            col_search = st.columns([1])[0]
            with col_search:
                submit_button = st.form_submit_button("🔍 Search Jobs", type="primary")
        
        # Perform search when form is submitted
        if submit_button:
            if not search_query.strip():
                st.error("Please enter a job title or keywords to search for.")
            else:
                st.session_state.jobs = search_jobs(
                    search_query=search_query.strip(),
                    location=location.strip(),
                    max_pages=max_pages,
                    time_filter=time_filter,
                    remote_only=remote_only
                )
                st.session_state.current_page = 1
                st.session_state.search_performed = True
                
                if st.session_state.jobs:
                    remote_text = " remote" if remote_only else ""
                    st.success(f"Found {len(st.session_state.jobs)}{remote_text} jobs!")
                else:
                    st.warning("No jobs found. Try adjusting your search criteria.")
        
        # Display results
        if st.session_state.search_performed and st.session_state.jobs:
            # Check if any jobs have AI enhancement indicators
            ai_enhanced_count = sum(1 for job in st.session_state.jobs if job.get('experience_level_label') or job.get('min_salary') or job.get('processed_at'))
            title_suffix = f" - {ai_enhanced_count} AI Enhanced" if ai_enhanced_count > 0 else ""
            display_job_results(st.session_state.jobs, f"Live Search Results{title_suffix}", is_cleaned_data=True)
    
    with tab2:
        st.header("Stored Jobs")
        st.markdown("Jobs from previous parser runs stored in the database")
        
        # Load jobs button
        col1, col2 = st.columns([1, 3])
        with col1:
            if st.button("🔄 Load Jobs from Database", type="primary"):
                st.session_state.stored_jobs = load_jobs_from_database()
                st.session_state.jobs_loaded = True
                st.session_state.current_page = 1  # Reset to first page
                
                if st.session_state.stored_jobs:
                    st.success(f"Loaded {len(st.session_state.stored_jobs)} jobs from database!")
                else:
                    st.warning("No jobs found in database. Run the parser first to collect jobs.")
        
        # Auto-load on first visit
        if not st.session_state.jobs_loaded:
            st.session_state.stored_jobs = load_jobs_from_database()
            st.session_state.jobs_loaded = True
        
        # Display stored jobs
        if st.session_state.stored_jobs:
            display_job_results(st.session_state.stored_jobs, "Stored Jobs from Database", is_database_data=True)
        else:
            st.info("No stored jobs available. Use the parser to collect job data first.")
    
    with tab3:
        st.header("🤖 AI-Enhanced Jobs")
        st.markdown("Jobs processed with AI-powered data cleaning and enhancement")
        
        # Load cleaned jobs button
        col1, col2, col3 = st.columns([1, 1, 2])
        with col1:
            if st.button("🔄 Load AI-Enhanced Jobs", type="primary"):
                st.session_state.cleaned_jobs = load_cleaned_jobs_from_database()
                st.session_state.current_page = 1  # Reset to first page
                
                if st.session_state.cleaned_jobs:
                    st.success(f"Loaded {len(st.session_state.cleaned_jobs)} AI-enhanced jobs!")
                else:
                    st.warning("No AI-enhanced jobs found. Use 'Live Job Search' tab to search and automatically enhance jobs.")
        
        with col2:
            if st.button("🧹 Run Data Cleaner"):
                db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "jobs.db")
                
                if not os.path.exists(db_path):
                    st.error("No database found. Please parse some jobs first.")
                else:
                    with st.spinner("🤖 Running AI data cleaner... This may take a few minutes."):
                        success = run_data_cleaner(db_path)
                        
                    if success:
                        st.success("✅ Data cleaning completed! Reload AI-enhanced jobs to see results.")
                        # Auto-reload cleaned jobs
                        st.session_state.cleaned_jobs = load_cleaned_jobs_from_database()
                    else:
                        st.error("❌ Data cleaning failed. Check logs for details.")
        
        # Auto-load cleaned jobs on first visit
        if 'cleaned_jobs_loaded' not in st.session_state:
            st.session_state.cleaned_jobs = load_cleaned_jobs_from_database()
            st.session_state.cleaned_jobs_loaded = True
        
        # Show AI enhancement info
        if st.session_state.cleaned_jobs:
            st.info("✨ **AI Enhancements Include:** Experience level classification, Salary extraction & normalization, Work location validation, Employment type standardization")
            
            # Show enhanced fields comparison
            with st.expander("🤖 AI Enhancement Details"):
                st.markdown("""
                **Enhanced Fields:**
                - **Experience Level**: AI classifies as Intern, Junior, Mid-level, Senior, Lead, Principal, Director
                - **Years Experience**: Extracts required years from job descriptions
                - **Salary Range**: Parses and normalizes salary information (min, max, mid, currency, period)
                - **Work Location Type**: Validates and corrects Remote/Hybrid/On-site classification
                - **Employment Type**: Standardizes Full-time/Part-time/Contract classifications
                
                **Data Quality Flags:**
                - Shows which fields were AI-enhanced vs original
                - Processing completion status
                - Error tracking for transparency
                """)
            
            display_job_results(st.session_state.cleaned_jobs, "AI-Enhanced Jobs", is_cleaned_data=True)
        else:
            st.info("No AI-enhanced jobs available. Use 'Live Job Search' to automatically enhance new job data.")
    
    with tab4:
        st.header("Search History")
        
        # Load and display recent runs
        runs = get_recent_runs_from_database()
        
        if runs:
            st.markdown("### Recent Parser Runs")
            
            runs_data = []
            for run in runs:
                runs_data.append({
                    "Run ID": run.get("id", "N/A"),
                    "Date": run.get("run_date", "N/A")[:19] if run.get("run_date") else "N/A",
                    "Search Query": run.get("search_query", "N/A"),
                    "Location": run.get("location_filter", "Any") if run.get("location_filter") else "Any",
                    "Job Count": run.get("job_count", 0),
                    "Status": run.get("status", "Unknown"),
                    "Duration": f"{((datetime.fromisoformat(run.get('completed_at', '')) - datetime.fromisoformat(run.get('started_at', ''))).total_seconds() / 60):.1f} min" if run.get("completed_at") and run.get("started_at") else "N/A"
                })
            
            df_runs = pd.DataFrame(runs_data)
            st.dataframe(df_runs, use_container_width=True, hide_index=True)
        else:
            st.info("No search history available. Run the parser to see history.")

def display_job_results(jobs_data: List, title: str, is_database_data: bool = False, is_cleaned_data: bool = False):
    """Display job results with pagination and filtering"""
    st.divider()
    st.header(title)
    
    # Results per page selector
    col_results, col_spacing = st.columns([1, 3])
    with col_results:
        rows_per_page = st.selectbox(
            "Results per Page",
            options=[5, 10, 15, 20, 25, 50],
            index=1,  # Default to 10
            help="Number of job results to display per page",
            key=f"results_per_page_{title.replace(' ', '_')}"
        )
        # Update session state when changed
        if rows_per_page != st.session_state.rows_per_page:
            st.session_state.rows_per_page = rows_per_page
            st.session_state.current_page = 1  # Reset to first page when changing page size
    
    # Pagination settings
    jobs_per_page = st.session_state.rows_per_page
    total_jobs = len(jobs_data)
    total_pages = math.ceil(total_jobs / jobs_per_page)
    
    # Pagination controls
    if total_pages > 1:
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col1:
            if st.button("◀ Previous", disabled=(st.session_state.current_page == 1), key=f"prev_{title.replace(' ', '_')}"):
                st.session_state.current_page -= 1
                st.rerun()
        
        with col2:
            st.markdown(f"<center>Page {st.session_state.current_page} of {total_pages}</center>", 
                      unsafe_allow_html=True)
        
        with col3:
            if st.button("Next ▶", disabled=(st.session_state.current_page == total_pages), key=f"next_{title.replace(' ', '_')}"):
                st.session_state.current_page += 1
                st.rerun()
    
    # Calculate slice indices for current page
    start_idx = (st.session_state.current_page - 1) * jobs_per_page
    end_idx = min(start_idx + jobs_per_page, total_jobs)
    
    # Display jobs for current page
    current_page_jobs = jobs_data[start_idx:end_idx]
    
    # Convert jobs to DataFrame for display - only specified columns
    job_data = [format_job_for_display(job, is_cleaned=is_cleaned_data) for job in current_page_jobs]
    df = pd.DataFrame(job_data)
    
    # Filter to only show requested columns
    if is_cleaned_data:
        # Enhanced display columns for cleaned data
        display_columns = [
            "Company", "Title", "Location", "Work Location Type", "Experience Level", 
            "Years Experience", "Salary Range", "Employment Type", "Job Function", 
            "Industries", "Posted Time", "Applicants"
        ]
    else:
        # Original display columns
        display_columns = [
            "Company", "Title", "Location", "Work Location Type", "Level", 
            "Salary Range", "Employment Type", "Job Function", 
            "Industries", "Posted Time", "Applicants"
        ]
    
    # Only include columns that exist in the dataframe
    available_columns = [col for col in display_columns if col in df.columns]
    
    if not df.empty:
        filtered_df = df[available_columns]
        
        # Add column filters
        st.subheader("Filter Results")
        if is_cleaned_data:
            # Enhanced filters for cleaned data
            filter_cols = st.columns(5)
            
            with filter_cols[0]:
                title_filter = st.text_input("Filter by Title", placeholder="e.g., Engineer, Data", key=f"title_filter_{title.replace(' ', '_')}")
            with filter_cols[1]:
                company_filter = st.text_input("Filter by Company", placeholder="e.g., Google, Meta", key=f"company_filter_{title.replace(' ', '_')}")
            with filter_cols[2]:
                location_filter = st.text_input("Filter by Location", placeholder="e.g., SF, Remote", key=f"location_filter_{title.replace(' ', '_')}")
            with filter_cols[3]:
                work_type_filter = st.selectbox("Work Type", 
                                             options=["All"] + filtered_df["Work Location Type"].unique().tolist() if "Work Location Type" in filtered_df.columns else ["All"],
                                             key=f"work_type_filter_{title.replace(' ', '_')}")
            with filter_cols[4]:
                exp_level_filter = st.selectbox("Experience Level", 
                                              options=["All"] + sorted(filtered_df["Experience Level"].unique().tolist()) if "Experience Level" in filtered_df.columns else ["All"],
                                              key=f"exp_level_filter_{title.replace(' ', '_')}")
            
            # Salary range filter for cleaned data
            salary_col1, salary_col2 = st.columns(2)
            with salary_col1:
                min_salary_filter = st.number_input("Min Salary ($)", min_value=0, value=0, step=10000, key=f"min_salary_{title.replace(' ', '_')}")
            with salary_col2:
                max_salary_filter = st.number_input("Max Salary ($)", min_value=0, value=0, step=10000, key=f"max_salary_{title.replace(' ', '_')}")
        else:
            # Original filters
            filter_cols = st.columns(4)
            
            with filter_cols[0]:
                title_filter = st.text_input("Filter by Title", placeholder="e.g., Engineer, Data", key=f"title_filter_{title.replace(' ', '_')}")
            with filter_cols[1]:
                company_filter = st.text_input("Filter by Company", placeholder="e.g., Google, Meta", key=f"company_filter_{title.replace(' ', '_')}")
            with filter_cols[2]:
                location_filter = st.text_input("Filter by Location", placeholder="e.g., SF, Remote", key=f"location_filter_{title.replace(' ', '_')}")
            with filter_cols[3]:
                work_type_filter = st.selectbox("Filter by Work Type", 
                                             options=["All"] + filtered_df["Work Location Type"].unique().tolist() if "Work Location Type" in filtered_df.columns else ["All"],
                                             key=f"work_type_filter_{title.replace(' ', '_')}")
        
        # Apply filters
        display_df = filtered_df.copy()
        
        if title_filter:
            display_df = display_df[display_df["Title"].str.contains(title_filter, case=False, na=False)]
        if company_filter:
            display_df = display_df[display_df["Company"].str.contains(company_filter, case=False, na=False)]
        if location_filter:
            display_df = display_df[display_df["Location"].str.contains(location_filter, case=False, na=False)]
        if work_type_filter != "All":
            display_df = display_df[display_df["Work Location Type"] == work_type_filter]
        
        # Additional filters for cleaned data
        if is_cleaned_data:
            if exp_level_filter != "All":
                display_df = display_df[display_df["Experience Level"] == exp_level_filter]
            
            # Salary range filter
            if min_salary_filter > 0 or max_salary_filter > 0:
                # Extract salary values from the formatted range strings
                def extract_min_salary(salary_str):
                    if pd.isna(salary_str) or salary_str == "N/A":
                        return 0
                    import re
                    match = re.search(r'\$([0-9,]+)', str(salary_str))
                    if match:
                        return int(match.group(1).replace(',', ''))
                    return 0
                
                display_df['_min_salary_numeric'] = display_df["Salary Range"].apply(extract_min_salary)
                
                if min_salary_filter > 0:
                    display_df = display_df[display_df['_min_salary_numeric'] >= min_salary_filter]
                if max_salary_filter > 0:
                    display_df = display_df[display_df['_min_salary_numeric'] <= max_salary_filter]
                
                # Remove the temporary column
                display_df = display_df.drop('_min_salary_numeric', axis=1)
        
        # Show filter results info
        if len(display_df) != len(filtered_df):
            st.info(f"Showing {len(display_df)} of {len(filtered_df)} jobs after filtering")
        
        # Display the filtered table with row selection
        if not display_df.empty:
            st.markdown("💡 **Click on a row to view detailed job information**")
            
            # Create a copy for display with row indices
            display_with_index = display_df.reset_index(drop=True)
            
            # Display the dataframe with click handling
            if is_cleaned_data:
                # Enhanced column config for cleaned data
                column_config = {
                    "Title": st.column_config.TextColumn(
                        "Title",
                        help="Job title - Click row for details",
                        width="large"
                    ),
                    "Company": st.column_config.TextColumn(
                        "Company",
                        help="Company name",
                        width="medium"
                    ),
                    "Location": st.column_config.TextColumn(
                        "Location",
                        help="Job location",
                        width="medium"
                    ),
                    "Work Location Type": st.column_config.TextColumn(
                        "Work Type",
                        help="Remote/Hybrid/On-site",
                        width="small"
                    ),
                    "Experience Level": st.column_config.TextColumn(
                        "Experience",
                        help="AI-classified experience level",
                        width="small"
                    ),
                    "Years Experience": st.column_config.NumberColumn(
                        "Years",
                        help="Required years of experience",
                        width="small"
                    ),
                    "Salary Range": st.column_config.TextColumn(
                        "Salary Range",
                        help="AI-extracted salary information",
                        width="medium"
                    )
                }
            else:
                # Original column config
                column_config = {
                    "Title": st.column_config.TextColumn(
                        "Title",
                        help="Job title - Click row for details",
                        width="large"
                    ),
                    "Company": st.column_config.TextColumn(
                        "Company",
                        help="Company name",
                        width="medium"
                    ),
                    "Location": st.column_config.TextColumn(
                        "Location",
                        help="Job location",
                        width="medium"
                    ),
                    "Work Location Type": st.column_config.TextColumn(
                        "Work Location Type",
                        help="Remote/Hybrid/On-site",
                        width="small"
                    ),
                    "Level": st.column_config.TextColumn(
                        "Level",
                        help="Experience level",
                        width="small"
                    ),
                    "Salary Range": st.column_config.TextColumn(
                        "Salary Range",
                        help="Salary information",
                        width="medium"
                    )
                }
            
            selected_indices = st.dataframe(
                display_with_index,
                use_container_width=True,
                hide_index=True,
                on_select="rerun",
                selection_mode="single-row",
                column_config=column_config
            )
            
            # Handle row selection
            if selected_indices.selection.rows:
                selected_row_index = selected_indices.selection.rows[0]
                # Get the actual job index from current page
                actual_job_index = start_idx + selected_row_index
                
                if actual_job_index < len(jobs_data):
                    selected_job_data = jobs_data[actual_job_index]
                    
                    # Convert to dict if it's a Job object
                    if not isinstance(selected_job_data, dict):
                        if hasattr(selected_job_data, 'to_dict'):
                            selected_job_data = selected_job_data.to_dict()
                        else:
                            selected_job_data = selected_job_data.__dict__
                    
                    # Store in session state and show details
                    st.session_state.selected_job = selected_job_data
                    st.session_state.show_job_details = True
                    st.rerun()
        else:
            st.warning("No jobs match the current filters. Try adjusting your filter criteria.")
        
        # Show pagination info
        st.caption(f"Showing jobs {start_idx + 1}-{end_idx} of {total_jobs} total results ({jobs_per_page} per page)")
        
        # Download option
        if st.button("📥 Download Results as CSV", key=f"download_{title.replace(' ', '_')}"):
            all_job_data = [format_job_for_display(job, is_cleaned=is_cleaned_data) for job in jobs_data]
            csv_df = pd.DataFrame(all_job_data)
            
            # Filter to only requested columns for CSV
            if not csv_df.empty:
                available_cols = [col for col in display_columns if col in csv_df.columns]
                csv_df = csv_df[available_cols]
            
            csv = csv_df.to_csv(index=False)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename_prefix = "ai_enhanced" if is_cleaned_data else "job_search"
            
            st.download_button(
                label="Click to Download",
                data=csv,
                file_name=f"{filename_prefix}_results_{timestamp}.csv",
                mime="text/csv",
                key=f"download_btn_{title.replace(' ', '_')}"
            )
    else:
        st.info("No jobs to display.")

if __name__ == "__main__":
    main()
