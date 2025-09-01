#!/usr/bin/env python3
"""
Comprehensive LinkedIn job parser with integrated company intelligence.
This single script handles all data extraction with proper rate limiting.

Usage: 
  python -m genai_job_finder.linkedin_parser.run_parser
  python run_parser.py

Features:
- ✅ Job data extraction with 20-column output
- ✅ Integrated company intelligence (size, followers, industry)
- ✅ Location intelligence and work type classification  
- ✅ Smart rate limiting to avoid LinkedIn restrictions
- ✅ Automatic CSV export
- ✅ Progress tracking and error handling
"""

import argparse
import logging
from .parser import LinkedInJobParser
from .database import DatabaseManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Run the comprehensive LinkedIn job parser with integrated company intelligence."""
    parser = argparse.ArgumentParser(description="LinkedIn Job Parser with Company Intelligence")
    parser.add_argument("--search-query", default="data scientist", help="Job search query")
    parser.add_argument("--location", default="San Antonio", help="Location filter")
    parser.add_argument("--total-jobs", type=int, default=50, help="Total jobs to parse")
    parser.add_argument("--time-filter", default="r86400", help="Time filter (r86400=24h, r604800=7d)")
    parser.add_argument("--remote", action="store_true", help="Include remote jobs")
    parser.add_argument("--parttime", action="store_true", help="Include part-time jobs")
    parser.add_argument("--db-path", default="data/jobs.db", help="Database path")
    parser.add_argument("--export-csv", default="data/jobs_export.csv", help="CSV export path")
    
    args = parser.parse_args()
    
    print("🚀 COMPREHENSIVE LINKEDIN JOB PARSER")
    print("=" * 50)
    print(f"🔍 Search Query: {args.search_query}")
    print(f"📍 Location: {args.location}")
    print(f"📊 Target Jobs: {args.total_jobs}")
    print(f"⏰ Time Filter: {args.time_filter}")
    print(f"🏠 Remote: {'Yes' if args.remote else 'No'}")
    print(f"⏰ Part-time: {'Yes' if args.parttime else 'No'}")
    print()
    
    print("✨ FEATURES ENABLED:")
    print("   🎯 Job data extraction (20-column output)")
    print("   🏢 Company intelligence (size, followers, industry)")
    print("   📍 Location intelligence & work type classification")
    print("   🛡️ Smart rate limiting (5-10s delays)")
    print("   📤 Automatic CSV export")
    print("   📊 Progress tracking")
    print()
    
    try:
        # Initialize database and parser
        db = DatabaseManager(args.db_path)
        job_parser = LinkedInJobParser(database=db)
        
        # Parse jobs with comprehensive data extraction
        print("🚀 Starting comprehensive job parsing...")
        jobs = job_parser.parse_jobs(
            search_query=args.search_query,
            location=args.location,
            total_jobs=args.total_jobs,
            time_filter=args.time_filter,
            remote=args.remote,
            parttime=args.parttime
        )
        
        print(f"\n✅ PARSING COMPLETE!")
        print(f"📊 Successfully parsed: {len(jobs)} jobs")
        print(f"💾 Saved to database: {args.db_path}")
        
        # Export to CSV with all enhanced data
        print(f"\n📤 Exporting to CSV...")
        csv_file = db.export_jobs_to_csv(args.export_csv)
        if csv_file:
            print(f"✅ Enhanced data exported to: {csv_file}")
            print(f"📋 Features: 20-column output with company intelligence")
        else:
            print("📊 Data saved to database only")
            
        # Show summary statistics
        print(f"\n📈 SUMMARY STATISTICS:")
        with db.get_connection() as conn:
            cursor = conn.cursor()
            
            # Job statistics
            cursor.execute("SELECT COUNT(*) FROM jobs")
            total_jobs = cursor.fetchone()[0]
            print(f"   Total jobs in database: {total_jobs}")
            
            # Company intelligence coverage
            cursor.execute("""
                SELECT 
                    COUNT(CASE WHEN company_size IS NOT NULL THEN 1 END) as with_size,
                    COUNT(CASE WHEN company_followers IS NOT NULL THEN 1 END) as with_followers,
                    COUNT(CASE WHEN company_industry IS NOT NULL THEN 1 END) as with_industry
                FROM jobs 
                WHERE id IN (SELECT id FROM jobs ORDER BY created_at DESC LIMIT ?)
            """, (len(jobs),))
            stats = cursor.fetchone()
            
            print(f"   📊 Company intelligence (last {len(jobs)} jobs):")
            print(f"      � Company size: {stats[0]}/{len(jobs)} jobs ({stats[0]/len(jobs)*100:.1f}%)")
            print(f"      📈 Company followers: {stats[1]}/{len(jobs)} jobs ({stats[1]/len(jobs)*100:.1f}%)")
            print(f"      🏭 Company industry: {stats[2]}/{len(jobs)} jobs ({stats[2]/len(jobs)*100:.1f}%)")
            
            # Work type distribution
            cursor.execute("""
                SELECT work_location_type, COUNT(*) 
                FROM jobs 
                WHERE work_location_type IS NOT NULL 
                  AND id IN (SELECT id FROM jobs ORDER BY created_at DESC LIMIT ?)
                GROUP BY work_location_type
            """, (len(jobs),))
            work_types = cursor.fetchall()
            
            if work_types:
                print(f"   🏠 Work location types:")
                for work_type, count in work_types:
                    emoji = {"Remote": "🏠", "Hybrid": "🔄", "On-site": "🏢"}.get(work_type, "📍")
                    print(f"      {emoji} {work_type}: {count} jobs")
        
        print(f"\n🎉 SUCCESS: Comprehensive parsing with company intelligence complete!")
        print(f"💡 Next steps:")
        print(f"   📊 Analyze data: Open notebooks/job_analysis.ipynb")
        print(f"   🧹 Clean data: make run-cleaner")
        print(f"   🌐 Frontend: make run-frontend")
        
    except Exception as e:
        logger.error(f"Error during parsing: {e}")
        print(f"❌ Parsing failed: {e}")
        print(f"💡 Try reducing --total-jobs or check network connection")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
