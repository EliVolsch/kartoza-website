# Scripts

This directory contains build and utility scripts for the Kartoza Hugo website.

## Setup

### ERPNext Integration

To sync training schedules from ERPNext:

1. **Copy the environment file:**
   ```bash
   cp .env.example .env
   ```

2. **Configure ERPNext credentials:**
   Edit `.env` and add your ERPNext API credentials:
   ```bash
   ERPNEXT_API_URL=https://erp.kartoza.com
   ERPNEXT_API_KEY=your_api_key_here
   ERPNEXT_API_SECRET=your_api_secret_here
   ```

   To generate API keys in ERPNext:
   - Go to User Menu → API Access → Generate Keys
   - Or use the API endpoint: `/api/method/frappe.core.doctype.user.user.generate_keys`

3. **Install Python dependencies:**
   ```bash
   pip install requests pyyaml
   ```

   Or if using nix-develop (recommended):
   ```bash
   nix develop
   ```

## Scripts

### `sync-content-from-erpnext.py`

Syncs ALL website content from ERPNext to Hugo (training, blog, portfolio, etc.).

**Features:**
- Syncs multiple content types (training, blog, portfolio)
- Downloads and caches images from ERPNext
- Smart caching mechanism to avoid excessive API calls
- Fallback to cached data if API is unavailable
- Configurable cache TTL per content type

**Usage:**
```bash
# Sync all content (uses cache if valid)
./scripts/sync-content-from-erpnext.py

# Force refresh all content (ignore cache)
./scripts/sync-content-from-erpnext.py --force

# Sync only specific content type
./scripts/sync-content-from-erpnext.py --only training
./scripts/sync-content-from-erpnext.py --only blog
./scripts/sync-content-from-erpnext.py --only portfolio

# Skip downloading images (faster)
./scripts/sync-content-from-erpnext.py --skip-images

# Dry run (fetch but don't write)
./scripts/sync-content-from-erpnext.py --dry-run

# Custom cache TTL (in hours)
./scripts/sync-content-from-erpnext.py --cache-ttl 12
```

**See Also**: `CONTENT_SYNC.md` for comprehensive documentation

**Cache Location:**
- Content cache: `.cache/training_cache.json`, `.cache/blog_cache.json`, etc.
- Image cache: `.cache/images/`
- Final images: `static/img/synced/`
- Default TTL: 6 hours in development, 1 hour in production

### `pre-build.sh`

Runs pre-build tasks before Hugo builds the site.

