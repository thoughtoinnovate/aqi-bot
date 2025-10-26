.PHONY: start stop restart status logs test clean install dev debug sensor-check

PID_FILE = app.pid
LOG_FILE = app.log

# Default target
all: install start

# Install dependencies
install:
	@echo "Installing Python dependencies..."
	@pip install -r requirements.txt
	@echo "Dependencies installed successfully"

# Start the application
start:
	@echo "Starting Air Quality Monitor..."
	@# Stop any existing instance first
	@$(MAKE) stop >/dev/null 2>&1 || true
	@sleep 1
	@# Start the app in background with proper logging
	@nohup python app.py >> $(LOG_FILE) 2>&1 & echo $$! > $(PID_FILE)
	@sleep 3
	@# Verify the app is running
	@if [ -f $(PID_FILE) ] && kill -0 `cat $(PID_FILE)` 2>/dev/null; then \
		echo "✓ Air Quality Monitor started successfully"; \
		echo "  Access at: http://$$(hostname -I | awk '{print $$1}'):5000"; \
		echo "  PID: `cat $(PID_FILE)`"; \
		echo "  Logs: tail -f $(LOG_FILE)"; \
	else \
		echo "✗ Failed to start Air Quality Monitor"; \
		rm -f $(PID_FILE); \
		exit 1; \
	fi

# Stop the application
stop:
	@echo "Stopping Air Quality Monitor..."
	@if [ -f $(PID_FILE) ]; then \
		if kill -0 `cat $(PID_FILE)` 2>/dev/null; then \
			kill `cat $(PID_FILE)` && \
			sleep 1 && \
			rm -f $(PID_FILE) && \
			echo "✓ Air Quality Monitor stopped"; \
		else \
			echo "✗ App PID file exists but process not running"; \
			rm -f $(PID_FILE); \
		fi; \
	else \
		echo "✓ No PID file found"; \
	fi
	@# Kill any remaining Python app processes
	@-pkill -f "python app.py" 2>/dev/null && echo "✓ Killed orphaned processes" || echo "✓ No processes to stop"

# Restart the application
restart: stop start

# Check application status
status:
	@echo "=== Air Quality Monitor Status ==="
	@if [ -f $(PID_FILE) ]; then \
		if kill -0 `cat $(PID_FILE)` 2>/dev/null; then \
			echo "Status: RUNNING"; \
			echo "PID: `cat $(PID_FILE)`"; \
			echo "URL: http://$$(hostname -I | awk '{print $$1}'):5000"; \
			echo "Uptime: $$(ps -o etime= -p $$(cat $(PID_FILE)) 2>/dev/null | tr -d ' ')"; \
		else \
			echo "Status: NOT RUNNING (stale PID file)"; \
			rm -f $(PID_FILE); \
		fi; \
	else \
		echo "Status: NOT RUNNING"; \
	fi
	@echo "=== Recent Logs ==="
	@if [ -f $(LOG_FILE) ]; then \
		tail -5 $(LOG_FILE); \
	else \
		echo "No log file found"; \
	fi

# Show logs
logs:
	@echo "=== Air Quality Monitor Logs ==="
	@if [ -f $(LOG_FILE) ]; then \
		tail -f $(LOG_FILE); \
	else \
		echo "No log file found. Start the application first."; \
	fi

# Test the application
test:
	@echo "=== Testing Air Quality Monitor ==="
	@echo "1. Checking if app is running..."
	@if [ -f $(PID_FILE) ] && kill -0 `cat $(PID_FILE)` 2>/dev/null; then \
		echo "✓ App is running (PID: `cat $(PID_FILE)`)"; \
	else \
		echo "✗ App is not running"; \
		exit 1; \
	fi
	@echo "2. Testing API endpoint..."
	@curl -s http://localhost:5000/api/data > /tmp/api_test.json 2>/tmp/api_error.txt; \
	if [ $$? -eq 0 ]; then \
		echo "✓ API endpoint responding (HTTP 200)"; \
		echo "Response: $$(cat /tmp/api_test.json)"; \
	else \
		echo "✗ API endpoint failed"; \
		echo "Error: $$(cat /tmp/api_error.txt)"; \
		exit 1; \
	fi
	@echo "3. Checking sensor communication..."
	@python3 -c "from sensor import SEN0460; s=SEN0460(); v=s.gain_version(); print(f'Sensor version: {v}' if v else 'Sensor communication failed')" 2>/dev/null || echo "✗ Sensor test failed"

# Clean up
clean:
	@echo "Cleaning up..."
	@$(MAKE) stop
	@rm -f $(PID_FILE) $(LOG_FILE)
	@echo "✓ Cleanup completed"

# Development mode (run in foreground)
dev:
	@echo "Starting Air Quality Monitor in development mode..."
	@echo "Press Ctrl+C to stop"
	@python app.py

# Debug mode with verbose output
debug:
	@echo "Starting Air Quality Monitor in debug mode..."
	@echo "Press Ctrl+C to stop"
	@FLASK_ENV=development python -u app.py

# Check sensor hardware
sensor-check:
	@echo "=== Sensor Hardware Check ==="
	@echo "1. Checking I2C bus..."
	@if command -v i2cdetect >/dev/null 2>&1; then \
		echo "I2C devices:"; \
		i2cdetect -y 1 || echo "Failed to scan I2C bus (try with sudo)"; \
	else \
		echo "i2cdetect not found - install i2c-tools"; \
	fi
	@echo "2. Testing sensor communication..."
	@python3 -c "from sensor import SEN0460; import time; s=SEN0460(); print('Version:', s.gain_version()); s.awake(); time.sleep(1); print('PM2.5:', s.gain_particle_concentration_ugm3(s.PARTICLE_PM2_5_STANDARD)); s.set_lowpower()" 2>/dev/null || echo "✗ Sensor test failed"

# Help
help:
	@echo "Air Quality Monitor - Available Commands:"
	@echo ""
	@echo "  install     - Install Python dependencies"
	@echo "  start       - Start the application in background"
	@echo "  stop        - Stop the application"
	@echo "  restart     - Restart the application"
	@echo "  status      - Show application status and recent logs"
	@echo "  logs        - Follow application logs (tail -f)"
	@echo "  test        - Run basic functionality tests"
	@echo "  dev         - Run in development mode (foreground)"
	@echo "  debug       - Run with debug output (foreground)"
	@echo "  sensor-check - Check sensor hardware and communication"
	@echo "  clean       - Stop app and remove log/PID files"
	@echo "  help        - Show this help message"
	@echo ""
	@echo "Examples:"
	@echo "  make install start    - Install deps and start"
	@echo "  make status           - Check if running"
	@echo "  make logs             - View live logs"
	@echo "  make sensor-check     - Debug sensor issues"