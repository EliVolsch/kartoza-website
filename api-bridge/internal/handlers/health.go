package handlers

import (
	"context"
	"encoding/json"
	"net/http"
	"time"

	"github.com/kartoza/api-bridge/internal/erpnext"
)

// HealthHandler handles health check endpoints
type HealthHandler struct {
	erpClient *erpnext.Client
}

// NewHealthHandler creates a new health handler
func NewHealthHandler(erpClient *erpnext.Client) *HealthHandler {
	return &HealthHandler{
		erpClient: erpClient,
	}
}

// HealthResponse represents the health check response
type HealthResponse struct {
	Status    string            `json:"status"`
	Timestamp string            `json:"timestamp"`
	Services  map[string]string `json:"services"`
}

// Handle returns a simple health check response
func (h *HealthHandler) Handle(w http.ResponseWriter, r *http.Request) {
	response := HealthResponse{
		Status:    "ok",
		Timestamp: time.Now().UTC().Format(time.RFC3339),
		Services: map[string]string{
			"api": "ok",
		},
	}

	w.WriteHeader(http.StatusOK)
	json.NewEncoder(w).Encode(response)
}

// HandleReady checks if all dependencies are ready
func (h *HealthHandler) HandleReady(w http.ResponseWriter, r *http.Request) {
	ctx, cancel := context.WithTimeout(r.Context(), 5*time.Second)
	defer cancel()

	response := HealthResponse{
		Timestamp: time.Now().UTC().Format(time.RFC3339),
		Services:  make(map[string]string),
	}

	// Check ERPNext connectivity
	if err := h.erpClient.HealthCheck(ctx); err != nil {
		response.Status = "degraded"
		response.Services["erpnext"] = "error: " + err.Error()
		w.WriteHeader(http.StatusServiceUnavailable)
	} else {
		response.Status = "ok"
		response.Services["erpnext"] = "ok"
		w.WriteHeader(http.StatusOK)
	}

	response.Services["api"] = "ok"
	json.NewEncoder(w).Encode(response)
}