**What it does:**
- Syncs all content from ERPNext (training, blog, portfolio)
- Downloads and caches images
- Sets appropriate cache TTL based on environment
- Gracefully handles failures (doesn't break build)

**Usage:**
```bash
./scripts/pre-build.sh
```

**Environment:**
- Development: `HUGO_ENV` not set or != "production"
- Production: `HUGO_ENV=production`

### `build.sh`

Complete build script that runs pre-build tasks then builds with Hugo.

**Usage:**
```bash
# Production build
./scripts/build.sh

# Development build
./scripts/build.sh --environment dev

# With minification
./scripts/build.sh --minify

# Pass any Hugo arguments
./scripts/build.sh --destination ./custom-output
```

### `dev-server.sh`

Runs pre-build tasks then starts Hugo development server.

**Usage:**
```bash
# Using nix develop (recommended)
nix develop --command ./scripts/dev-server.sh

# Or directly
./scripts/dev-server.sh
```

## Development Workflow

### Local Development

1. **Start development server with auto-sync:**
   ```bash
   nix develop --command ./scripts/dev-server.sh
   ```

2. **Manual sync (if needed):**
   ```bash
   # Sync all content
   ./scripts/sync-content-from-erpnext.py

   # Or just training
   ./scripts/sync-content-from-erpnext.py --only training
   ```

3. **Test without ERPNext:**
   If you don't have ERPNext credentials, the scripts will:
   - Use cached data if available
   - Fall back to the manually-maintained YAML file
   - Not break the build

### Production Build

```bash
# Set production environment
export HUGO_ENV=production

# Run build (includes pre-build sync)
./scripts/build.sh
```

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Build and Deploy

on:
  push:
    branches: [main]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Setup Hugo
        uses: peaceiris/actions-hugo@v2
        with:
          hugo-version: 'latest'
          extended: true

      - name: Install dependencies
        run: pip install requests pyyaml

      - name: Build site
        env:
          HUGO_ENV: production
          ERPNEXT_API_URL: ${{ secrets.ERPNEXT_API_URL }}
          ERPNEXT_API_KEY: ${{ secrets.ERPNEXT_API_KEY }}
          ERPNEXT_API_SECRET: ${{ secrets.ERPNEXT_API_SECRET }}
        run: ./scripts/build.sh --minify

      - name: Deploy
        # Your deployment step here
```

## Customizing ERPNext Integration

The sync script needs to be customized based on your ERPNext setup:

### 1. Training Course DocType

Edit `sync-training-from-erpnext.py` and update `fetch_training_courses()`:
- Change the DocType name if you're not using "Item"
- Adjust filters to match your setup
- Update field mappings

### 2. Session/Event Structure

Update `fetch_training_sessions()`:
- Change DocType (e.g., "Event", "Project", or custom)
- Adjust date field names
- Update participant tracking logic

### 3. Pricing Structure

Modify `fetch_training_pricing()`:
- Change price list filters
- Update currency mappings
- Adjust venue-type pricing logic

### 4. Field Mappings

Update the helper methods:
- `_extract_course_slug()`: Map ERPNext course names to Hugo slugs
- `_determine_venue()`: Extract venue from session data
- `_extract_instructor()`: Get instructor information

## Troubleshooting

### Cache Issues

```bash
# Clear cache
rm -rf .cache/

# Force fresh data
./scripts/sync-training-from-erpnext.py --force
```

### API Errors

1. **Check credentials:**
   ```bash
   # Test API connection
   curl -X GET "https://erp.kartoza.com/api/resource/Item" \
     -H "Authorization: token YOUR_KEY:YOUR_SECRET"
   ```

2. **Check ERPNext permissions:**
   - Ensure API user has read access to required DocTypes
   - Check if IP whitelisting is enabled

3. **Enable debug mode:**
   ```python
   # In sync-training-from-erpnext.py, add:
   import logging
   logging.basicConfig(level=logging.DEBUG)
   ```

### Build Fails

If builds fail due to sync errors:

1. **Check if using cached/existing data:**
   The pre-build script won't fail the build if sync fails

2. **Temporarily disable sync:**
   Comment out the sync line in `pre-build.sh`

3. **Use manual YAML:**
   Edit `data/training_schedule.yml` directly

## Data Structure

The generated `training_schedule.yml` has this structure:

```yaml
venues:
  cape-town:
    name: "Cape Town, South Africa"
    address: "..."
    type: "in-person"
    icon: "fa-building"
    description: "..."

currencies:
  ZAR:
    symbol: "R"
    name: "South African Rand"
    code: "ZAR"

pricing:
  qgis-introduction:
    ZAR:
      in-person: 7500
      remote: 5500
      on-site: null

sessions:
  - id: "QGIS-INTRO-2024-Q2-CPT"
    course: "qgis-introduction"
    venue: "cape-town"
    start_date: "2024-04-15"
    end_date: "2024-04-17"
    seats_total: 12
    seats_available: 8
    instructor: "Tim Sutton"
    status: "open"

group_discounts:
  - min_attendees: 3
    max_attendees: 5
    discount_percent: 10
    label: "Small Team"

early_bird:
  days_before: 30
  discount_percent: 10

api:
  base_url: "https://kartoza.com/api/v1"
  endpoints:
    check_availability: "/training/sessions/{session_id}/availability"
    create_booking: "/training/bookings"
```
