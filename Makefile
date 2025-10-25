.PHONY: start stop restart

PID_FILE = app.pid

start:
	@echo "Starting Air Quality Monitor..."
	@if [ -f $(PID_FILE) ]; then echo "App already running"; exit 1; fi
	@python app.py &
	@echo $$! > $(PID_FILE)
	@echo "App started. Access at http://$$(hostname -I | awk '{print $$1}'):5000"

stop:
	@echo "Stopping Air Quality Monitor..."
	@if [ -f $(PID_FILE) ]; then kill `cat $(PID_FILE)` && rm $(PID_FILE); else echo "App not running"; fi

restart: stop start