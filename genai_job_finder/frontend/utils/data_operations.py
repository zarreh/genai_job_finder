"""
Data operations module for database and search functionality
"""
import os
import sqlite3
import json
import pandas as pd
import logging
from typing import List, Optional, Dict, Any
import asyncio
import tempfile
import time
import random
from datetime import datetime
from bs4 import BeautifulSoup

from ..utils.common import get_database_path
from ...linkedin_parser.parser import LinkedInJobParser
from ...linkedin_parser.database import DatabaseManager
from ...data_cleaner.graph import JobCleaningGraph
from ...data_cleaner.config import CleanerConfig

logger = logging.getLogger(__name__)

def load_jobs_from_database() -> List[dict]:
    """Load all jobs from the database"""
    try:
        db_path = get_database_path()
        
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
        db_path = get_database_path()
        
        if not os.path.exists(db_path):
            logger.warning(f"Database not found at {db_path}")
            return []
        
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

def get_recent_runs_from_database() -> List[dict]:
    """Get recent job runs from database"""
    try:
        db_path = get_database_path()
        
        if not os.path.exists(db_path):
            return []
        
        db_manager = DatabaseManager(db_path)
        runs = db_manager.get_recent_runs()
        return runs
        
    except Exception as e:
        logger.error(f"Error loading runs from database: {e}")
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

def search_jobs(search_query: str, location: str, max_pages: int, 
                time_filter: Optional[str] = None, remote_only: bool = False, 
                progress_callback=None) -> List[dict]:
    """Enhanced search with real-time progress tracking"""
    try:
        # Clean and prepare inputs
        search_query = search_query.strip()
        location = location.strip() if location else ""
        
        # If remote_only is True, modify the search query to include remote keywords
        if remote_only:
            search_query += " remote"
        
        logger.info(f"Starting job search for: '{search_query}' in '{location or 'Any location'}' (max_pages: {max_pages}, remote_only: {remote_only})")
        
        # Initialize progress callback
        def update_progress(message: str, step: int = 0):
            if progress_callback:
                progress_callback(message, step)
        
        # Step 1: Initialize
        update_progress("🚀 Initializing LinkedIn job parser...", 1)
        
        # Initialize the parser with temporary database
        logger.info("Initializing parser for temporary search...")
        
        # Use a temporary in-memory database
        temp_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
        temp_db.close()
        
        db_manager = DatabaseManager(temp_db.name)
        parser = LinkedInJobParser(database=db_manager)
        
        # Step 2: Start parsing
        update_progress("🔍 Searching for job listings...", 2)
        logger.info("Starting job parsing...")
        
        # Parse jobs using the parser's built-in functionality
        try:
            # Convert max_pages to total_jobs estimate (25 jobs per page)
            total_jobs_estimate = max_pages * 25
            
            # Step 3: Getting job IDs
            update_progress(f"📋 Collecting job IDs from {max_pages} pages...", 3)
            
            # Get job IDs first
            # Use the provided time filter or default to past 24 hours
            linkedin_time_filter = time_filter if time_filter else "r86400"
            
            job_ids = parser._get_job_ids(
                search_query=search_query,
                location=location,
                total_jobs=total_jobs_estimate,
                time_filter=linkedin_time_filter,
                remote=remote_only,
                parttime=False
            )
            
            # Step 4: Found job IDs
            update_progress(f"✅ Found {len(job_ids)} job listings! Now fetching detailed information...", 4)
            time.sleep(1)  # Brief pause to show the count
            
            # Step 5: Getting detailed job data with progress tracking
            update_progress("🔄 Extracting detailed job information...", 5)
            
            # Create a temporary job run
            job_run = db_manager.create_job_run(search_query, location)
            
            # Get detailed data with progress updates
            jobs_list = []
            for i, job_id in enumerate(job_ids, 1):
                update_progress(f"🔄 Getting job details ({i}/{len(job_ids)})...", 5 + i)
                
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
                    
                    time.sleep(random.uniform(1, 3))
                    
                except Exception as e:
                    logger.warning(f"Error fetching job {job_id}: {e}")
                    continue
            
            # Step 6: Processing results
            update_progress(f"⚙️ Processing {len(jobs_list)} job details...", 6)
            
            # Convert Job objects to dict format for display
            jobs_dict = [job.to_dict() for job in jobs_list]
            
            logger.info(f"Found {len(jobs_dict)} jobs from parsing")
            
            # Step 7: AI Enhancement with Data Cleaner
            if jobs_dict:
                update_progress(f"🤖 Enhancing {len(jobs_dict)} jobs with AI analysis...", 7)
                
                logger.info("Starting AI enhancement with data cleaner...")
                
                try:
                    # Run data cleaner on the temporary database
                    config = CleanerConfig(
                        ollama_model="llama3.2",
                        ollama_base_url="http://localhost:11434"
                    )
                    graph = JobCleaningGraph(config)
                    
                    # Process the jobs through the AI cleaning pipeline
                    try:
                        logger.info(f"Processing {len(jobs_dict)} jobs with AI enhancement...")
                        update_progress("🔧 Running AI data enhancement pipeline...", 8)
                        
                        # Run the async process_database_table in a new event loop
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        loop.run_until_complete(graph.process_database_table(temp_db.name, "jobs", "cleaned_jobs"))
                        loop.close()
                        logger.info("AI enhancement completed successfully")
                    except RuntimeError as re:
                        # If we're already in an event loop, use run_data_cleaner instead
                        logger.info(f"AsyncIO RuntimeError: {re}, using synchronous data cleaner approach...")
                        update_progress("🔧 Using alternative AI enhancement method...", 8)
                        success = run_data_cleaner(temp_db.name)
                        if not success:
                            raise Exception("Data cleaner failed")
                    except Exception as e:
                        logger.error(f"AI enhancement error: {e}")
                        raise Exception(f"AI enhancement failed: {e}")
                    
                    update_progress("🔄 Loading AI-enhanced job data...", 9)
                    
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
                    update_progress("⚠️ AI enhancement failed, showing original job data", 9)
                    time.sleep(2)
            
            # Step 10: Complete
            ai_enhanced_count = sum(1 for job in jobs_dict if job.get('experience_level_label') or job.get('min_salary') or job.get('processed_at'))
            enhanced_msg = f" ({ai_enhanced_count} AI-enhanced)" if ai_enhanced_count > 0 else ""
            
            update_progress(f"🎉 Search completed! Found {len(jobs_dict)} jobs{enhanced_msg} ready to view.", 10)
            
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
        if progress_callback:
            progress_callback(f"❌ {error_msg}", -1)
        return []
