package handlers

import (
	"context"
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"strings"
	"time"

	"github.com/kartoza/api-bridge/internal/erpnext"
)

// ContactHandler handles contact form submissions
type ContactHandler struct {
	erpClient   *erpnext.Client
	notifyEmail string
}

// NewContactHandler creates a new contact handler
func NewContactHandler(erpClient *erpnext.Client, notifyEmail string) *ContactHandler {
	return &ContactHandler{
		erpClient:   erpClient,
		notifyEmail: notifyEmail,
	}
}

// ContactRequest represents the incoming contact form data
type ContactRequest struct {
	Name         string `json:"name"`
	Email        string `json:"email"`
	Organisation string `json:"organisation,omitempty"`
	Phone        string `json:"phone,omitempty"`
	Interest     string `json:"interest"`
	Message      string `json:"message"`
	Source       string `json:"source,omitempty"` // How they heard about us
}

// ContactResponse is the response sent back to the client
type ContactResponse struct {
	Success bool   `json:"success"`
	Message string `json:"message"`
	LeadID  string `json:"lead_id,omitempty"`
}

// ErrorResponse represents an error response
type ErrorResponse struct {
	Error   string `json:"error"`
	Message string `json:"message"`
}

// Handle processes contact form submissions
func (h *ContactHandler) Handle(w http.ResponseWriter, r *http.Request) {
	// Only accept POST
	if r.Method != http.MethodPost {
		writeError(w, http.StatusMethodNotAllowed, "method_not_allowed", "Only POST requests are accepted")
		return
	}

	// Parse request body
	var req ContactRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		writeError(w, http.StatusBadRequest, "invalid_json", "Invalid JSON in request body")
		return
	}

	// Validate required fields
	if err := validateContactRequest(&req); err != nil {
		writeError(w, http.StatusBadRequest, "validation_error", err.Error())
		return
	}

	// Sanitize inputs
	sanitizeContactRequest(&req)

	// Create context with timeout
	ctx, cancel := context.WithTimeout(r.Context(), 30*time.Second)
	defer cancel()

	// Create Lead in ERPNext
	lead := &erpnext.Lead{
		LeadName:      req.Name,
		EmailID:       req.Email,
		Phone:         req.Phone,
		Company:       req.Organisation,
		Source:        "Website",
		RequestType:   mapInterestToRequestType(req.Interest),
		Notes:         formatNotes(&req),
		WebsiteSource: req.Source,
		Territory:     "All Territories", // Default territory
	}

	result, err := h.erpClient.CreateLead(ctx, lead)
	if err != nil {
		log.Printf("ERROR: Failed to create lead in ERPNext: %v", err)
		// Don't expose internal errors to client
		writeError(w, http.StatusInternalServerError, "submission_failed", "Failed to process your request. Please try again or contact us directly.")
		return
	}

	// Also create a communication record with the full message
	comm := &erpnext.Communication{
		Subject:          fmt.Sprintf("Website Contact: %s", req.Interest),
		Content:          formatCommunicationContent(&req),
		Sender:           req.Email,
		Recipients:       h.notifyEmail,
		ReferenceDoctype: "Lead",
		ReferenceName:    result.Name,
	}

	if err := h.erpClient.CreateCommunication(ctx, comm); err != nil {
		// Log but don't fail - lead was created successfully
		log.Printf("WARNING: Failed to create communication record: %v", err)
	}

	log.Printf("INFO: Created lead %s for %s <%s>", result.Name, req.Name, req.Email)

	// Send success response
	w.WriteHeader(http.StatusOK)
	json.NewEncoder(w).Encode(ContactResponse{
		Success: true,
		Message: "Thank you! Your message has been received. We'll be in touch soon.",
		LeadID:  result.Name,
	})
}

