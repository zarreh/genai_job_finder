import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any
import logging

from .models import Job, JobRun, JobType, ExperienceLevel


logger = logging.getLogger(__name__)


class DatabaseManager:
    """Manages database operations for job data"""
    
    def __init__(self, db_path: str = "jobs.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize_database()
    
    @contextmanager
    def get_connection(self):
        """Context manager for database connections"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    def _initialize_database(self):
        """Create database tables if they don't exist"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Create job_runs table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS job_runs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    run_date TIMESTAMP NOT NULL,
                    search_query TEXT,
                    location_filter TEXT,
                    job_count INTEGER DEFAULT 0,
                    status TEXT DEFAULT 'pending',
                    error_message TEXT,
                    started_at TIMESTAMP,
                    completed_at TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create jobs table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS jobs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    job_id TEXT NOT NULL,
                    run_id INTEGER NOT NULL,
                    title TEXT NOT NULL,
                    company TEXT NOT NULL,
                    location TEXT NOT NULL,
                    description TEXT,
                    posted_date TIMESTAMP,
                    salary_range TEXT,
                    job_type TEXT,
                    experience_level TEXT,
                    skills TEXT,
                    benefits TEXT,
                    applicants_count INTEGER,
                    remote_option BOOLEAN DEFAULT 0,
                    easy_apply BOOLEAN DEFAULT 0,
                    linkedin_url TEXT,
                    company_linkedin_url TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (run_id) REFERENCES job_runs (id),
                    UNIQUE(job_id, run_id)
                )
            ''')
            
            # Create indexes
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_jobs_run_id ON jobs(run_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_jobs_job_id ON jobs(job_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_job_runs_run_date ON job_runs(run_date)')
    
    def create_job_run(self, search_query: Optional[str] = None, 
                      location_filter: Optional[str] = None) -> JobRun:
        """Create a new job run entry"""
        job_run = JobRun(
            search_query=search_query,
            location_filter=location_filter
        )
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO job_runs (run_date, search_query, location_filter, started_at)
                VALUES (?, ?, ?, ?)
            ''', (job_run.run_date, search_query, location_filter, job_run.started_at))
            
            job_run.id = cursor.lastrowid
            
        logger.info(f"Created job run {job_run.id} at {job_run.run_date}")
        return job_run
    
    def update_job_run(self, run_id: int, status: str, job_count: int = 0, 
                      error_message: Optional[str] = None):
        """Update job run status"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE job_runs 
                SET status = ?, job_count = ?, error_message = ?, completed_at = ?
                WHERE id = ?
            ''', (status, job_count, error_message, datetime.now(), run_id))
    
    def save_job(self, job: Job) -> int:
        """Save a job to the database"""
        job_dict = job.to_dict()
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Check if job already exists for this run
            cursor.execute('''
                SELECT id FROM jobs WHERE job_id = ? AND run_id = ?
            ''', (job.job_id, job.run_id))
            
            existing = cursor.fetchone()
            if existing:
                logger.debug(f"Job {job.job_id} already exists for run {job.run_id}")
                return existing['id']
            
            # Insert new job
            cursor.execute('''
                INSERT INTO jobs (
                    job_id, run_id, title, company, location, description,
                    posted_date, salary_range, job_type, experience_level,
                    skills, benefits, applicants_count, remote_option,
                    easy_apply, linkedin_url, company_linkedin_url
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                job_dict['job_id'], job_dict['run_id'], job_dict['title'],
                job_dict['company'], job_dict['location'], job_dict['description'],
                job_dict['posted_date'], job_dict['salary_range'], job_dict['job_type'],
                job_dict['experience_level'], job_dict['skills'], job_dict['benefits'],
                job_dict['applicants_count'], job_dict['remote_option'],
                job_dict['easy_apply'], job_dict['linkedin_url'],
                job_dict['company_linkedin_url']
            ))
            
            return cursor.lastrowid
    
    def save_jobs_batch(self, jobs: List[Job]) -> int:
        """Save multiple jobs in a batch"""
        saved_count = 0
        for job in jobs:
            try:
                self.save_job(job)
                saved_count += 1
            except Exception as e:
                logger.error(f"Error saving job {job.job_id}: {e}")
        
        return saved_count
    
    def get_jobs_by_run(self, run_id: int) -> List[Dict[str, Any]]:
        """Get all jobs from a specific run"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM jobs WHERE run_id = ?', (run_id,))
            return [dict(row) for row in cursor.fetchall()]
    
    def get_recent_runs(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent job runs"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM job_runs 
                ORDER BY run_date DESC 
                LIMIT ?
            ''', (limit,))
            return [dict(row) for row in cursor.fetchall()]
