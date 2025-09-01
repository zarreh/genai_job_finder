# GenAI Job Finder Makefile

.PHONY: help install run-parser run-pipeline run-cleaner run-frontend test clean

# Default target
help:
	@echo "Available targets:"
	@echo "  install              - Install dependencies using Poetry"
	@echo "  run-parser           - Run comprehensive LinkedIn parser with company intelligence"
	@echo "  run-pipeline         - Run parser + data cleaner pipeline (full processing)"
	@echo "  run-cleaner          - Run data cleaner only on existing data"
	@echo "  run-frontend         - Run the frontend application with AI features"
	@echo "  test                 - Run tests"
	@echo "  clean                - Clean up temporary files"
	@echo ""
	@echo "Advanced options:"
	@echo "  make run-parser QUERY='software engineer' LOCATION='Austin' JOBS=100"
	@echo "  make run-parser REMOTE=true PARTTIME=true"

# Install dependencies
install:
	poetry install

# Run comprehensive LinkedIn parser with integrated company intelligence
run-parser:
	@echo "🚀 COMPREHENSIVE LINKEDIN JOB PARSER"
	@echo "======================================"
	@echo "✨ Features:"
	@echo "   🎯 Job data extraction (20-column output)"
	@echo "   🏢 Company intelligence (size, followers, industry)"
	@echo "   📍 Location intelligence & work type classification"
	@echo "   🛡️ Smart rate limiting (5-10s delays)"
	@echo "   📤 Automatic CSV export"
	@echo ""
	@if [ "$(QUERY)" != "" ]; then \
		echo "🔍 Custom search query: $(QUERY)"; \
		ARGS="--search-query '$(QUERY)'"; \
	else \
		ARGS=""; \
	fi; \
	if [ "$(LOCATION)" != "" ]; then \
		echo "📍 Custom location: $(LOCATION)"; \
		ARGS="$$ARGS --location '$(LOCATION)'"; \
	fi; \
	if [ "$(JOBS)" != "" ]; then \
		echo "📊 Custom job count: $(JOBS)"; \
		ARGS="$$ARGS --total-jobs $(JOBS)"; \
	fi; \
	if [ "$(REMOTE)" = "true" ]; then \
		echo "🏠 Including remote jobs"; \
		ARGS="$$ARGS --remote"; \
	fi; \
	if [ "$(PARTTIME)" = "true" ]; then \
		echo "⏰ Including part-time jobs"; \
		ARGS="$$ARGS --parttime"; \
	fi; \
	echo ""; \
	echo "🚀 Starting parser..."; \
	poetry run python run_parser.py $$ARGS

# Run full pipeline: parser + data cleaner
run-pipeline:
	@echo "🚀 FULL PROCESSING PIPELINE"
	@echo "============================"
	@echo "📥 Step 1: Comprehensive LinkedIn parsing with company intelligence"
	@$(MAKE) run-parser
	@echo ""
	@echo "🧹 Step 2: AI-powered data cleaning and enhancement"
	poetry run python -m genai_job_finder.data_cleaner.run_graph --verbose
	@echo ""
	@echo "✅ PIPELINE COMPLETE!"
	@echo "💾 Results in data/jobs.db (raw + cleaned tables)"
	@echo "📤 CSV exports available in data/ folder"
	@echo "📊 Analyze: notebooks/job_analysis.ipynb"

# Run data cleaner only
run-cleaner:
	@echo "🧹 Running AI data cleaner on existing data..."
	poetry run python -m genai_job_finder.data_cleaner.run_graph --verbose

# Run the frontend application with AI features
run-frontend:
	@echo "🚀 GENAI JOB FINDER FRONTEND"
	@echo "============================"
	@echo "📊 Features:"
	@echo "  - Live LinkedIn job search with automatic AI enhancement"
	@echo "  - Stored job database browsing with company intelligence"
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
	@echo "🌟 Starting frontend at http://localhost:8501"
	@echo "💡 Use Ctrl+C to stop"
	@echo ""
	@export PYTHONPATH="${PYTHONPATH}:$(PWD)" && \
	poetry run streamlit run genai_job_finder/frontend/app.py \
		--server.port 8501 \
		--server.address 0.0.0.0 \
		--server.headless true \
		--browser.gatherUsageStats false \
		--logger.level info

# Run tests
test:
	poetry run pytest

# Clean up temporary files
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name ".coverage" -delete