// validateContactRequest validates the contact form fields
func validateContactRequest(req *ContactRequest) error {
	if strings.TrimSpace(req.Name) == "" {
		return fmt.Errorf("name is required")
	}
	if strings.TrimSpace(req.Email) == "" {
		return fmt.Errorf("email is required")
	}
	if !isValidEmail(req.Email) {
		return fmt.Errorf("invalid email address")
	}
	if strings.TrimSpace(req.Interest) == "" {
		return fmt.Errorf("interest selection is required")
	}
	if strings.TrimSpace(req.Message) == "" {
		return fmt.Errorf("message is required")
	}
	if len(req.Message) > 5000 {
		return fmt.Errorf("message is too long (max 5000 characters)")
	}
	return nil
}

// sanitizeContactRequest cleans up user input
func sanitizeContactRequest(req *ContactRequest) {
	req.Name = strings.TrimSpace(req.Name)
	req.Email = strings.TrimSpace(strings.ToLower(req.Email))
	req.Organisation = strings.TrimSpace(req.Organisation)
	req.Phone = strings.TrimSpace(req.Phone)
	req.Interest = strings.TrimSpace(req.Interest)
	req.Message = strings.TrimSpace(req.Message)
	req.Source = strings.TrimSpace(req.Source)
}

// isValidEmail performs basic email validation
func isValidEmail(email string) bool {
	// Basic validation - contains @ and has something before and after
	parts := strings.Split(email, "@")
	if len(parts) != 2 {
		return false
	}
	if len(parts[0]) == 0 || len(parts[1]) == 0 {
		return false
	}
	// Check domain has at least one dot
	if !strings.Contains(parts[1], ".") {
		return false
	}
	return true
}

// mapInterestToRequestType maps form interest values to ERPNext request types
func mapInterestToRequestType(interest string) string {
	mapping := map[string]string{
		"hosting":     "Product Enquiry",
		"mycivitas":   "Product Enquiry",
		"bims":        "Product Enquiry",
		"training":    "Training",
		"development": "Product Enquiry",
		"consulting":  "Request for Information",
		"support":     "Technical Support",
		"partnership": "Partnership",
		"other":       "Request for Information",
	}
	if rt, ok := mapping[strings.ToLower(interest)]; ok {
		return rt
	}
	return "Request for Information"
}

// formatNotes creates a formatted notes field for the lead
func formatNotes(req *ContactRequest) string {
	var notes strings.Builder
	notes.WriteString(fmt.Sprintf("**Interest:** %s\n\n", req.Interest))
	if req.Organisation != "" {
		notes.WriteString(fmt.Sprintf("**Organisation:** %s\n\n", req.Organisation))
	}
	if req.Source != "" {
		notes.WriteString(fmt.Sprintf("**How they found us:** %s\n\n", req.Source))
	}
	notes.WriteString(fmt.Sprintf("**Message:**\n%s", req.Message))
	return notes.String()
}

// formatCommunicationContent creates HTML content for the communication
func formatCommunicationContent(req *ContactRequest) string {
	var content strings.Builder
	content.WriteString("<h3>Contact Form Submission</h3>")
	content.WriteString(fmt.Sprintf("<p><strong>From:</strong> %s &lt;%s&gt;</p>", req.Name, req.Email))
	if req.Organisation != "" {
		content.WriteString(fmt.Sprintf("<p><strong>Organisation:</strong> %s</p>", req.Organisation))
	}
	if req.Phone != "" {
		content.WriteString(fmt.Sprintf("<p><strong>Phone:</strong> %s</p>", req.Phone))
	}
	content.WriteString(fmt.Sprintf("<p><strong>Interest:</strong> %s</p>", req.Interest))
	if req.Source != "" {
		content.WriteString(fmt.Sprintf("<p><strong>Source:</strong> %s</p>", req.Source))
	}
	content.WriteString("<hr>")
	content.WriteString(fmt.Sprintf("<p>%s</p>", strings.ReplaceAll(req.Message, "\n", "<br>")))
	return content.String()
}

// writeError writes a JSON error response
func writeError(w http.ResponseWriter, status int, errCode, message string) {
	w.WriteHeader(status)
	json.NewEncoder(w).Encode(ErrorResponse{
		Error:   errCode,
		Message: message,
	})
}
