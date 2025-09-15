# GenAI Job Finder Makefile

.PHONY: help install run-parser run-pipeline run-cleaner run-frontend run-company-enrichment run-query-definition docker-build docker-push docker-deploy docker-deploy-local docker-deploy-ollama docker-stop docker-status docker-logs docker-restart test clean

# Default target
help:
	@echo "Available targets:"
	@echo "  install              - Install dependencies using Poetry"
	@echo "  run-parser           - Run comprehensive LinkedIn parser with company intelligence"
	@echo "  run-pipeline         - Run parser + data cleaner pipeline (full processing)"
	@echo "  run-cleaner          - Run data cleaner only on existing data"
	@echo "  run-frontend         - Run the frontend application with AI features"
	@echo "  run-company-enrichment - Run company enrichment pipeline separately"
	@echo "  run-query-definition - Generate LinkedIn job search queries from resume analysis"
	@echo ""
	@echo "Docker Deployment:"
	@echo "  docker-build         - Build Docker image locally"
	@echo "  docker-push          - Build and push to Docker Hub (zarreh/genai-job-finder)"
	@echo "  docker-deploy        - Deploy from Docker Hub (pull and start)"
	@echo "  docker-deploy-local  - Deploy with local build"
	@echo "  docker-deploy-ollama - Deploy with Ollama LLM support"
	@echo "  docker-stop          - Stop Docker deployment"
	@echo "  docker-status        - Show Docker deployment status"
	@echo "  docker-logs          - Show Docker logs"
	@echo "  docker-restart       - Restart Docker deployment"
	@echo ""
	@echo "Other:"
	@echo "  config               - Show current parser configuration"
	@echo "  test                 - Run tests"
	@echo "  clean                - Clean up temporary files"
	@echo ""
	@echo "Advanced options:"
	@echo "  make run-parser QUERY='software engineer' LOCATION='Austin' JOBS=100"
	@echo "  make run-parser REMOTE=true PARTTIME=true"
	@echo "  make run-company-enrichment STATS=true  # Show enrichment statistics"
	@echo "  make run-company-enrichment ENRICH=true # Enrich all companies"
	@echo "  make run-query-definition RESUME=path/to/resume.pdf"
	@echo "  make run-query-definition RESUME=path/to/resume.pdf PROVIDER=ollama"
	@echo ""
	@echo "Docker examples:"
	@echo "  make docker-push VERSION=v1.0.0    # Push with version tag"
	@echo "  make docker-logs SERVICE=genai-job-finder  # Show specific service logs"

# Install dependencies
install:
	poetry install

# Run comprehensive LinkedIn parser with integrated company intelligence
run-parser:
	@echo "🚀 COMPREHENSIVE LINKEDIN JOB PARSER (OPTIMIZED)"
	@echo "=================================================="
	@echo "✨ Features:"
	@echo "   🎯 Job data extraction (21-column output)"
	@echo "   🏢 Optimized company handling (lookup-first approach)"
	@echo "   📍 Location intelligence & work type classification"
	@echo "   🛡️ Smart rate limiting (5-10s delays)"
	@echo "   📤 Automatic CSV export"
	@echo "   ⚡ Avoids redundant company parsing"
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
	@echo "📥 Step 1: Comprehensive LinkedIn parsing with optimized company handling"
	@$(MAKE) run-parser
	@echo ""
	@echo "🏢 Step 2: Company enrichment for any missing company data"
	@echo "   (Only enriches companies that need additional information)"
	poetry run python run_company_enrichment.py --enrich-all --verbose
	@echo ""
	@echo "🧹 Step 3: AI-powered data cleaning and enhancement"
	poetry run python -m genai_job_finder.data_cleaner.run_graph --verbose
	@echo ""
	@echo "✅ PIPELINE COMPLETE!"
	@echo "💾 Results in data/jobs.db (jobs + companies + cleaned tables)"
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

# Run company enrichment pipeline separately
run-company-enrichment:
	@echo "🏢 COMPANY ENRICHMENT PIPELINE"
	@echo "=============================="
	@echo "📊 Features:"
	@echo "   🔍 Lookup-first approach (avoids redundant parsing)"
	@echo "   🏢 Separate company data management"
	@echo "   📈 Enrichment statistics and progress tracking"
	@echo "   ⚡ Efficient batch processing"
	@echo ""
	@if [ "$(STATS)" = "true" ]; then \
		echo "📊 Showing company enrichment statistics..."; \
		poetry run python run_company_enrichment.py --stats; \
	elif [ "$(ENRICH)" = "true" ]; then \
		echo "🚀 Starting company enrichment process..."; \
		poetry run python run_company_enrichment.py --enrich-all --verbose; \
	elif [ "$(COMPANY)" != "" ]; then \
		echo "🔍 Enriching specific company: $(COMPANY)"; \
		poetry run python run_company_enrichment.py --company "$(COMPANY)" --verbose; \
	elif [ "$(CREATE)" = "true" ]; then \
		echo "🏗️  Creating missing company records..."; \
		poetry run python run_company_enrichment.py --create-missing --verbose; \
	else \
		echo "💡 Usage examples:"; \
		echo "   make run-company-enrichment STATS=true     # Show statistics"; \
		echo "   make run-company-enrichment ENRICH=true    # Enrich all companies"; \
		echo "   make run-company-enrichment COMPANY='Microsoft'  # Enrich specific company"; \
		echo "   make run-company-enrichment CREATE=true    # Create missing company records"; \
		echo ""; \
		echo "📊 Showing current statistics:"; \
		poetry run python run_company_enrichment.py --stats; \
	fi

