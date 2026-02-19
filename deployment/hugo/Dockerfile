# Hugo Builder Service
FROM hugomods/hugo:exts-0.144.0

# Set working directory
WORKDIR /src

# Copy all project files
COPY . .

# Build the Hugo site
# --gc: Run garbage collection after build
# --cleanDestinationDir: Remove files from destination not found in static dirs
RUN hugo --gc --cleanDestinationDir

# Output will be in /src/public
# This directory will be shared with nginx via a volume
CMD ["sh", "-c", "echo 'Hugo build complete. Static files are in /src/public' && tail -f /dev/null"]
