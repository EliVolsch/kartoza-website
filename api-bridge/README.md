# Kartoza API Bridge

A lightweight Go service that bridges the Kartoza static website with ERPNext for form submissions and other interactions.

## Features

- **Contact Form Processing**: Creates leads in ERPNext from website contact form submissions
- **CORS Support**: Configured for Kartoza domains
- **Rate Limiting**: Prevents abuse (configurable requests per minute)
- **Health Checks**: Kubernetes-ready health and readiness endpoints
- **Docker Ready**: Multi-stage Dockerfile for minimal image size

## Quick Start

### Local Development

1. Copy the environment file:
   ```bash
   cp .env.example .env
   ```

2. Fill in your ERPNext credentials in `.env`

3. Run with Go:
   ```bash
   go run ./cmd/server
   ```

   Or with command-line flags:
   ```bash
   go run ./cmd/server \
     -erpnext-url=https://your-erpnext.com \
     -erpnext-key=your-key \
     -erpnext-secret=your-secret \
     -port=8080
   ```

### Docker

Build and run:
```bash
docker build -t kartoza-api-bridge .
docker run -p 8080:8080 \
  -e ERPNEXT_URL=https://your-erpnext.com \
  -e ERPNEXT_API_KEY=your-key \
  -e ERPNEXT_API_SECRET=your-secret \
  kartoza-api-bridge
```

Or with docker-compose:
```bash
# Set env vars or create .env file
docker-compose up -d
```

## API Endpoints

### POST /api/contact

Submit a contact form.

**Request:**
```json
{
  "name": "John Doe",
  "email": "john@example.com",
  "organisation": "Acme Corp",
  "phone": "+27 21 123 4567",
  "interest": "hosting",
  "message": "I'm interested in GeoSpatial Hosting...",
  "source": "search"
}
```

**Response (success):**
```json
{
  "success": true,
  "message": "Thank you! Your message has been received.",
  "lead_id": "CRM-LEAD-2024-00001"
}
```

**Interest values:**
- `hosting` - GeoSpatial Hosting
- `mycivitas` - MyCivitas product
- `bims` - BIMS product
- `training` - Training courses
- `development` - Custom development
- `consulting` - Consulting services
- `support` - Technical support
- `partnership` - Partnership enquiry
- `other` - Other

### GET /health

Basic health check (always returns 200 if service is running).

### GET /ready

Readiness check that verifies ERPNext connectivity.

## Configuration

### Core Settings

| Environment Variable | Description | Default |
|---------------------|-------------|---------|
| `BRIDGE_PORT` | Server port | `8080` |
| `BRIDGE_ENV` | Environment (development/production) | `development` |
| `ERPNEXT_URL` | ERPNext instance URL | *required* |
| `AUTH_MODE` | Authentication mode: `apikey` or `oauth2` | `apikey` |
| `ALLOWED_ORIGINS` | Comma-separated CORS origins | `https://kartoza.com,...` |
| `RATE_LIMIT` | Requests per minute per IP | `10` |
| `RATE_LIMIT_BURST` | Burst allowance | `5` |
| `NOTIFY_EMAIL` | Email for notifications | `info@kartoza.com` |

### API Key Authentication (AUTH_MODE=apikey)

| Environment Variable | Description | Default |
|---------------------|-------------|---------|
| `ERPNEXT_API_KEY` | ERPNext API key | *required* |
| `ERPNEXT_API_SECRET` | ERPNext API secret | *required* |

### OAuth2 Authentication (AUTH_MODE=oauth2)

| Environment Variable | Description | Default |
|---------------------|-------------|---------|
| `OAUTH2_ACCESS_TOKEN` | OAuth2 access token | *required* |
| `OAUTH2_REFRESH_TOKEN` | OAuth2 refresh token | *recommended* |
| `OAUTH2_CLIENT_ID` | OAuth2 client ID | *optional* |
| `OAUTH2_CLIENT_SECRET` | OAuth2 client secret | *optional* |

## Kubernetes Deployment

Example deployment manifest:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: api-bridge
spec:
  replicas: 2
  selector:
    matchLabels:
      app: api-bridge
  template:
    metadata:
      labels:
        app: api-bridge
    spec:
      containers:
      - name: api-bridge
        image: kartoza/api-bridge:latest
        ports:
        - containerPort: 8080
        env:
        - name: ERPNEXT_URL
          valueFrom:
            secretKeyRef:
              name: erpnext-credentials
              key: url
        - name: ERPNEXT_API_KEY
          valueFrom:
            secretKeyRef:
              name: erpnext-credentials
              key: api-key
        - name: ERPNEXT_API_SECRET
          valueFrom:
            secretKeyRef:
              name: erpnext-credentials
              key: api-secret
        - name: BRIDGE_ENV
          value: "production"
        livenessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 5
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8080
          initialDelaySeconds: 5
          periodSeconds: 10
        resources:
          requests:
            memory: "32Mi"
            cpu: "10m"
          limits:
            memory: "64Mi"
            cpu: "100m"
