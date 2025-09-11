#!/usr/bin/env python3
"""
Configuration manager for LinkedIn job parser.
Allows easy modification of search parameters without editing code.

Usage:
    python -m genai_job_finder.linkedin_parser.config_manager --show
    python -m genai_job_finder.linkedin_parser.config_manager --set-defaults
    python -m genai_job_finder.linkedin_parser.config_manager --add-search "Software Engineer" "Austin" --remote --jobs 100
"""

import argparse
import os
import sys
from typing import Dict, Any
from .config import ParserConfig, SearchParams, LINKEDIN_JOB_SEARCH_PARAMS, TIME_FILTERS


class ConfigManager:
    """Manage LinkedIn parser configuration"""
    
    def __init__(self):
        self.config = ParserConfig.from_env()
    
    def show_current_config(self):
        """Display current configuration"""
        print("🔧 CURRENT LINKEDIN PARSER CONFIGURATION")
        print("=" * 50)
        print()
        
        # Show the active search parameters from config
        try:
            base_search_params = self.config.get_search_params()
            print("📊 CURRENT SEARCH PARAMETERS (from config.py):")
            print(f"   🔍 Search Query: {base_search_params.keywords}")
            print(f"   📍 Location: {base_search_params.location}")
            print(f"   📊 Total Jobs: {base_search_params.total_jobs}")
            print(f"   ⏰ Time Filter: {base_search_params.time_filter}")
            print(f"   🏠 Remote: {'Yes' if base_search_params.remote else 'No'}")
            print(f"   ⏰ Part-time: {'Yes' if base_search_params.parttime else 'No'}")
        except ValueError:
            print("📊 SEARCH PARAMETERS:")
            print("   ❌ No search configurations found in LINKEDIN_JOB_SEARCH_PARAMS")
            print("   💡 Please add at least one SearchParams entry to config.py")
        print()
        
        print("🗃️ DATABASE & EXPORT:")
        print(f"   💾 Database Path: {self.config.database_path}")
        print(f"   📤 CSV Export Path: {self.config.export_csv_path}")
        print()
        
        print("🕸️ SCRAPING SETTINGS:")
        print(f"   🖥️ Headless Browser: {'Yes' if self.config.headless_browser else 'No'}")
        print(f"   ⏱️ Page Timeout: {self.config.page_timeout}s")
        print(f"   📄 Max Pages: {self.config.max_pages_per_search}")
        print(f"   ⏳ Request Delay: {self.config.delay_between_requests}s")
        print()
        
        print("🔍 PREDEFINED SEARCH CONFIGURATIONS:")
        for i, search_param in enumerate(LINKEDIN_JOB_SEARCH_PARAMS, 1):
            print(f"   {i}. {search_param.keywords} in {search_param.location}")
            print(f"      Time: {search_param.time_filter}, Remote: {search_param.remote}, "
                  f"Part-time: {search_param.parttime}, Jobs: {search_param.total_jobs}")
        print()
        
        print("⏰ AVAILABLE TIME FILTERS:")
        for name, code in TIME_FILTERS.items():
            print(f"   {name}: {code}")
    
    def show_env_variables(self):
        """Show how to set environment variables to customize config"""
        print("🌍 CONFIGURATION SETUP")
        print("=" * 50)
        print()
        print("📝 SEARCH PARAMETERS are now configured in config.py file:")
        print("   Edit LINKEDIN_JOB_SEARCH_PARAMS list in genai_job_finder/linkedin_parser/config.py")
        print("   The first entry in the list becomes your default search configuration.")
        print()
        print("🌍 ENVIRONMENT VARIABLES for system settings:")
        print()
        print("# Database and export:")
        print(f'export JOB_DB_PATH="{self.config.database_path}"')
        print(f'export EXPORT_CSV_PATH="{self.config.export_csv_path}"')
        print()
        print("# Scraping settings:")
        print(f'export HEADLESS_BROWSER="{str(self.config.headless_browser).lower()}"')
        print(f'export PAGE_TIMEOUT="{self.config.page_timeout}"')
        print(f'export MAX_PAGES="{self.config.max_pages_per_search}"')
        print(f'export REQUEST_DELAY="{self.config.delay_between_requests}"')
        print()
        print("# Logging:")
        print(f'export LOG_LEVEL="{self.config.log_level}"')
        if self.config.log_file:
            print(f'export LOG_FILE="{self.config.log_file}"')
        print()
        print("💡 TIP: Add these to your ~/.bashrc or ~/.zshrc for persistence")
    
    def generate_makefile_examples(self):
        """Show Makefile usage examples"""
        print("🔨 MAKEFILE USAGE EXAMPLES")
        print("=" * 50)
        print()
        print("# Use current config.py defaults:")
        print("make run-parser")
        print()
        print("# Override specific parameters:")
        print('make run-parser QUERY="Software Engineer" LOCATION="Austin" JOBS=100')
        print('make run-parser QUERY="Data Analyst" LOCATION="Remote" REMOTE=true')
        print('make run-parser QUERY="Product Manager" LOCATION="San Francisco" PARTTIME=true')
        print()
        print("# Common searches:")
        print('make run-parser QUERY="Machine Learning Engineer" LOCATION="United States" REMOTE=true JOBS=200')
        print('make run-parser QUERY="DevOps Engineer" LOCATION="Texas" JOBS=75')
        print('make run-parser QUERY="Python Developer" LOCATION="California" REMOTE=true JOBS=150')
        print()
        print("💡 Default values come from the first entry in LINKEDIN_JOB_SEARCH_PARAMS in config.py")
        print("💡 Command line parameters override config.py values when provided")


def main():
    """Main configuration manager CLI"""
    parser = argparse.ArgumentParser(description="LinkedIn Parser Configuration Manager")
    parser.add_argument("--show", action="store_true", help="Show current configuration")
    parser.add_argument("--env", action="store_true", help="Show environment variable setup")
    parser.add_argument("--examples", action="store_true", help="Show Makefile usage examples")
    parser.add_argument("--all", action="store_true", help="Show all information")
    
    args = parser.parse_args()
    
    if not any([args.show, args.env, args.examples, args.all]):
        # Default to showing basic config
        args.show = True
    
    config_manager = ConfigManager()
    
    if args.all:
        config_manager.show_current_config()
        print("\n")
        config_manager.show_env_variables()
        print("\n")
        config_manager.generate_makefile_examples()
    else:
        if args.show:
            config_manager.show_current_config()
        
        if args.env:
            config_manager.show_env_variables()
        
        if args.examples:
            config_manager.generate_makefile_examples()


if __name__ == "__main__":
    main()
