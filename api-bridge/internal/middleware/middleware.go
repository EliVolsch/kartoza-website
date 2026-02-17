package middleware

import (
	"encoding/json"
	"log"
	"net/http"
	"time"

	"github.com/go-chi/chi/v5/middleware"
	"github.com/go-chi/cors"
	"github.com/go-chi/httprate"
)

// CORS returns a CORS middleware configured for the allowed origins
func CORS(allowedOrigins []string) func(http.Handler) http.Handler {
	return cors.Handler(cors.Options{
		AllowedOrigins:   allowedOrigins,
		AllowedMethods:   []string{"GET", "POST", "OPTIONS"},
		AllowedHeaders:   []string{"Accept", "Authorization", "Content-Type", "X-Requested-With"},
		ExposedHeaders:   []string{"Link"},
		AllowCredentials: false,
		MaxAge:           300, // Maximum value not ignored by any of major browsers
	})
}

// RateLimit returns a rate limiting middleware
func RateLimit(requestsPerMinute int, burst int) func(http.Handler) http.Handler {
	return httprate.Limit(
		requestsPerMinute,
		time.Minute,
		httprate.WithLimitHandler(func(w http.ResponseWriter, r *http.Request) {
			w.Header().Set("Content-Type", "application/json")
			w.WriteHeader(http.StatusTooManyRequests)
			json.NewEncoder(w).Encode(map[string]string{
				"error":   "rate_limit_exceeded",
				"message": "Too many requests. Please try again later.",
			})
		}),
	)
}

// Logger returns a request logging middleware
func Logger(isDevelopment bool) func(http.Handler) http.Handler {
	if isDevelopment {
		return middleware.Logger
	}
	// In production, use a more structured logger
	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			start := time.Now()
			ww := middleware.NewWrapResponseWriter(w, r.ProtoMajor)

			defer func() {
				log.Printf(
					"[%s] %s %s %d %s",
					r.Method,
					r.URL.Path,
					r.RemoteAddr,
					ww.Status(),
					time.Since(start),
				)
			}()

			next.ServeHTTP(ww, r)
		})
	}
}

// Recoverer returns a panic recovery middleware
func Recoverer() func(http.Handler) http.Handler {
	return middleware.Recoverer
}

// RequestID adds a unique request ID to each request
func RequestID() func(http.Handler) http.Handler {
	return middleware.RequestID
}

// RealIP sets the RemoteAddr to the real client IP when behind a proxy
func RealIP() func(http.Handler) http.Handler {
	return middleware.RealIP
}

// SecurityHeaders adds common security headers
func SecurityHeaders() func(http.Handler) http.Handler {
	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			w.Header().Set("X-Content-Type-Options", "nosniff")
			w.Header().Set("X-Frame-Options", "DENY")
			w.Header().Set("X-XSS-Protection", "1; mode=block")
			w.Header().Set("Referrer-Policy", "strict-origin-when-cross-origin")
			next.ServeHTTP(w, r)
		})
	}
}

// ContentTypeJSON ensures response is JSON
func ContentTypeJSON() func(http.Handler) http.Handler {
	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			w.Header().Set("Content-Type", "application/json")
			next.ServeHTTP(w, r)
		})
	}
}
