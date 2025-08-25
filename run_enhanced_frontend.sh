#!/bin/bash

# Enhanced GenAI Job Finder Frontend with Data Cleaner Integration
# This script runs the Streamlit frontend with AI-powered job data cleaning

echo "🚀 Starting Enhanced GenAI Job Finder Frontend..."
echo "📊 Features:"
echo "  - Live LinkedIn job search with automatic AI enhancement"
echo "  - Stored job database browsing"
echo "  - 🤖 AI-enhanced job data with cleaning"
echo "  - Enhanced filtering and display"
echo ""

# Activate virtual environment
source /home/alireza/.cache/pypoetry/virtualenvs/genai-job-finder-Y_k-9c-5-py3.12/bin/activate

# Set Python path
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Check if Ollama is running (required for AI enhancement)
echo "🔍 Checking Ollama availability..."
if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo "✅ Ollama is running - AI features available"
else
    echo "⚠️  Ollama not detected at localhost:11434"
    echo "   AI enhancement features may not work"
    echo "   Start Ollama to enable full functionality"
fi

echo ""
echo "🌟 Starting frontend..."
echo "📱 Access at: http://localhost:8501"
echo "💡 Use Ctrl+C to stop"
echo ""

# Run Streamlit
streamlit run genai_job_finder/frontend/app.py \
    --server.port 8501 \
    --server.address 0.0.0.0 \
    --server.headless true \
    --browser.gatherUsageStats false \
    --logger.level info
