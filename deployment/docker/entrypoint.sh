#!/bin/bash
set -e

# Default baseURL if not provided
BASE_URL="${BASE_URL:-/}"

echo "Building Hugo site with baseURL: $BASE_URL"

# Build Hugo site with runtime baseURL
cd /src

# Update baseURL in config.toml
sed -i "s|^baseURL = .*|baseURL = '$BASE_URL'|g" config.toml

hugo \
    --config config.toml,config/config.gh-pages.toml \
    --gc \
    --cleanDestinationDir

# Copy output to nginx
cp -r /src/public/* /usr/share/nginx/html/
chown -R www:www /usr/share/nginx/html

echo "Hugo build complete. Starting nginx..."

# Start nginx
exec nginx -g "daemon off;"
