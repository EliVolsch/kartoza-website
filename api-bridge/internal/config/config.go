package config

import (
	"flag"
	"fmt"
	"os"
	"strconv"
)

// AuthMode represents the authentication mode for ERPNext
type AuthMode string

const (
	AuthModeAPIKey AuthMode = "apikey"   // API key:secret authentication
	AuthModeOAuth2 AuthMode = "oauth2"   // OAuth2 Bearer token authentication
)

// Config holds all configuration for the API bridge
type Config struct {
	// Server settings
	Port        int
	Environment string // "development" or "production"

	// ERPNext settings
	ERPNextURL    string
	ERPNextAPIKey string
	ERPNextSecret string

	// OAuth2 settings (alternative to API key/secret)
	AuthMode           AuthMode
	OAuth2ClientID     string
	OAuth2ClientSecret string
	OAuth2AccessToken  string
	OAuth2RefreshToken string

	// CORS settings
	AllowedOrigins []string

	// Rate limiting
	RateLimit         int // requests per minute per IP
	RateLimitBurst    int // burst allowance

	// Optional: Email notification fallback
	SMTPHost     string
	SMTPPort     int
	SMTPUser     string
	SMTPPassword string
	SMTPFrom     string
	NotifyEmail  string
}

// Load reads configuration from environment variables with command-line flag overrides
func Load() (*Config, error) {
	cfg := &Config{}

	// Define command-line flags for local development
	port := flag.Int("port", 0, "Server port (overrides BRIDGE_PORT env var)")
	erpURL := flag.String("erpnext-url", "", "ERPNext URL (overrides ERPNEXT_URL env var)")
	erpKey := flag.String("erpnext-key", "", "ERPNext API key (overrides ERPNEXT_API_KEY env var)")
	erpSecret := flag.String("erpnext-secret", "", "ERPNext API secret (overrides ERPNEXT_API_SECRET env var)")
	env := flag.String("env", "", "Environment: development or production (overrides BRIDGE_ENV env var)")
	authMode := flag.String("auth-mode", "", "Auth mode: apikey or oauth2 (overrides AUTH_MODE env var)")
	oauth2Token := flag.String("oauth2-token", "", "OAuth2 access token (overrides OAUTH2_ACCESS_TOKEN env var)")
	oauth2Refresh := flag.String("oauth2-refresh", "", "OAuth2 refresh token (overrides OAUTH2_REFRESH_TOKEN env var)")
	oauth2ClientID := flag.String("oauth2-client-id", "", "OAuth2 client ID (overrides OAUTH2_CLIENT_ID env var)")
	oauth2ClientSecret := flag.String("oauth2-client-secret", "", "OAuth2 client secret (overrides OAUTH2_CLIENT_SECRET env var)")

	flag.Parse()

	// Server settings
	cfg.Port = getIntEnv("BRIDGE_PORT", 8080)
	if *port != 0 {
		cfg.Port = *port
	}

	cfg.Environment = getEnv("BRIDGE_ENV", "development")
	if *env != "" {
		cfg.Environment = *env
	}

	// ERPNext settings
	cfg.ERPNextURL = getEnv("ERPNEXT_URL", "")
	if *erpURL != "" {
		cfg.ERPNextURL = *erpURL
	}

	cfg.ERPNextAPIKey = getEnv("ERPNEXT_API_KEY", "")
	if *erpKey != "" {
		cfg.ERPNextAPIKey = *erpKey
	}

	cfg.ERPNextSecret = getEnv("ERPNEXT_API_SECRET", "")
	if *erpSecret != "" {
		cfg.ERPNextSecret = *erpSecret
	}

	// OAuth2 settings
	cfg.AuthMode = AuthMode(getEnv("AUTH_MODE", "apikey"))
	if *authMode != "" {
		cfg.AuthMode = AuthMode(*authMode)
	}

	cfg.OAuth2ClientID = getEnv("OAUTH2_CLIENT_ID", "")
	if *oauth2ClientID != "" {
		cfg.OAuth2ClientID = *oauth2ClientID
	}

	cfg.OAuth2ClientSecret = getEnv("OAUTH2_CLIENT_SECRET", "")
	if *oauth2ClientSecret != "" {
		cfg.OAuth2ClientSecret = *oauth2ClientSecret
	}

	cfg.OAuth2AccessToken = getEnv("OAUTH2_ACCESS_TOKEN", "")
	if *oauth2Token != "" {
		cfg.OAuth2AccessToken = *oauth2Token
	}

	cfg.OAuth2RefreshToken = getEnv("OAUTH2_REFRESH_TOKEN", "")
	if *oauth2Refresh != "" {
		cfg.OAuth2RefreshToken = *oauth2Refresh
	}

	// CORS - default to Kartoza domains
	originsStr := getEnv("ALLOWED_ORIGINS", "https://kartoza.com,https://www.kartoza.com,http://localhost:1313")
	cfg.AllowedOrigins = splitAndTrim(originsStr)

	// Rate limiting
	cfg.RateLimit = getIntEnv("RATE_LIMIT", 10)          // 10 requests per minute
	cfg.RateLimitBurst = getIntEnv("RATE_LIMIT_BURST", 5) // burst of 5

	// Optional SMTP settings for fallback email notification
	cfg.SMTPHost = getEnv("SMTP_HOST", "")
	cfg.SMTPPort = getIntEnv("SMTP_PORT", 587)
	cfg.SMTPUser = getEnv("SMTP_USER", "")
	cfg.SMTPPassword = getEnv("SMTP_PASSWORD", "")
	cfg.SMTPFrom = getEnv("SMTP_FROM", "noreply@kartoza.com")
	cfg.NotifyEmail = getEnv("NOTIFY_EMAIL", "info@kartoza.com")

	// Validate required fields
	if err := cfg.Validate(); err != nil {
		return nil, err
	}

	return cfg, nil
}

