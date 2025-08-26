"""
Live Job Search tab functionality
"""
import streamlit as st
from ..utils.common import get_time_filter_options
from ..utils.data_operations import search_jobs
from ..components.job_display import display_job_results

def render_live_search_tab():
    """Render the Live Job Search tab"""
    st.header("Live Job Search with AI Enhancement")
    st.info("⚠️ This performs live LinkedIn scraping with automatic AI enhancement. Results include enhanced data but are not saved to database.")
    
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
            # Progress tracking UI
            progress_container = st.container()
            status_placeholder = st.empty()
            
            def progress_callback(message: str, step: int = 0):
                """Callback function to update progress"""
                with status_placeholder.container():
                    if step == -1:  # Error
                        st.error(message)
                    elif step == 10:  # Complete
                        st.success(message)
                    else:  # In progress
                        st.info(message)
            
            # Perform the search
            st.session_state.jobs = search_jobs(
                search_query=search_query.strip(),
                location=location.strip(),
                max_pages=max_pages,
                time_filter=time_filter,
                remote_only=remote_only,
                progress_callback=progress_callback
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
        # Check if any jobs have AI enhancement indicators
        ai_enhanced_count = sum(1 for job in st.session_state.jobs if job.get('experience_level_label') or job.get('min_salary') or job.get('processed_at'))
        title_suffix = f" - {ai_enhanced_count} AI Enhanced" if ai_enhanced_count > 0 else ""
        display_job_results(st.session_state.jobs, f"Live Search Results{title_suffix}", is_cleaned_data=True)
