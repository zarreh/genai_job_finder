import streamlit as st
import pandas as pd
import sys
import os
import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
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
if 'stored_jobs' not in st.session_state:
    st.session_state.stored_jobs = []
if 'current_page' not in st.session_state:
    st.session_state.current_page = 1
if 'search_performed' not in st.session_state:
    st.session_state.search_performed = False
if 'rows_per_page' not in st.session_state:
    st.session_state.rows_per_page = 10
if 'jobs_loaded' not in st.session_state:
    st.session_state.jobs_loaded = False
if 'selected_job' not in st.session_state:
    st.session_state.selected_job = None
if 'show_job_details' not in st.session_state:
    st.session_state.show_job_details = False

def get_time_filter_options():
    """Get time filter options for job posting dates"""
    return {
        "Any time": None,
        "Past 24 hours": 1,
        "Past week": 7,
        "Past month": 30
    }

def load_jobs_from_database() -> List[dict]:
    """Load all jobs from the database"""
    try:
        # Use the main database in data/ folder
        db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "jobs.db")
        
        if not os.path.exists(db_path):
            logger.warning(f"Database not found at {db_path}")
            return []
        
        db_manager = DatabaseManager(db_path)
        df = db_manager.get_all_jobs_as_dataframe()
        
        if df.empty:
            return []
        
        # Convert DataFrame to list of dictionaries
        jobs = df.to_dict('records')
        logger.info(f"Loaded {len(jobs)} jobs from database")
        return jobs
        
    except Exception as e:
        logger.error(f"Error loading jobs from database: {e}")
        return []

def get_recent_runs_from_database() -> List[dict]:
    """Get recent job runs from database"""
    try:
        db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "jobs.db")
        
        if not os.path.exists(db_path):
            return []
        
        db_manager = DatabaseManager(db_path)
        runs = db_manager.get_recent_runs()
        return runs
        
    except Exception as e:
        logger.error(f"Error loading runs from database: {e}")
        return []

