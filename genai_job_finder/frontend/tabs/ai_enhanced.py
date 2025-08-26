"""
AI Enhanced Jobs tab functionality
"""
import streamlit as st
import os
from ..utils.data_operations import load_cleaned_jobs_from_database, run_data_cleaner
from ..utils.common import get_database_path
from ..components.job_display import display_job_results

def render_ai_enhanced_tab():
    """Render the AI Enhanced Jobs tab"""
    st.header("🤖 AI-Enhanced Jobs")
    st.markdown("Jobs processed with AI-powered data cleaning and enhancement")
    
    # Load cleaned jobs button
    col1, col2, col3 = st.columns([1, 1, 2])
    with col1:
        if st.button("🔄 Load AI-Enhanced Jobs", type="primary"):
            st.session_state.cleaned_jobs = load_cleaned_jobs_from_database()
            st.session_state.current_page = 1  # Reset to first page
            
            if st.session_state.cleaned_jobs:
                st.success(f"Loaded {len(st.session_state.cleaned_jobs)} AI-enhanced jobs!")
            else:
                st.warning("No AI-enhanced jobs found. Use 'Live Job Search' tab to search and automatically enhance jobs.")
    
    with col2:
        if st.button("🧹 Run Data Cleaner"):
            db_path = get_database_path()
            
            if not os.path.exists(db_path):
                st.error("No database found. Please parse some jobs first.")
            else:
                with st.spinner("🤖 Running AI data cleaner... This may take a few minutes."):
                    success = run_data_cleaner(db_path)
                    
                if success:
                    st.success("✅ Data cleaning completed! Reload AI-enhanced jobs to see results.")
                    # Auto-reload cleaned jobs
                    st.session_state.cleaned_jobs = load_cleaned_jobs_from_database()
                else:
                    st.error("❌ Data cleaning failed. Check logs for details.")
    
    # Auto-load cleaned jobs on first visit
    if 'cleaned_jobs_loaded' not in st.session_state:
        st.session_state.cleaned_jobs = load_cleaned_jobs_from_database()
        st.session_state.cleaned_jobs_loaded = True
    
    # Show AI enhancement info
    if st.session_state.cleaned_jobs:
        st.info("✨ **AI Enhancements Include:** Experience level classification, Salary extraction & normalization, Work location validation, Employment type standardization")
        
        # Show enhanced fields comparison
        with st.expander("🤖 AI Enhancement Details"):
            st.markdown("""
            **Enhanced Fields:**
            - **Experience Level**: AI classifies as Intern, Junior, Mid-level, Senior, Lead, Principal, Director
            - **Years Experience**: Extracts required years from job descriptions
            - **Salary Range**: Parses and normalizes salary information (min, max, mid, currency, period)
            - **Work Location Type**: Validates and corrects Remote/Hybrid/On-site classification
            - **Employment Type**: Standardizes Full-time/Part-time/Contract classifications
            
            **Data Quality Flags:**
            - Shows which fields were AI-enhanced vs original
            - Processing completion status
            - Error tracking for transparency
            """)
        
        display_job_results(st.session_state.cleaned_jobs, "AI-Enhanced Jobs", is_cleaned_data=True)
    else:
        st.info("No AI-enhanced jobs available. Use 'Live Job Search' to automatically enhance new job data.")
