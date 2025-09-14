"""
GenAI Job Finder - Main Streamlit Application

This is the refactored main application file that orchestrates all the different
components and tabs. The application has been split into multiple modules for
better maintainability and development.

Structure:
- tabs/: Individual tab implementations
- components/: Reusable UI components
- utils/: Common utilities and data operations
"""
import streamlit as st
import sys
import os

# Add the parent directory to the path so we can import from genai_job_finder
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

# Import utilities and setup
from genai_job_finder.frontend.utils.common import setup_logging
from genai_job_finder.frontend.components.job_display import display_job_details

# Import tab modules
from genai_job_finder.frontend.tabs.live_search import render_live_search_tab
from genai_job_finder.frontend.tabs.stored_jobs import render_stored_jobs_tab
from genai_job_finder.frontend.tabs.ai_enhanced import render_ai_enhanced_tab
from genai_job_finder.frontend.tabs.search_history import render_search_history_tab
from genai_job_finder.frontend.tabs.career_chat import render_career_chat_tab

# Setup logging
setup_logging()

# Page configuration
st.set_page_config(
    page_title="GenAI Job Finder",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

def initialize_session_state():
    """Initialize all session state variables"""
    session_vars = {
        'jobs': [],
        'stored_jobs': [],
        'cleaned_jobs': [],
        'current_page': 1,
        'search_performed': False,
        'rows_per_page': 30,
        'jobs_loaded': False,
        'selected_job': None,
        'show_job_details': False,
        'use_cleaned_data': False,
        'cleaning_in_progress': False
    }
    
    for var, default_value in session_vars.items():
        if var not in st.session_state:
            st.session_state[var] = default_value

def main():
    """Main application function"""
    # Initialize session state
    initialize_session_state()
    
    # App title and description
    st.title("🔍 GenAI Job Finder")
    st.markdown("Find your dream job using AI-powered search and analysis")
    
    # Check if we should show job details
    if st.session_state.show_job_details and st.session_state.selected_job:
        display_job_details(st.session_state.selected_job)
        return
    
    # Create tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "🔍 Live Job Search", 
        "📊 Stored Jobs", 
        "🤖 AI-Enhanced Jobs", 
        "📈 Search History",
        "💼 Career Chat"
    ])
    
    # Render each tab
    with tab1:
        render_live_search_tab()
    
    with tab2:
        render_stored_jobs_tab()
    
    with tab3:
        render_ai_enhanced_tab()
    
    with tab4:
        render_search_history_tab()
    
    with tab5:
        render_career_chat_tab()

if __name__ == "__main__":
    main()
