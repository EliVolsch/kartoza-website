package main

import (
	"fmt"
	"log"
	"net/http"
	"os"
	"os/signal"
	"syscall"

	"github.com/go-chi/chi/v5"
	"github.com/joho/godotenv"

	"github.com/kartoza/api-bridge/internal/config"
	"github.com/kartoza/api-bridge/internal/erpnext"
	"github.com/kartoza/api-bridge/internal/handlers"
	"github.com/kartoza/api-bridge/internal/middleware"
)

func main() {
	// Load .env file if present (for local development)
	if err := godotenv.Load(); err != nil {
		// Not an error if .env doesn't exist - we may be using env vars directly
		log.Println("INFO: No .env file found, using environment variables")
	}

	// Load configuration
	cfg, err := config.Load()
	if err != nil {
		log.Fatalf("FATAL: Failed to load configuration: %v", err)
	}

	log.Printf("INFO: Starting API Bridge in %s mode on port %d", cfg.Environment, cfg.Port)

	// Initialize ERPNext client based on auth mode
	var erpClient *erpnext.Client
	if cfg.UseOAuth2() {
		log.Printf("INFO: Using OAuth2 Bearer token authentication")
		oauth2Cfg := &erpnext.OAuth2Config{
			ClientID:     cfg.OAuth2ClientID,
			ClientSecret: cfg.OAuth2ClientSecret,
			AccessToken:  cfg.OAuth2AccessToken,
			RefreshToken: cfg.OAuth2RefreshToken,
		}
		erpClient = erpnext.NewOAuth2Client(cfg.ERPNextURL, oauth2Cfg)
	} else {
		log.Printf("INFO: Using API key/secret authentication")
		erpClient = erpnext.NewClient(cfg.ERPNextURL, cfg.ERPNextAPIKey, cfg.ERPNextSecret)
	}

	// Initialize handlers
	contactHandler := handlers.NewContactHandler(erpClient, cfg.NotifyEmail)
	healthHandler := handlers.NewHealthHandler(erpClient)

	// Setup router
	r := chi.NewRouter()

	// Global middleware
	r.Use(middleware.RealIP())
	r.Use(middleware.RequestID())
	r.Use(middleware.Logger(cfg.IsDevelopment()))
	r.Use(middleware.Recoverer())
	r.Use(middleware.SecurityHeaders())
	r.Use(middleware.CORS(cfg.AllowedOrigins))

	// Health check endpoints (no rate limiting)
	r.Get("/health", healthHandler.Handle)
	r.Get("/ready", healthHandler.HandleReady)

	// API routes with rate limiting
	r.Route("/api", func(r chi.Router) {
		r.Use(middleware.RateLimit(cfg.RateLimit, cfg.RateLimitBurst))
		r.Use(middleware.ContentTypeJSON())

		// Contact form endpoint
		r.Post("/contact", contactHandler.Handle)

		// Future endpoints can be added here:
		// r.Post("/quote", quoteHandler.Handle)
		// r.Post("/newsletter", newsletterHandler.Handle)
		// r.Post("/support", supportHandler.Handle)
	})

	// Create server
	server := &http.Server{
		Addr:    fmt.Sprintf(":%d", cfg.Port),
		Handler: r,
	}

	// Handle graceful shutdown
	go func() {
		sigChan := make(chan os.Signal, 1)
		signal.Notify(sigChan, syscall.SIGINT, syscall.SIGTERM)
		<-sigChan

		log.Println("INFO: Shutting down server...")
		if err := server.Close(); err != nil {
			log.Printf("ERROR: Server close error: %v", err)
		}
	}()

	// Start server
	log.Printf("INFO: Server listening on http://localhost:%d", cfg.Port)
	log.Printf("INFO: Endpoints available:")
	log.Printf("       POST /api/contact  - Contact form submission")
	log.Printf("       GET  /health       - Health check")
	log.Printf("       GET  /ready        - Readiness check (includes ERPNext)")

	if err := server.ListenAndServe(); err != http.ErrServerClosed {
		log.Fatalf("FATAL: Server error: %v", err)
	}

	log.Println("INFO: Server stopped")
}
