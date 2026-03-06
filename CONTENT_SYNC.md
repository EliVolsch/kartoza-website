# Content Synchronization from ERPNext

This document explains the comprehensive content synchronization system that keeps the Hugo website updated with content from ERPNext.

## 📦 What Gets Synced

The sync system handles multiple content types:

### 1. Training Content
- **Training courses** - Course details, descriptions, prerequisites
- **Training sessions** - Scheduled dates, venues, instructors, availability
- **Pricing** - Multi-currency pricing (ZAR, USD, EUR) for different venue types
- **Discounts** - Group discounts and early bird pricing

**Output**: `data/training_schedule.yml`

### 2. Blog Articles
- **Article content** - Title, description, full content (HTML)
- **Metadata** - Author, publish date, tags, SEO fields
- **Featured images** - Automatically downloaded and cached
- **Inline images** - All images in content are downloaded

**Output**: `content/blog/*.md` (one file per article)

### 3. Portfolio Items
- **Project details** - Name, description, client, dates
- **Project images** - Automatically downloaded
- **Tags** - For filtering and categorization
- **Status** - Project status tracking

**Output**: `content/portfolio/*.md` (one file per project)

## 🚀 Usage

### Quick Start

```bash
# Sync all content (uses cache if valid)
nix develop --command ./scripts/sync-content-from-erpnext.py

# Force fresh sync (ignore cache)
nix develop --command ./scripts/sync-content-from-erpnext.py --force

# Sync only specific content type
nix develop --command ./scripts/sync-content-from-erpnext.py --only training
nix develop --command ./scripts/sync-content-from-erpnext.py --only blog
nix develop --command ./scripts/sync-content-from-erpnext.py --only portfolio

# Skip downloading images (faster, for testing)
nix develop --command ./scripts/sync-content-from-erpnext.py --skip-images

# Dry run (don't write files)
nix develop --command ./scripts/sync-content-from-erpnext.py --dry-run
```

### Integrated with Build

The sync happens automatically when you build:

```bash
# Development server (auto-syncs on start)
nix develop --command ./scripts/dev-server.sh

# Production build (auto-syncs before building)
nix develop --command ./scripts/build.sh
```

## 🔧 Setup

### 1. Configure ERPNext Credentials

```bash
# Copy the example file
cp .env.example .env

# Edit with your credentials
nano .env
```

Add your ERPNext API credentials:
```bash
ERPNEXT_API_URL=https://erp.kartoza.com
ERPNEXT_API_KEY=your_api_key_here
ERPNEXT_API_SECRET=your_api_secret_here
```

### 2. Customize for Your ERPNext Structure

Edit `scripts/sync-content-from-erpnext.py` to match your ERPNext setup:

**Training Content** (if you use different DocTypes):
```python
# Line ~107: Change DocType for courses
response = self.session.get(
    f"{self.api_url}/api/resource/YourCourseDocType",  # Change this
    # ...
)

# Line ~130: Change DocType for sessions
response = self.session.get(
    f"{self.api_url}/api/resource/YourSessionDocType",  # Change this
    # ...
)
```

**Blog Articles** (lines 286-310):
```python
# Adjust based on your blog DocType
response = self.session.get(
    f"{self.api_url}/api/resource/Blog Post",  # Change if needed
    # Adjust field names to match your schema
)
```

**Portfolio Items** (lines 406-429):
```python
# Adjust based on your portfolio structure
response = self.session.get(
    f"{self.api_url}/api/resource/Project",  # Change if needed
    # Adjust filters and fields
)
```

## 📁 How It Works

### Caching System

