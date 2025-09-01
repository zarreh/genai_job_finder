"""
Display components for job data formatting and viewing
"""
import pandas as pd
import streamlit as st
import math
import sqlite3
import os
from typing import List, Dict, Any, Optional
from datetime import datetime

def get_company_info(company_name: str, database_path: str = None) -> Dict[str, Any]:
    """Get company information from the companies table"""
    if not database_path:
        database_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data', 'jobs.db')
    
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"DEBUG: Looking up company '{company_name}' in database: {database_path}")
    
    try:
        conn = sqlite3.connect(database_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT company_size, followers, industry, company_url 
            FROM companies 
            WHERE company_name = ? LIMIT 1
        """, (company_name,))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            company_info = {
                'company_size': result[0],
                'followers': result[1],
                'industry': result[2],
                'company_url': result[3]
            }
            logger.info(f"DEBUG: Found company info for '{company_name}': {company_info}")
            return company_info
        else:
            logger.info(f"DEBUG: No company info found for '{company_name}'")
    except Exception as e:
        logger.error(f"DEBUG: Error getting company info for '{company_name}': {e}")
    
    return {}

def format_company_info_only(company_info: Dict) -> str:
    """Format only the company info part (without company name) for a separate column"""
    if not company_info:
        return "N/A"
    
    parts = []
    if company_info.get('industry'):
        parts.append(f"🏭 {company_info['industry']}")
    if company_info.get('company_size'):
        parts.append(f"👥 {company_info['company_size']}")
    if company_info.get('followers'):
        followers = company_info['followers']
        # Handle both raw numbers and formatted strings like "13,632 followers"
        if isinstance(followers, str):
            if 'followers' in followers:
                # Extract number from "13,632 followers"
                followers_str = followers.replace(' followers', '').replace(',', '')
                if followers_str.isdigit():
                    followers_num = int(followers_str)
                    if followers_num >= 1000000:
                        followers_display = f"{followers_num/1000000:.1f}M"
                    elif followers_num >= 1000:
                        followers_display = f"{followers_num/1000:.1f}K"
                    else:
                        followers_display = str(followers_num)
                    parts.append(f"👨‍💼 {followers_display} followers")
                else:
                    # Use as-is if we can't parse it
                    parts.append(f"👨‍💼 {followers}")
            elif followers.isdigit():
                followers_num = int(followers)
                if followers_num >= 1000000:
                    followers_display = f"{followers_num/1000000:.1f}M"
                elif followers_num >= 1000:
                    followers_display = f"{followers_num/1000:.1f}K"
                else:
                    followers_display = str(followers_num)
                parts.append(f"👨‍💼 {followers_display} followers")
        elif isinstance(followers, int):
            if followers >= 1000000:
                followers_display = f"{followers/1000000:.1f}M"
            elif followers >= 1000:
                followers_display = f"{followers/1000:.1f}K"
            else:
                followers_display = str(followers)
            parts.append(f"👨‍💼 {followers_display} followers")
    
    return " • ".join(parts) if parts else "N/A"

def format_company_display(company_name: str, company_info: Dict = None, job_data: Dict = None) -> str:
    """Format company information for display"""
    if not company_info:
        # First try to get company info from job data (for live search results)
        if job_data:
            company_info = {}
            if job_data.get('company_size'):
                company_info['company_size'] = job_data['company_size']
            if job_data.get('company_followers'):
                company_info['followers'] = job_data['company_followers']
            if job_data.get('company_industry'):
                company_info['industry'] = job_data['company_industry']
            if job_data.get('company_info_link'):
                company_info['company_url'] = job_data['company_info_link']
            
            # Debug print for immediate feedback
            print(f"🔍 COMPANY DEBUG: '{company_name}' job_data fields: size={job_data.get('company_size')}, followers={job_data.get('company_followers')}, industry={job_data.get('company_industry')}")
            print(f"🔍 COMPANY DEBUG: Built company_info: {company_info}")
        
        # If no company info from job data, try database lookup
        if not company_info or not any(company_info.values()):
            company_info = get_company_info(company_name)
            print(f"🔍 COMPANY DEBUG: '{company_name}' database lookup result: {company_info}")
    
    company_display = company_name
    
    if company_info:
        parts = []
        if company_info.get('industry'):
            parts.append(f"🏭 {company_info['industry']}")
        if company_info.get('company_size'):
            parts.append(f"👥 {company_info['company_size']}")
        if company_info.get('followers'):
            followers = company_info['followers']
            if isinstance(followers, (int, str)) and str(followers).isdigit():
                followers_num = int(followers)
                if followers_num >= 1000000:
                    followers_str = f"{followers_num/1000000:.1f}M"
                elif followers_num >= 1000:
                    followers_str = f"{followers_num/1000:.1f}K"
                else:
                    followers_str = str(followers_num)
                parts.append(f"👨‍💼 {followers_str} followers")
        
        if parts:
            company_display += f" ({' • '.join(parts)})"
            print(f"🔍 COMPANY DEBUG: Final display for '{company_name}': {company_display}")
    else:
        print(f"🔍 COMPANY DEBUG: No company_info for '{company_name}', using plain name")
    
    return company_display

def format_job_for_display(job_data: dict, is_cleaned: bool = False) -> dict:
    """Format job data for display in table - supports both Job objects and dict data"""
    # Handle both Job objects and dictionary data
    if isinstance(job_data, dict):
        company_name = job_data.get("company", "N/A")
        
        # Get company info for separate column
        company_info = {}
        if job_data.get('company_size'):
            company_info['company_size'] = job_data['company_size']
        if job_data.get('company_followers'):
            company_info['followers'] = job_data['company_followers']
        if job_data.get('company_industry'):
            company_info['industry'] = job_data['company_industry']
        if job_data.get('company_info_link'):
            company_info['company_url'] = job_data['company_info_link']
        
        # If no company info from job data, try database lookup
        if not company_info or not any(company_info.values()):
            company_info = get_company_info(company_name)
        
        company_info_display = format_company_info_only(company_info)
        
        if is_cleaned:
            # Enhanced cleaned data format with AI-enhanced fields
            
            # Handle salary formatting with proper NaN checking
            min_sal = job_data.get('min_salary')
            max_sal = job_data.get('max_salary')
            mid_sal = job_data.get('mid_salary')
            
            # Check if salary values are valid numbers (not None, not NaN)
            if (min_sal is not None and max_sal is not None and 
                not pd.isna(min_sal) and not pd.isna(max_sal) and
                min_sal > 0 and max_sal > 0):
                if mid_sal and not pd.isna(mid_sal) and mid_sal > 0:
                    salary_display = f"${min_sal:,.0f} - ${max_sal:,.0f} (Mid: ${mid_sal:,.0f})"
                else:
                    salary_display = f"${min_sal:,.0f} - ${max_sal:,.0f}"
            else:
                salary_display = job_data.get("salary_range", "N/A")
            
            # Use enhanced fields from cleaned_jobs table
            experience_level = job_data.get("experience_level_label", "N/A")
            years_exp = job_data.get("min_years_experience")
            if years_exp is None or pd.isna(years_exp):
                years_exp = "N/A"
            
            base_format = {
                "Company": company_name,
                "Company Info": company_info_display,
                "Title": job_data.get("title", "N/A"),
                "Location": job_data.get("location", "N/A"),
                "Work Location Type": job_data.get("work_location_type", "N/A"),
                "Experience Level": experience_level,
                "Years Experience": years_exp,
                "Salary Range": salary_display,
                "Employment Type": job_data.get("employment_type", "N/A"),
                "Job Function": job_data.get("job_function", "N/A"),
                "Industries": job_data.get("industries", "N/A"),
                "Posted Time": job_data.get("posted_time", "N/A"),
                "Applicants": job_data.get("applicants", "N/A"),
                "Job ID": job_data.get("id") or job_data.get("job_id", "N/A")  # Keep ID for selection
            }
            return base_format
        else:
            # Data from database (dictionary format) - original
            return {
                "Company": company_name,
                "Company Info": company_info_display,
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
        company_name = job_data.company if job_data.company else "N/A"
        # Convert job object to dict for company display lookup
        job_dict = {
            'company_size': getattr(job_data, 'company_size', None),
            'company_followers': getattr(job_data, 'company_followers', None),
            'company_industry': getattr(job_data, 'company_industry', None),
            'company_info_link': getattr(job_data, 'company_info_link', None)
        }
        # Create company_info from job attributes and get database info if needed
        company_info = {
            'company_size': job_dict.get('company_size'),
            'followers': job_dict.get('company_followers'),
            'industry': job_dict.get('company_industry')
        }
        
        # If no company info from job object, try database lookup
        if not company_info or not any(company_info.values()):
            company_info = get_company_info(company_name)
        
        company_info_display = format_company_info_only(company_info)
        
        return {
            "Company": company_name,
            "Company Info": company_info_display,
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

def display_job_details(job_data: dict):
    """Display detailed view of a selected job"""
    st.header("📋 Job Details")
    
    # Check if this is cleaned data
    is_cleaned = 'experience_level_label' in job_data
    
    # Back button
    col1, col2 = st.columns([1, 4])
    with col1:
        if st.button("← Back to Jobs", type="primary"):
            st.session_state.show_job_details = False
            st.session_state.selected_job = None
            st.rerun()
    
    with col2:
        if is_cleaned:
            st.success("🤖 AI-Enhanced Job Data")
        else:
            st.info("📊 Original Job Data")
    
    # Job header with company information
    st.subheader(f"🎯 {job_data.get('title', 'N/A')}")
    
    # Company information with enhanced display
    company_name = job_data.get('company', 'N/A')
    
    # Try to get company info from job data first (for live search), then from database
    company_info = {}
    if job_data.get('company_size'):
        company_info['company_size'] = job_data['company_size']
    if job_data.get('company_followers'):
        company_info['followers'] = job_data['company_followers']
    if job_data.get('company_industry'):
        company_info['industry'] = job_data['company_industry']
    if job_data.get('company_info_link'):
        company_info['company_url'] = job_data['company_info_link']
    
    # If no company info from job data, try database lookup
    if not company_info or not any(company_info.values()):
        company_info = get_company_info(company_name)
    
    if company_info and any(company_info.values()):
        col_company1, col_company2 = st.columns([2, 3])
        with col_company1:
            st.markdown(f"**🏢 Company:** {company_name}")
            if company_info.get('company_url'):
                st.markdown(f"🔗 [Company Profile]({company_info['company_url']})")
        
        with col_company2:
            company_details = []
            if company_info.get('industry'):
                company_details.append(f"🏭 **Industry:** {company_info['industry']}")
            if company_info.get('company_size'):
                company_details.append(f"👥 **Size:** {company_info['company_size']}")
            if company_info.get('followers'):
                followers = company_info['followers']
                if isinstance(followers, (int, str)) and str(followers).isdigit():
                    followers_num = int(followers)
                    if followers_num >= 1000000:
                        followers_str = f"{followers_num/1000000:.1f}M"
                    elif followers_num >= 1000:
                        followers_str = f"{followers_num/1000:.1f}K"
                    else:
                        followers_str = str(followers_num)
                    company_details.append(f"👨‍💼 **Followers:** {followers_str}")
            
            for detail in company_details:
                st.markdown(detail)
    else:
        st.markdown(f"**🏢 Company:** {company_name}")
    
    st.divider()
    
    # Key information in columns
    if is_cleaned:
        # Enhanced view for cleaned data
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("📍 Location", job_data.get('location', 'N/A'))
            st.metric("💼 Employment Type", job_data.get('employment_type', 'N/A'))
            st.metric("🎯 Experience Level", job_data.get('experience_level_label', 'N/A'))
            st.metric("📅 Years Required", str(job_data.get('min_years_experience', 'N/A')))
        
        with col2:
            st.metric("🏠 Work Location Type", job_data.get('work_location_type', 'N/A'))
            
            # Handle salary display with proper NaN checking
            min_sal = job_data.get('min_salary')
            max_sal = job_data.get('max_salary')
            mid_sal = job_data.get('mid_salary')
            
            if (min_sal is not None and max_sal is not None and 
                not pd.isna(min_sal) and not pd.isna(max_sal) and
                min_sal > 0 and max_sal > 0):
                st.metric("💰 Salary Range", f"${min_sal:,.0f} - ${max_sal:,.0f}")
                if mid_sal is not None and not pd.isna(mid_sal) and mid_sal > 0:
                    st.metric("💵 Mid Salary", f"${mid_sal:,.0f}")
                else:
                    st.metric("💵 Mid Salary", "N/A")
                st.metric("💱 Currency", job_data.get('salary_currency', 'N/A'))
            else:
                st.metric("💰 Salary Range", job_data.get('salary_range', 'Not specified'))
            
        with col3:
            st.metric("⏰ Posted", job_data.get('posted_time', 'N/A'))
            st.metric("👥 Applicants", job_data.get('applicants', 'N/A'))
            st.metric("🔧 Job Function", job_data.get('job_function', 'N/A'))
            st.metric("🏭 Industries", job_data.get('industries', 'N/A'))
            
        # AI Processing status
        if job_data.get('processing_complete'):
            st.success("✅ AI Processing Complete")
        if job_data.get('processing_errors'):
            st.warning(f"⚠️ Processing Errors: {job_data.get('processing_errors')}")
            
    else:
        # Original view for raw data
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
    
    if is_cleaned and job_data.get('updated_at'):
        st.caption(f"🤖 AI Enhanced on: {job_data.get('updated_at')}")
    
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
            
    # Show AI enhancement details for cleaned data
    if is_cleaned:
        st.subheader("🤖 AI Enhancement Details")
        enhancement_cols = st.columns(4)
        
        with enhancement_cols[0]:
            if job_data.get('salary_corrected'):
                st.success("💰 Salary Enhanced")
            else:
                st.info("💰 Salary Original")
                
        with enhancement_cols[1]:
            if job_data.get('location_corrected'):
                st.success("📍 Location Enhanced")
            else:
                st.info("📍 Location Original")
                
        with enhancement_cols[2]:
            if job_data.get('employment_corrected'):
                st.success("💼 Employment Enhanced")
            else:
                st.info("💼 Employment Original")
                
        with enhancement_cols[3]:
            exp_level = job_data.get('experience_level', 0)
            if exp_level > 0:
                st.success(f"🎯 Experience: Level {exp_level}")
            else:
                st.info("🎯 Experience: Not classified")

def display_job_results(jobs_data: List, title: str, is_database_data: bool = False, is_cleaned_data: bool = False):
    """Display job results with pagination and filtering"""
    st.divider()
    st.header(title)
    
    # Results per page selector
    col_results, col_spacing = st.columns([1, 3])
    with col_results:
        rows_per_page = st.selectbox(
            "Results per Page",
            options=[5, 10, 15, 20, 25, 30, 50],
            index=5,  # Default to 30
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
    job_data = [format_job_for_display(job, is_cleaned=is_cleaned_data) for job in current_page_jobs]
    df = pd.DataFrame(job_data)
    
    # Add original indices to track which job from current_page_jobs each row represents
    df['_original_job_index'] = range(len(current_page_jobs))
    
    # Filter to only show requested columns
    if is_cleaned_data:
        # Enhanced display columns for cleaned data
        display_columns = [
            "Company", "Company Info", "Title", "Location", "Work Location Type", "Experience Level", 
            "Years Experience", "Salary Range", "Employment Type", "Job Function", 
            "Industries", "Posted Time", "Applicants"
        ]
    else:
        # Original display columns
        display_columns = [
            "Company", "Company Info", "Title", "Location", "Work Location Type", "Level", 
            "Salary Range", "Employment Type", "Job Function", 
            "Industries", "Posted Time", "Applicants"
        ]
    
    # Only include columns that exist in the dataframe
    available_columns = [col for col in display_columns if col in df.columns]
    
    if not df.empty:
        filtered_df = df[available_columns]
        
        # Add column filters
        st.subheader("Filter Results")
        if is_cleaned_data:
            # Enhanced filters for cleaned data
            filter_cols = st.columns(5)
            
            with filter_cols[0]:
                title_filter = st.text_input("Filter by Title", placeholder="e.g., Engineer, Data", key=f"title_filter_{title.replace(' ', '_')}")
            with filter_cols[1]:
                company_filter = st.text_input("Filter by Company", placeholder="e.g., Google, Meta", key=f"company_filter_{title.replace(' ', '_')}")
            with filter_cols[2]:
                location_filter = st.text_input("Filter by Location", placeholder="e.g., SF, Remote", key=f"location_filter_{title.replace(' ', '_')}")
            with filter_cols[3]:
                work_type_filter = st.selectbox("Work Type", 
                                             options=["All"] + filtered_df["Work Location Type"].unique().tolist() if "Work Location Type" in filtered_df.columns else ["All"],
                                             key=f"work_type_filter_{title.replace(' ', '_')}")
            with filter_cols[4]:
                exp_level_filter = st.selectbox("Experience Level", 
                                              options=["All"] + sorted(filtered_df["Experience Level"].unique().tolist()) if "Experience Level" in filtered_df.columns else ["All"],
                                              key=f"exp_level_filter_{title.replace(' ', '_')}")
            
            # Salary range filter for cleaned data
            salary_col1, salary_col2 = st.columns(2)
            with salary_col1:
                min_salary_filter = st.number_input("Min Salary ($)", min_value=0, value=0, step=10000, key=f"min_salary_{title.replace(' ', '_')}")
            with salary_col2:
                max_salary_filter = st.number_input("Max Salary ($)", min_value=0, value=0, step=10000, key=f"max_salary_{title.replace(' ', '_')}")
        else:
            # Original filters
            filter_cols = st.columns(4)
            
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
        
        # Apply filters - we need to preserve the _original_job_index during filtering
        display_df = filtered_df.copy()
        
        # Include the tracking column from original df for filtering operations
        if '_original_job_index' in df.columns:
            display_df['_original_job_index'] = df['_original_job_index']
        
        if title_filter:
            display_df = display_df[display_df["Title"].str.contains(title_filter, case=False, na=False)]
        if company_filter:
            display_df = display_df[display_df["Company"].str.contains(company_filter, case=False, na=False)]
        if location_filter:
            display_df = display_df[display_df["Location"].str.contains(location_filter, case=False, na=False)]
        if work_type_filter != "All":
            display_df = display_df[display_df["Work Location Type"] == work_type_filter]
        
        # Additional filters for cleaned data
        if is_cleaned_data:
            if exp_level_filter != "All":
                display_df = display_df[display_df["Experience Level"] == exp_level_filter]
            
            # Salary range filter
            if min_salary_filter > 0 or max_salary_filter > 0:
                # Extract salary values from the formatted range strings
                def extract_min_salary(salary_str):
                    if pd.isna(salary_str) or salary_str == "N/A":
                        return 0
                    import re
                    match = re.search(r'\$([0-9,]+)', str(salary_str))
                    if match:
                        return int(match.group(1).replace(',', ''))
                    return 0
                
                display_df['_min_salary_numeric'] = display_df["Salary Range"].apply(extract_min_salary)
                
                if min_salary_filter > 0:
                    display_df = display_df[display_df['_min_salary_numeric'] >= min_salary_filter]
                if max_salary_filter > 0:
                    display_df = display_df[display_df['_min_salary_numeric'] <= max_salary_filter]
                
                # Remove the temporary column
                if '_min_salary_numeric' in display_df.columns:
                    display_df = display_df.drop('_min_salary_numeric', axis=1)
        
        # Show filter results info
        if len(display_df) != len(filtered_df):
            st.info(f"Showing {len(display_df)} of {len(filtered_df)} jobs after filtering")
        
        # Display the filtered table with row selection
        if not display_df.empty:
            st.markdown("💡 **Click on a row to view detailed job information**")
            
            # Create a copy for display, removing the original index tracking column if it exists
            # but preserve the tracking information separately
            display_columns_to_show = [col for col in display_df.columns if col != '_original_job_index']
            display_with_index = display_df[display_columns_to_show].reset_index(drop=True)
            
            # Create a mapping from the reset index to the original job index
            if '_original_job_index' in display_df.columns:
                # Extract the original job indices corresponding to the filtered rows
                original_indices_mapping = display_df['_original_job_index'].reset_index(drop=True)
            else:
                original_indices_mapping = None
            
            # Display the dataframe with click handling
            if is_cleaned_data:
                # Enhanced column config for cleaned data
                column_config = {
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
                        "Work Type",
                        help="Remote/Hybrid/On-site",
                        width="small"
                    ),
                    "Experience Level": st.column_config.TextColumn(
                        "Experience",
                        help="AI-classified experience level",
                        width="small"
                    ),
                    "Years Experience": st.column_config.NumberColumn(
                        "Years",
                        help="Required years of experience",
                        width="small"
                    ),
                    "Salary Range": st.column_config.TextColumn(
                        "Salary Range",
                        help="AI-extracted salary information",
                        width="medium"
                    )
                }
            else:
                # Original column config
                column_config = {
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
            
            selected_indices = st.dataframe(
                display_with_index,
                use_container_width=True,
                height=min(1000, len(display_with_index) * 35 + 50),  # Dynamic height to show all rows
                hide_index=True,
                on_select="rerun",
                selection_mode="single-row",
                column_config=column_config
            )
            
            # Handle row selection
            if selected_indices.selection.rows:
                selected_row_index = selected_indices.selection.rows[0]
                
                # Check if we have the original job index mapping
                if original_indices_mapping is not None:
                    # Get the original job index from the mapping
                    original_job_index = original_indices_mapping.iloc[selected_row_index]
                    
                    # Get the job data from current_page_jobs using the original index
                    if original_job_index < len(current_page_jobs):
                        selected_job_data = current_page_jobs[original_job_index]
                    else:
                        selected_job_data = None
                else:
                    # Fallback to the old method if no tracking mapping
                    actual_job_index = start_idx + selected_row_index
                    if actual_job_index < len(jobs_data):
                        selected_job_data = jobs_data[actual_job_index]
                    else:
                        selected_job_data = None
                
                if selected_job_data:
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
            all_job_data = [format_job_for_display(job, is_cleaned=is_cleaned_data) for job in jobs_data]
            csv_df = pd.DataFrame(all_job_data)
            
            # Filter to only requested columns for CSV
            if not csv_df.empty:
                available_cols = [col for col in display_columns if col in csv_df.columns]
                csv_df = csv_df[available_cols]
            
            csv = csv_df.to_csv(index=False)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename_prefix = "ai_enhanced" if is_cleaned_data else "job_search"
            
            st.download_button(
                label="Click to Download",
                data=csv,
                file_name=f"{filename_prefix}_results_{timestamp}.csv",
                mime="text/csv",
                key=f"download_btn_{title.replace(' ', '_')}"
            )
    else:
        st.info("No jobs to display.")
