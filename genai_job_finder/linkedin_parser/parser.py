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
from .company_parser import LinkedInCompanyParser
from ..legacy.utils import text_clean

logger = logging.getLogger(__name__)


def html_to_markdown(html_content: str) -> str:
    """Convert HTML content to Markdown format while preserving structure"""
    if not html_content:
        return ""
    
    # Create BeautifulSoup object to parse HTML
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Convert common HTML tags to Markdown equivalents
    # Handle headings
    for i in range(1, 7):
        for tag in soup.find_all(f'h{i}'):
            tag.string = f"{'#' * i} {tag.get_text().strip()}\n\n"
            tag.unwrap()
    
    # Handle bold text
    for tag in soup.find_all(['b', 'strong']):
        if tag.string:
            tag.string = f"**{tag.get_text().strip()}**"
        tag.unwrap()
    
    # Handle italic text
    for tag in soup.find_all(['i', 'em']):
        if tag.string:
            tag.string = f"*{tag.get_text().strip()}*"
        tag.unwrap()
    
    # Handle unordered lists
    for ul in soup.find_all('ul'):
        list_items = []
        for li in ul.find_all('li'):
            list_items.append(f"• {li.get_text().strip()}")
        ul.replace_with('\n'.join(list_items) + '\n\n')
    
    # Handle ordered lists
    for ol in soup.find_all('ol'):
        list_items = []
        for i, li in enumerate(ol.find_all('li'), 1):
            list_items.append(f"{i}. {li.get_text().strip()}")
        ol.replace_with('\n'.join(list_items) + '\n\n')
    
    # Handle links
    for a in soup.find_all('a', href=True):
        link_text = a.get_text().strip()
        href = a.get('href')
        if link_text and href:
            a.replace_with(f"[{link_text}]({href})")
        else:
            a.unwrap()
    
    # Handle line breaks
    for br in soup.find_all('br'):
        br.replace_with('\n')
    
    # Handle paragraphs
    for p in soup.find_all('p'):
        p_text = p.get_text().strip()
        if p_text:
            p.replace_with(f"{p_text}\n\n")
        else:
            p.unwrap()
    
    # Handle divs by adding line breaks
    for div in soup.find_all('div'):
        div_text = div.get_text().strip()
        if div_text:
            div.replace_with(f"{div_text}\n\n")
        else:
            div.unwrap()
    
    # Get the final text content
    markdown_text = soup.get_text()
    
    # Clean up extra whitespace and line breaks
    markdown_text = re.sub(r'\n\s*\n\s*\n+', '\n\n', markdown_text)  # Multiple line breaks to double
    markdown_text = re.sub(r'[ \t]+', ' ', markdown_text)  # Multiple spaces to single
    markdown_text = re.sub(r'[ \t]*\n', '\n', markdown_text)  # Remove trailing spaces
    markdown_text = markdown_text.strip()
    
    return markdown_text