```
┌─────────────┐
│   ERPNext   │
│   Content   │
└──────┬──────┘
       │
       │ API Call (if cache expired)
       │
       ▼
┌──────────────────┐
│  Cache Files     │
│  .cache/         │
│  - training.json │
│  - blog.json     │
│  - portfolio.json│
│  - images/       │
└──────┬───────────┘
       │
       │ Transform & Write
       │
       ▼
┌──────────────────┐
│  Hugo Content    │
│  - data/         │
│  - content/blog/ │
│  - content/      │
│    portfolio/    │
│  - static/img/   │
│    synced/       │
└──────────────────┘
```

### Cache TTL (Time To Live)

**Development Mode** (`HUGO_ENV` != production):
- Cache TTL: 6 hours
- Reduces API calls during frequent rebuilds
- Good for rapid development

**Production Mode** (`HUGO_ENV=production`):
- Cache TTL: 1 hour
- Fresher content for production
- Still has fallback if API fails

**Cache Locations**:
- Content data: `.cache/*.json`
- Downloaded images: `.cache/images/`
- Final images: `static/img/synced/`

### Image Handling

1. **Download**: Images from ERPNext are downloaded via API
2. **Cache**: Saved to `.cache/images/` to avoid re-downloading
3. **Deploy**: Copied to `static/img/synced/` for Hugo
4. **Reference**: Markdown files reference `/img/synced/filename.ext`

**Image Naming**:
```
{context}-{hash}.{ext}
```
Example: `blog-my-article-a1b2c3d4.jpg`

## 🎯 Content Type Details

### Training Schedule

**ERPNext Source**:
- Items (with item_group = "Training Courses")
- Events (with event_category = "Training")
- Item Price (for multi-currency pricing)

**Hugo Output**:
- Single YAML file: `data/training_schedule.yml`
- Used by training pages and booking widget

**Structure**:
```yaml
venues:
  cape-town:
    name: "Cape Town, South Africa"
    address: "..."
    type: "in-person"

sessions:
  - id: "SESSION-001"
    course: "qgis-introduction"
    venue: "cape-town"
    start_date: "2024-04-15"
    end_date: "2024-04-17"
    seats_available: 8
    instructor: "Tim Sutton"

pricing:
  qgis-introduction:
    ZAR:
      in-person: 7500
      remote: 5500
```

### Blog Articles

**ERPNext Source**:
- Blog Post DocType (or your custom blog DocType)

**Hugo Output**:
- One markdown file per article in `content/blog/`
- Images downloaded to `static/img/synced/`

**Markdown Format**:
```markdown
---
title: "Article Title"
description: "Short description"
date: "2024-01-15"
author: "Author Name"
featured_image: "/img/synced/blog-slug-12345678.jpg"
tags:
  - GIS
  - QGIS
---

Article content here with local image references...
```

### Portfolio Items

**ERPNext Source**:
- Project DocType (with project_type = "Portfolio")

**Hugo Output**:
- One markdown file per project in `content/portfolio/`
- Project images downloaded

**Markdown Format**:
```markdown
---
title: "Project Name"
description: "Project description"
client: "Client Name"
start_date: "2023-06-01"
end_date: "2024-02-01"
status: "Completed"
image: "/img/synced/portfolio-slug-87654321.jpg"
tags:
  - Web Mapping
  - GeoServer
---

Project details here...
```

## 🔍 Troubleshooting

### No ERPNext Credentials

**Symptom**: "⚠ ERPNext credentials not found"

**Solution**:
1. Check `.env` file exists
2. Verify credentials are correct
3. Test API access:
   ```bash
   curl -X GET "https://erp.kartoza.com/api/resource/Item" \
     -H "Authorization: token YOUR_KEY:YOUR_SECRET"
   ```

### API Connection Fails

**Symptom**: Errors fetching from ERPNext

**Check**:
- ERPNext URL is correct and accessible
- API user has read permissions for required DocTypes
- IP whitelisting (if enabled in ERPNext)
- SSL certificate validity

### Cache Issues

**Clear all caches**:
```bash
rm -rf .cache/
./scripts/sync-content-from-erpnext.py --force
```

