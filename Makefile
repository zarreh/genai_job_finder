# GenAI Job Finder Makefile

.PHONY: help install run-parser run-frontend test clean

# Default target
help:
	@echo "Available targets:"
	@echo "  install        - Install dependencies using Poetry"
	@echo "  run-parser     - Run the LinkedIn job parser (simple script)"
	@echo "  run-parser-mod - Run the LinkedIn job parser (as module)"
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
