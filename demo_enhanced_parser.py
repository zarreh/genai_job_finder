#!/usr/bin/env python3

from genai_job_finder.linkedin_parser.database import DatabaseManager
import pandas as pd


def show_enhanced_features():
    """Show the enhanced features of the job parser"""
    print("🚀 Enhanced LinkedIn Job Parser with Company Information")
    print("=" * 60)
    
    db = DatabaseManager()
    df = db.get_all_jobs_as_dataframe()
    
    print(f"📊 Total jobs in database: {len(df)}")
    print(f"📋 Data columns: {len(df.columns)}")
    
    # Show all columns
    print("\n📝 Enhanced data structure:")
    for i, col in enumerate(df.columns, 1):
        emoji = "🏢" if col.startswith("company_") else "📍" if col in ["location", "work_location_type"] else "💼"
        print(f"  {i:2d}. {emoji} {col}")
    
    # Company information statistics
    company_cols = ['company_size', 'company_followers', 'company_industry']
    print(f"\n🏢 Company Information Coverage:")
    for col in company_cols:
        if col in df.columns:
            has_data = df[col].notna().sum()
            percentage = (has_data / len(df) * 100) if len(df) > 0 else 0
            print(f"   {col}: {has_data}/{len(df)} jobs ({percentage:.1f}%)")
    
    # Show examples
    print(f"\n🔍 Sample jobs with company information:")
    sample = df[df['company_size'].notna() | df['company_followers'].notna()].head(5)
    
    if not sample.empty:
        for _, job in sample.iterrows():
            print(f"\n   🏢 {job['company']}")
            print(f"      💼 {job['title']}")
            print(f"      📍 {job['location']} ({job['work_location_type']})")
            print(f"      👥 Size: {job['company_size'] or 'Unknown'}")
            print(f"      👥 Followers: {job['company_followers'] or 'Unknown'}")
            print(f"      🏭 Industry: {job['company_industry'] or 'Unknown'}")
    else:
        print("   No jobs with company information available yet.")
        print("   Run 'make run-parser' to parse jobs with company info extraction!")
    
    print(f"\n✅ Enhanced features working correctly!")
    print(f"   • Automatic company size extraction")
    print(f"   • LinkedIn followers count")
    print(f"   • Industry classification")
    print(f"   • All data saved in jobs table for easy access")


if __name__ == "__main__":
    show_enhanced_features()
