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
                # If we have a company link, try to get detailed info from company page
                detailed_info = self._get_company_page_info(company_link)
                if detailed_info:
                    company_info.update(detailed_info)
            
            # If we couldn't get detailed info, try to extract from job page itself
            if not company_info['company_size'] or not company_info['followers']:
                job_page_info = self._extract_company_info_from_job_page_content(soup)
                for key, value in job_page_info.items():
                    if value and not company_info[key]:
                        company_info[key] = value
            
            # Create Company object if we have at least some information
            if any([company_info['company_size'], company_info['followers'], company_info['industry']]):
                return Company(
                    company_name=company_info['company_name'],
                    company_size=company_info['company_size'],
                    followers=company_info['followers'],
                    industry=company_info['industry'],
                    company_url=company_info['company_url']
                )
            
            return None
            
        except Exception as e:
            logger.error(f"Error extracting company info for {company_name}: {e}")
            return None
    
    def _extract_company_link(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract company profile link from job page"""
        try:
            # Look for company link in various locations
            selectors = [
                "a[href*='/company/']",
                ".topcard__org-name-link",
                ".top-card-layout__card a[href*='/company/']",
                "a[data-tracking-control-name='public_jobs_topcard-org-name']"
            ]
            
            for selector in selectors:
                element = soup.select_one(selector)
                if element and element.get('href'):
                    href = element.get('href')
                    if '/company/' in href:
                        # Ensure it's a full URL
                        if href.startswith('http'):
                            return href
                        else:
                            return urljoin('https://www.linkedin.com', href)
            
            return None
            
        except Exception as e:
            logger.warning(f"Error extracting company link: {e}")
            return None
    
    def _extract_company_info_from_job_page_content(self, soup: BeautifulSoup) -> dict:
        """Extract company info directly from job page content"""
        info = {
            'company_size': None,
            'followers': None,
            'industry': None
        }
        
        try:
            # Look for company size patterns in the page text
            page_text = soup.get_text()
            
            # Company size patterns
            size_patterns = [
                r'(\d{1,3}(?:,\d{3})*(?:-\d{1,3}(?:,\d{3})*)?)\s+employees?',
                r'(\d+(?:\.\d+)?[KMB]?)\s+employees?',
                r'Company size[:\s]*(\d{1,3}(?:,\d{3})*(?:-\d{1,3}(?:,\d{3})*)?)\s+employees?'
            ]
            
            for pattern in size_patterns:
                match = re.search(pattern, page_text, re.IGNORECASE)
                if match:
                    info['company_size'] = f"{match.group(1)} employees"
                    break
            
            # Followers patterns
            follower_patterns = [
                r'(\d{1,3}(?:,\d{3})*(?:\.\d+)?[KMB]?)\s+followers?',
                r'(\d+(?:\.\d+)?[KMB]?)\s+followers?'
            ]
            
            for pattern in follower_patterns:
                match = re.search(pattern, page_text, re.IGNORECASE)
                if match:
                    info['followers'] = f"{match.group(1)} followers"
                    break
            
            # Try to extract industry from job criteria if available
            try:
                industries_elem = soup.find("li", string=re.compile("Industries", re.IGNORECASE))
                if industries_elem:
                    # Get the next text content which should be the industry
                    industry_text = industries_elem.get_text()
                    industry = industry_text.replace("Industries", "").strip()
                    if industry:
                        info['industry'] = industry
            except:
                pass
            
        except Exception as e:
            logger.warning(f"Error extracting company info from job page: {e}")
        
        return info
    
    def _get_company_page_info(self, company_url: str) -> Optional[dict]:
        """Get detailed company information from LinkedIn company page"""
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
            
            # Extract company size
            size_element = soup.find(string=re.compile(r'\d+(?:-\d+)?\s+employees?', re.IGNORECASE))
            if size_element:
                size_match = re.search(r'(\d+(?:-\d+)?)\s+employees?', size_element, re.IGNORECASE)
                if size_match:
                    info['company_size'] = f"{size_match.group(1)} employees"
            
            # Extract followers
            followers_element = soup.find(string=re.compile(r'\d+(?:\.\d+)?[KMB]?\s+followers?', re.IGNORECASE))
            if followers_element:
                followers_match = re.search(r'(\d+(?:\.\d+)?[KMB]?)\s+followers?', followers_element, re.IGNORECASE)
                if followers_match:
                    info['followers'] = f"{followers_match.group(1)} followers"
            
            # Extract industry
            # Look for industry information in various selectors
            industry_selectors = [
                ".org-top-card-summary__industry",
                "[data-test='company-industry']",
                ".org-about-company-module__company-size-definition-term:contains('Industry') + dd"
            ]
            
            for selector in industry_selectors:
                try:
                    element = soup.select_one(selector)
                    if element:
                        industry = element.get_text().strip()
                        if industry and len(industry) > 2:
                            info['industry'] = industry
                            break
                except:
                    continue
            
            # Add delay to be respectful
            time.sleep(random.uniform(2, 4))
            
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
