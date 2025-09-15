#!/bin/bash
# GenAI Job Finder - Deployment Script
# Usage: ./deploy.sh [option]
# Options: start, stop, restart, logs, status, update, backup

set -e

PROJECT_NAME="genai-job-finder"
COMPOSE_FILE="docker-compose.yml"
ENV_FILE=".env.production"

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

# Check prerequisites
check_prerequisites() {
    log "Checking prerequisites..."
    
    if ! command -v docker &> /dev/null; then
        error "Docker is not installed. Please install Docker first."
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        error "Docker Compose is not installed. Please install Docker Compose first."
    fi
    
    if [ ! -f "$COMPOSE_FILE" ]; then
        error "docker-compose.yml not found in current directory"
    fi
    
    log "Prerequisites check passed ✓"
}

# Setup environment
setup_environment() {
    log "Setting up environment..."
    
    if [ ! -f ".env" ]; then
        if [ -f "$ENV_FILE" ]; then
            log "Copying production environment file..."
            cp "$ENV_FILE" ".env"
        else
            warn "No .env file found. Please create one before deployment."
            echo "You can copy from .env.example and modify as needed."
        fi
    fi
    
    # Create necessary directories
    mkdir -p data
    mkdir -p genai_job_finder/data
    
    log "Environment setup completed ✓"
}

# Build and start services
start_services() {
    log "Building and starting services..."
    
    # Build the application
    docker-compose build --no-cache
    
    # Start services based on profile
    if [ "$1" = "full" ] || [ "$1" = "ollama" ]; then
        log "Starting with Ollama service..."
        docker-compose --profile ollama up -d
    else
        log "Starting without Ollama (OpenAI mode)..."
        docker-compose up -d genai-job-finder
    fi
    
    log "Services started ✓"
    log "Application will be available at: http://localhost:8501"
}

# Build and push to Docker Hub
build_and_push() {
    log "Building and pushing to Docker Hub..."
    
    VERSION=${1:-latest}
    
    # Use the docker-push.sh script
    if [ -f "./docker-push.sh" ]; then
        ./docker-push.sh "$VERSION"
    else
        error "docker-push.sh script not found"
    fi
}

# Pull and start services (no build)
start_services_pull() {
    log "Pulling and starting services..."
    
    # Pull latest images
    docker-compose pull
    
    # Start services based on profile
    if [ "$1" = "full" ] || [ "$1" = "ollama" ]; then
        log "Starting with Ollama service..."
        docker-compose --profile ollama up -d
    else
        log "Starting without Ollama (OpenAI mode)..."
        docker-compose up -d genai-job-finder
    fi
    
    log "Services started ✓"
    log "Application will be available at: http://localhost:8501"
}

# Stop services
stop_services() {
    log "Stopping services..."
    docker-compose down
    log "Services stopped ✓"
}

# Restart services
restart_services() {
    log "Restarting services..."
    stop_services
    start_services "$1"
    log "Services restarted ✓"
}

# Show logs
show_logs() {
    if [ -n "$1" ]; then
        docker-compose logs -f "$1"
    else
        docker-compose logs -f
    fi
}

# Show status
show_status() {
    log "Service status:"
    docker-compose ps
    
    log "\nHealth status:"
    docker-compose exec genai-job-finder curl -f http://localhost:8501/healthz 2>/dev/null && echo "✓ Application is healthy" || echo "✗ Application health check failed"
}

# Update application
update_application() {
    log "Updating application..."
    
    # Pull latest changes
    git pull origin main
    
    # Rebuild and restart
    docker-compose build --no-cache
    docker-compose up -d --force-recreate
    
    log "Application updated ✓"
}

# Backup data
backup_data() {
    log "Creating backup..."
    
    BACKUP_DIR="backups/$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$BACKUP_DIR"
    
    # Backup databases
    cp -r data "$BACKUP_DIR/"
    cp -r genai_job_finder/data "$BACKUP_DIR/"
    
    # Create archive
    tar -czf "$BACKUP_DIR.tar.gz" "$BACKUP_DIR"
    rm -rf "$BACKUP_DIR"
    
    log "Backup created: $BACKUP_DIR.tar.gz ✓"
}

# Cleanup old containers and images
cleanup() {
    log "Cleaning up old containers and images..."
    
    docker system prune -f
    docker volume prune -f
    
    log "Cleanup completed ✓"
}

# Main script logic
case "${1:-start}" in
    start)
        check_prerequisites
        setup_environment
        start_services "${2:-default}"
        ;;
    start-pull)
        check_prerequisites
        setup_environment
        start_services_pull "${2:-default}"
        ;;
    start-ollama)
        check_prerequisites
        setup_environment
        start_services "ollama"
        ;;
    start-full)
        check_prerequisites
        setup_environment
        start_services "full"
        ;;
    push)
        check_prerequisites
        build_and_push "$2"
        ;;
    stop)
        stop_services
        ;;
    restart)
        check_prerequisites
        restart_services "${2:-default}"
        ;;
    restart-ollama)
        check_prerequisites
        restart_services "ollama"
        ;;
    logs)
        show_logs "$2"
        ;;
    status)
        show_status
        ;;
    update)
        update_application
        ;;
    backup)
        backup_data
        ;;
    cleanup)
        cleanup
        ;;
    *)
        echo "Usage: $0 {start|start-pull|start-ollama|start-full|push|stop|restart|restart-ollama|logs|status|update|backup|cleanup}"
        echo ""
        echo "Commands:"
        echo "  start         - Build and start application (OpenAI mode)"
        echo "  start-pull    - Pull from Docker Hub and start (no build)"
        echo "  start-ollama  - Start application with Ollama"
        echo "  start-full    - Start application with Ollama and setup"
        echo "  push [version]- Build and push to Docker Hub (zarreh/genai-job-finder)"
        echo "  stop          - Stop all services"
        echo "  restart       - Restart application (OpenAI mode)"
        echo "  restart-ollama- Restart application with Ollama"
        echo "  logs [service]- Show logs (optionally for specific service)"
        echo "  status        - Show service status and health"
        echo "  update        - Update application from git and restart"
        echo "  backup        - Create backup of data"
        echo "  cleanup       - Clean up old containers and images"
        exit 1
        ;;
esac