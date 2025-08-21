#!/usr/bin/env python3
"""
Debug script to test LinkedIn parser directly
"""
import sys
import os
import logging

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from genai_job_finder.linkedin_parser.parser import LinkedInJobParser
from genai_job_finder.linkedin_parser.database import DatabaseManager

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_parser():
    """Test the LinkedIn parser with various scenarios"""
    
    print("🧪 DEBUG: Starting LinkedIn parser test...")
    
    # Test 1: Empty location
    print("\n📍 Test 1: Empty location")
    try:
        db_path = os.path.join(os.path.dirname(__file__), "data", "test_jobs.db")
        print(f"Database path: {db_path}")
        
        db_manager = DatabaseManager(db_path)
        parser = LinkedInJobParser(database=db_manager)
        
        # Test URL building
        test_url = parser._build_url("software engineer", "", 0)
        print(f"Generated URL for empty location: {test_url}")
        
        # Test with 1 page only
        jobs = parser.parse_jobs(
            search_query="software engineer",
            location="",
            max_pages=1
        )
        
        print(f"✅ Test 1 completed: Found {len(jobs)} jobs with empty location")
        
    except Exception as e:
        print(f"❌ Test 1 failed: {e}")
        import traceback
        traceback.print_exc()
    
    # Test 2: Case sensitivity
    print("\n🔤 Test 2: Case sensitivity")
    try:
        jobs_upper = parser.parse_jobs(
            search_query="SOFTWARE ENGINEER",
            location="SAN FRANCISCO",
            max_pages=1
        )
        
        jobs_lower = parser.parse_jobs(
            search_query="software engineer",
            location="san francisco",
            max_pages=1
        )
        
        print(f"✅ Test 2 completed:")
        print(f"   Upper case: {len(jobs_upper)} jobs")
        print(f"   Lower case: {len(jobs_lower)} jobs")
        
    except Exception as e:
        print(f"❌ Test 2 failed: {e}")
        import traceback
        traceback.print_exc()
    
    # Test 3: Direct HTTP request
    print("\n🌐 Test 3: Direct HTTP request")
    try:
        import requests
        from bs4 import BeautifulSoup
        
        session = requests.Session()
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        }
        session.headers.update(headers)
        
        test_url = "https://www.linkedin.com/jobs/search/?keywords=software%20engineer"
        print(f"Testing direct request to: {test_url}")
        
        response = session.get(test_url, timeout=15)
        print(f"HTTP Status: {response.status_code}")
        print(f"Response length: {len(response.content)}")
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            job_cards = soup.select('div.job-search-card')
            print(f"Found {len(job_cards)} job cards with selector 'div.job-search-card'")
            
            # Try alternative selectors
            alt_selectors = [
                'div.base-card',
                'div.result-card', 
                'article.job-card',
                'div[data-job-id]'
            ]
            
            for selector in alt_selectors:
                cards = soup.select(selector)
                print(f"Found {len(cards)} cards with selector '{selector}'")
        
        print("✅ Test 3 completed")
        
    except Exception as e:
        print(f"❌ Test 3 failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_parser()
