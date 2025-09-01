#!/usr/bin/env python3
"""
LinkedIn Company Information Enrichment Script

This script enriches existing job data with detailed company information including:
- Company size (number of employees)
- Number of followers
- Industry information

Usage:
    python company_enrichment.py [options]

Examples:
    # Enrich all companies in database
    python company_enrichment.py
    
    # Enrich specific company
    python company_enrichment.py --company "Microsoft"
    
    # Show companies that need enrichment
    python company_enrichment.py --show-missing
"""

import argparse
import logging
import sys
from pathlib import Path
from typing import List, Dict, Any
import time
import random

# Add the project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from genai_job_finder.linkedin_parser.database import DatabaseManager
from genai_job_finder.linkedin_parser.company_parser import LinkedInCompanyParser

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class CompanyEnrichmentService:
    """Service for enriching company data from LinkedIn"""
    
    def __init__(self, db_path: str = "data/jobs.db"):
        self.db = DatabaseManager(db_path)
        self.company_parser = LinkedInCompanyParser(self.db)
        self.enriched_count = 0
        self.failed_count = 0
    
    def get_companies_needing_enrichment(self) -> List[Dict[str, Any]]:
        """Get list of companies that need additional information"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            
            # Get companies with missing information
            cursor.execute('''
                SELECT DISTINCT c.*, 
                       COUNT(j.id) as job_count
                FROM companies c
                LEFT JOIN jobs j ON c.id = j.company_id
                WHERE c.company_size IS NULL 
                   OR c.followers IS NULL 
                   OR c.industry IS NULL
                GROUP BY c.id, c.company_name
                ORDER BY job_count DESC, c.company_name
            ''')
            
            return [dict(row) for row in cursor.fetchall()]
    
    def get_all_companies(self) -> List[Dict[str, Any]]:
        """Get all companies in database"""
        return self.db.get_all_companies()
    
    def get_companies_from_jobs(self) -> List[str]:
        """Get unique company names from jobs that don't have company records"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT DISTINCT j.company
                FROM jobs j
                LEFT JOIN companies c ON j.company = c.company_name
                WHERE c.id IS NULL
                ORDER BY j.company
            ''')
            
            return [row[0] for row in cursor.fetchall()]
    
    def enrich_company_by_name(self, company_name: str, force: bool = False) -> bool:
        """Enrich a specific company by name"""
        try:
            logger.info(f"Enriching company: {company_name}")
            
            # Check if company already has complete information
            existing = self.db.get_company_by_name(company_name)
            if existing and not force:
                if all([existing.get('company_size'), existing.get('followers'), existing.get('industry')]):
                    logger.info(f"Company {company_name} already has complete information")
                    return True
            
            # Try to get a recent job posting for this company to extract info
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT job_posting_link 
                    FROM jobs 
                    WHERE company = ? 
                    AND job_posting_link IS NOT NULL 
                    AND job_posting_link != 'N/A'
                    ORDER BY created_at DESC 
                    LIMIT 1
                ''', (company_name,))
                
                result = cursor.fetchone()
                if not result:
                    logger.warning(f"No job posting link found for {company_name}")
                    return False
                
                job_link = result[0]
                logger.info(f"Using job posting: {job_link}")
            
            # Fetch the job page and extract company info
            response = self.company_parser.session.get(job_link, timeout=15)
            response.raise_for_status()
            
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract and save company information
            company_id = self.company_parser.parse_and_save_company(soup, company_name)
            
            if company_id:
                self.enriched_count += 1
                logger.info(f"✅ Successfully enriched: {company_name}")
                
                # Add respectful delay
                time.sleep(random.uniform(2, 5))
                return True
            else:
                self.failed_count += 1
                logger.warning(f"❌ Failed to enrich: {company_name}")
                return False
                
        except Exception as e:
            self.failed_count += 1
            logger.error(f"❌ Error enriching {company_name}: {e}")
            return False
    
    def enrich_all_companies(self, limit: int = None) -> Dict[str, int]:
        """Enrich all companies that need additional information"""
        companies_to_enrich = self.get_companies_needing_enrichment()
        
        if limit:
            companies_to_enrich = companies_to_enrich[:limit]
        
        logger.info(f"Found {len(companies_to_enrich)} companies needing enrichment")
        
        for i, company in enumerate(companies_to_enrich, 1):
            logger.info(f"Processing {i}/{len(companies_to_enrich)}: {company['company_name']}")
            self.enrich_company_by_name(company['company_name'])
            
            # Progress update every 5 companies
            if i % 5 == 0:
                logger.info(f"Progress: {i}/{len(companies_to_enrich)} - Success: {self.enriched_count}, Failed: {self.failed_count}")
        
        return {
            'total_processed': len(companies_to_enrich),
            'enriched': self.enriched_count,
            'failed': self.failed_count
        }
    
    def create_missing_company_records(self) -> int:
        """Create basic company records for companies found in jobs but not in companies table"""
        missing_companies = self.get_companies_from_jobs()
        created_count = 0
        
        logger.info(f"Found {len(missing_companies)} companies without records")
        
        for company_name in missing_companies:
            try:
                from genai_job_finder.linkedin_parser.models import Company
                basic_company = Company(company_name=company_name)
                self.db.save_company(basic_company)
                created_count += 1
                logger.info(f"Created basic record for: {company_name}")
            except Exception as e:
                logger.error(f"Error creating record for {company_name}: {e}")
        
        return created_count
    
    def show_statistics(self):
        """Show company enrichment statistics"""
        all_companies = self.get_all_companies()
        companies_needing_enrichment = self.get_companies_needing_enrichment()
        missing_companies = self.get_companies_from_jobs()
        
        total_companies = len(all_companies)
        complete_companies = total_companies - len(companies_needing_enrichment)
        
        print("\n📊 Company Enrichment Statistics")
        print("=" * 50)
        print(f"Total companies in database: {total_companies}")
        print(f"Companies with complete info: {complete_companies}")
        print(f"Companies needing enrichment: {len(companies_needing_enrichment)}")
        print(f"Companies missing records: {len(missing_companies)}")
        
        if companies_needing_enrichment:
            print(f"\n🔍 Companies needing enrichment (top 10):")
            for company in companies_needing_enrichment[:10]:
                missing_fields = []
                if not company.get('company_size'):
                    missing_fields.append('size')
                if not company.get('followers'):
                    missing_fields.append('followers')
                if not company.get('industry'):
                    missing_fields.append('industry')
                
                print(f"  • {company['company_name']} ({company['job_count']} jobs) - Missing: {', '.join(missing_fields)}")
        
        if missing_companies:
            print(f"\n❌ Companies without records (top 10):")
            for company in missing_companies[:10]:
                print(f"  • {company}")


