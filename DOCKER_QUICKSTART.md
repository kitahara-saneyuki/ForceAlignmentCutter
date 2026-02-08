# ForceAlignmentCutter - Docker Quick Reference

## Quick Start Commands

### Development Mode

```bash
# Build image
make docker-build

# Start services
make docker-up

# Access application
open http://localhost:8000/static/index.html

# View logs
make docker-logs

# Stop services
make docker-down
```

### Production Mode (with Nginx)

```bash
# Build production image
make docker-prod-build

# Start production services
make docker-prod-up

# Access application
open http://localhost/static/index.html

# View logs
make docker-prod-logs

# Stop services
make docker-prod-down
```

## Common Tasks

### View running containers
```bash
docker-compose ps
```

### Shell access
```bash
make docker-shell
# Or: docker-compose exec fastapi bash
```

### Restart services
```bash
make docker-restart
```

### Clean up everything
```bash
make docker-clean
```

### Check GPU availability
```bash
docker-compose exec fastapi nvidia-smi
```

### Manual docker-compose commands
```bash
# Start
docker-compose up -d

# Stop
docker-compose down

# Rebuild
docker-compose build --no-cache

# View logs
docker-compose logs -f

# Scale workers (if using worker service)
docker-compose up -d --scale worker=3
```

## Troubleshooting

### Container won't start
```bash
# Check logs
docker-compose logs fastapi

# Remove and rebuild
docker-compose down -v
docker-compose build --no-cache
docker-compose up -d
```

### GPU not detected
```bash
# Test GPU access
docker run --rm --gpus all nvidia/cuda:12.1.0-base-ubuntu22.04 nvidia-smi

# Check nvidia-docker runtime
docker info | grep -i runtime
```

### Port conflict
```bash
# Find process using port
lsof -i :8000

# Kill process
kill -9 <PID>

# Or change port in docker-compose.yml
```

### Permission issues
```bash
# Fix upload directory permissions
sudo chown -R $USER:$USER uploads/
chmod -R 755 uploads/
```

## File Locations

- **Dockerfile**: Main container definition
- **docker-compose.yml**: Development orchestration
- **docker-compose.prod.yml**: Production orchestration
- **docker-entrypoint.sh**: Container startup script
- **.dockerignore**: Files excluded from image
- **nginx/nginx.conf**: Nginx configuration

## Environment Variables

Create `.env` file (see `.env.example`):

```bash
cp .env.example .env
# Edit .env with your settings
```

## Performance

### CPU Only (no GPU)
Comment out `deploy` section in docker-compose.yml

### More workers
Edit `command` in docker-compose.yml:
```yaml
command: uvicorn api.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Increase upload limit
Edit `nginx/nginx.conf`:
```nginx
client_max_body_size 1G;
```

## Monitoring

### Resource usage
```bash
docker stats
```

### Health check
```bash
curl http://localhost:8000/health
```

### Nginx status
```bash
docker-compose exec nginx nginx -t
```

## Backup & Restore

### Backup uploads
```bash
tar -czf uploads-backup-$(date +%Y%m%d).tar.gz uploads/
```

### Restore uploads
```bash
tar -xzf uploads-backup-YYYYMMDD.tar.gz
```

## Updates

### Pull latest code
```bash
git pull origin main
make docker-down
make docker-build
make docker-up
```

### Update dependencies
1. Edit `environment.yml`
2. Rebuild image: `make docker-build`
3. Restart: `make docker-up`

## Documentation

- **[DOCKER.md](DOCKER.md)** - Complete Docker guide
- **[README.md](README.md)** - Main project documentation
- **[API_README.md](API_README.md)** - API documentation
- **[plan.md](plan.md)** - Project roadmap

## Support

For detailed information, see [DOCKER.md](DOCKER.md)
