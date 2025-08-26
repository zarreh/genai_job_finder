"""
Stored Jobs tab functionality
"""
import streamlit as st
from ..utils.data_operations import load_jobs_from_database
from ..components.job_display import display_job_results

def render_stored_jobs_tab():
    """Render the Stored Jobs tab"""
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