class LinkedInJobParser:
    """LinkedIn job parser using requests and BeautifulSoup - matches legacy functionality"""
    
    BASE_URL = "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"
    JOB_DETAILS_URL = "https://www.linkedin.com/jobs-guest/jobs/api/jobPosting/{}"
    
    def __init__(self, database: Optional[DatabaseManager] = None):
        self.database = database or DatabaseManager()
        self.company_parser = LinkedInCompanyParser(self.database)
        self.session = requests.Session()
        self._setup_session()
    
    def _setup_session(self):
        """Setup requests session with proper headers"""
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'max-age=0',
        }
        self.session.headers.update(headers)
    
    def parse_jobs(self, search_query: str, location: str = "", total_jobs: int = 500, 
                  time_filter: str = "r86400", remote: bool = False, parttime: bool = False) -> List[Job]:
        """Parse job listings from LinkedIn - matches legacy functionality"""
        job_run = self.database.create_job_run(search_query, location)
        jobs = []
        
        try:
            logger.info(f"Starting job search: '{search_query}' in '{location}'")
            
            # Step 1: Get job IDs (like legacy get_job_ids)
            job_ids = self._get_job_ids(search_query, location, total_jobs, time_filter, remote, parttime)
            logger.info(f"Found {len(job_ids)} unique job IDs")
            
            # Step 2: Get detailed job data for each ID (like legacy get_job_data)
            jobs = self._get_job_data(job_ids, job_run.id)
            
            # Update run status
            self.database.update_job_run(job_run.id, "completed", len(jobs))
            logger.info(f"Completed parsing {len(jobs)} jobs")
            
        except Exception as e:
            logger.error(f"Error during parsing: {e}")
            self.database.update_job_run(job_run.id, "failed", len(jobs), str(e))
            raise
        
        return jobs
    
    def _get_job_ids(self, search_query: str, location: str, total_jobs: int, 
                    time_filter: str, remote: bool, parttime: bool) -> List[str]:
        """Get job IDs from LinkedIn search results - matches legacy get_job_ids"""
        import math
        from tqdm import tqdm
        
        # Build URL like legacy linkedin_link_constructor
        url = f"{self.BASE_URL}?keywords={search_query.replace(' ', '%20')}"
        url += f"&location={location.replace(' ', '%20')}"
        url += f"&f_TPR={time_filter}"
        
        if parttime:
            url += "&f_JT=P"
        if remote:
            url += "&f_WT=2"
        
        url += "&start={}"
        
        job_ids = []
        pages = math.ceil(total_jobs / 25)  # 25 jobs per page
        
        logger.info(f"Will fetch {pages} pages for up to {total_jobs} jobs")
        logger.info(f"URL template: {url}")
        
        for i in tqdm(range(0, pages), desc="Getting job IDs"):
            try:
                page_url = url.format(i * 25)
                logger.debug(f"Fetching page {i}: {page_url}")
                
                response = self.session.get(page_url, timeout=15)
                response.raise_for_status()
                soup = BeautifulSoup(response.text, "html.parser")
                jobs_on_page = soup.find_all("li")
                
                logger.debug(f"Page {i}: Found {len(jobs_on_page)} <li> elements")
                
                page_job_ids = []
                for job in jobs_on_page:
                    try:
                        job_id = (
                            job.find("div", {"class": "base-card"})
                            .get("data-entity-urn")
                            .split(":")[-1]
                        )
                        page_job_ids.append(job_id)
                    except:
                        continue
                
                logger.info(f"Page {i}: Extracted {len(page_job_ids)} job IDs")
                job_ids.extend(page_job_ids)
                
                time.sleep(random.uniform(1, 3))
                
            except Exception as e:
                logger.warning(f"Error fetching page {i}: {e}")
                continue
        
        unique_job_ids = list(set(job_ids))  # Remove duplicates
        logger.info(f"Total unique job IDs found: {len(unique_job_ids)}")
        return unique_job_ids
    
    def _get_job_data(self, job_ids: List[str], run_id: int) -> List[Job]:
        """Get detailed job data for each job ID - matches legacy get_job_data"""
        from tqdm import tqdm
        
        jobs = []
        date = datetime.now().date().isoformat()
        
        for job_id in tqdm(job_ids, desc="Getting job details"):
            try:
                job_details_url = self.JOB_DETAILS_URL.format(job_id)
                response = self.session.get(job_details_url, timeout=15)
                response.raise_for_status()
                soup = BeautifulSoup(response.text, "html.parser")
                
                job_info = self._extract_job_details(soup, job_id, date, job_details_url, run_id)
                if job_info:
                    jobs.append(job_info)
                    # Save individual job to database
                    self.database.save_job(job_info)
                
                time.sleep(random.uniform(1, 3))
                
            except Exception as e:
                logger.warning(f"Error fetching job {job_id}: {e}")
                continue
        
        return jobs
    
    def _extract_job_details(self, soup: BeautifulSoup, job_id: str, date: str, 
                           parsing_link: str, run_id: int) -> Optional[Job]:
        """Extract detailed job information from job page - matches legacy extraction"""
        try:
            job_info = {}
            
            # Company name
            try:
                job_info["company"] = (
                    soup.find("div", {"class": "top-card-layout__card"})
                    .find("a")
                    .find("img")
                    .get("alt")
                )
            except:
                job_info["company"] = "Unknown Company"
            
            # Job title
            try:
                job_info["title"] = (
                    soup.find("div", {"class": "top-card-layout__entity-info"})
                    .find("a")
                    .text.strip()
                )
            except:
                job_info["title"] = "Unknown Title"
            
            # Location extraction
            try:
                # Look for location in the top card area
                location_elem = soup.find("span", {"class": "topcard__flavor topcard__flavor--bullet"})
                if location_elem:
                    job_info["location"] = location_elem.text.strip()
                else:
                    # Alternative location selectors
                    location_selectors = [
                        ".topcard__flavor",
                        ".sub-nav-cta__meta-text",
                        "[class*='location']"
                    ]
                    for selector in location_selectors:
                        elem = soup.select_one(selector)
                        if elem:
                            job_info["location"] = elem.text.strip()
                            break
                    else:
                        job_info["location"] = "Location not specified"
            except:
                job_info["location"] = "Location not specified"
            
            # Work location type (Remote/Hybrid/On-site) detection
            job_info["work_location_type"] = self._determine_work_location_type(soup, job_info.get("location", ""))
            
            # Extract and save company information
            company_id = None
            company_info = None
            try:
                company_info = self.company_parser.extract_company_info_from_job_page(soup, job_info["company"])
                if company_info:
                    company_id = self.database.save_company(company_info)
                    # Add company information to job data
                    job_info["company_size"] = company_info.company_size
                    job_info["company_followers"] = company_info.followers
                    job_info["company_industry"] = company_info.industry
                    logger.debug(f"Company info extracted for: {job_info['company']}")
                else:
                    # Try to get existing company info from database
                    existing_company = self.database.get_company_by_name(job_info["company"])
                    if existing_company:
                        company_id = existing_company['id']
                        job_info["company_size"] = existing_company.get('company_size')
                        job_info["company_followers"] = existing_company.get('followers')
                        job_info["company_industry"] = existing_company.get('industry')
                    else:
                        # Create basic company record
                        from .models import Company
                        basic_company = Company(company_name=job_info["company"])
                        company_id = self.database.save_company(basic_company)
                        job_info["company_size"] = None
                        job_info["company_followers"] = None
                        job_info["company_industry"] = None
            except Exception as e:
                logger.warning(f"Error processing company info for {job_info['company']}: {e}")
                # Set default values
                job_info["company_size"] = None
                job_info["company_followers"] = None
                job_info["company_industry"] = None
            
            job_info["company_id"] = company_id
            
            # Job criteria (level, employment_type, job_function, industries)
            try:
                criteria_list = soup.find(
                    "ul", {"class": "description__job-criteria-list"}
                ).find_all("li")
                
                field_names = ["level", "employment_type", "job_function", "industries"]
                field_labels = [
                    "Seniority level",
                    "Employment type", 
                    "Job function",
                    "Industries",
                ]
                
                for i, field in enumerate(field_names):
                    if i < len(criteria_list):
                        job_info[field] = (
                            criteria_list[i].text.replace(field_labels[i], "").strip()
                        )
                    else:
                        job_info[field] = ""
            except:
                job_info["level"] = ""
                job_info["employment_type"] = ""
                job_info["job_function"] = ""
                job_info["industries"] = ""
            
            # Job description/content
            try:
                desc_elem = soup.find(
                    "div", {"class": "description__text description__text--rich"}
                )
                if desc_elem:
                    # Use HTML-to-Markdown conversion for better formatting preservation
                    job_info["content"] = html_to_markdown(str(desc_elem))
                else:
                    job_info["content"] = ""
            except:
                job_info["content"] = ""
            
            # Posted time
            try:
                posted_time_elem = soup.find("span", {"class": "posted-time-ago__text"})
                job_info["posted_time"] = (
                    posted_time_elem.text.strip() if posted_time_elem else "N/A"
                )
            except:
                job_info["posted_time"] = "N/A"
            
            # Salary range
            try:
                salary_div = soup.find("div", class_="compensation__salary-range")
                if salary_div:
                    salary = salary_div.find("div", class_="salary compensation__salary")
                    if salary:
                        job_info["salary_range"] = salary.get_text(strip=True)
                    else:
                        job_info["salary_range"] = None
                else:
                    job_info["salary_range"] = None
            except:
                job_info["salary_range"] = None
            
            # Number of applicants
            try:
                applicants_elem = soup.find("span", {"class": "num-applicants__caption"})
                job_info["applicants"] = (
                    applicants_elem.text.strip() if applicants_elem else "N/A"
                )
            except:
                job_info["applicants"] = "N/A"
            
            # Job posting link
            try:
                link_elem = soup.find("a", {"class": "topcard__link"})
                job_info["job_posting_link"] = link_elem.get("href") if link_elem else "N/A"
            except:
                job_info["job_posting_link"] = "N/A"
            
            # Create Job object
            job = Job(
                job_id=job_id,
                company=job_info["company"],
                title=job_info["title"],
                location=job_info["location"],
                work_location_type=job_info["work_location_type"],
                level=job_info["level"],
                salary_range=job_info["salary_range"],
                content=job_info["content"],
                employment_type=job_info["employment_type"],
                job_function=job_info["job_function"],
                industries=job_info["industries"],
                posted_time=job_info["posted_time"],
                applicants=job_info["applicants"],
                date=date,
                parsing_link=parsing_link,
                job_posting_link=job_info["job_posting_link"],
                run_id=run_id,
                company_id=company_id,
                company_size=job_info["company_size"],
                company_followers=job_info["company_followers"],
                company_industry=job_info["company_industry"]
            )
            
            return job
            
        except Exception as e:
            logger.error(f"Error extracting job details: {e}")
            return None
    
    def _determine_work_location_type(self, soup: BeautifulSoup, location: str) -> str:
        """Determine if job is Remote, Hybrid, or On-site"""
        # Check the full page content for remote/hybrid indicators
        page_text = soup.get_text().lower()
        location_lower = location.lower()
        
        # Remote indicators
        remote_keywords = [
            'remote', 'work from home', 'wfh', 'telecommute', 'distributed',
            'anywhere', 'location independent', 'fully remote'
        ]
        
        # Hybrid indicators
        hybrid_keywords = [
            'hybrid', 'flexible', 'mix of remote', 'partially remote',
            'some remote', 'remote friendly', 'flexible location'
        ]
        
        # Check location field first
        for keyword in remote_keywords:
            if keyword in location_lower:
                return "Remote"
        
        for keyword in hybrid_keywords:
            if keyword in location_lower:
                return "Hybrid"
        
        # Check full page content
        for keyword in remote_keywords:
            if keyword in page_text:
                return "Remote"
        
        for keyword in hybrid_keywords:
            if keyword in page_text:
                return "Hybrid"
        
        # Default to On-site if no remote/hybrid indicators found
        return "On-site"