# Show current parser configuration
config:
	@echo "🔧 PARSER CONFIGURATION"
	@echo "======================="
	poetry run python -m genai_job_finder.linkedin_parser.config_manager --all

# Docker deployment targets
docker-build:
	@echo "🐳 BUILDING DOCKER IMAGE"
	@echo "========================"
	@echo "📦 Building: zarreh/genai-job-finder:latest"
	@echo ""
	./deploy.sh build

docker-push:
	@echo "🐳 BUILD AND PUSH TO DOCKER HUB"
	@echo "==============================="
	@echo "📦 Repository: zarreh/genai-job-finder"
	@echo "🚀 Building and pushing to Docker Hub..."
	@echo ""
	@if [ "$(VERSION)" != "" ]; then \
		echo "🏷️  Version: $(VERSION)"; \
		./deploy.sh push $(VERSION); \
	else \
		echo "🏷️  Version: latest"; \
		./deploy.sh push; \
	fi

docker-deploy:
	@echo "🐳 DEPLOY FROM DOCKER HUB"
	@echo "========================="
	@echo "📥 Pulling: zarreh/genai-job-finder:latest"
	@echo "🚀 Deploying with OpenAI configuration..."
	@echo ""
	./deploy.sh start-pull

docker-deploy-local:
	@echo "🐳 DEPLOY WITH LOCAL BUILD"
	@echo "=========================="
	@echo "🔨 Building locally and deploying..."
	@echo ""
	./deploy.sh start

docker-deploy-ollama:
	@echo "🐳 DEPLOY WITH OLLAMA"
	@echo "===================="
	@echo "🤖 Deploying with Ollama LLM support..."
	@echo ""
	./deploy.sh start-ollama

docker-stop:
	@echo "🐳 STOPPING DOCKER DEPLOYMENT"
	@echo "============================="
	./deploy.sh stop

docker-status:
	@echo "🐳 DOCKER DEPLOYMENT STATUS"
	@echo "==========================="
	./deploy.sh status

docker-logs:
	@echo "🐳 DOCKER DEPLOYMENT LOGS"
	@echo "========================="
	@if [ "$(SERVICE)" != "" ]; then \
		echo "📋 Showing logs for: $(SERVICE)"; \
		./deploy.sh logs $(SERVICE); \
	else \
		echo "📋 Showing all logs..."; \
		./deploy.sh logs; \
	fi

docker-restart:
	@echo "🐳 RESTARTING DOCKER DEPLOYMENT"
	@echo "==============================="
	./deploy.sh restart

# Generate LinkedIn job search queries from resume analysis
run-query-definition:
	@echo "🔍 RESUME-BASED JOB QUERY GENERATOR"
	@echo "==================================="
	@echo "🎯 Features:"
	@echo "   📄 Resume analysis (PDF/DOC/DOCX support)"
	@echo "   🤖 AI-powered job title extraction"
	@echo "   🔬 5 primary + 8 secondary job titles"
	@echo "   🚀 Future-focused career opportunities"
	@echo "   💾 JSON export support"
	@echo ""
	@if [ "$(RESUME)" != "" ]; then \
		echo "📄 Resume file: $(RESUME)"; \
		ARGS="$(RESUME)"; \
	else \
		echo "❌ Error: RESUME parameter required"; \
		echo "💡 Usage: make run-query-definition RESUME=path/to/resume.pdf"; \
		echo "💡 Examples:"; \
		echo "   make run-query-definition RESUME=data/Ali_Zarreh_CV_2025_08_30.pdf"; \
		echo "   make run-query-definition RESUME=resume.pdf PROVIDER=ollama"; \
		echo "   make run-query-definition RESUME=resume.pdf OUTPUT=queries.json"; \
		exit 1; \
	fi; \
	if [ "$(PROVIDER)" != "" ]; then \
		echo "🤖 LLM Provider: $(PROVIDER)"; \
		ARGS="$$ARGS --provider $(PROVIDER)"; \
	else \
		echo "🤖 LLM Provider: OpenAI (default)"; \
	fi; \
	if [ "$(MODEL)" != "" ]; then \
		echo "🧠 Model: $(MODEL)"; \
		ARGS="$$ARGS --model $(MODEL)"; \
	fi; \
	if [ "$(OUTPUT)" != "" ]; then \
		echo "💾 Output file: $(OUTPUT)"; \
		ARGS="$$ARGS --output $(OUTPUT)"; \
	fi; \
	if [ "$(VERBOSE)" = "true" ]; then \
		echo "🔍 Verbose mode enabled"; \
		ARGS="$$ARGS --verbose"; \
	fi; \
	echo ""; \
	echo "🚀 Starting analysis..."; \
	poetry run python -m genai_job_finder.query_definition.run_query_definition $$ARGS

# Clean up temporary files
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name ".coverage" -delete
