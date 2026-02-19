# Stage 1: Build the Hugo site
# Using Debian slim with Hugo - fewer CVEs than Alpine in practice
FROM debian:bookworm-slim AS builder

# Hugo version
ARG HUGO_VERSION=0.144.0
ARG BASE_URL=http://localhost:8888

# Install only wget and ca-certificates, then clean up
RUN apt-get update && \
    apt-get install -y --no-install-recommends wget ca-certificates && \
    wget -qO- https://github.com/gohugoio/hugo/releases/download/v${HUGO_VERSION}/hugo_extended_${HUGO_VERSION}_linux-amd64.tar.gz | tar xz -C /usr/local/bin/ && \
    apt-get purge -y wget && \
    apt-get autoremove -y && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /src
COPY . .
RUN hugo --gc --cleanDestinationDir --baseURL="${BASE_URL}"

# Stage 2: Minimal Nginx runtime
FROM nginx:1.27.3-alpine-slim

# Upgrade all packages and install only essentials
RUN apk upgrade --no-cache --available && \
    apk add --no-cache ca-certificates && \
    rm -rf /var/cache/apk/* /tmp/*

COPY deployment/nginx/sites-enabled/nginx.conf /etc/nginx/nginx.conf
COPY deployment/nginx/sites-enabled/default.conf /etc/nginx/conf.d/default.conf
COPY --from=builder /src/public /usr/share/nginx/html

# Security hardening
RUN addgroup -g 1001 -S www && \
    adduser -u 1001 -S www -G www && \
    chown -R www:www /usr/share/nginx/html /var/cache/nginx && \
    touch /var/run/nginx.pid && \
    chown www:www /var/run/nginx.pid

USER www
EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD wget -q --spider http://localhost:8080/health || exit 1

CMD ["nginx", "-g", "daemon off;"]