def main():
    parser = argparse.ArgumentParser(description='Enrich LinkedIn company information')
    parser.add_argument('--company', type=str, help='Enrich specific company by name')
    parser.add_argument('--limit', type=int, help='Limit number of companies to process')
    parser.add_argument('--force', action='store_true', help='Force re-enrichment even if data exists')
    parser.add_argument('--show-missing', action='store_true', help='Show companies that need enrichment')
    parser.add_argument('--create-missing', action='store_true', help='Create basic records for missing companies')
    parser.add_argument('--db-path', type=str, default='data/jobs.db', help='Path to database file')
    
    args = parser.parse_args()
    
    # Initialize service
    service = CompanyEnrichmentService(args.db_path)
    
    try:
        if args.show_missing:
            service.show_statistics()
            return
        
        if args.create_missing:
            created = service.create_missing_company_records()
            logger.info(f"Created {created} basic company records")
            return
        
        if args.company:
            # Enrich specific company
            success = service.enrich_company_by_name(args.company, args.force)
            if success:
                logger.info(f"✅ Successfully enriched {args.company}")
            else:
                logger.error(f"❌ Failed to enrich {args.company}")
        else:
            # Enrich all companies
            logger.info("🚀 Starting company enrichment process...")
            results = service.enrich_all_companies(args.limit)
            
            logger.info("\n📊 Enrichment Complete!")
            logger.info(f"Total processed: {results['total_processed']}")
            logger.info(f"Successfully enriched: {results['enriched']}")
            logger.info(f"Failed: {results['failed']}")
            
            if results['enriched'] > 0:
                success_rate = (results['enriched'] / results['total_processed']) * 100
                logger.info(f"Success rate: {success_rate:.1f}%")
    
    except KeyboardInterrupt:
        logger.info("\n⏹️  Process interrupted by user")
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")


if __name__ == "__main__":
    main()