// Validate checks that required configuration is present
func (c *Config) Validate() error {
	if c.ERPNextURL == "" {
		return fmt.Errorf("ERPNEXT_URL is required")
	}

	switch c.AuthMode {
	case AuthModeOAuth2:
		// OAuth2 mode requires access token (and preferably refresh token)
		if c.OAuth2AccessToken == "" {
			return fmt.Errorf("OAUTH2_ACCESS_TOKEN is required when AUTH_MODE=oauth2")
		}
		// Refresh token is highly recommended for long-running services
		if c.OAuth2RefreshToken == "" && c.OAuth2ClientID == "" {
			fmt.Println("WARNING: No OAUTH2_REFRESH_TOKEN or OAUTH2_CLIENT_ID provided - token cannot be refreshed when it expires")
		}
	case AuthModeAPIKey, "":
		// API key mode (default)
		if c.ERPNextAPIKey == "" {
			return fmt.Errorf("ERPNEXT_API_KEY is required when AUTH_MODE=apikey")
		}
		if c.ERPNextSecret == "" {
			return fmt.Errorf("ERPNEXT_API_SECRET is required when AUTH_MODE=apikey")
		}
	default:
		return fmt.Errorf("invalid AUTH_MODE: %s (must be 'apikey' or 'oauth2')", c.AuthMode)
	}

	return nil
}

// UseOAuth2 returns true if OAuth2 authentication is configured
func (c *Config) UseOAuth2() bool {
	return c.AuthMode == AuthModeOAuth2
}

// IsDevelopment returns true if running in development mode
func (c *Config) IsDevelopment() bool {
	return c.Environment == "development"
}

// Helper functions

func getEnv(key, defaultValue string) string {
	if value := os.Getenv(key); value != "" {
		return value
	}
	return defaultValue
}

func getIntEnv(key string, defaultValue int) int {
	if value := os.Getenv(key); value != "" {
		if intVal, err := strconv.Atoi(value); err == nil {
			return intVal
		}
	}
	return defaultValue
}

func splitAndTrim(s string) []string {
	var result []string
	for _, part := range splitString(s, ",") {
		trimmed := trimSpace(part)
		if trimmed != "" {
			result = append(result, trimmed)
		}
	}
	return result
}

func splitString(s, sep string) []string {
	var result []string
	start := 0
	for i := 0; i < len(s); i++ {
		if i+len(sep) <= len(s) && s[i:i+len(sep)] == sep {
			result = append(result, s[start:i])
			start = i + len(sep)
			i += len(sep) - 1
		}
	}
	result = append(result, s[start:])
	return result
}

func trimSpace(s string) string {
	start, end := 0, len(s)
	for start < end && (s[start] == ' ' || s[start] == '\t' || s[start] == '\n' || s[start] == '\r') {
		start++
	}
	for end > start && (s[end-1] == ' ' || s[end-1] == '\t' || s[end-1] == '\n' || s[end-1] == '\r') {
		end--
	}
	return s[start:end]
}
