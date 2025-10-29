#!/bin/bash

# PM2.5 Web App Stop Script

echo "Stopping PM2.5 Web App..."

# Stop API server
echo "Stopping API server..."
pkill -f "python aqi_apis.py" 2>/dev/null && echo "API server stopped" || echo "API server not running"

# Stop web app server
echo "Stopping web app server..."
pkill -f "http.server 8000" 2>/dev/null && echo "Web app server stopped" || echo "Web app server not running"

echo "Web app stopped."