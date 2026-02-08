# Docker Deployment Guide

This guide covers deploying ForceAlignmentCutter using Docker and Docker Compose.

## Prerequisites

- Docker Engine 20.10+ ([Install Docker](https://docs.docker.com/engine/install/))
- Docker Compose 2.0+ (included with Docker Desktop)
- NVIDIA GPU with Docker GPU support for acceleration:
  - [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html)

## Quick Start

### 1. Build the Docker Image

```bash
make docker-build
# Or: ./docker.sh build
# Or: docker compose build
```

### 2. Start the Services

**Development Mode** (with code hot-reload):
```bash
make docker-up
# Or: ./docker.sh up
# Or: docker compose up -d
```

**Production Mode** (with Nginx reverse proxy):
```bash
make docker-prod-up
# Or: ./docker.sh prod-up
# Or: docker compose -f docker-compose.prod.yml up -d
```

### 3. Access the Application

**Development Mode:**
- Web Interface: http://localhost:8000/static/index.html
- API Documentation: http://localhost:8000/docs
- API Base URL: http://localhost:8000/api

**Production Mode:**
- Web Interface: http://localhost/static/index.html
- API Documentation: http://localhost/docs
- API Base URL: http://localhost/api

### 4. View Logs

```bash
make docker-logs
# Or: ./docker.sh logs
# Or: docker compose logs -f
```

### 5. Stop the Services

```bash
make docker-down
# Or: ./docker.sh down
# Or: docker compose down
```

## Docker Commands Reference

### Development Commands

| Command | Description |
|---------|-------------|
| `make docker-build` | Build Docker image |
| `make docker-up` | Start services in development mode |
| `make docker-down` | Stop all services |
| `make docker-logs` | View logs (follow mode) |
| `make docker-restart` | Restart all services |
| `make docker-shell` | Open bash shell in container |
| `make docker-clean` | Remove containers and volumes |

### Production Commands

| Command | Description |
|---------|-------------|
| `make docker-prod-build` | Build for production |
| `make docker-prod-up` | Start production services |
| `make docker-prod-down` | Stop production services |
| `make docker-prod-logs` | View production logs |

## Architecture

### Development Setup

```
┌─────────────────┐
│                 │
│  Your Browser   │
│                 │
└────────┬────────┘
         │
         │ :8000
         ▼
┌─────────────────┐     ┌──────────────┐
│                 │     │              │
│  FastAPI App    │────▶│  GPU (CUDA)  │
│  (Container)    │     │              │
│                 │     └──────────────┘
└─────────────────┘
         │
         ▼
    ┌────────┐
    │ Volume │
    │uploads/│
    └────────┘
```

### Production Setup

```
┌─────────────────┐
│                 │
│  Your Browser   │
│                 │
└────────┬────────┘
         │
         │ :80/:443
         ▼
┌─────────────────┐
│                 │
│  Nginx Proxy    │
│  (Container)    │
│                 │
└────────┬────────┘
         │
         │ :8000
         ▼
┌─────────────────┐     ┌──────────────┐
│                 │     │              │
│  FastAPI App    │────▶│  GPU (CUDA)  │
│  (Container)    │     │              │
│                 │     └──────────────┘
└─────────────────┘
         │
         ▼
    ┌────────┐
    │ Volume │
    │uploads/│
    └────────┘
```

## Configuration

### Environment Variables

Create a `.env` file in the project root (optional):

```bash
# API Configuration
API_HOST=0.0.0.0
API_PORT=8000

# CUDA Configuration
CUDA_VISIBLE_DEVICES=0

# Processing Defaults
DEFAULT_MIN_SILENCE_LEN=800
DEFAULT_MANUAL_SILENCE_LEN=300
DEFAULT_SILENCE_THRESH=-60
```

### GPU Configuration

**Enable GPU support** (requires NVIDIA Container Toolkit):

The GPU is enabled by default in `docker compose.yml`:

```yaml
deploy:
  resources:
    reservations:
      devices:
        - driver: nvidia
          count: 1
          capabilities: [gpu]
```

**To disable GPU** (use CPU only), comment out the `deploy` section in `docker compose.yml`.

### Volume Mounts

Persistent data is stored in volumes:

- `./uploads` - Uploaded and processed audio files
- `./static` - Web interface files
- `./api` - API source code (development mode only)
- `./src` - Utility source code (development mode only)

## Production Deployment

### 1. Build Production Image

```bash
make docker-prod-build
```

### 2. Configure Nginx (Optional)

Edit `nginx/nginx.conf` for custom configuration:

- Domain name
- SSL certificates
- Rate limiting
- Upload size limits

### 3. SSL/TLS Setup (HTTPS)

Place your SSL certificates in `nginx/ssl/`:

```bash
mkdir -p nginx/ssl
cp your-cert.pem nginx/ssl/cert.pem
cp your-key.pem nginx/ssl/key.pem
```

Uncomment the HTTPS server block in `nginx/nginx.conf`.

### 4. Start Production Services

```bash
make docker-prod-up
```

### 5. Monitor Services

```bash
# View logs
make docker-prod-logs

# Check container status
docker compose -f docker-compose.prod.yml ps

# View resource usage
docker stats
```

## Troubleshooting

### GPU Not Available

**Check NVIDIA Docker runtime:**
```bash
docker run --rm --gpus all nvidia/cuda:12.1.0-base-ubuntu22.04 nvidia-smi
```

If this fails, install [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html).

### Container Fails to Start

**View detailed logs:**
```bash
docker compose logs fastapi
```

**Check container status:**
```bash
docker compose ps
```

**Rebuild image:**
```bash
docker compose down
docker compose build --no-cache
docker compose up -d
```

### Permission Issues with Volumes

```bash
# Fix permissions
sudo chown -R $USER:$USER uploads/
chmod -R 755 uploads/
```

### Port Already in Use

**Change port in docker compose.yml:**
```yaml
ports:
  - "8001:8000"  # Host:Container
```

Or stop the conflicting service:
```bash
lsof -ti:8000 | xargs kill -9
```

### Out of Memory

**Reduce workers** in production:
```yaml
command: uvicorn api.main:app --host 0.0.0.0 --port 8000 --workers 2
```

**Or use CPU mode** by commenting out GPU deployment in docker compose.yml.

## Performance Tuning

### CPU Mode (No GPU)

Comment out the `deploy` section in `docker compose.yml`:

```yaml
# deploy:
#   resources:
#     reservations:
#       devices:
#         - driver: nvidia
#           count: 1
#           capabilities: [gpu]
```

### Increase Workers (Production)

For multi-core systems:

```yaml
command: uvicorn api.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Adjust Upload Limits

In `nginx/nginx.conf`:

```nginx
client_max_body_size 1G;  # Increase upload limit
```

## Maintenance

### Update Application Code

**Development mode** (with volume mounts):
```bash
# Code changes are reflected immediately
make docker-restart
```

**Production mode**:
```bash
make docker-prod-down
make docker-prod-build
make docker-prod-up
```

### Clean Up Old Data

```bash
# Remove old uploads (be careful!)
rm -rf uploads/*

# Clean Docker resources
make docker-clean
docker system prune -a
```

### Backup Data

```bash
# Backup uploads
tar -czf uploads-backup-$(date +%Y%m%d).tar.gz uploads/

# Backup entire app
docker compose down
tar -czf forcealignmentcutter-backup-$(date +%Y%m%d).tar.gz .
```

## Security Best Practices

1. **Use HTTPS in production** - Configure SSL certificates in Nginx
2. **Set upload limits** - Prevent disk space exhaustion
3. **Enable rate limiting** - Configured in Nginx
4. **Use secrets** - Store API keys in environment variables
5. **Regular updates** - Keep base images and dependencies updated
6. **Network isolation** - Use Docker networks for service communication
7. **Read-only containers** - Mount volumes as read-only where possible

## Monitoring and Logging

### View Real-time Logs

```bash
docker compose logs -f --tail=100 fastapi
```

### Export Logs

```bash
docker compose logs > logs-$(date +%Y%m%d).txt
```

### Health Checks

```bash
# API health check
curl http://localhost:8000/health

# Container health status
docker compose ps
```

### Resource Monitoring

```bash
# Real-time resource usage
docker stats

# Container inspection
docker inspect forcealignmentcutter-api
```

## Advanced Configuration

### Custom Base Image

Modify `Dockerfile` to use a different base image:

```dockerfile
FROM nvidia/cuda:12.2.0-runtime-ubuntu22.04
```

### Multi-stage Build

For smaller images, implement multi-stage builds in `Dockerfile`.

### Docker Secrets

For sensitive data in production:

```yaml
services:
  fastapi:
    secrets:
      - api_key
      
secrets:
  api_key:
    file: ./secrets/api_key.txt
```

## Comparison: Docker vs Conda

| Feature | Docker | Conda |
|---------|--------|-------|
| Isolation | Full OS-level | Python environment |
| Portability | Very High | Medium |
| Reproducibility | Excellent | Good |
| Setup Time | Longer | Faster |
| Size | Larger (~5GB) | Smaller (~3GB) |
| GPU Support | Requires toolkit | Direct |
| Production Ready | Yes | Requires setup |
| Development Speed | Slower rebuild | Faster iteration |

**Recommendation:**
- **Development**: Use Conda for faster iteration
- **Production**: Use Docker for reliability and scalability
- **Deployment**: Use Docker Compose for orchestration

## Next Steps

- Add Redis for task queue management
- Implement RabbitMQ/Celery for distributed processing
- Set up monitoring with Prometheus and Grafana
- Add CI/CD pipeline with GitHub Actions
- Configure horizontal scaling with Kubernetes

## Support

For issues related to:
- **Docker**: Check [Docker documentation](https://docs.docker.com/)
- **GPU Support**: See [NVIDIA Container Toolkit](https://github.com/NVIDIA/nvidia-docker)
- **Application**: See [README.md](README.md) and [API_README.md](API_README.md)
