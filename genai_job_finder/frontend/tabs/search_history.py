"""
Search History tab functionality
"""
import streamlit as st
import pandas as pd
from datetime import datetime
from ..utils.data_operations import get_recent_runs_from_database

def render_search_history_tab():
    """Render the Search History tab"""
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
