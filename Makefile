.PHONY: start stop restart

start:
	@echo "Starting Air Quality Monitor..."
	@python app.py &
	@echo "App started. Access at http://$$(hostname -I | awk '{print $$1}'):5000"

stop:
	@echo "Stopping Air Quality Monitor..."
	@pkill -f "python app.py" || echo "App not running"

restart: stop start