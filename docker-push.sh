#!/bin/bash
# Docker Hub Build and Push Script
# Usage: ./docker-push.sh [version]

set -e

# Configuration
DOCKER_USERNAME="zarreh"
IMAGE_NAME="genai-job-finder"
REGISTRY="docker.io"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}"
    exit 1
}

# Get version from argument or use 'latest'
VERSION=${1:-latest}
FULL_IMAGE_NAME="${REGISTRY}/${DOCKER_USERNAME}/${IMAGE_NAME}"

log "Starting Docker build and push process..."
log "Image: ${FULL_IMAGE_NAME}:${VERSION}"

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    error "Docker is not running. Please start Docker and try again."
fi

# Check if user is logged in to Docker Hub
if ! docker info | grep -q "Username: ${DOCKER_USERNAME}"; then
    warn "Not logged in to Docker Hub. Attempting login..."
    echo "Please enter your Docker Hub credentials:"
    docker login
fi

# Build the image
log "Building Docker image..."
docker build -t "${FULL_IMAGE_NAME}:${VERSION}" .

# Tag as latest if version is not latest
if [ "$VERSION" != "latest" ]; then
    log "Tagging as latest..."
    docker tag "${FULL_IMAGE_NAME}:${VERSION}" "${FULL_IMAGE_NAME}:latest"
fi

# Push the image(s)
log "Pushing image to Docker Hub..."
docker push "${FULL_IMAGE_NAME}:${VERSION}"

if [ "$VERSION" != "latest" ]; then
    log "Pushing latest tag..."
    docker push "${FULL_IMAGE_NAME}:latest"
fi

# Show image info
log "Image successfully pushed!"
echo ""
echo -e "${BLUE}Image Details:${NC}"
echo "Repository: ${FULL_IMAGE_NAME}"
echo "Tags: ${VERSION}$([ "$VERSION" != "latest" ] && echo ", latest")"
echo ""
echo -e "${BLUE}Usage Examples:${NC}"
echo "docker pull ${FULL_IMAGE_NAME}:${VERSION}"
echo "docker run -p 8501:8501 ${FULL_IMAGE_NAME}:${VERSION}"
echo ""
echo -e "${BLUE}Docker Compose:${NC}"
echo "The docker-compose.yml is already configured to use this image."
echo "Run: ./deploy.sh start"

log "Build and push completed successfully! ✓"