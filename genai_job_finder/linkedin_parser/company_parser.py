import logging
import re
import time
import random
from typing import Optional
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

from .models import Company
from .database import DatabaseManager

logger = logging.getLogger(__name__)


class LinkedInCompanyParser:
    """LinkedIn company information parser"""
    
    def __init__(self, database: Optional[DatabaseManager] = None):
        self.database = database or DatabaseManager()
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
    
    def extract_company_info_from_job_page(self, soup: BeautifulSoup, company_name: str) -> Optional[Company]:
        """Extract company information from a job posting page"""
        try:
            company_info = {
                'company_name': company_name,
                'company_size': None,
                'followers': None,
                'industry': None,
                'company_url': None
            }
            
            # Try to find company link first
            company_link = self._extract_company_link(soup)
            if company_link:
                company_info['company_url'] = company_link
                logger.info(f"Found company link for {company_name}: {company_link}")
                # If we have a company link, try to get detailed info from company page
                detailed_info = self._get_company_page_info(company_link)
                if detailed_info:
                    company_info.update(detailed_info)
            else:
                logger.debug(f"No company link found for {company_name}")

            # If we couldn't get detailed info, try to extract from job page itself
            if not company_info['company_size'] or not company_info['followers']:
                job_page_info = self._extract_company_info_from_job_page_content(soup)
                for key, value in job_page_info.items():
                    if value and not company_info[key]:
                        company_info[key] = value

            # Create Company object if we have at least some information (including just company_url)
            if any([company_info['company_size'], company_info['followers'], 
                   company_info['industry'], company_info['company_url']]):
                return Company(
                    company_name=company_info['company_name'],
                    company_size=company_info['company_size'],
                    followers=company_info['followers'],
                    industry=company_info['industry'],
                    company_url=company_info['company_url']
                )
            
            logger.debug(f"No company information found for {company_name}")
            return None
            
        except Exception as e:
            logger.error(f"Error extracting company info for {company_name}: {e}")
            return None
    
    def _extract_company_link(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract company profile link from job page"""
        try:
            # Updated selectors for LinkedIn's current HTML structure
            selectors = [
                # Modern LinkedIn job page selectors
                "a[href*='/company/'][data-tracking-control-name*='public_jobs_topcard']",
                "a[href*='/company/'][data-tracking-control-name*='company']",
                ".jobs-unified-top-card__company-name a[href*='/company/']",
                ".job-details-jobs-unified-top-card__company-name a[href*='/company/']",
                ".jobs-details__main-content a[href*='/company/']",
                "[data-test-id*='company'] a[href*='/company/']",
                
                # Fallback selectors for different page layouts
                "a[href*='/company/']",
                ".topcard__org-name-link",
                ".top-card-layout__card a[href*='/company/']",
                "a[data-tracking-control-name='public_jobs_topcard-org-name']",
                ".jobs-company__company-name a[href*='/company/']",
                
                # Additional modern selectors
                "[data-entity-urn*='company'] a[href*='/company/']",
                ".job-details-jobs-unified-top-card a[href*='/company/']",
                ".jobs-unified-top-card a[href*='/company/']"
            ]
            
            for selector in selectors:
                elements = soup.select(selector)
                for element in elements:
                    if element and element.get('href'):
                        href = element.get('href')
                        if '/company/' in href:
                            # Clean up the URL and ensure it's valid
                            href = href.split('?')[0]  # Remove query parameters
                            href = href.split('#')[0]  # Remove fragments
                            
                            # Ensure it's a full URL
                            if href.startswith('http'):
                                logger.debug(f"Found company link: {href}")
                                return href
                            else:
                                full_url = urljoin('https://www.linkedin.com', href)
                                logger.debug(f"Found company link (relative): {href} -> {full_url}")
                                return full_url
            
            logger.debug("No company link found with any selector")
            return None
            
        except Exception as e:
            logger.warning(f"Error extracting company link: {e}")
            return None
    
    def _extract_company_info_from_job_page_content(self, soup: BeautifulSoup) -> dict:
        """Extract company info directly from job page content using LinkedIn's specific data-test-id attributes"""
        info = {
            'company_size': None,
            'followers': None,
            'industry': None
        }
        
        try:
            # PRIORITY 1: Use LinkedIn's specific data-test-id selectors (most reliable)
            logger.debug("Attempting extraction using LinkedIn data-test-id selectors...")
            
            # Company size from data-test-id="about-us__size"
            size_section = soup.find(attrs={"data-test-id": "about-us__size"})
            if size_section:
                size_dd = size_section.find("dd")
                if size_dd:
                    size_text = size_dd.get_text().strip()
                    # Clean up the text and extract meaningful size info
                    if size_text and len(size_text) > 0:
                        info['company_size'] = size_text
                        logger.debug(f"Found company size via data-test-id: {size_text}")
            
            # Industry from data-test-id="about-us__industry" 
            industry_section = soup.find(attrs={"data-test-id": "about-us__industry"})
            if industry_section:
                industry_dd = industry_section.find("dd")
                if industry_dd:
                    industry_text = industry_dd.get_text().strip()
                    if industry_text and len(industry_text) > 2:
                        info['industry'] = industry_text
                        logger.debug(f"Found industry via data-test-id: {industry_text}")
            
            # PRIORITY 2: Face-pile exact employee count (more precise than ranges)
            if not info['company_size'] or "employees" not in info['company_size']:
                face_pile_elements = soup.select(".face-pile__text")
                for element in face_pile_elements:
                    text = element.get_text().strip()
                    # Look for "View all X employees" pattern
                    match = re.search(r'View all ([\d,]+) employees?', text, re.IGNORECASE)
                    if match:
                        count = match.group(1).replace(',', '')
                        info['company_size'] = f"{count} employees"
                        logger.debug(f"Found exact employee count via face-pile: {count}")
                        break
            
            # PRIORITY 3: Followers from h3 elements or follower-specific selectors
            follower_selectors = [
                "h3",  # User mentioned h3 elements contain follower info
                "[data-tracking-control-name*='follower']",
                ".org-top-card-summary__follower-count", 
                "*[class*='follower']"
            ]
            
            for selector in follower_selectors:
                try:
                    elements = soup.select(selector)
                    for element in elements:
                        text = element.get_text().strip()
                        # Look for follower patterns
                        match = re.search(r'([\d,]+(?:\.\d+)?[KMB]?)\s+followers?', text, re.IGNORECASE)
                        if match:
                            info['followers'] = f"{match.group(1)} followers"
                            logger.debug(f"Found followers via {selector}: {match.group(1)}")
                            break
                    if info['followers']:
                        break
                except Exception as e:
                    logger.debug(f"Error with follower selector {selector}: {e}")
                    continue
            
            # PRIORITY 4: Fallback patterns for any missed data
            if not info['company_size'] or not info['followers']:
                page_text = soup.get_text()
                
                # Company size fallback patterns
                if not info['company_size']:
                    size_patterns = [
                        r'View all ([\d,]+) employees?',
                        r'(\d{1,3}(?:,\d{3})*(?:-\d{1,3}(?:,\d{3})*)?)\s+employees?',
                        r'(\d+(?:\.\d+)?[KMB]?)\s+employees?',
                        r'Company size[:\s]*(\d{1,3}(?:,\d{3})*(?:-\d{1,3}(?:,\d{3})*)?)\s+employees?'
                    ]
                    
                    for pattern in size_patterns:
                        match = re.search(pattern, page_text, re.IGNORECASE)
                        if match:
                            count = match.group(1).replace(',', '')
                            info['company_size'] = f"{count} employees"
                            logger.debug(f"Found employee count via fallback pattern: {count}")
                            break
                
                # Followers fallback patterns
                if not info['followers']:
                    follower_patterns = [
                        r'([\d,]+(?:\.\d+)?[KMB]?)\s+followers?',
                        r'Follow[^0-9]*([\d,]+(?:\.\d+)?[KMB]?)\s+followers?'
                    ]
                    
                    for pattern in follower_patterns:
                        match = re.search(pattern, page_text, re.IGNORECASE)
                        if match:
                            info['followers'] = f"{match.group(1)} followers"
                            logger.debug(f"Found followers via fallback pattern: {match.group(1)}")
                            break
            
            # PRIORITY 5: Additional LinkedIn-specific data-test-id attributes for comprehensive extraction
            # Check for other useful company info
            additional_selectors = [
                ("about-us__headquarters", "headquarters"),
                ("about-us__organizationType", "organization_type"), 
                ("about-us__foundedOn", "founded"),
                ("about-us__specialties", "specialties")
            ]
            
            for test_id, field_name in additional_selectors:
                try:
                    section = soup.find(attrs={"data-test-id": test_id})
                    if section:
                        dd_element = section.find("dd")
                        if dd_element:
                            value = dd_element.get_text().strip()
                            if value:
                                logger.debug(f"Found {field_name} via data-test-id: {value}")
                                # We could store these in future expansion
                except Exception as e:
                    logger.debug(f"Error extracting {field_name}: {e}")
                    continue
            
        except Exception as e:
            logger.warning(f"Error extracting company info from job page: {e}")
        
        return info
    
    def _get_company_page_info(self, company_url: str) -> Optional[dict]:
        """Get detailed company information from LinkedIn company page using specific data-test-id selectors"""
        try:
            logger.info(f"Fetching company page: {company_url}")
            response = self.session.get(company_url, timeout=15)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            info = {
                'company_size': None,
                'followers': None,
                'industry': None
            }
            
            # PRIORITY 1: Use LinkedIn's specific data-test-id selectors (most reliable)
            logger.debug("Attempting company page extraction using LinkedIn data-test-id selectors...")
            
            # Company size from data-test-id="about-us__size"
            size_section = soup.find(attrs={"data-test-id": "about-us__size"})
            if size_section:
                size_dd = size_section.find("dd")
                if size_dd:
                    size_text = size_dd.get_text().strip()
                    if size_text and len(size_text) > 0:
                        info['company_size'] = size_text
                        logger.debug(f"Found company size via data-test-id: {size_text}")
            
            # Industry from data-test-id="about-us__industry"
            industry_section = soup.find(attrs={"data-test-id": "about-us__industry"})
            if industry_section:
                industry_dd = industry_section.find("dd")
                if industry_dd:
                    industry_text = industry_dd.get_text().strip()
                    if industry_text and len(industry_text) > 2:
                        info['industry'] = industry_text
                        logger.debug(f"Found industry via data-test-id: {industry_text}")
            
            # PRIORITY 2: Face-pile exact employee count (if data-test-id didn't work or for more precise count)
            if not info['company_size'] or "employees" not in info['company_size']:
                face_pile_elements = soup.select(".face-pile__text")
                for element in face_pile_elements:
                    text = element.get_text().strip()
                    # Look for "View all X employees" pattern
                    match = re.search(r'View all ([\d,]+) employees?', text, re.IGNORECASE)
                    if match:
                        count = match.group(1).replace(',', '')
                        info['company_size'] = f"{count} employees"
                        logger.debug(f"Found exact employee count via face-pile: {count}")
                        break
            
            # PRIORITY 3: Followers from h3 elements and other follower selectors
            follower_selectors = [
                "h3",  # User mentioned h3 elements contain follower info
                "[data-tracking-control-name*='follower']",
                ".org-top-card-summary__follower-count",
                "*[class*='follower']",
                ".artdeco-button--secondary"
            ]
            
            for selector in follower_selectors:
                try:
                    elements = soup.select(selector)
                    for element in elements:
                        text = element.get_text().strip()
                        match = re.search(r'([\d,]+(?:\.\d+)?[KMB]?)\s+followers?', text, re.IGNORECASE)
                        if match:
                            info['followers'] = f"{match.group(1)} followers"
                            logger.debug(f"Found followers via {selector}: {match.group(1)}")
                            break
                    if info['followers']:
                        break
                except Exception as e:
                    logger.debug(f"Error with follower selector {selector}: {e}")
                    continue
            
            # PRIORITY 4: Fallback extraction if data-test-id selectors didn't work
            if not info['company_size'] or not info['followers'] or not info['industry']:
                page_text = soup.get_text()
                
                # Company size fallback
                if not info['company_size']:
                    size_patterns = [
                        r'View all ([\d,]+) employees?',
                        r'(\d{1,3}(?:,\d{3})*(?:-\d{1,3}(?:,\d{3})*)?)\s+employees?',
                        r'Company size[:\s]*(\d{1,3}(?:,\d{3})*(?:-\d{1,3}(?:,\d{3})*)?)',
                        r'(\d+(?:\.\d+)?[KMB]?)\s+employees?'
                    ]
                    
                    for pattern in size_patterns:
                        match = re.search(pattern, page_text, re.IGNORECASE)
                        if match:
                            count = match.group(1).replace(',', '')
                            info['company_size'] = f"{count} employees"
                            logger.debug(f"Found company size via fallback pattern: {count}")
                            break
                
                # Followers fallback
                if not info['followers']:
                    followers_patterns = [
                        r'([\d,]+(?:\.\d+)?[KMB]?)\s+followers?',
                        r'Follow[^0-9]*([\d,]+(?:\.\d+)?[KMB]?)\s+followers?'
                    ]
                    
                    for pattern in followers_patterns:
                        match = re.search(pattern, page_text, re.IGNORECASE)
                        if match:
                            info['followers'] = f"{match.group(1)} followers"
                            logger.debug(f"Found followers via fallback pattern: {match.group(1)}")
                            break
                
                # Industry fallback
                if not info['industry']:
                    # Try old-style industry selectors as fallback
                    industry_selectors = [
                        ".org-top-card-summary__industry",
                        "[data-test='company-industry']",
                        "*[class*='industry']"
                    ]
                    
                    for selector in industry_selectors:
                        try:
                            element = soup.select_one(selector)
                            if element:
                                industry = element.get_text().strip()
                                if not re.search(r'\d+\s+(employees?|followers?)', industry, re.IGNORECASE):
                                    if industry and len(industry) > 2 and len(industry) < 100:
                                        info['industry'] = industry
                                        logger.debug(f"Found industry via fallback {selector}: {industry}")
                                        break
                        except Exception as e:
                            logger.debug(f"Error with fallback industry selector {selector}: {e}")
                            continue
            
            # Add longer delay to be more respectful and avoid rate limiting
            time.sleep(random.uniform(5, 10))
            
            return info if any(info.values()) else None
            
        except Exception as e:
            logger.warning(f"Error fetching company page {company_url}: {e}")
            return None
    
    def parse_and_save_company(self, soup: BeautifulSoup, company_name: str) -> Optional[str]:
        """Parse company information and save to database"""
        try:
            # Check if company already exists
            existing_company = self.database.get_company_by_name(company_name)
            if existing_company:
                logger.debug(f"Company {company_name} already exists in database")
                return existing_company['id']
            
            # Extract company information
            company = self.extract_company_info_from_job_page(soup, company_name)
            if company:
                company_id = self.database.save_company(company)
                logger.info(f"Saved company information for: {company_name}")
                return company_id
            else:
                logger.debug(f"No additional company information found for: {company_name}")
                # Still create a basic company record
                basic_company = Company(company_name=company_name)
                company_id = self.database.save_company(basic_company)
                return company_id
                
        except Exception as e:
            logger.error(f"Error parsing and saving company {company_name}: {e}")
            return None


def main():
    """Test the company parser with sample data"""
    parser = LinkedInCompanyParser()
    
    # This would be called with actual BeautifulSoup object from job page
    print("LinkedIn Company Parser initialized successfully")
    print("Use parser.parse_and_save_company(soup, company_name) to extract company info")


if __name__ == "__main__":
    main()
