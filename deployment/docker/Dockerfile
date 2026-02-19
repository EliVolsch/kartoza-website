# Stage 1: Build the Hugo site
FROM hugomods/hugo:exts-0.144.0 AS builder

# Build argument for baseURL (default to localhost for local dev)
ARG BASE_URL=http://localhost:8888

# Set working directory
WORKDIR /src

# Copy all project files
COPY . .

# Build the Hugo site with custom baseURL
# --gc: Run garbage collection after build
# --cleanDestinationDir: Remove files from destination not found in static dirs
# --baseURL: Override the baseURL from config.toml
RUN hugo --gc --cleanDestinationDir --baseURL="${BASE_URL}"

# Stage 2: Serve with Nginx
FROM nginx:1.29.0-alpine-perl

# Install ca-certificates and tools
RUN apk add --no-cache ca-certificates tzdata wget

# Copy custom nginx configuration
COPY deployment/nginx/sites-enabled/nginx.conf /etc/nginx/nginx.conf
COPY deployment/nginx/sites-enabled/default.conf /etc/nginx/conf.d/default.conf

# Copy built site from builder stage
COPY --from=builder /src/public /usr/share/nginx/html

# Create non-root user for nginx
RUN addgroup -g 1001 -S www && \
    adduser -u 1001 -S www -G www && \
    chown -R www:www /usr/share/nginx/html && \
    chown -R www:www /var/cache/nginx && \
    touch /var/run/nginx.pid && \
    chown -R www:www /var/run/nginx.pid

# Use non-root user
USER www

# Expose port 8080 (non-privileged port)
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:8080/health || exit 1

# Start nginx
CMD ["nginx", "-g", "daemon off;"]
