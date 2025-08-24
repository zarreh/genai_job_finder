# GenAI Job Finder Makefile

.PHONY: help install run-parser run-parser-mod run-pipeline run-cleaner run-frontend test clean

# Default target
help:
	@echo "Available targets:"
	@echo "  install        - Install dependencies using Poetry"
	@echo "  run-parser     - Run the LinkedIn job parser (simple script)"
	@echo "  run-parser-mod - Run the LinkedIn job parser (as module)"
	@echo "  run-pipeline   - Run parser + data cleaner pipeline (full processing)"
	@echo "  run-cleaner    - Run data cleaner only on existing data"
	@echo "  run-frontend   - Run the frontend application"
	@echo "  test           - Run tests"
	@echo "  clean          - Clean up temporary files"

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

# Run the frontend application
run-frontend:
	poetry run python genai_job_finder/frontend/run.py

# Run tests
test:
	poetry run pytest

# Clean up temporary files
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name ".coverage" -delete
