package erpnext

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"net/url"
	"sync"
	"time"
)

// AuthMode represents the authentication method
type AuthMode int

const (
	AuthModeAPIKey AuthMode = iota // API key:secret authentication
	AuthModeOAuth2                 // OAuth2 Bearer token authentication
)

// OAuth2Config holds OAuth2 credentials
type OAuth2Config struct {
	ClientID     string
	ClientSecret string
	AccessToken  string
	RefreshToken string
}

// Client handles communication with ERPNext API
type Client struct {
	baseURL    string
	authMode   AuthMode
	apiKey     string
	apiSecret  string
	oauth2     *OAuth2Config
	httpClient *http.Client
	mu         sync.RWMutex // protects OAuth2 token updates
}

// NewClient creates a new ERPNext API client with API key/secret authentication
func NewClient(baseURL, apiKey, apiSecret string) *Client {
	return &Client{
		baseURL:   baseURL,
		authMode:  AuthModeAPIKey,
		apiKey:    apiKey,
		apiSecret: apiSecret,
		httpClient: &http.Client{
			Timeout: 30 * time.Second,
		},
	}
}

// NewOAuth2Client creates a new ERPNext API client with OAuth2 Bearer token authentication
func NewOAuth2Client(baseURL string, oauth2Cfg *OAuth2Config) *Client {
	return &Client{
		baseURL:  baseURL,
		authMode: AuthModeOAuth2,
		oauth2:   oauth2Cfg,
		httpClient: &http.Client{
			Timeout: 30 * time.Second,
		},
	}
}

// Lead represents an ERPNext Lead document
type Lead struct {
	LeadName     string `json:"lead_name"`
	EmailID      string `json:"email_id"`
	Phone        string `json:"phone,omitempty"`
	Company      string `json:"company_name,omitempty"`
	Source       string `json:"source,omitempty"`
	Notes        string `json:"notes,omitempty"`
	Status       string `json:"status,omitempty"`
	LeadOwner    string `json:"lead_owner,omitempty"`
	Territory    string `json:"territory,omitempty"`
	Industry     string `json:"industry,omitempty"`
	RequestType  string `json:"request_type,omitempty"`
	WebsiteSource string `json:"custom_website_source,omitempty"` // Custom field for tracking
}

// APIResponse represents a generic ERPNext API response
type APIResponse struct {
	Data    json.RawMessage `json:"data"`
	Message string          `json:"message,omitempty"`
	Exc     string          `json:"exc,omitempty"`
}

// CreateLeadResponse is the response when creating a lead
type CreateLeadResponse struct {
	Name string `json:"name"`
}

// CreateLead creates a new Lead in ERPNext
func (c *Client) CreateLead(ctx context.Context, lead *Lead) (*CreateLeadResponse, error) {
	// Set defaults
	if lead.Status == "" {
		lead.Status = "Lead"
	}
	if lead.Source == "" {
		lead.Source = "Website"
	}

	payload := map[string]interface{}{
		"doctype":              "Lead",
		"lead_name":            lead.LeadName,
		"email_id":             lead.EmailID,
		"phone":                lead.Phone,
		"company_name":         lead.Company,
		"source":               lead.Source,
		"notes":                lead.Notes,
		"status":               lead.Status,
		"territory":            lead.Territory,
		"request_type":         lead.RequestType,
		"custom_website_source": lead.WebsiteSource,
	}

	// Remove empty fields
	for k, v := range payload {
		if str, ok := v.(string); ok && str == "" {
			delete(payload, k)
		}
	}

	resp, err := c.doRequest(ctx, "POST", "/api/resource/Lead", payload)
	if err != nil {
		return nil, fmt.Errorf("failed to create lead: %w", err)
	}

	var result struct {
		Data CreateLeadResponse `json:"data"`
	}
	if err := json.Unmarshal(resp, &result); err != nil {
		return nil, fmt.Errorf("failed to parse response: %w", err)
	}

	return &result.Data, nil
}

// Communication represents an ERPNext Communication document (for logging interactions)
type Communication struct {
	Subject        string `json:"subject"`
	Content        string `json:"content"`
	SentOrReceived string `json:"sent_or_received"` // "Sent" or "Received"
	CommType       string `json:"communication_type"` // "Communication", "Comment", etc.
	CommMedium     string `json:"communication_medium"` // "Email", "Phone", "Website"
	Sender         string `json:"sender,omitempty"`
	Recipients     string `json:"recipients,omitempty"`
	ReferenceDoctype string `json:"reference_doctype,omitempty"`
	ReferenceName   string `json:"reference_name,omitempty"`
}

// CreateCommunication logs a communication in ERPNext
func (c *Client) CreateCommunication(ctx context.Context, comm *Communication) error {
	if comm.SentOrReceived == "" {
		comm.SentOrReceived = "Received"
	}
	if comm.CommType == "" {
		comm.CommType = "Communication"
	}
	if comm.CommMedium == "" {
		comm.CommMedium = "Website"
	}

	payload := map[string]interface{}{
		"doctype":              "Communication",
		"subject":              comm.Subject,
		"content":              comm.Content,
		"sent_or_received":     comm.SentOrReceived,
		"communication_type":   comm.CommType,
		"communication_medium": comm.CommMedium,
		"sender":               comm.Sender,
		"recipients":           comm.Recipients,
		"reference_doctype":    comm.ReferenceDoctype,
		"reference_name":       comm.ReferenceName,
	}

	_, err := c.doRequest(ctx, "POST", "/api/resource/Communication", payload)
	if err != nil {
		return fmt.Errorf("failed to create communication: %w", err)
	}

	return nil
}

