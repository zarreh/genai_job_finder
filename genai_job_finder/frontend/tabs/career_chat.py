import streamlit as st
import tempfile
import os
from pathlib import Path
from typing import Optional

from ..utils.chat_service import CareerChatService
from ..config import get_chat_config


def render_career_chat_tab():
    """Render the career chat tab with LLM assistant."""
    
    # Initialize chat service
    if "chat_service" not in st.session_state:
        config = get_chat_config()
        st.session_state.chat_service = CareerChatService(config)
        st.session_state.chat_config = config
    
    # Initialize chat history
    if "chat_messages" not in st.session_state:
        st.session_state.chat_messages = []
        # Add welcome message
        welcome_msg = st.session_state.chat_service.get_welcome_message()
        st.session_state.chat_messages.append({"role": "assistant", "content": welcome_msg})
    
    # Initialize resume state
    if "resume_uploaded" not in st.session_state:
        st.session_state.resume_uploaded = False
    
    st.header("💼 Career Finding Assistant")
    
    # Import LLM configuration
    from ...llm_config import frontend_chat_llm, frontend_resume_llm
    st.markdown(f"**🤖 Chat:** {frontend_chat_llm} | **📄 Resume:** {frontend_resume_llm}")
    
    # Show status info
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.session_state.resume_uploaded:
            st.success("📄 Resume Analyzed")
        else:
            st.info("📤 Upload Resume")
    
    with col2:
        try:
            st.session_state.chat_service.llm.invoke("test")
            st.success("🤖 AI Connected")
        except:
            st.error("🤖 AI Offline")
    
    with col3:
        st.info(f"💬 {len(st.session_state.chat_messages)} Messages")
    
    # Chat container
    chat_container = st.container()
    
    # Display chat messages
    with chat_container:
        for message in st.session_state.chat_messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
    
    # File upload section (only show if no resume uploaded yet)
    if not st.session_state.resume_uploaded:
        st.subheader("📄 Upload Your Resume")
        uploaded_file = st.file_uploader(
            "Upload your resume (PDF, DOC, DOCX)",
            type=['pdf', 'doc', 'docx'],
            key="resume_uploader"
        )
        
        if uploaded_file is not None:
            if st.button("📤 Analyze Resume", type="primary"):
                with st.spinner("🔍 Analyzing your resume..."):
                    # Save uploaded file temporarily
                    with tempfile.NamedTemporaryFile(delete=False, suffix=f".{uploaded_file.name.split('.')[-1]}") as tmp_file:
                        tmp_file.write(uploaded_file.getvalue())
                        tmp_file_path = tmp_file.name
                    
                    try:
                        # Process resume with chat service
                        response = st.session_state.chat_service.process_resume(tmp_file_path)
                        
                        # Add user message (resume upload)
                        st.session_state.chat_messages.append({
                            "role": "user", 
                            "content": f"📄 Uploaded resume: {uploaded_file.name}"
                        })
                        
                        # Add assistant response
                        st.session_state.chat_messages.append({
                            "role": "assistant", 
                            "content": response
                        })
                        
                        st.session_state.resume_uploaded = True
                        st.rerun()
                        
                    except Exception as e:
                        st.error(f"Error analyzing resume: {str(e)}")
                    finally:
                        # Clean up temporary file
                        os.unlink(tmp_file_path)
    
    # Chat input
    if user_input := st.chat_input("Ask me about your career, job search, or upload your resume..."):
        # Add user message
        st.session_state.chat_messages.append({"role": "user", "content": user_input})
        
        # Get assistant response
        with st.spinner("🤔 Thinking..."):
            response = st.session_state.chat_service.get_response(user_input)
            st.session_state.chat_messages.append({"role": "assistant", "content": response})
        
        st.rerun()
    
    # Chat controls
    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("🔄 New Conversation"):
            st.session_state.chat_messages = []
            st.session_state.resume_uploaded = False
            config = get_chat_config()
            st.session_state.chat_service = CareerChatService(config)
            st.session_state.chat_config = config
            welcome_msg = st.session_state.chat_service.get_welcome_message()
            st.session_state.chat_messages.append({"role": "assistant", "content": welcome_msg})
            st.rerun()
    
    with col2:
        if st.button("📥 Download Chat History"):
            chat_text = "\n\n".join([
                f"**{msg['role'].title()}:** {msg['content']}" 
                for msg in st.session_state.chat_messages
            ])
            st.download_button(
                label="💾 Download as Text",
                data=chat_text,
                file_name="career_chat_history.txt",
                mime="text/plain"
            )