---
apiVersion: v1
kind: Service
metadata:
  name: api-bridge
spec:
  selector:
    app: api-bridge
  ports:
  - port: 80
    targetPort: 8080
```

## ERPNext Setup

The API bridge creates:
1. **Lead** documents for each contact form submission
2. **Communication** records linked to the Lead with the full message

### Minimal Permissions Required

The API user needs **only** these permissions:
- **Lead**: Create
- **Communication**: Create

This is the principle of least privilege - the API bridge cannot read, modify, or delete any other data.

### Option 1: API Key/Secret Setup (Simpler)

1. In ERPNext, go to **Settings > User**
2. Create a new user (e.g., `api-bridge@kartoza.com`) or use an existing one
3. Assign a **Role** with minimal permissions:
   - Go to **Settings > Role** and create a new role (e.g., "Website API")
   - Under **Role Permissions Manager**, add:
     - Document Type: Lead, Permissions: Create only (Level 0)
     - Document Type: Communication, Permissions: Create only (Level 0)
4. Assign this role to the API user
5. Go to the user's profile and generate **API Key and Secret**:
   - Click "Generate API Key" under the API Access section
   - Copy both the API Key and API Secret

### Option 2: OAuth2 Setup (Recommended for Production)

OAuth2 provides better security with automatic token refresh and explicit scopes.

#### Step 1: Create a Limited User

1. Go to **Settings > User**
2. Create a new user (e.g., `website-api@kartoza.com`)
3. Assign the minimal role as described above

#### Step 2: Create OAuth2 Client

1. Go to **Integrations > OAuth Client**
2. Click **+ Add OAuth Client**
3. Fill in the details:
   - **App Name**: Kartoza Website API Bridge
   - **Redirect URIs**: `http://localhost:8080/oauth/callback` (for initial token generation)
   - **Default Redirect URI**: Same as above
   - **Grant Type**: Authorization Code
   - **User**: Select the limited user created above
4. Save and note the **Client ID** and **Client Secret**

#### Step 3: Obtain Initial Access Token

You can obtain the initial access token using curl:

```bash
# Step 1: Get authorization code (do this in a browser)
# Visit: https://your-erpnext.com/api/method/frappe.integrations.oauth2.authorize?client_id=YOUR_CLIENT_ID&response_type=code&redirect_uri=http://localhost:8080/oauth/callback&scope=openid

# Step 2: Exchange code for tokens
curl -X POST https://your-erpnext.com/api/method/frappe.integrations.oauth2.get_token \
  -d "grant_type=authorization_code" \
  -d "code=AUTHORIZATION_CODE_FROM_STEP_1" \
  -d "client_id=YOUR_CLIENT_ID" \
  -d "client_secret=YOUR_CLIENT_SECRET" \
  -d "redirect_uri=http://localhost:8080/oauth/callback"
```

The response will contain:
```json
{
  "access_token": "...",
  "refresh_token": "...",
  "token_type": "Bearer",
  "expires_in": 3600
}
```

#### Step 4: Configure the API Bridge

Use the tokens in your environment:

```bash
AUTH_MODE=oauth2
ERPNEXT_URL=https://your-erpnext.com
OAUTH2_CLIENT_ID=your-client-id
OAUTH2_CLIENT_SECRET=your-client-secret
OAUTH2_ACCESS_TOKEN=your-access-token
OAUTH2_REFRESH_TOKEN=your-refresh-token
```

The API bridge will automatically refresh the access token when it expires.

### Security Best Practices

1. **Use OAuth2 in production** - It supports automatic token refresh and better access control
2. **Create a dedicated user** - Never use admin or employee accounts for API access
3. **Minimal permissions** - Only grant Create permission on Lead and Communication
4. **Rotate tokens regularly** - For API key/secret, regenerate periodically
5. **Use HTTPS** - Always connect to ERPNext over HTTPS
6. **Restrict CORS origins** - Only allow your website domains

## Adding New Endpoints

To add a new endpoint (e.g., newsletter subscription):

1. Create a handler in `internal/handlers/newsletter.go`
2. Add the ERPNext API methods in `internal/erpnext/client.go` if needed
3. Register the route in `cmd/server/main.go`

## License

MIT
