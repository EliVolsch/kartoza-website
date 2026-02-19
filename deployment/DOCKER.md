# Docker Deployment Guide

This guide explains how to build and run the Kartoza website using Docker and Docker Compose.

## Prerequisites

- Docker Engine 20.10+
- Docker Compose 2.0+

## Quick Start

### 1. Navigate to Deployment Directory

```bash
cd deployment
```

### 2. Build and Start the Service

```bash
docker-compose up -d
```

This will:
- Build the Hugo website with Hugo 0.144.0
- Serve it with nginx on port 8888
- Create a network for the service

### 3. Access the Website

- **Website**: http://localhost:8888
- **Health Check**: http://localhost:8888/health

### 4. Stop the Service

```bash
docker-compose down
```

## Environment Configuration

If you need custom environment variables:

1. Copy the template environment file:
   ```bash
   cd deployment
   cp .template.env .env
   ```

2. Edit `.env` and add your custom variables as needed.

## Docker Architecture

### Multi-Stage Build

The Dockerfile uses a multi-stage build approach:

1. **Builder Stage**: Uses `hugomods/hugo:exts-0.144.0` to build the static site
   - Copies all source files from parent directory
   - Runs Hugo with garbage collection and clean destination
   - Outputs to `/src/public` directory

2. **Production Stage**: Uses `nginx:1.29.0-alpine-perl` to serve the built site
   - Copies built site from builder stage
   - Uses custom nginx configuration from deployment/nginx/sites-enabled/
   - Runs as non-root user for security
   - Exposes port 8080 (mapped to host port 8888)

### Service

#### Website
- **Container**: `kartoza-website`
- **Port**: 8888 (host) → 8080 (container)
- **Image**: Custom built from deployment/Dockerfile
- **Health Check**: HTTP GET to `/health`
- **Architecture**: Multi-stage (Hugo build + Nginx serve)

### Network

The service is connected to a bridge network named `kartoza-network`.

## Development Workflow

### Rebuild After Changes

```bash
cd deployment

# Rebuild and restart
docker-compose up -d --build

# Or rebuild then start
docker-compose build
docker-compose up -d
```

### View Logs

```bash
cd deployment

# View logs
docker-compose logs -f website
```

### Execute Commands in Container

```bash
cd deployment

# Access website container shell
docker-compose exec website sh
```

## Production Deployment

### Build and Deploy

```bash
cd deployment

# Build and start
docker-compose up -d --build
```

### Resource Limits (Optional)

Add to `docker-compose.yml` under each service:

```yaml
deploy:
  resources:
    limits:
      cpus: '1.0'
      memory: 512M
    reservations:
      cpus: '0.5'
      memory: 256M
```

## Security Features

- Non-root user execution in containers
- Health checks for service monitoring
- Gzip compression enabled
- Security headers configured

## Troubleshooting

### Port Already in Use

If port 8888 is already in use, modify the ports in `docker-compose.yml`:

```yaml
ports:
  - "8080:8080"  # Use port 8080 instead
```

### Build Failures

Clear Docker cache and rebuild:

```bash
docker-compose build --no-cache
```

### Permission Issues

Ensure the nginx user has proper permissions:

```bash
docker-compose exec website ls -la /usr/share/nginx/html
```

## Monitoring

### Check Service Health

```bash
cd deployment

# Check all containers status
docker-compose ps

# Test health endpoint
curl http://localhost:8888/health
```

### Resource Usage

```bash
docker stats kartoza-website
```

## Cleanup

### Remove Containers

```bash
cd deployment
docker-compose down
```

### Remove Containers and Volumes

```bash
cd deployment
docker-compose down -v
```

### Remove Images

```bash
cd deployment
docker-compose down --rmi all
```

## Further Customization

### Nginx Configuration

Edit `deployment/nginx/sites-enabled/nginx.conf` or `deployment/nginx/sites-enabled/default.conf` to customize:
- Cache settings
- Compression
- Security headers
- Custom error pages

### Hugo Build Options

Modify the Hugo build command in `deployment/Dockerfile` (builder stage):

```dockerfile
RUN hugo --gc --cleanDestinationDir --baseURL "https://yourdomain.com"
```

## Support

For issues or questions:
- Email: info@kartoza.com
- Website: https://kartoza.com