**Clear only images**:
```bash
rm -rf .cache/images/
rm -rf static/img/synced/
```

### Images Not Downloading

**Check**:
1. Image URLs in ERPNext are accessible
2. `--skip-images` flag not used
3. Network connectivity
4. Image file permissions

**Debug**:
```bash
# Run with just one content type to isolate
./scripts/sync-content-from-erpnext.py --only blog --force
```

### Build Fails

**The build should never fail due to sync issues!**

If sync fails:
1. Falls back to cache (any age)
2. Falls back to existing files
3. Build continues

**Manual override**:
```bash
# Build without sync
hugo server  # Instead of ./scripts/dev-server.sh
```

## 🎨 Customization

### Add New Content Type

1. **Add to CACHE_FILES** (line ~63):
   ```python
   CACHE_FILES = {
       # ...
       'your_type': CACHE_DIR / 'your_type_cache.json',
   }
   ```

2. **Create sync method**:
   ```python
   def sync_your_content(self, download_images: bool = True) -> List[Dict]:
       """Sync your content from ERPNext"""
       items = self.fetch_your_items()
       processed = []
       for item in items:
           processed.append(self.transform_your_item(item))
       return processed
   ```

3. **Add to main()** (line ~711):
   ```python
   # Sync Your Content
   if args.only in ['your_type', 'all']:
       # ... implement caching logic
   ```

### Customize Field Mappings

Edit the transform methods to map ERPNext fields to Hugo frontmatter:

```python
def transform_blog_article(self, article: Dict, download_images: bool):
    return {
        'slug': self._slugify(article.get('title')),
        'title': article.get('your_title_field'),  # Customize
        'custom_field': article.get('erpnext_custom_field'),  # Add custom fields
        # ...
    }
```

## 📊 Statistics

After running, you'll see output like:

```
============================================================
  Kartoza Content Sync from ERPNext
============================================================

→ Syncing training content...
  ✓ Fetched 8 courses
  ✓ Fetched 14 sessions
  ✓ Fetched 24 pricing entries
✓ Saved to data/training_schedule.yml

→ Syncing blog articles...
  ✓ Fetched 45 articles
    ↓ Downloading: blog-new-features-a1b2c3d4.jpg
    ✓ Downloaded: blog-new-features-a1b2c3d4.jpg
  ✓ Processed 45 articles

→ Syncing portfolio items...
  ✓ Fetched 32 portfolio items
    ✓ Using cached image: portfolio-project-x-12345678.png
  ✓ Processed 32 portfolio items

============================================================
  ✓ Content sync completed successfully
============================================================
```

## 🔐 Security

**Important**:
- `.env` file is git-ignored (never commit credentials!)
- `.cache/` directory is git-ignored
- `static/img/synced/` is git-ignored (regenerated from source)
- API credentials use token-based auth (secure)

## 🚦 CI/CD Integration

### GitHub Actions Example

```yaml
- name: Sync Content from ERPNext
  env:
    ERPNEXT_API_URL: ${{ secrets.ERPNEXT_API_URL }}
    ERPNEXT_API_KEY: ${{ secrets.ERPNEXT_API_KEY }}
    ERPNEXT_API_SECRET: ${{ secrets.ERPNEXT_API_SECRET }}
    HUGO_ENV: production
  run: ./scripts/build.sh
```

Store credentials in GitHub Secrets, not in code!

## 📚 Related Documentation

- `scripts/README.md` - Build scripts documentation
- `ERPNEXT_INTEGRATION.md` - ERPNext setup guide (training-specific)
- `.env.example` - Environment variables template

## 🆘 Getting Help

If you need help customizing the sync for your specific ERPNext structure:

1. Check the inline comments in `sync-content-from-erpnext.py`
2. Run with `--dry-run` to test without writing files
3. Use `--only TYPE` to test one content type at a time
4. Check ERPNext API docs: https://frappeframework.com/docs/user/en/api
