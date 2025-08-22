import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any
import logging

from .models import Job, JobRun


logger = logging.getLogger(__name__)


class DatabaseManager:
    """Manages database operations for job data - matches legacy structure"""
    
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
        """Create database tables if they don't exist - matches legacy structure"""
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
            
            # Create jobs table with legacy column structure + location fields
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS jobs (
                    id TEXT PRIMARY KEY,
                    company TEXT NOT NULL,
                    title TEXT NOT NULL,
                    location TEXT,
                    work_location_type TEXT,
                    level TEXT,
                    salary_range TEXT,
                    content TEXT,
                    employment_type TEXT,
                    job_function TEXT,
                    industries TEXT,
                    posted_time TEXT,
                    applicants TEXT,
                    job_id TEXT NOT NULL,
                    date TEXT,
                    parsing_link TEXT,
                    job_posting_link TEXT,
                    run_id INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (run_id) REFERENCES job_runs (id)
                )
            ''')
            
            # Migrate existing tables if needed
            self._migrate_tables(cursor)
            
            # Create indexes
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_jobs_run_id ON jobs(run_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_jobs_job_id ON jobs(job_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_job_runs_run_date ON job_runs(run_date)')
    
    def _migrate_tables(self, cursor):
        """Add new columns to existing tables if they don't exist"""
        try:
            # Check if location column exists
            cursor.execute("PRAGMA table_info(jobs)")
            columns = [column[1] for column in cursor.fetchall()]
            
            if 'location' not in columns:
                cursor.execute('ALTER TABLE jobs ADD COLUMN location TEXT')
                logger.info("Added location column to jobs table")
            
            if 'work_location_type' not in columns:
                cursor.execute('ALTER TABLE jobs ADD COLUMN work_location_type TEXT')
                logger.info("Added work_location_type column to jobs table")
                
        except Exception as e:
            logger.warning(f"Migration warning: {e}")
    
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
    
    def save_job(self, job: Job) -> str:
        """Save a job to the database - matches legacy format"""
        job_dict = job.to_dict()
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Check if job already exists
            cursor.execute('''
                SELECT id FROM jobs WHERE id = ?
            ''', (job.id,))
            
            existing = cursor.fetchone()
            if existing:
                logger.debug(f"Job {job.id} already exists")
                return existing['id']
            
            # Insert new job with legacy column structure + location fields
            cursor.execute('''
                INSERT INTO jobs (
                    id, company, title, location, work_location_type, level, salary_range, content,
                    employment_type, job_function, industries, posted_time,
                    applicants, job_id, date, parsing_link, job_posting_link, run_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                job_dict['id'], job_dict['company'], job_dict['title'],
                job_dict['location'], job_dict['work_location_type'], job_dict['level'], 
                job_dict['salary_range'], job_dict['content'], job_dict['employment_type'], 
                job_dict['job_function'], job_dict['industries'], job_dict['posted_time'], 
                job_dict['applicants'], job_dict['job_id'], job_dict['date'], 
                job_dict['parsing_link'], job_dict['job_posting_link'], job_dict['run_id']
            ))
            
            return job.id
    
    def save_jobs_batch(self, jobs: List[Job]) -> int:
        """Save multiple jobs in a batch"""
        saved_count = 0
        for job in jobs:
            try:
                self.save_job(job)
                saved_count += 1
            except Exception as e:
                logger.error(f"Error saving job {job.id}: {e}")
        
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
    
    def export_jobs_to_csv(self, filename: str, run_id: Optional[int] = None) -> str:
        """Export jobs to CSV in legacy format"""
        import pandas as pd
        
        with self.get_connection() as conn:
            if run_id:
                query = '''
                    SELECT id, company, title, location, work_location_type, level, salary_range, content,
                           employment_type, job_function, industries, posted_time,
                           applicants, job_id, date, parsing_link, job_posting_link
                    FROM jobs WHERE run_id = ?
                    ORDER BY created_at DESC
                '''
                df = pd.read_sql_query(query, conn, params=(run_id,))
            else:
                query = '''
                    SELECT id, company, title, location, work_location_type, level, salary_range, content,
                           employment_type, job_function, industries, posted_time,
                           applicants, job_id, date, parsing_link, job_posting_link
                    FROM jobs
                    ORDER BY created_at DESC
                '''
                df = pd.read_sql_query(query, conn)
        
        df.to_csv(filename, index=False, encoding="utf-8-sig")
        return filename
        logger.info(f"Exported {len(df)} jobs to {filename}")
    
    def get_all_jobs_as_dataframe(self, run_id: Optional[int] = None):
        """Get all jobs as pandas DataFrame in legacy format"""
        import pandas as pd
        
        with self.get_connection() as conn:
            if run_id:
                query = '''
                    SELECT id, company, title, location, work_location_type, level, salary_range, content,
                           employment_type, job_function, industries, posted_time,
                           applicants, job_id, date, parsing_link, job_posting_link
                    FROM jobs WHERE run_id = ?
                    ORDER BY created_at DESC
                '''
                df = pd.read_sql_query(query, conn, params=(run_id,))
            else:
                query = '''
                    SELECT id, company, title, location, work_location_type, level, salary_range, content,
                           employment_type, job_function, industries, posted_time,
                           applicants, job_id, date, parsing_link, job_posting_link
                    FROM jobs
                    ORDER BY created_at DESC
                '''
                df = pd.read_sql_query(query, conn)
        
        return df
