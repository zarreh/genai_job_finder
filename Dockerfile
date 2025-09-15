FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies (minimal)
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Install Poetry
RUN pip install --no-cache-dir poetry==1.8.3

# Configure Poetry to not create virtual environment
ENV POETRY_NO_INTERACTION=1 \
    POETRY_VENV_IN_PROJECT=false \
    POETRY_CACHE_DIR=/tmp/poetry_cache

# Copy dependency files
COPY pyproject.toml poetry.lock ./

# Install dependencies directly to system Python (no venv)
RUN poetry config virtualenvs.create false \
    && poetry install --no-dev --no-root \
    && rm -rf $POETRY_CACHE_DIR \
    && rm -rf /root/.cache \
    && rm -rf /tmp/*

# Copy application code
COPY . .

# Install the application
RUN poetry install --no-dev \
    && rm -rf $POETRY_CACHE_DIR \
    && rm -rf /root/.cache

# Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser \
    && chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8501

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

# Run the application directly with streamlit (since dependencies are in system Python)
CMD ["streamlit", "run", "genai_job_finder/frontend/app.py", "--server.port=8501", "--server.address=0.0.0.0"]