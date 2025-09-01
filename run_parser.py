#!/usr/bin/env python3
"""
Comprehensive LinkedIn job parser with integrated company intelligence.
This single script handles all data extraction with proper rate limiting.

Usage: python run_parser.py [options]

Features:
- ✅ Job data extraction with 20-column output
- ✅ Integrated company intelligence (size, followers, industry)
- ✅ Location intelligence and work type classification  
- ✅ Smart rate limiting to avoid LinkedIn restrictions
- ✅ Automatic CSV export
- ✅ Progress tracking and error handling
"""

from genai_job_finder.linkedin_parser.run_parser import main

if __name__ == "__main__":
    exit(main())
