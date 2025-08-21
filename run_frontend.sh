#!/bin/bash
# Launch script for GenAI Job Finder Frontend

echo "Starting GenAI Job Finder Frontend..."
echo "The application will be available at: http://localhost:8501"
echo "Press Ctrl+C to stop the application"
echo ""

cd /home/alireza/projects/genai_job_finder
poetry run streamlit run genai_job_finder/frontend/app.py --server.address localhost --server.port 8501 --browser.gatherUsageStats false