def display_job_details(job_data: dict):
    """Display detailed view of a selected job"""
    st.header("📋 Job Details")
    
    # Back button
    col1, col2 = st.columns([1, 4])
    with col1:
        if st.button("← Back to Jobs", type="primary"):
            st.session_state.show_job_details = False
            st.session_state.selected_job = None
            st.rerun()
    
    # Job header
    st.subheader(f"🎯 {job_data.get('title', 'N/A')}")
    st.markdown(f"**🏢 Company:** {job_data.get('company', 'N/A')}")
    
    # Key information in columns
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("📍 Location", job_data.get('location', 'N/A'))
        st.metric("💼 Employment Type", job_data.get('employment_type', 'N/A'))
        st.metric("📊 Level", job_data.get('level', 'N/A'))
    
    with col2:
        st.metric("🏠 Work Location Type", job_data.get('work_location_type', 'N/A'))
        st.metric("💰 Salary Range", job_data.get('salary_range', 'N/A') if job_data.get('salary_range') else 'Not specified')
        st.metric("⏰ Posted", job_data.get('posted_time', 'N/A'))
    
    with col3:
        st.metric("👥 Applicants", job_data.get('applicants', 'N/A'))
        st.metric("🔧 Job Function", job_data.get('job_function', 'N/A'))
        st.metric("🏭 Industries", job_data.get('industries', 'N/A'))
    
    # LinkedIn link
    if job_data.get('job_posting_link'):
        st.markdown(f"🔗 **[View on LinkedIn]({job_data.get('job_posting_link')})**")
    
    # Date parsed
    if job_data.get('date'):
        st.caption(f"📅 Parsed on: {job_data.get('date')}")
    
    st.divider()
    
    # Job description
    st.subheader("📝 Job Description")
    content = job_data.get('content', 'No job description available.')
    
    if content and content != 'N/A':
        # Format the content for better readability
        formatted_content = content.replace('\\n', '\n').replace('\\t', '\t')
        
        # Display in a scrollable container
        with st.container():
            st.markdown(f"""
            <div style="background-color: #f0f2f6; padding: 20px; border-radius: 10px; max-height: 500px; overflow-y: auto;">
                <pre style="white-space: pre-wrap; font-family: inherit; margin: 0;">{formatted_content}</pre>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("No detailed job description available.")
    
    # Additional metadata
    st.divider()
    st.subheader("🔍 Additional Information")
    
    detail_cols = st.columns(2)
    with detail_cols[0]:
        if job_data.get('job_id'):
            st.text(f"Job ID: {job_data.get('job_id')}")
        if job_data.get('id'):
            st.text(f"Record ID: {job_data.get('id')}")
    
    with detail_cols[1]:
        if job_data.get('parsing_link'):
            st.markdown(f"**Parsing Source:** [LinkedIn API]({job_data.get('parsing_link')})")
        if job_data.get('run_id'):
            st.text(f"Parser Run ID: {job_data.get('run_id')}")

def find_job_by_id(job_id: str, jobs_data: List[dict]) -> Optional[dict]:
    """Find a job by its ID in the jobs data"""
    for job in jobs_data:
        if isinstance(job, dict):
            if job.get('id') == job_id:
                return job
        else:
            if hasattr(job, 'id') and job.id == job_id:
                return job.to_dict() if hasattr(job, 'to_dict') else job.__dict__
    return None

def format_job_for_display(job_data: dict) -> dict:
    """Format job data for display in table - supports both Job objects and dict data"""
    # Handle both Job objects and dictionary data
    if isinstance(job_data, dict):
        # Data from database (dictionary format)
        return {
            "Company": job_data.get("company", "N/A"),
            "Title": job_data.get("title", "N/A"),
            "Location": job_data.get("location", "N/A"),
            "Work Location Type": job_data.get("work_location_type", "N/A"),
            "Level": job_data.get("level", "N/A"),
            "Salary Range": job_data.get("salary_range", "N/A"),
            "Employment Type": job_data.get("employment_type", "N/A"),
            "Job Function": job_data.get("job_function", "N/A"),
            "Industries": job_data.get("industries", "N/A"),
            "Posted Time": job_data.get("posted_time", "N/A"),
            "Applicants": job_data.get("applicants", "N/A"),
            "Job ID": job_data.get("id", "N/A")  # Keep ID for selection
        }
    else:
        # Job object format (for backwards compatibility)
        return {
            "Company": job_data.company if job_data.company else "N/A",
            "Title": job_data.title if job_data.title else "N/A",
            "Location": job_data.location if job_data.location else "N/A",
            "Work Location Type": job_data.work_location_type if job_data.work_location_type else "N/A",
            "Level": job_data.level if job_data.level else "N/A",
            "Salary Range": job_data.salary_range if job_data.salary_range else "N/A",
            "Employment Type": job_data.employment_type if job_data.employment_type else "N/A",
            "Job Function": job_data.job_function if job_data.job_function else "N/A",
            "Industries": job_data.industries if job_data.industries else "N/A",
            "Posted Time": job_data.posted_time if job_data.posted_time else "N/A",
            "Applicants": job_data.applicants if job_data.applicants else "N/A",
            "Job ID": job_data.id if job_data.id else "N/A"
        }

def search_jobs(search_query: str, location: str, max_pages: int, time_filter: Optional[int] = None, remote_only: bool = False):
    """Search for jobs using the LinkedIn parser and return in new format"""
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
            
            # Initialize the parser with temporary database 
            logger.info("Initializing parser for temporary search...")
            print("📊 FRONTEND: Initializing parser for temporary search...")
            
            # Use a temporary in-memory database
            import tempfile
            temp_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
            temp_db.close()
            
            db_manager = DatabaseManager(temp_db.name)
            parser = LinkedInJobParser(database=db_manager)
            
            # Run the parser to get jobs
            logger.info("Starting job parsing...")
            print("🚀 FRONTEND: Starting LinkedIn job parsing...")
            
            # Parse jobs using the parser's built-in functionality
            try:
                # Convert max_pages to total_jobs estimate (25 jobs per page)
                total_jobs_estimate = max_pages * 25
                
                # Parse jobs - this creates its own run
                jobs_list = parser.parse_jobs(
                    search_query=search_query, 
                    location=location, 
                    total_jobs=total_jobs_estimate,
                    remote=remote_only
                )
                
                # Convert Job objects to dict format for display
                jobs_dict = [job.to_dict() for job in jobs_list]
                
                logger.info(f"Found {len(jobs_dict)} jobs from parsing")
                print(f"✅ FRONTEND: Parsing completed. Found {len(jobs_dict)} jobs.")
                
                # Apply time filter if specified
                if time_filter and jobs_dict:
                    logger.info(f"Applying time filter: {time_filter} days")
                    print(f"⏰ FRONTEND: Applying time filter ({time_filter} days)...")
                    
                    cutoff_date = datetime.now() - timedelta(days=time_filter)
                    original_count = len(jobs_dict)
                    
                    filtered_jobs = []
                    for job in jobs_dict:
                        # Try to parse posted_time - this is simplified since it's live search
                        try:
                            if job.get('posted_time'):
                                # For simplicity, include all jobs in live search
                                filtered_jobs.append(job)
                            else:
                                filtered_jobs.append(job)
                        except:
                            filtered_jobs.append(job)
                    
                    logger.info(f"After time filtering: {len(filtered_jobs)} jobs remain")
                    print(f"   Filtered from {original_count} to {len(filtered_jobs)} jobs")
                    
                    jobs_dict = filtered_jobs
                
                # Clean up temporary database
                try:
                    os.unlink(temp_db.name)
                except:
                    pass
                
                logger.info(f"Final result: {len(jobs_dict)} jobs")
                print(f"🎉 FRONTEND: Search completed! Final result: {len(jobs_dict)} jobs")
                
                return jobs_dict
                
            except Exception as e:
                # Clean up and re-raise
                try:
                    os.unlink(temp_db.name)
                except:
                    pass
                raise e
            
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
    
    # Check if we should show job details
    if st.session_state.show_job_details and st.session_state.selected_job:
        display_job_details(st.session_state.selected_job)
        return
    
    # Create tabs
    tab1, tab2, tab3 = st.tabs(["🔍 Live Job Search", "📊 Stored Jobs", "📈 Search History"])
    
    with tab1:
        st.header("Live Job Search")
        st.info("⚠️ This performs live LinkedIn scraping and may take time. Results are not saved to database.")
        
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
            display_job_results(st.session_state.jobs, "Live Search Results")
    
    with tab2:
        st.header("Stored Jobs")
        st.markdown("Jobs from previous parser runs stored in the database")
        
        # Load jobs button
        col1, col2 = st.columns([1, 3])
        with col1:
            if st.button("🔄 Load Jobs from Database", type="primary"):
                st.session_state.stored_jobs = load_jobs_from_database()
                st.session_state.jobs_loaded = True
                st.session_state.current_page = 1  # Reset to first page
                
                if st.session_state.stored_jobs:
                    st.success(f"Loaded {len(st.session_state.stored_jobs)} jobs from database!")
                else:
                    st.warning("No jobs found in database. Run the parser first to collect jobs.")
        
        # Auto-load on first visit
        if not st.session_state.jobs_loaded:
            st.session_state.stored_jobs = load_jobs_from_database()
            st.session_state.jobs_loaded = True
        
        # Display stored jobs
        if st.session_state.stored_jobs:
            display_job_results(st.session_state.stored_jobs, "Stored Jobs from Database", is_database_data=True)
        else:
            st.info("No stored jobs available. Use the parser to collect job data first.")
    
    with tab3:
        st.header("Search History")
        
        # Load and display recent runs
        runs = get_recent_runs_from_database()
        
        if runs:
            st.markdown("### Recent Parser Runs")
            
            runs_data = []
            for run in runs:
                runs_data.append({
                    "Run ID": run.get("id", "N/A"),
                    "Date": run.get("run_date", "N/A")[:19] if run.get("run_date") else "N/A",
                    "Search Query": run.get("search_query", "N/A"),
                    "Location": run.get("location_filter", "Any") if run.get("location_filter") else "Any",
                    "Job Count": run.get("job_count", 0),
                    "Status": run.get("status", "Unknown"),
                    "Duration": f"{((datetime.fromisoformat(run.get('completed_at', '')) - datetime.fromisoformat(run.get('started_at', ''))).total_seconds() / 60):.1f} min" if run.get("completed_at") and run.get("started_at") else "N/A"
                })
            
            df_runs = pd.DataFrame(runs_data)
            st.dataframe(df_runs, use_container_width=True, hide_index=True)
        else:
            st.info("No search history available. Run the parser to see history.")

def display_job_results(jobs_data: List, title: str, is_database_data: bool = False):
    """Display job results with pagination and filtering"""
    st.divider()
    st.header(title)
    
    # Results per page selector
    col_results, col_spacing = st.columns([1, 3])
    with col_results:
        rows_per_page = st.selectbox(
            "Results per Page",
            options=[5, 10, 15, 20, 25, 50],
            index=1,  # Default to 10
            help="Number of job results to display per page",
            key=f"results_per_page_{title.replace(' ', '_')}"
        )
        # Update session state when changed
        if rows_per_page != st.session_state.rows_per_page:
            st.session_state.rows_per_page = rows_per_page
            st.session_state.current_page = 1  # Reset to first page when changing page size
    
    # Pagination settings
    jobs_per_page = st.session_state.rows_per_page
    total_jobs = len(jobs_data)
    total_pages = math.ceil(total_jobs / jobs_per_page)
    
    # Pagination controls
    if total_pages > 1:
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col1:
            if st.button("◀ Previous", disabled=(st.session_state.current_page == 1), key=f"prev_{title.replace(' ', '_')}"):
                st.session_state.current_page -= 1
                st.rerun()
        
        with col2:
            st.markdown(f"<center>Page {st.session_state.current_page} of {total_pages}</center>", 
                      unsafe_allow_html=True)
        
        with col3:
            if st.button("Next ▶", disabled=(st.session_state.current_page == total_pages), key=f"next_{title.replace(' ', '_')}"):
                st.session_state.current_page += 1
                st.rerun()
    
    # Calculate slice indices for current page
    start_idx = (st.session_state.current_page - 1) * jobs_per_page
    end_idx = min(start_idx + jobs_per_page, total_jobs)
    
    # Display jobs for current page
    current_page_jobs = jobs_data[start_idx:end_idx]
    
    # Convert jobs to DataFrame for display - only specified columns
    job_data = [format_job_for_display(job) for job in current_page_jobs]
    df = pd.DataFrame(job_data)
    
    # Filter to only show requested columns (removed content and date)
    display_columns = [
        "Company", "Title", "Location", "Work Location Type", "Level", 
        "Salary Range", "Employment Type", "Job Function", 
        "Industries", "Posted Time", "Applicants"
    ]
    
    # Only include columns that exist in the dataframe
    available_columns = [col for col in display_columns if col in df.columns]
    
    if not df.empty:
        filtered_df = df[available_columns]
        
        # Add column filters
        st.subheader("Filter Results")
        filter_cols = st.columns(4)
        
        # Create filters for key columns
        with filter_cols[0]:
            title_filter = st.text_input("Filter by Title", placeholder="e.g., Engineer, Data", key=f"title_filter_{title.replace(' ', '_')}")
        with filter_cols[1]:
            company_filter = st.text_input("Filter by Company", placeholder="e.g., Google, Meta", key=f"company_filter_{title.replace(' ', '_')}")
        with filter_cols[2]:
            location_filter = st.text_input("Filter by Location", placeholder="e.g., SF, Remote", key=f"location_filter_{title.replace(' ', '_')}")
        with filter_cols[3]:
            work_type_filter = st.selectbox("Filter by Work Type", 
                                         options=["All"] + filtered_df["Work Location Type"].unique().tolist() if "Work Location Type" in filtered_df.columns else ["All"],
                                         key=f"work_type_filter_{title.replace(' ', '_')}")
        
        # Apply filters
        display_df = filtered_df.copy()
        
        if title_filter:
            display_df = display_df[display_df["Title"].str.contains(title_filter, case=False, na=False)]
        if company_filter:
            display_df = display_df[display_df["Company"].str.contains(company_filter, case=False, na=False)]
        if location_filter:
            display_df = display_df[display_df["Location"].str.contains(location_filter, case=False, na=False)]
        if work_type_filter != "All":
            display_df = display_df[display_df["Work Location Type"] == work_type_filter]
        
        # Show filter results info
        if len(display_df) != len(filtered_df):
            st.info(f"Showing {len(display_df)} of {len(filtered_df)} jobs after filtering")
        
        # Display the filtered table with row selection
        if not display_df.empty:
            st.markdown("💡 **Click on a row to view detailed job information**")
            
            # Create a copy for display with row indices
            display_with_index = display_df.reset_index(drop=True)
            
            # Display the dataframe with click handling
            selected_indices = st.dataframe(
                display_with_index,
                use_container_width=True,
                hide_index=True,
                on_select="rerun",
                selection_mode="single-row",
                column_config={
                    "Title": st.column_config.TextColumn(
                        "Title",
                        help="Job title - Click row for details",
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
                    "Work Location Type": st.column_config.TextColumn(
                        "Work Location Type",
                        help="Remote/Hybrid/On-site",
                        width="small"
                    ),
                    "Level": st.column_config.TextColumn(
                        "Level",
                        help="Experience level",
                        width="small"
                    ),
                    "Salary Range": st.column_config.TextColumn(
                        "Salary Range",
                        help="Salary information",
                        width="medium"
                    )
                }
            )
            
            # Handle row selection
            if selected_indices.selection.rows:
                selected_row_index = selected_indices.selection.rows[0]
                # Get the actual job index from current page
                actual_job_index = start_idx + selected_row_index
                
                if actual_job_index < len(jobs_data):
                    selected_job_data = jobs_data[actual_job_index]
                    
                    # Convert to dict if it's a Job object
                    if not isinstance(selected_job_data, dict):
                        if hasattr(selected_job_data, 'to_dict'):
                            selected_job_data = selected_job_data.to_dict()
                        else:
                            selected_job_data = selected_job_data.__dict__
                    
                    # Store in session state and show details
                    st.session_state.selected_job = selected_job_data
                    st.session_state.show_job_details = True
                    st.rerun()
        else:
            st.warning("No jobs match the current filters. Try adjusting your filter criteria.")
        
        # Show pagination info
        st.caption(f"Showing jobs {start_idx + 1}-{end_idx} of {total_jobs} total results ({jobs_per_page} per page)")
        
        # Download option
        if st.button("📥 Download Results as CSV", key=f"download_{title.replace(' ', '_')}"):
            all_job_data = [format_job_for_display(job) for job in jobs_data]
            csv_df = pd.DataFrame(all_job_data)
            
            # Filter to only requested columns (excluding content and date)
            display_columns_for_csv = [
                "Company", "Title", "Location", "Work Location Type", "Level", 
                "Salary Range", "Employment Type", "Job Function", 
                "Industries", "Posted Time", "Applicants"
            ]
            
            if not csv_df.empty:
                available_cols = [col for col in display_columns_for_csv if col in csv_df.columns]
                csv_df = csv_df[available_cols]
            
            csv = csv_df.to_csv(index=False)
            st.download_button(
                label="Click to Download",
                data=csv,
                file_name=f"job_search_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                key=f"download_btn_{title.replace(' ', '_')}"
            )
    else:
        st.info("No jobs to display.")

if __name__ == "__main__":
    main()
