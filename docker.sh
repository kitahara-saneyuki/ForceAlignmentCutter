#!/bin/bash
# Docker helper scripts for ForceAlignmentCutter

set -e

case "$1" in
  build)
    echo "Building Docker image..."
    docker-compose build
    ;;
    
  up)
    echo "Starting services in development mode..."
    docker-compose up -d
    echo "Services started!"
    echo "Web interface: http://localhost:8000/static/index.html"
    echo "API docs: http://localhost:8000/docs"
    ;;
    
  down)
    echo "Stopping services..."
    docker-compose down
    ;;
    
  logs)
    docker-compose logs -f fastapi
    ;;
    
  restart)
    echo "Restarting services..."
    docker-compose restart
    ;;
    
  prod-build)
    echo "Building Docker image for production..."
    docker-compose -f docker-compose.prod.yml build
    ;;
    
  prod-up)
    echo "Starting services in production mode..."
    docker-compose -f docker-compose.prod.yml up -d
    echo "Services started!"
    echo "Web interface: http://localhost/"
    echo "API docs: http://localhost/docs"
    ;;
    
  prod-down)
    echo "Stopping production services..."
    docker-compose -f docker-compose.prod.yml down
    ;;
    
  prod-logs)
    docker-compose -f docker-compose.prod.yml logs -f
    ;;
    
  shell)
    echo "Opening shell in FastAPI container..."
    docker-compose exec fastapi /bin/bash
    ;;
    
  clean)
    echo "Cleaning up Docker resources..."
    docker-compose down -v
    docker system prune -f
    ;;
    
  status)
    docker-compose ps
    ;;
    
  *)
    echo "ForceAlignmentCutter Docker Helper"
    echo ""
    echo "Usage: ./docker.sh [command]"
    echo ""
    echo "Development Commands:"
    echo "  build       - Build Docker image"
    echo "  up          - Start services in development mode"
    echo "  down        - Stop services"
    echo "  logs        - View logs"
    echo "  restart     - Restart services"
    echo "  shell       - Open shell in container"
    echo "  status      - Show container status"
    echo ""
    echo "Production Commands:"
    echo "  prod-build  - Build for production"
    echo "  prod-up     - Start production services (with Nginx)"
    echo "  prod-down   - Stop production services"
    echo "  prod-logs   - View production logs"
    echo ""
    echo "Maintenance:"
    echo "  clean       - Remove containers and volumes"
    echo ""
    exit 1
    ;;
esac
