# Nginx Service - Serves static files built by Hugo
FROM nginx:1.29.0-alpine-perl

# Install ca-certificates and tools
RUN apk add --no-cache ca-certificates tzdata wget

# Copy custom nginx configuration
COPY deployment/nginx/sites-enabled/nginx.conf /etc/nginx/nginx.conf
COPY deployment/nginx/sites-enabled/default.conf /etc/nginx/conf.d/default.conf

# Create directory for static files
RUN mkdir -p /usr/share/nginx/html

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
