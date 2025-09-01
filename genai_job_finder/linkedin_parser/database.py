import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any
import logging

from .models import Job, JobRun, Company


logger = logging.getLogger(__name__)


class DatabaseManager:
    """Manages database operations for job data - matches legacy structure"""
    
    def __init__(self, db_path: str = "data/jobs.db"):
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
            
            # Create companies table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS companies (
                    id TEXT PRIMARY KEY,
                    company_name TEXT NOT NULL UNIQUE,
                    company_size TEXT,
                    followers TEXT,
                    industry TEXT,
                    company_url TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create jobs table with legacy column structure + location fields + company_id + company info
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
                    company_id TEXT,
                    company_size TEXT,
                    company_followers TEXT,
                    company_industry TEXT,
                    company_info_link TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (run_id) REFERENCES job_runs (id),
                    FOREIGN KEY (company_id) REFERENCES companies (id)
                )
            ''')
            
            # Migrate existing tables if needed
            self._migrate_tables(cursor)
            
            # Create indexes
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_jobs_run_id ON jobs(run_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_jobs_job_id ON jobs(job_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_jobs_company_id ON jobs(company_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_job_runs_run_date ON job_runs(run_date)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_companies_name ON companies(company_name)')
    
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
            
            if 'company_id' not in columns:
                cursor.execute('ALTER TABLE jobs ADD COLUMN company_id TEXT')
                logger.info("Added company_id column to jobs table")
            
            if 'company_size' not in columns:
                cursor.execute('ALTER TABLE jobs ADD COLUMN company_size TEXT')
                logger.info("Added company_size column to jobs table")
            
            if 'company_followers' not in columns:
                cursor.execute('ALTER TABLE jobs ADD COLUMN company_followers TEXT')
                logger.info("Added company_followers column to jobs table")
            
            if 'company_industry' not in columns:
                cursor.execute('ALTER TABLE jobs ADD COLUMN company_industry TEXT')
                logger.info("Added company_industry column to jobs table")
            
            if 'company_info_link' not in columns:
                cursor.execute('ALTER TABLE jobs ADD COLUMN company_info_link TEXT')
                logger.info("Added company_info_link column to jobs table")
                
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
    
    def save_job(self, job: Job) -> int:
        """Save job to database"""
        try:
            # Convert job to dict for database insertion
            job_data = job.to_dict()
            
            # Define the INSERT query
            query = """
                INSERT INTO jobs (
                    id, company, title, location, work_location_type,
                    level, salary_range, content, employment_type, job_function,
                    industries, posted_time, applicants, job_id, date,
                    parsing_link, job_posting_link, run_id, company_id,
                    company_size, company_followers, company_industry, company_info_link
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            values = (
                job_data['id'], job_data['company'], job_data['title'],
                job_data['location'], job_data['work_location_type'],
                job_data['level'], job_data['salary_range'], job_data['content'],
                job_data['employment_type'], job_data['job_function'],
                job_data['industries'], job_data['posted_time'], job_data['applicants'],
                job_data['job_id'], job_data['date'], job_data['parsing_link'],
                job_data['job_posting_link'], job_data['run_id'], job_data['company_id'],
                job_data['company_size'], job_data['company_followers'],
                job_data['company_industry'], job_data['company_info_link']
            )
            
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, values)
                return cursor.lastrowid
            
        except sqlite3.Error as e:
            logger.error(f"Database error saving job: {e}")
            raise
        except Exception as e:
            logger.error(f"Error saving job: {e}")
            raise
    
    def save_company(self, company: Company) -> str:
        """Save a company to the database"""
        company_dict = company.to_dict()
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Check if company already exists by name
            cursor.execute('''
                SELECT id FROM companies WHERE company_name = ?
            ''', (company.company_name,))
            
            existing = cursor.fetchone()
            if existing:
                # Update existing company with new information
                cursor.execute('''
                    UPDATE companies 
                    SET company_size = COALESCE(?, company_size),
                        followers = COALESCE(?, followers),
                        industry = COALESCE(?, industry),
                        company_url = COALESCE(?, company_url),
                        updated_at = CURRENT_TIMESTAMP
                    WHERE company_name = ?
                ''', (
                    company.company_size, company.followers, company.industry,
                    company.company_url, company.company_name
                ))
                logger.debug(f"Updated company {company.company_name}")
                return existing['id']
            
            # Insert new company
            cursor.execute('''
                INSERT INTO companies (
                    id, company_name, company_size, followers, industry, company_url
                ) VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                company_dict['id'], company_dict['company_name'], 
                company_dict['company_size'], company_dict['followers'],
                company_dict['industry'], company_dict['company_url']
            ))
            
            logger.info(f"Saved new company: {company.company_name}")
            return company.id
    
    def get_company_by_name(self, company_name: str) -> Optional[Dict[str, Any]]:
        """Get company by name"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM companies WHERE company_name = ?', (company_name,))
            result = cursor.fetchone()
            return dict(result) if result else None
    
    def get_all_companies(self) -> List[Dict[str, Any]]:
        """Get all companies"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM companies ORDER BY company_name')
            return [dict(row) for row in cursor.fetchall()]
    
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
        """Export jobs to CSV including company information"""
        import pandas as pd
        
        with self.get_connection() as conn:
            if run_id:
                query = '''
                    SELECT id, company, title, location, work_location_type, level, salary_range, content,
                           employment_type, job_function, industries, posted_time,
                           applicants, job_id, date, parsing_link, job_posting_link,
                           company_size, company_followers, company_industry, company_info_link
                    FROM jobs WHERE run_id = ?
                    ORDER BY created_at DESC
                '''
                df = pd.read_sql_query(query, conn, params=(run_id,))
            else:
                query = '''
                    SELECT id, company, title, location, work_location_type, level, salary_range, content,
                           employment_type, job_function, industries, posted_time,
                           applicants, job_id, date, parsing_link, job_posting_link,
                           company_size, company_followers, company_industry, company_info_link
                    FROM jobs
                    ORDER BY created_at DESC
                '''
                df = pd.read_sql_query(query, conn)
        
        df.to_csv(filename, index=False, encoding="utf-8-sig")
        return filename
        logger.info(f"Exported {len(df)} jobs to {filename}")
    
    def get_all_jobs_as_dataframe(self, run_id: Optional[int] = None):
        """Get all jobs as pandas DataFrame including company information"""
        import pandas as pd
        
        with self.get_connection() as conn:
            if run_id:
                query = '''
                    SELECT id, company, title, location, work_location_type, level, salary_range, content,
                           employment_type, job_function, industries, posted_time,
                           applicants, job_id, date, parsing_link, job_posting_link,
                           company_size, company_followers, company_industry, company_info_link
                    FROM jobs WHERE run_id = ?
                    ORDER BY created_at DESC
                '''
                df = pd.read_sql_query(query, conn, params=(run_id,))
            else:
                query = '''
                    SELECT id, company, title, location, work_location_type, level, salary_range, content,
                           employment_type, job_function, industries, posted_time,
                           applicants, job_id, date, parsing_link, job_posting_link,
                           company_size, company_followers, company_industry, company_info_link
                    FROM jobs
                    ORDER BY created_at DESC
                '''
                df = pd.read_sql_query(query, conn)
        
        return df