// HealthCheck verifies connectivity to ERPNext
func (c *Client) HealthCheck(ctx context.Context) error {
	_, err := c.doRequest(ctx, "GET", "/api/method/frappe.auth.get_logged_user", nil)
	if err != nil {
		return fmt.Errorf("ERPNext health check failed: %w", err)
	}
	return nil
}

// refreshOAuth2Token attempts to refresh the OAuth2 access token
func (c *Client) refreshOAuth2Token(ctx context.Context) error {
	if c.oauth2 == nil || c.oauth2.RefreshToken == "" {
		return fmt.Errorf("no refresh token available")
	}

	// Prepare token refresh request
	data := url.Values{}
	data.Set("grant_type", "refresh_token")
	data.Set("refresh_token", c.oauth2.RefreshToken)
	if c.oauth2.ClientID != "" {
		data.Set("client_id", c.oauth2.ClientID)
	}
	if c.oauth2.ClientSecret != "" {
		data.Set("client_secret", c.oauth2.ClientSecret)
	}

	req, err := http.NewRequestWithContext(ctx, "POST", c.baseURL+"/api/method/frappe.integrations.oauth2.get_token", bytes.NewBufferString(data.Encode()))
	if err != nil {
		return fmt.Errorf("failed to create token refresh request: %w", err)
	}
	req.Header.Set("Content-Type", "application/x-www-form-urlencoded")

	resp, err := c.httpClient.Do(req)
	if err != nil {
		return fmt.Errorf("token refresh request failed: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		body, _ := io.ReadAll(resp.Body)
		return fmt.Errorf("token refresh failed (status %d): %s", resp.StatusCode, string(body))
	}

	var tokenResp struct {
		AccessToken  string `json:"access_token"`
		RefreshToken string `json:"refresh_token"`
		TokenType    string `json:"token_type"`
		ExpiresIn    int    `json:"expires_in"`
	}

	if err := json.NewDecoder(resp.Body).Decode(&tokenResp); err != nil {
		return fmt.Errorf("failed to parse token response: %w", err)
	}

	// Update tokens (thread-safe)
	c.mu.Lock()
	c.oauth2.AccessToken = tokenResp.AccessToken
	if tokenResp.RefreshToken != "" {
		c.oauth2.RefreshToken = tokenResp.RefreshToken
	}
	c.mu.Unlock()

	return nil
}

// getAuthHeader returns the appropriate authorization header value
func (c *Client) getAuthHeader() string {
	switch c.authMode {
	case AuthModeOAuth2:
		c.mu.RLock()
		token := c.oauth2.AccessToken
		c.mu.RUnlock()
		return "Bearer " + token
	default:
		return fmt.Sprintf("token %s:%s", c.apiKey, c.apiSecret)
	}
}

// doRequest performs an HTTP request to the ERPNext API
func (c *Client) doRequest(ctx context.Context, method, endpoint string, payload interface{}) ([]byte, error) {
	return c.doRequestWithRetry(ctx, method, endpoint, payload, true)
}

// doRequestWithRetry performs an HTTP request with optional token refresh retry
func (c *Client) doRequestWithRetry(ctx context.Context, method, endpoint string, payload interface{}, allowRetry bool) ([]byte, error) {
	reqURL := c.baseURL + endpoint

	var body io.Reader
	var bodyBytes []byte
	if payload != nil {
		var err error
		bodyBytes, err = json.Marshal(payload)
		if err != nil {
			return nil, fmt.Errorf("failed to marshal payload: %w", err)
		}
		body = bytes.NewBuffer(bodyBytes)
	}

	req, err := http.NewRequestWithContext(ctx, method, reqURL, body)
	if err != nil {
		return nil, fmt.Errorf("failed to create request: %w", err)
	}

	// Set authentication header
	req.Header.Set("Authorization", c.getAuthHeader())
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("Accept", "application/json")

	resp, err := c.httpClient.Do(req)
	if err != nil {
		return nil, fmt.Errorf("request failed: %w", err)
	}
	defer resp.Body.Close()

	respBody, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, fmt.Errorf("failed to read response: %w", err)
	}

	// Handle 401 Unauthorized - try to refresh token if using OAuth2
	if resp.StatusCode == http.StatusUnauthorized && c.authMode == AuthModeOAuth2 && allowRetry {
		if err := c.refreshOAuth2Token(ctx); err != nil {
			return nil, fmt.Errorf("authentication failed and token refresh failed: %w", err)
		}
		// Retry the request with the new token (but don't allow another retry)
		if bodyBytes != nil {
			body = bytes.NewBuffer(bodyBytes)
		}
		return c.doRequestWithRetry(ctx, method, endpoint, payload, false)
	}

	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		var apiErr APIResponse
		if json.Unmarshal(respBody, &apiErr) == nil && apiErr.Exc != "" {
			return nil, fmt.Errorf("ERPNext error (status %d): %s", resp.StatusCode, apiErr.Exc)
		}
		return nil, fmt.Errorf("ERPNext error (status %d): %s", resp.StatusCode, string(respBody))
	}

	return respBody, nil
}
