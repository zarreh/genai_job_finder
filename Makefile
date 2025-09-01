# GenAI Job Finder Makefile

.PHONY: help install run-parser run-parser-mod run-pipeline run-cleaner run-frontend run-company-enrichment show-company-stats test clean

# Default target
help:
	@echo "Available targets:"
	@echo "  install              - Install dependencies using Poetry"
	@echo "  run-parser           - Run the LinkedIn job parser (simple script)"
	@echo "  run-parser-mod       - Run the LinkedIn job parser (as module)"
	@echo "  run-pipeline         - Run parser + data cleaner pipeline (full processing)"
	@echo "  run-cleaner          - Run data cleaner only on existing data"
	@echo "  run-frontend         - Run the frontend application with AI features"
	@echo "  run-company-enrichment - Enrich companies with detailed information"
	@echo "  show-company-stats   - Show company enrichment statistics"
	@echo "  test                 - Run tests"
	@echo "  clean                - Clean up temporary files"

# Install dependencies
install:
	poetry install

# Run the LinkedIn parser (simple script)
run-parser:
	poetry run python run_parser.py

# Run the LinkedIn parser (as module)
run-parser-mod:
	poetry run python -m genai_job_finder.linkedin_parser.run_parser

# Run full pipeline: parser + data cleaner
run-pipeline:
	@echo "🚀 Running full processing pipeline..."
	@echo "📥 Step 1: Running LinkedIn parser..."
	poetry run python run_parser.py
	@echo "🧹 Step 2: Running AI data cleaner..."
	poetry run python -m genai_job_finder.data_cleaner.run_graph --verbose
	@echo "✅ Pipeline complete! Check data/jobs.db for results."

# Run data cleaner only
run-cleaner:
	@echo "🧹 Running AI data cleaner on existing data..."
	poetry run python -m genai_job_finder.data_cleaner.run_graph --verbose

# Run the frontend application with AI features
run-frontend:
	@echo "🚀 Starting GenAI Job Finder Frontend..."
	@echo "📊 Features:"
	@echo "  - Live LinkedIn job search with automatic AI enhancement"
	@echo "  - Stored job database browsing"
	@echo "  - 🤖 AI-enhanced job data with cleaning"
	@echo "  - Enhanced filtering and display"
	@echo ""
	@echo "🔍 Checking Ollama availability..."
	@if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then \
		echo "✅ Ollama is running - AI features available"; \
	else \
		echo "⚠️  Ollama not detected at localhost:11434"; \
		echo "   AI enhancement features may not work"; \
		echo "   Start Ollama to enable full functionality"; \
	fi
	@echo ""
	@echo "🌟 Starting frontend..."
	@echo "📱 Access at: http://localhost:8501"
	@echo "💡 Use Ctrl+C to stop"
	@echo ""
	@export PYTHONPATH="${PYTHONPATH}:$(PWD)" && \
	poetry run streamlit run genai_job_finder/frontend/app.py \
		--server.port 8501 \
		--server.address 0.0.0.0 \
		--server.headless true \
		--browser.gatherUsageStats false \
		--logger.level info

# Run company enrichment to add detailed company information
run-company-enrichment:
	@echo "🏢 Starting company information enrichment..."
	@echo "📊 This will add company size, followers, and industry data"
	@echo ""
	poetry run python genai_job_finder/linkedin_parser/company_enrichment.py --create-missing
	@echo "🔍 Enriching companies with detailed information..."
	poetry run python genai_job_finder/linkedin_parser/company_enrichment.py --limit 20
	@echo "✅ Company enrichment complete!"

# Show company statistics
show-company-stats:
	@echo "📊 Company Database Statistics"
	@echo "=============================="
	poetry run python genai_job_finder/linkedin_parser/company_enrichment.py --show-missing

# Run tests
test:
	poetry run pytest

# Clean up temporary files
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name ".coverage" -delete
