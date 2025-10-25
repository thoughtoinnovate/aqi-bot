.PHONY: start stop restart

PID_FILE = app.pid

start:
	@echo "Starting Air Quality Monitor with identifier aqibot..."
	@-pkill -f "aqibot" 2>/dev/null || true
	@rm -f $(PID_FILE)
	@sleep 1
	@nohup python app.py > /dev/null 2>&1 &
	@echo $$! > $(PID_FILE)
	@echo "App started with identifier aqibot. Access at http://$$(hostname -I | awk '{print $$1}'):5000"

stop:
	@echo "Stopping Air Quality Monitor..."
	@if [ -f $(PID_FILE) ] && kill -0 `cat $(PID_FILE)` 2>/dev/null; then kill `cat $(PID_FILE)` && rm $(PID_FILE) && echo "App stopped"; else echo "App not running" && rm -f $(PID_FILE); fi

restart: stop start