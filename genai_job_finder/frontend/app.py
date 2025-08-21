import streamlit as st
import pandas as pd
import sys
import os
import logging
from datetime import datetime, timedelta
from typing import List, Optional
import math

# Add the parent directory to the path so we can import from genai_job_finder
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from genai_job_finder.linkedin_parser.parser import LinkedInJobParser
from genai_job_finder.linkedin_parser.database import DatabaseManager
from genai_job_finder.linkedin_parser.models import Job, JobType, ExperienceLevel

# Configure logging to show in terminal
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),  # This will show logs in terminal
        logging.FileHandler('frontend.log')  # Also save to file
    ]
)

logger = logging.getLogger(__name__)

# Page configuration
st.set_page_config(
    page_title="GenAI Job Finder",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'jobs' not in st.session_state:
    st.session_state.jobs = []
if 'current_page' not in st.session_state:
    st.session_state.current_page = 1
if 'search_performed' not in st.session_state:
    st.session_state.search_performed = False
if 'rows_per_page' not in st.session_state:
    st.session_state.rows_per_page = 10

def get_time_filter_options():
    """Get time filter options for job posting dates"""
    return {
        "Any time": None,
        "Past 24 hours": 1,
        "Past week": 7,
        "Past month": 30
    }

def format_job_for_display(job: Job) -> dict:
    """Format job data for display in table"""
    return {
        "Title": job.title,
        "Company": job.company,
        "Location": job.location,
        "Posted": job.posted_date.strftime("%Y-%m-%d %H:%M") if job.posted_date else "N/A",
        "Job Type": job.job_type.value if job.job_type else "N/A",
        "Experience": job.experience_level.value if job.experience_level else "N/A",
        "Remote": "✅ Yes" if job.remote_option else "❌ No",
        "Easy Apply": "✅ Yes" if job.easy_apply else "❌ No",
        "Applicants": job.applicants_count if job.applicants_count else "N/A",
        "LinkedIn URL": job.linkedin_url if job.linkedin_url else "N/A"
    }

def search_jobs(search_query: str, location: str, max_pages: int, time_filter: Optional[int] = None, remote_only: bool = False):
    """Search for jobs using the LinkedIn parser without persisting to database"""
    try:
        # Clean and prepare inputs
        search_query = search_query.strip()
        location = location.strip() if location else ""
        
        # If remote_only is True, modify the search query to include remote keywords
        if remote_only:
            search_query += " remote"
        
        logger.info(f"Starting job search for: '{search_query}' in '{location or 'Any location'}' (max_pages: {max_pages}, remote_only: {remote_only})")
        
        with st.spinner(f"Searching for jobs... This may take a few minutes (parsing {max_pages} pages)"):
            # Show progress in terminal
            print(f"\n🔍 FRONTEND: Starting job search...")
            print(f"   Query: '{search_query}'")
            print(f"   Location: '{location}' {'(Any location)' if not location else ''}")
            print(f"   Remote only: {remote_only}")
            print(f"   Max pages: {max_pages}")
            print(f"   Time filter: {time_filter} days" if time_filter else "   Time filter: Any time")
            
            # Initialize the parser with temporary database (won't persist searches)
            logger.info("Initializing parser for temporary search...")
            print("📊 FRONTEND: Initializing parser for temporary search...")
            
            # Use a temporary in-memory database
            import tempfile
            temp_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
            temp_db.close()
            
            db_manager = DatabaseManager(temp_db.name)
            parser = LinkedInJobParser(database=db_manager)
            
            # Search for jobs using direct parsing without database persistence
            logger.info("Starting job parsing...")
            print("🚀 FRONTEND: Starting LinkedIn job parsing...")
            
            jobs = []
            
            # Parse pages manually without persisting job runs
            for page in range(max_pages):
                print(f"   Parsing page {page + 1} of {max_pages}...")
                
                try:
                    # Build URL directly
                    url = parser._build_url(search_query, location, page)
                    logger.debug(f"Fetching: {url}")
                    
                    # Get page content
                    response = parser.session.get(url, timeout=15)
                    response.raise_for_status()
                    
                    # Parse job cards
                    from bs4 import BeautifulSoup
                    soup = BeautifulSoup(response.content, 'html.parser')
                    job_cards = parser._find_job_cards(soup)
                    
                    print(f"     Found {len(job_cards)} job cards on page {page + 1}")
                    
                    # Parse each job card
                    for card in job_cards:
                        try:
                            job = parser._parse_job_card(card, run_id=0)  # No run_id since we're not persisting
                            if job:
                                jobs.append(job)
                        except Exception as e:
                            logger.warning(f"Error parsing job card: {e}")
                            continue
                    
                    # Random delay between pages
                    import time
                    import random
                    time.sleep(random.uniform(2, 4))
                    
                except Exception as e:
                    logger.error(f"Error parsing page {page + 1}: {e}")
                    continue
            
            # Clean up temporary database
            import os
            try:
                os.unlink(temp_db.name)
            except:
                pass
            
            logger.info(f"Raw job parsing completed. Found {len(jobs)} jobs.")
            print(f"✅ FRONTEND: Raw parsing completed. Found {len(jobs)} jobs.")
            
            # Debug: Show some job details if found
            if jobs:
                print(f"   First job title: '{jobs[0].title}'")
                print(f"   First job company: '{jobs[0].company}'")
                print(f"   First job location: '{jobs[0].location}'")
            
            # Apply time filter if specified
            if time_filter and jobs:
                logger.info(f"Applying time filter: {time_filter} days")
                print(f"⏰ FRONTEND: Applying time filter ({time_filter} days)...")
                
                cutoff_date = datetime.now() - timedelta(days=time_filter)
                original_count = len(jobs)
                
                # Only filter if jobs have posted_date
                filtered_jobs = []
                for job in jobs:
                    if job.posted_date:
                        if job.posted_date >= cutoff_date:
                            filtered_jobs.append(job)
                    else:
                        # Include jobs without posted_date (assume they're recent)
                        filtered_jobs.append(job)
                
                logger.info(f"After time filtering: {len(filtered_jobs)} jobs remain")
                print(f"   Filtered from {original_count} to {len(filtered_jobs)} jobs")
                
                jobs = filtered_jobs
            
            logger.info(f"Final result: {len(jobs)} jobs")
            print(f"🎉 FRONTEND: Search completed! Final result: {len(jobs)} jobs")
            
            return jobs
            
    except Exception as e:
        error_msg = f"Error searching for jobs: {str(e)}"
        logger.error(error_msg, exc_info=True)
        print(f"❌ FRONTEND ERROR: {error_msg}")
        import traceback
        print("Full traceback:")
        traceback.print_exc()
        st.error(error_msg)
        return []

def main():
    st.title("🔍 GenAI Job Finder")
    st.markdown("Find your dream job using AI-powered search and analysis")
    
    # Create tabs
    tab1, tab2 = st.tabs(["🔍 Job Search", "📊 Search History"])
    
    with tab1:
        st.header("Job Search")
        
        # Search form
        with st.form("job_search_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                search_query = st.text_input(
                    "Job Title/Keywords*",
                    placeholder="e.g., Software Engineer, Data Scientist, AI/ML Engineer",
                    help="Enter job titles, skills, or keywords to search for"
                )
                
                location = st.text_input(
                    "Location",
                    placeholder="e.g., San Francisco, CA, United States, London, UK",
                    help="Leave empty to search all locations"
                )
                
                remote_only = st.checkbox(
                    "🏠 Remote Jobs Only",
                    value=False,
                    help="Search specifically for remote job opportunities (adds 'remote' to search query)"
                )
            
            with col2:
                time_filter_options = get_time_filter_options()
                time_filter_label = st.selectbox(
                    "Time Posted",
                    options=list(time_filter_options.keys()),
                    index=0,
                    help="Filter jobs by when they were posted"
                )
                time_filter = time_filter_options[time_filter_label]
                
                max_pages = st.slider(
                    "Max Pages to Search",
                    min_value=1,
                    max_value=10,
                    value=3,
                    help="Each page contains ~25 job listings. More pages = more results but longer search time"
                )
            
            col_search = st.columns([1])[0]
            with col_search:
                submit_button = st.form_submit_button("🔍 Search Jobs", type="primary")
        
        # Perform search when form is submitted
        if submit_button:
            if not search_query.strip():
                st.error("Please enter a job title or keywords to search for.")
            else:
                st.session_state.jobs = search_jobs(
                    search_query=search_query.strip(),
                    location=location.strip(),
                    max_pages=max_pages,
                    time_filter=time_filter,
                    remote_only=remote_only
                )
                st.session_state.current_page = 1
                st.session_state.search_performed = True
                
                if st.session_state.jobs:
                    remote_text = " remote" if remote_only else ""
                    st.success(f"Found {len(st.session_state.jobs)}{remote_text} jobs!")
                else:
                    st.warning("No jobs found. Try adjusting your search criteria.")
        
        # Display results
        if st.session_state.search_performed and st.session_state.jobs:
            st.divider()
            st.header("Search Results")
            
            # Results per page selector - placed here for immediate reactivity
            col_results, col_spacing = st.columns([1, 3])
            with col_results:
                rows_per_page = st.selectbox(
                    "Results per Page",
                    options=[5, 10, 15, 20, 25, 50],
                    index=1,  # Default to 10
                    help="Number of job results to display per page",
                    key="results_per_page"
                )
                # Update session state when changed
                if rows_per_page != st.session_state.rows_per_page:
                    st.session_state.rows_per_page = rows_per_page
                    st.session_state.current_page = 1  # Reset to first page when changing page size
            
            # Pagination settings
            jobs_per_page = st.session_state.rows_per_page
            total_jobs = len(st.session_state.jobs)
            total_pages = math.ceil(total_jobs / jobs_per_page)
            
            # Pagination controls
            if total_pages > 1:
                col1, col2, col3 = st.columns([1, 2, 1])
                
                with col1:
                    if st.button("◀ Previous", disabled=(st.session_state.current_page == 1)):
                        st.session_state.current_page -= 1
                        st.rerun()
                
                with col2:
                    st.markdown(f"<center>Page {st.session_state.current_page} of {total_pages}</center>", 
                              unsafe_allow_html=True)
                
                with col3:
                    if st.button("Next ▶", disabled=(st.session_state.current_page == total_pages)):
                        st.session_state.current_page += 1
                        st.rerun()
            
            # Calculate slice indices for current page
            start_idx = (st.session_state.current_page - 1) * jobs_per_page
            end_idx = min(start_idx + jobs_per_page, total_jobs)
            
            # Display jobs for current page
            current_page_jobs = st.session_state.jobs[start_idx:end_idx]
            
            # Convert jobs to DataFrame for display
            job_data = [format_job_for_display(job) for job in current_page_jobs]
            df = pd.DataFrame(job_data)
            
            # Add column filters
            st.subheader("Filter Results")
            filter_cols = st.columns(4)
            
            # Create filters for key columns
            with filter_cols[0]:
                title_filter = st.text_input("Filter by Title", placeholder="e.g., Engineer, Data")
            with filter_cols[1]:
                company_filter = st.text_input("Filter by Company", placeholder="e.g., Google, Meta")
            with filter_cols[2]:
                location_filter = st.text_input("Filter by Location", placeholder="e.g., SF, Remote")
            with filter_cols[3]:
                job_type_filter = st.selectbox("Filter by Job Type", 
                                             options=["All"] + df["Job Type"].unique().tolist() if not df.empty else ["All"])
            
            # Apply filters
            filtered_df = df.copy()
            if not df.empty:
                if title_filter:
                    filtered_df = filtered_df[filtered_df["Title"].str.contains(title_filter, case=False, na=False)]
                if company_filter:
                    filtered_df = filtered_df[filtered_df["Company"].str.contains(company_filter, case=False, na=False)]
                if location_filter:
                    filtered_df = filtered_df[filtered_df["Location"].str.contains(location_filter, case=False, na=False)]
                if job_type_filter != "All":
                    filtered_df = filtered_df[filtered_df["Job Type"] == job_type_filter]
            
            # Show filter results info
            if not df.empty:
                if len(filtered_df) != len(df):
                    st.info(f"Showing {len(filtered_df)} of {len(df)} jobs after filtering")
            
            # Display the filtered table with enhanced features
            if not filtered_df.empty:
                st.dataframe(
                    filtered_df,
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "LinkedIn URL": st.column_config.LinkColumn(
                            "LinkedIn URL",
                            help="Click to view job on LinkedIn"
                        ),
                        "Posted": st.column_config.TextColumn(
                            "Posted",
                            help="When the job was posted"
                        ),
                        "Title": st.column_config.TextColumn(
                            "Title",
                            help="Job title",
                            width="large"
                        ),
                        "Company": st.column_config.TextColumn(
                            "Company",
                            help="Company name",
                            width="medium"
                        ),
                        "Location": st.column_config.TextColumn(
                            "Location",
                            help="Job location",
                            width="medium"
                        ),
                        "Remote": st.column_config.TextColumn(
                            "Remote",
                            help="Remote work availability"
                        ),
                        "Easy Apply": st.column_config.TextColumn(
                            "Easy Apply",
                            help="LinkedIn Easy Apply available"
                        )
                    }
                )
            else:
                if df.empty:
                    st.info("No jobs to display.")
                else:
                    st.warning("No jobs match the current filters. Try adjusting your filter criteria.")
            
            # Show pagination info
            st.caption(f"Showing jobs {start_idx + 1}-{end_idx} of {total_jobs} total results ({jobs_per_page} per page)")
            
            # Download option
            if st.button("📥 Download Results as CSV"):
                all_job_data = [format_job_for_display(job) for job in st.session_state.jobs]
                csv_df = pd.DataFrame(all_job_data)
                csv = csv_df.to_csv(index=False)
                st.download_button(
                    label="Click to Download",
                    data=csv,
                    file_name=f"job_search_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
    
    with tab2:
        st.header("Search History")
        st.info("🚧 Search history feature coming soon!")
        st.markdown("""
        This tab will show:
        - Previous search queries and results
        - Saved job listings
        - Search analytics and trends
        """)

if __name__ == "__main__":
    main()
