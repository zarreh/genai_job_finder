#!/bin/bash
# Quick deployment test script

set -e

echo "🚀 Testing GenAI Job Finder Docker Deployment"
echo "=============================================="

# Check prerequisites
echo "📋 Checking prerequisites..."
if ! command -v docker &> /dev/null; then
    echo "❌ Docker not found"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose not found"
    exit 1
fi

echo "✅ Prerequisites OK"

# Validate docker-compose.yml
echo "📝 Validating docker-compose.yml..."
if docker-compose config > /dev/null; then
    echo "✅ Docker Compose configuration valid"
else
    echo "❌ Docker Compose configuration invalid"
    exit 1
fi

# Test build context
echo "🔨 Testing build context..."
if [ -f "Dockerfile" ] && [ -f "pyproject.toml" ] && [ -f "poetry.lock" ]; then
    echo "✅ Build files present"
else
    echo "❌ Missing build files"
    exit 1
fi

# Check environment
echo "🔧 Checking environment setup..."
if [ -f ".env" ]; then
    echo "✅ Environment file found"
else
    echo "⚠️ No .env file - copying from .env.production"
    cp .env.production .env
fi

# Create necessary directories
echo "📁 Creating data directories..."
mkdir -p data
mkdir -p genai_job_finder/data
echo "✅ Data directories created"

echo ""
echo "🎉 Deployment test completed successfully!"
echo ""
echo "To deploy the application:"
echo "  • OpenAI mode:    ./deploy.sh start"
echo "  • Ollama mode:    ./deploy.sh start-ollama"
echo "  • Full setup:     ./deploy.sh start-full"
echo ""
echo "The application will be available at: http://localhost:8501"