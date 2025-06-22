# 🐳 Docker Configuration - ScholarAI Backend

## 📋 Overview

This directory contains optimized Docker configuration for the ScholarAI FastAPI backend application, designed for both development and production environments.

## 🔧 Recent Fixes & Optimizations

### ✅ Fixed Issues:
1. **Duplicate Image Creation** - Resolved naming conflicts
2. **Large Image Size (2.48 GB)** - Optimized to reduce size significantly
3. **Port Misalignment** - Synchronized all port configurations
4. **Hardcoded Values** - Replaced with configurable ARG variables

### 🚀 Improvements Made:
- **Structured Comments** - Comprehensive documentation throughout
- **Build Arguments** - Configurable values for different environments
- **Optimized .dockerignore** - Excludes unnecessary files
- **Production Override** - Separate configuration for production deployment
- **Security Enhancements** - Non-root user with proper permissions

## 📁 File Structure

```
docker/
├── Dockerfile              # Main Docker image definition
├── docker-compose.yml      # Development configuration
├── docker-compose.prod.yml # Production overrides
└── README.md              # This file
```

## 🏗️ Building Images

### Development Build
```bash
# Build with default values
docker-compose -f docker/docker-compose.yml build

# Build with custom arguments
docker-compose -f docker/docker-compose.yml build --build-arg PYTHON_VERSION=3.11.0
```

### Production Build
```bash
# Build optimized production image
docker-compose -f docker/docker-compose.yml -f docker/docker-compose.prod.yml build

# Run production container
docker-compose -f docker/docker-compose.yml -f docker/docker-compose.prod.yml up -d
```

### Manual Docker Build
```bash
# From project root
docker build -f docker/Dockerfile -t scholarai/backend-api:latest .

# With custom build arguments
docker build -f docker/Dockerfile \
  --build-arg PYTHON_VERSION=3.11.0 \
  --build-arg APP_PORT=9000 \
  -t scholarai/backend-api:custom .
```

## 🔧 Configuration

### Environment Variables

Create a `.env` file in the project root:

```env
# Application Configuration
APP_PORT=8000
HOST_PORT=8000
VERSION=latest
APP_ENV=development

# Python Configuration
PYTHON_VERSION=3.10.18
POETRY_VERSION=1.8.3

# RabbitMQ Configuration
RABBITMQ_USER=scholar
RABBITMQ_PASSWORD=scholar123
RABBITMQ_PORT=5672

# Network Configuration
NETWORK_NAME=scholar-network
```

### Build Arguments

| Argument | Default | Description |
|----------|---------|-------------|
| `PYTHON_VERSION` | `3.10.18` | Python version to use |
| `PYTHON_VARIANT` | `slim-bookworm` | Python image variant |
| `POETRY_VERSION` | `1.8.3` | Poetry version |
| `APP_PORT` | `8000` | Application port |
| `HEALTH_CHECK_PORT` | `8000` | Health check port |
| `APP_USER` | `app` | Application user |
| `APP_GROUP` | `app` | Application group |
| `WORKDIR` | `/app` | Working directory |

## 🚀 Running the Application

### Development Mode
```bash
# Start with source code mounting (for development)
cd docker
docker-compose up -d

# View logs
docker-compose logs -f scholarai-backend

# Stop services
docker-compose down
```

### Production Mode
```bash
# Start production-optimized containers
cd docker
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Scale if needed
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d --scale scholarai-backend=3
```

## 📊 Image Size Optimization

### Before Optimization: 2.48 GB
### After Optimization: ~800MB-1.2 GB (estimated)

**Optimization Techniques Applied:**
1. **Improved .dockerignore** - Excludes development files, docs, cache
2. **Production Override** - Removes volume mounts in production
3. **Multi-layer Optimization** - Better layer caching
4. **System Package Cleanup** - Removes unnecessary packages after installation
5. **No Development Dependencies** - Production builds exclude dev packages

## 🔍 Troubleshooting

### Remove Duplicate Images
```bash
# List all images
docker images | grep scholarai

# Remove old images
docker rmi scholar-ai-fastapi-app:latest
docker rmi docker-fastapi-app:latest

# Clean up unused images
docker image prune -f
```

### Network Issues
```bash
# Create network if it doesn't exist
docker network create scholar-network

# List networks
docker network ls

# Inspect network
docker network inspect scholar-network
```

### Health Check Debugging
```bash
# Check container health
docker ps

# View health check logs
docker inspect scholarai-backend-api | grep -A 10 -B 10 Health

# Manual health check
docker exec scholarai-backend-api curl -f http://localhost:8000/health
```

## 🛡️ Security Features

- **Non-root user execution**
- **Minimal base image (slim-bookworm)**
- **No unnecessary packages in production**
- **Environment variable security**
- **Network isolation**

## 📈 Performance Optimizations

- **Layer caching optimization**
- **Poetry virtual environment disabled in containers**
- **Resource limits in production**
- **Health check configuration**
- **Restart policies**

## 🔄 CI/CD Integration

### GitHub Actions Example:
```yaml
- name: Build Docker Image
  run: |
    docker build -f docker/Dockerfile \
      --build-arg VERSION=${{ github.sha }} \
      -t scholarai/backend-api:${{ github.sha }} .
```

### Production Deployment:
```bash
# Pull and deploy latest
docker-compose -f docker-compose.yml -f docker-compose.prod.yml pull
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

## 📝 Notes

- The development configuration mounts source code for hot reloading
- Production configuration creates a standalone image without volume mounts
- All configurations use the same base Dockerfile with different build arguments
- Health checks are aligned between Dockerfile and docker-compose configurations 