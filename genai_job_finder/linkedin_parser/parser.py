import logging
import re
import time
import random
from datetime import datetime, timedelta
from typing import List, Optional
from urllib.parse import quote, urljoin

import requests
from bs4 import BeautifulSoup

from .models import Job, JobType, ExperienceLevel
from .database import DatabaseManager

logger = logging.getLogger(__name__)


class LinkedInJobParser:
    """LinkedIn job parser using requests and BeautifulSoup"""
    
    BASE_URL = "https://www.linkedin.com/jobs/search/"
    
    def __init__(self, database: Optional[DatabaseManager] = None):
        self.database = database or DatabaseManager()
        self.session = requests.Session()
        self._setup_session()
    
    def _setup_session(self):
        """Setup requests session with proper headers"""
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'max-age=0',
        }
        self.session.headers.update(headers)
    
    def parse_jobs(self, search_query: str, location: str = "", max_pages: int = 5) -> List[Job]:
        """Parse job listings from LinkedIn"""
        job_run = self.database.create_job_run(search_query, location)
        jobs = []
        
        try:
            logger.info(f"Starting job search: '{search_query}' in '{location}'")
            
            for page in range(max_pages):
                logger.info(f"Parsing page {page + 1}")
                
                page_jobs = self._parse_page(search_query, location, page, job_run.id)
                jobs.extend(page_jobs)
                
                # Save batch to database
                if page_jobs:
                    self.database.save_jobs_batch(page_jobs)
                
                # Random delay between pages
                time.sleep(random.uniform(2, 4))
            
            # Update run status
            self.database.update_job_run(job_run.id, "completed", len(jobs))
            logger.info(f"Completed parsing {len(jobs)} jobs")
            
        except Exception as e:
            logger.error(f"Error during parsing: {e}")
            self.database.update_job_run(job_run.id, "failed", len(jobs), str(e))
            raise
        
        return jobs
    
    def _parse_page(self, search_query: str, location: str, page: int, run_id: int) -> List[Job]:
        """Parse jobs from a single page"""
        jobs = []
        
        try:
            url = self._build_url(search_query, location, page)
            logger.debug(f"Fetching: {url}")
            
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            job_cards = self._find_job_cards(soup)
            
            logger.info(f"Found {len(job_cards)} job cards on page {page + 1}")
            
            for card in job_cards:
                try:
                    job = self._parse_job_card(card, run_id)
                    if job:
                        jobs.append(job)
                except Exception as e:
                    logger.warning(f"Error parsing job card: {e}")
                    continue
            
        except requests.RequestException as e:
            logger.error(f"Request failed for page {page + 1}: {e}")
        except Exception as e:
            logger.error(f"Error parsing page {page + 1}: {e}")
        
        return jobs
    
    def _build_url(self, search_query: str, location: str, page: int) -> str:
        """Build LinkedIn search URL"""
        url = f"{self.BASE_URL}?keywords={quote(search_query)}"
        
        if location:
            url += f"&location={quote(location)}"
        
        if page > 0:
            url += f"&start={page * 25}"  # LinkedIn shows 25 jobs per page
        
        # Add time filter for recent jobs (last 7 days)
        url += "&f_TPR=r604800"
        
        return url
    
    def _find_job_cards(self, soup: BeautifulSoup) -> List:
        """Find job cards using various selectors"""
        selectors = [
            'div.job-search-card',
            'div.base-card',
            'div.result-card',
            'article.job-card',
            'div[data-job-id]'
        ]
        
        for selector in selectors:
            cards = soup.select(selector)
            if cards:
                return cards
        
        return []
    
    def _parse_job_card(self, card, run_id: int) -> Optional[Job]:
        """Parse individual job card"""
        try:
            # Extract job ID
            job_id = self._extract_job_id(card)
            
            # Extract basic information
            title = self._extract_title(card)
            company = self._extract_company(card)
            location = self._extract_location(card)
            
            # Extract additional information
            job_url = self._extract_job_url(card)
            posted_date = self._extract_posted_date(card)
            description = self._extract_description(card)
            easy_apply = self._check_easy_apply(card)
            
            # Create job object
            job = Job(
                job_id=job_id,
                title=title,
                company=company,
                location=location,
                description=description,
                posted_date=posted_date,
                easy_apply=easy_apply,
                linkedin_url=job_url,
                run_id=run_id
            )
            
            # Extract additional details from text
            self._enhance_job_details(job)
            
            return job
            
        except Exception as e:
            logger.error(f"Error parsing job card: {e}")
            return None
    
    def _extract_job_id(self, card) -> str:
        """Extract job ID from card"""
        job_id = (
            card.get('data-job-id') or
            card.get('data-entity-urn', '').split(':')[-1] or
            str(abs(hash(str(card)[:100])))  # Fallback hash
        )
        return job_id
    
    def _extract_title(self, card) -> str:
        """Extract job title"""
        selectors = [
            'h3.base-search-card__title',
            'h3',
            'a.base-card__full-link',
            '.job-card-title'
        ]
        
        for selector in selectors:
            elem = card.select_one(selector)
            if elem:
                return elem.get_text(strip=True)
        
        return "Unknown Title"
    
    def _extract_company(self, card) -> str:
        """Extract company name"""
        selectors = [
            'h4.base-search-card__subtitle',
            'a[data-tracking-control-name*="job-search-card-subtitle"]',
            '.job-search-card__subtitle-text',
            'h4'
        ]
        
        for selector in selectors:
            elem = card.select_one(selector)
            if elem:
                return elem.get_text(strip=True)
        
        return "Unknown Company"
    
    def _extract_location(self, card) -> str:
        """Extract job location"""
        selectors = [
            '.job-search-card__location',
            '.base-search-card__metadata',
            '[class*="location"]'
        ]
        
        for selector in selectors:
            elem = card.select_one(selector)
            if elem:
                text = elem.get_text(strip=True)
                if text and (',' in text or len(text) > 3):  # Basic location format check
                    return text
        
        return "Unknown Location"
    
    def _extract_job_url(self, card) -> str:
        """Extract job URL"""
        selectors = [
            'a.base-card__full-link',
            'a[href*="/jobs/view/"]',
            'a[href]'
        ]
        
        for selector in selectors:
            elem = card.select_one(selector)
            if elem and elem.get('href'):
                url = elem['href']
                if not url.startswith('http'):
                    url = urljoin(self.BASE_URL, url)
                return url
        
        return ""
    
    def _extract_posted_date(self, card) -> Optional[datetime]:
        """Extract when job was posted"""
        try:
            # Look for time element
            time_elem = card.select_one('time')
            if time_elem:
                time_text = time_elem.get('datetime') or time_elem.get_text()
            else:
                # Look for text patterns in card
                card_text = card.get_text().lower()
                patterns = [
                    r'(\d+)\s*(hour|hr)s?\s*ago',
                    r'(\d+)\s*(day|d)s?\s*ago',
                    r'(\d+)\s*(week|w)s?\s*ago',
                    r'(\d+)\s*(month|mo)s?\s*ago'
                ]
                
                for pattern in patterns:
                    match = re.search(pattern, card_text)
                    if match:
                        time_text = match.group(0)
                        break
                else:
                    return None
            
            # Parse relative time
            return self._parse_relative_time(time_text.lower())
            
        except Exception:
            return None
    
    def _parse_relative_time(self, time_text: str) -> Optional[datetime]:
        """Parse relative time text to datetime"""
        try:
            if 'hour' in time_text or 'hr' in time_text:
                hours = int(re.search(r'(\d+)', time_text).group(1))
                return datetime.now() - timedelta(hours=hours)
            elif 'day' in time_text:
                days = int(re.search(r'(\d+)', time_text).group(1))
                return datetime.now() - timedelta(days=days)
            elif 'week' in time_text:
                weeks = int(re.search(r'(\d+)', time_text).group(1))
                return datetime.now() - timedelta(weeks=weeks)
            elif 'month' in time_text:
                months = int(re.search(r'(\d+)', time_text).group(1))
                return datetime.now() - timedelta(days=months*30)
        except:
            pass
        
        return None
    
    def _extract_description(self, card) -> str:
        """Extract job description snippet"""
        selectors = [
            '.job-search-card__snippet',
            '.base-search-card__snippet',
            'p'
        ]
        
        for selector in selectors:
            elem = card.select_one(selector)
            if elem:
                return elem.get_text(strip=True)
        
        return ""
    
    def _check_easy_apply(self, card) -> bool:
        """Check if job has Easy Apply option"""
        return bool(card.find(string=re.compile(r'Easy Apply', re.IGNORECASE)))
    
    def _enhance_job_details(self, job: Job):
        """Extract additional details from job text"""
        text = f"{job.title} {job.description}".lower()
        
        # Extract salary
        salary_patterns = [
            r'\$[\d,]+\s*-\s*\$[\d,]+',
            r'\$[\d,]+k?\s*-\s*\$[\d,]+k?',
            r'[\d,]+\s*-\s*[\d,]+\s*(usd|dollar)'
        ]
        
        for pattern in salary_patterns:
            match = re.search(pattern, text)
            if match:
                job.salary_range = match.group(0)
                break
        
        # Detect job type
        if any(term in text for term in ['full-time', 'full time', 'fulltime']):
            job.job_type = JobType.FULL_TIME
        elif any(term in text for term in ['part-time', 'part time', 'parttime']):
            job.job_type = JobType.PART_TIME
        elif 'contract' in text:
            job.job_type = JobType.CONTRACT
        elif 'intern' in text:
            job.job_type = JobType.INTERNSHIP
        
        # Detect experience level
        if any(term in text for term in ['senior', 'sr.', 'lead', 'principal']):
            job.experience_level = ExperienceLevel.SENIOR
        elif any(term in text for term in ['junior', 'jr.', 'entry level', 'entry-level']):
            job.experience_level = ExperienceLevel.ENTRY
        elif any(term in text for term in ['director', 'head of']):
            job.experience_level = ExperienceLevel.DIRECTOR
        
        # Check for remote work
        if any(term in text for term in ['remote', 'work from home', 'wfh']):
            job.remote_option = True
