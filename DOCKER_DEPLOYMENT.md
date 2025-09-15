# Docker Deployment Guide

## GenAI Job Finder - Server Deployment

This guide explains how to deploy the GenAI Job Finder application on a server using Docker.

## Prerequisites

- Docker 20.10+
- Docker Compose 2.0+
- Git
- 4GB+ RAM recommended
- 10GB+ disk space

## Quick Start

1. **Clone the repository:**
   ```bash
   git clone <your-repo-url>
   cd genai_job_finder
   ```

2. **Set up environment:**
   ```bash
   cp .env.production .env
   # Edit .env with your configuration
   ```

3. **Deploy with OpenAI (recommended for production):**
   ```bash
   ./deploy.sh start
   ```

4. **Or deploy with Ollama (local LLM):**
   ```bash
   ./deploy.sh start-ollama
   ```

## Deployment Options

### Option 1: OpenAI Mode (Recommended)
- Uses OpenAI GPT-3.5 Turbo
- Requires OpenAI API key
- Lower resource usage
- Better performance

```bash
# Edit .env file
CHAT_CONFIG_MODE=openai
OPENAI_API_KEY=your_api_key_here

# Deploy
./deploy.sh start
```

### Option 2: Ollama Mode (Self-hosted)
- Uses local Llama 3.2 model
- No external API required
- Higher resource usage (8GB+ RAM recommended)
- Complete privacy

```bash
# Deploy with Ollama
./deploy.sh start-ollama
```

### Option 3: Mixed Mode
- Ollama for chat, OpenAI for resume analysis
- Balanced approach

```bash
# Edit .env file
CHAT_CONFIG_MODE=mixed
OPENAI_API_KEY=your_api_key_here

# Deploy
./deploy.sh start-ollama
```

## Configuration

### Environment Variables

Key configuration in `.env`:

```bash
# Chat Configuration
CHAT_CONFIG_MODE=default  # default, mixed, openai, env

# OpenAI (if using)
OPENAI_API_KEY=your_api_key_here

# Application
STREAMLIT_SERVER_PORT=8501
DATABASE_URL=sqlite:///data/jobs.db

# Security
SECRET_KEY=your_secret_key_here_change_in_production
```

### LLM Provider Configuration

The application supports flexible LLM configuration:

1. **Default Mode**: All services use Ollama
2. **Mixed Mode**: Chat uses Ollama, Resume analysis uses OpenAI
3. **OpenAI Mode**: All services use OpenAI
4. **Env Mode**: Custom configuration via environment variables

## Deployment Commands

```bash
# Start services
./deploy.sh start              # OpenAI mode
./deploy.sh start-ollama       # With Ollama
./deploy.sh start-full         # With Ollama + model download

# Monitor
./deploy.sh status             # Check service status
./deploy.sh logs               # View logs
./deploy.sh logs genai-job-finder  # App logs only

# Maintenance
./deploy.sh restart            # Restart services
./deploy.sh stop               # Stop services
./deploy.sh update             # Update from git
./deploy.sh backup             # Backup data
./deploy.sh cleanup            # Clean old containers
```

## Service Architecture

### Services Overview

1. **genai-job-finder**: Main Streamlit application
2. **ollama**: Local LLM service (optional)
3. **ollama-setup**: Model download service (optional)

### Ports

- **8501**: Streamlit application
- **11434**: Ollama API (if using Ollama)

### Volumes

- `./data`: Application databases
- `./genai_job_finder/data`: User files and CVs
- `ollama_data`: Ollama models (if using Ollama)

## Server Setup

### 1. System Requirements

**Minimum (OpenAI mode):**
- 2 CPU cores
- 4GB RAM
- 10GB disk space

**Recommended (Ollama mode):**
- 4 CPU cores
- 8GB RAM
- 20GB disk space

### 2. Firewall Configuration

```bash
# Allow HTTP traffic
sudo ufw allow 8501/tcp

# If using Ollama externally
sudo ufw allow 11434/tcp
```

### 3. Reverse Proxy (Optional)

For production, use nginx or traefik:

```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://localhost:8501;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## Monitoring

### Health Checks

The application includes health checks:

```bash
# Check application health
curl http://localhost:8501/healthz

# Check via deployment script
./deploy.sh status
```

### Logs

```bash
# View all logs
./deploy.sh logs

# View specific service logs
./deploy.sh logs genai-job-finder
./deploy.sh logs ollama

# Follow logs in real-time
docker-compose logs -f genai-job-finder
```

## Backup and Recovery

### Automatic Backups

```bash
# Create backup
./deploy.sh backup

# Backups are stored in backups/ directory
```

### Manual Backup

```bash
# Backup data directories
tar -czf backup_$(date +%Y%m%d).tar.gz data/ genai_job_finder/data/

# Backup Docker volumes
docker run --rm -v genai-job-finder_ollama_data:/data -v $(pwd):/backup alpine tar czf /backup/ollama_backup.tar.gz -C /data .
```

### Recovery

```bash
# Restore data
tar -xzf backup_YYYYMMDD.tar.gz

# Restart services
./deploy.sh restart
```

## Troubleshooting

### Common Issues

1. **Application not starting:**
   ```bash
   ./deploy.sh logs genai-job-finder
   ```

2. **Ollama model download fails:**
   ```bash
   docker-compose exec ollama ollama pull llama3.2:3b
   ```

3. **Permission issues:**
   ```bash
   sudo chown -R 1000:1000 data/ genai_job_finder/data/
   ```

4. **Port conflicts:**
   ```bash
   # Check what's using port 8501
   sudo netstat -tlnp | grep 8501
   ```

### Performance Tuning

1. **For Ollama mode:**
   - Increase RAM allocation
   - Use SSD storage
   - Monitor GPU usage if available

2. **For OpenAI mode:**
   - Tune API rate limits
   - Monitor API usage
   - Configure appropriate timeouts

## Security

### Best Practices

1. **Change default secrets:**
   ```bash
   # Generate new secret key
   python -c "import secrets; print(secrets.token_hex(32))"
   ```

2. **Use HTTPS in production:**
   - Set up SSL certificates
   - Configure reverse proxy with SSL

3. **Regular updates:**
   ```bash
   ./deploy.sh update
   ```

4. **Monitor logs:**
   ```bash
   ./deploy.sh logs | grep ERROR
   ```

## Scaling

### Horizontal Scaling

For high traffic, consider:

1. **Load balancer** with multiple app instances
2. **External database** (PostgreSQL)
3. **Redis cache** for sessions
4. **CDN** for static assets

### Resource Scaling

```yaml
# In docker-compose.yml
services:
  genai-job-finder:
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 4G
        reservations:
          cpus: '1.0'
          memory: 2G
```

## Support

For issues and questions:

1. Check logs: `./deploy.sh logs`
2. Check status: `./deploy.sh status`
3. Review this documentation
4. Check GitHub issues

## Updates

To update the application:

```bash
# Automatic update
./deploy.sh update

# Manual update
git pull origin main
docker-compose build --no-cache
./deploy.sh restart
```

---

**Note**: Replace `<your-repo-url>` with your actual repository URL and update domain names as needed.