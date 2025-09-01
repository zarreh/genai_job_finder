"""
Company enrichment service for LinkedIn parser.
Manages company information in a separate pipeline to avoid redundant parsing.
"""

import logging
import time
from typing import Optional, Dict, Any, List
from dataclasses import dataclass

from .models import Company
from .database import DatabaseManager
from .company_parser import LinkedInCompanyParser

logger = logging.getLogger(__name__)


@dataclass
class CompanyEnrichmentResult:
    """Result of company enrichment operation"""
    company_id: str
    was_existing: bool
    was_enriched: bool
    error: Optional[str] = None


class CompanyEnrichmentService:
    """
    Service to manage company information enrichment.
    Uses a lookup-first approach to avoid redundant parsing.
    """
    
    def __init__(self, db_path: str = "data/jobs.db", database: Optional[DatabaseManager] = None):
        # Support both legacy (db_path) and new (database) initialization
        if database:
            self.database = database
        else:
            self.database = DatabaseManager(db_path)
        self.company_parser = LinkedInCompanyParser(database=self.database)
        self.enriched_count = 0
        self.failed_count = 0
        
    def get_or_enrich_company(self, company_name: str, job_soup=None) -> CompanyEnrichmentResult:
        """
        Get company information from database or enrich if not exists.
        
        Args:
            company_name: Name of the company
            job_soup: BeautifulSoup object from job page (optional, for company link extraction)
            
        Returns:
            CompanyEnrichmentResult with company_id and enrichment status
        """
        try:
            # First, check if company exists in database
            existing_company = self.database.get_company_by_name(company_name)
            
            if existing_company:
                # Company exists - check if it needs enrichment
                if self._needs_enrichment(existing_company):
                    logger.debug(f"Company {company_name} exists but needs enrichment")
                    return self._enrich_existing_company(existing_company, job_soup)
                else:
                    logger.debug(f"Company {company_name} already fully enriched")
                    return CompanyEnrichmentResult(
                        company_id=existing_company['id'],
                        was_existing=True,
                        was_enriched=False
                    )
            else:
                # Company doesn't exist - create and enrich
                logger.debug(f"Company {company_name} not found, creating new entry")
                return self._create_and_enrich_company(company_name, job_soup)
                
        except Exception as e:
            logger.error(f"Error enriching company {company_name}: {e}")
            # Create basic company record as fallback
            basic_company = Company(company_name=company_name)
            company_id = self.database.save_company(basic_company)
            return CompanyEnrichmentResult(
                company_id=company_id,
                was_existing=False,
                was_enriched=False,
                error=str(e)
            )
    
    def _needs_enrichment(self, company_data: Dict[str, Any]) -> bool:
        """
        Check if a company needs enrichment (missing key information).
        
        Args:
            company_data: Company data from database
            
        Returns:
            True if company needs enrichment, False otherwise
        """
        # Consider a company "enriched" if it has at least one of the key fields
        key_fields = ['company_size', 'followers', 'industry', 'company_url']
        has_any_info = any(company_data.get(field) for field in key_fields)
        
        # Also check if data is too old (older than 30 days) - optional future enhancement
        # For now, we'll consider any company with some info as "enriched"
        
        return not has_any_info
    
    def _enrich_existing_company(self, existing_company: Dict[str, Any], job_soup=None) -> CompanyEnrichmentResult:
        """
        Enrich an existing company with more information.
        
        Args:
            existing_company: Existing company data from database
            job_soup: BeautifulSoup object from job page (optional)
            
        Returns:
            CompanyEnrichmentResult
        """
        try:
            company_name = existing_company['company_name']
            
            if job_soup:
                # Try to extract company information from job page
                company_info = self.company_parser.extract_company_info_from_job_page(job_soup, company_name)
                if company_info:
                    # Update the existing company with new information
                    company_id = self.database.save_company(company_info)
                    logger.info(f"Enriched existing company: {company_name}")
                    return CompanyEnrichmentResult(
                        company_id=company_id,
                        was_existing=True,
                        was_enriched=True
                    )
            
            # If we couldn't enrich, return the existing company
            return CompanyEnrichmentResult(
                company_id=existing_company['id'],
                was_existing=True,
                was_enriched=False
            )
            
        except Exception as e:
            logger.warning(f"Failed to enrich existing company {existing_company['company_name']}: {e}")
            return CompanyEnrichmentResult(
                company_id=existing_company['id'],
                was_existing=True,
                was_enriched=False,
                error=str(e)
            )
    
    def _create_and_enrich_company(self, company_name: str, job_soup=None) -> CompanyEnrichmentResult:
        """
        Create a new company and enrich it with information.
        
        Args:
            company_name: Name of the company
            job_soup: BeautifulSoup object from job page (optional)
            
        Returns:
            CompanyEnrichmentResult
        """
        try:
            if job_soup:
                # Try to extract company information from job page
                company_info = self.company_parser.extract_company_info_from_job_page(job_soup, company_name)
                if company_info:
                    company_id = self.database.save_company(company_info)
                    logger.info(f"Created and enriched new company: {company_name}")
                    return CompanyEnrichmentResult(
                        company_id=company_id,
                        was_existing=False,
                        was_enriched=True
                    )
            
            # Create basic company record if we couldn't extract info
            basic_company = Company(company_name=company_name)
            company_id = self.database.save_company(basic_company)
            logger.debug(f"Created basic company record: {company_name}")
            return CompanyEnrichmentResult(
                company_id=company_id,
                was_existing=False,
                was_enriched=False
            )
            
        except Exception as e:
            logger.error(f"Failed to create and enrich company {company_name}: {e}")
            raise
    
    def bulk_enrich_companies(self, company_names: List[str], force_refresh: bool = False) -> Dict[str, CompanyEnrichmentResult]:
        """
        Enrich multiple companies in bulk.
        
        Args:
            company_names: List of company names to enrich
            force_refresh: If True, re-enrich even if companies exist
            
        Returns:
            Dictionary mapping company names to enrichment results
        """
        import random
        
        results = {}
        
        for i, company_name in enumerate(company_names):
            try:
                logger.info(f"Enriching company {i+1}/{len(company_names)}: {company_name}")
                
                if force_refresh:
                    # Force re-enrichment by extracting fresh data
                    result = self._create_and_enrich_company(company_name)
                else:
                    # Use normal lookup-first approach
                    result = self.get_or_enrich_company(company_name)
                
                results[company_name] = result
                
                # Add delay between company enrichments to be respectful
                if i < len(company_names) - 1:  # Don't delay after the last one
                    delay = 8  # 8 seconds between company enrichments
                    logger.debug(f"Waiting {delay} seconds before next company...")
                    time.sleep(delay)
                    
            except Exception as e:
                logger.error(f"Error enriching company {company_name}: {e}")
                results[company_name] = CompanyEnrichmentResult(
                    company_id="",
                    was_existing=False,
                    was_enriched=False,
                    error=str(e)
                )
        
        return results
    
    def get_companies_needing_enrichment(self) -> List[Dict[str, Any]]:
        """
        Get list of companies that need enrichment.
        
        Returns:
            List of company records that need enrichment
        """
        all_companies = self.database.get_all_companies()
        return [company for company in all_companies if self._needs_enrichment(company)]
    
    def get_enrichment_stats(self) -> Dict[str, int]:
        """
        Get statistics about company enrichment status.
        
        Returns:
            Dictionary with enrichment statistics
        """
        all_companies = self.database.get_all_companies()
        
        total = len(all_companies)
        enriched = len([c for c in all_companies if not self._needs_enrichment(c)])
        needs_enrichment = total - enriched
        
        return {
            'total_companies': total,
            'enriched_companies': enriched,
            'companies_needing_enrichment': needs_enrichment,
            'enrichment_percentage': round((enriched / total * 100) if total > 0 else 0, 1)
        }

    # Legacy methods for compatibility with existing scripts
    def get_companies_needing_enrichment_legacy(self) -> List[Dict[str, Any]]:
        """Get list of companies that need additional information (legacy compatibility)"""
        with self.database.get_connection() as conn:
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
        return self.database.get_all_companies()
    
    def get_companies_from_jobs(self) -> List[str]:
        """Get unique company names from jobs that don't have company records"""
        with self.database.get_connection() as conn:
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
        """Enrich a specific company by name (legacy compatibility)"""
        import random
        
        try:
            logger.info(f"Enriching company: {company_name}")
            
            # Check if company already has complete information
            existing = self.database.get_company_by_name(company_name)
            if existing and not force:
                if all([existing.get('company_size'), existing.get('followers'), existing.get('industry')]):
                    logger.info(f"Company {company_name} already has complete information")
                    return True
            
            # Try to get a recent job posting for this company to extract info
            with self.database.get_connection() as conn:
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
        """Enrich all companies that need additional information (legacy compatibility)"""
        companies_to_enrich = self.get_companies_needing_enrichment_legacy()
        
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
                basic_company = Company(company_name=company_name)
                self.database.save_company(basic_company)
                created_count += 1
                logger.info(f"Created basic record for: {company_name}")
            except Exception as e:
                logger.error(f"Error creating record for {company_name}: {e}")
        
        return created_count
    
    def show_statistics(self):
        """Show company enrichment statistics"""
        all_companies = self.get_all_companies()
        companies_needing_enrichment = self.get_companies_needing_enrichment_legacy()
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
    """CLI for company enrichment service"""
    import argparse
    
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
