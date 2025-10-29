# PM2.5 Air Quality API Server - Makefile

.PHONY: help setup run test integration-test integration-test-real clean webapp-run webapp-stop webapp-status webapp-logs

# Virtual environment setup
VENV := venv
PYTHON := python3
PIP := $(VENV)/bin/pip
PYTHON_VENV := $(VENV)/bin/python
ACTIVATE := . $(VENV)/bin/activate &&

# Check if virtual environment exists and create if needed
$(VENV)/bin/activate:
	@echo "Creating virtual environment..."
	$(PYTHON) -m venv $(VENV)
	@echo "Installing dependencies..."
	$(PIP) install -r requirements.txt

# Default target
help: ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-20s %s\n", $$1, $$2}'

setup: $(VENV)/bin/activate ## Create virtual environment and install dependencies
	@echo "Setup complete! Run 'make run' to start the server."

run: $(VENV)/bin/activate ## Start the Flask API server
	@echo "Starting PM2.5 API server..."
	$(ACTIVATE) python aqi_apis.py

test: $(VENV)/bin/activate ## Run unit tests with pytest
	@echo "Running unit tests..."
	$(ACTIVATE) python -m pytest test_api.py::TestAQICalculation -v

integration-test: $(VENV)/bin/activate ## Run integration tests with real sensor hardware
	@echo "Running integration tests with real sensor data..."
	$(ACTIVATE) python -m pytest test_api.py::TestAPIEndpoints test_api.py::TestErrorHandling -v

integration-test-real: $(VENV)/bin/activate ## Run integration tests with real sensor hardware (server must be running)
	@echo "Running integration tests with real sensor data..."
	@echo "WARNING: This requires the PM2.5 sensor to be connected via I2C"
	@echo "Make sure the server is running with 'make run' in another terminal"
	$(ACTIVATE) python test_real_integration.py

clean: ## Remove virtual environment and cache files
	@echo "Cleaning up..."
	rm -rf $(VENV)
	rm -rf __pycache__
	rm -rf .pytest_cache
	rm -f *.pyc
	rm -f server.log
	rm -f webapp.log
	@echo "Cleanup complete!"

# Development targets
lint: $(VENV)/bin/activate ## Run code linting (if ruff is available)
	@echo "Running linter..."
	$(ACTIVATE) python -m ruff check . || echo "Ruff not installed, skipping lint"

format: $(VENV)/bin/activate ## Format code (if ruff is available)
	@echo "Formatting code..."
	$(ACTIVATE) python -m ruff format . || echo "Ruff not installed, skipping format"

# Production deployment
prod-run: $(VENV)/bin/activate ## Run in production mode with Gunicorn
	@echo "Starting production server with Gunicorn..."
	$(ACTIVATE) gunicorn -w 4 -b 0.0.0.0:5000 aqi_apis:app

# Web App targets
webapp-run: $(VENV)/bin/activate ## Start the complete web app (API server + static files)
	@echo "Starting PM2.5 Web App..."
	@echo "API Server: http://localhost:5000"
	@echo "Web App: http://localhost:8000"
	@echo ""
	@echo "Starting servers in background..."
	./start-webapp.sh > webapp-output.log 2>&1 &
	@sleep 3
	@echo ""
	@echo "Web app started successfully!"
	@echo "Check status with: make webapp-status"
	@echo "View logs with: make webapp-logs"
	@echo ""
	@echo "To stop: make webapp-stop"

webapp-stop: ## Stop the complete web app
	./stop-webapp.sh

webapp-status: ## Check status of web app servers
	@echo "PM2.5 Web App Status:"
	@if pgrep -f "python aqi_apis.py" > /dev/null 2>&1; then \
		echo "✅ API Server: Running (PID: $$(pgrep -f "python aqi_apis.py")) - http://localhost:5000"; \
	else \
		echo "❌ API Server: Not running"; \
	fi
	@if pgrep -f "http.server 8000" > /dev/null 2>&1; then \
		echo "✅ Web App: Running (PID: $$(pgrep -f "http.server 8000")) - http://localhost:8000"; \
	else \
		echo "❌ Web App: Not running"; \
	fi
	@if [ -f server.log ]; then \
		echo ""; \
		echo "Recent API server logs:"; \
		tail -5 server.log 2>/dev/null || echo "No recent logs"; \
	fi

webapp-logs: ## Show web app logs
	@echo "API Server Logs (server.log):"
	@if [ -f server.log ]; then \
		cat server.log; \
	else \
		echo "No server.log found"; \
	fi
	@echo ""
	@echo "Web App Logs (webapp.log):"
	@if [ -f webapp.log ]; then \
		cat webapp.log; \
	else \
		echo "No webapp.log found"; \
	fi

# Docker support (if Dockerfile exists)
docker-build: ## Build Docker image
	@echo "Building Docker image..."
	docker build -t pm25-api .

docker-run: ## Run with Docker
	@echo "Running with Docker..."
	docker run -p 5000:5000 --device /dev/i2c-1 pm25-api