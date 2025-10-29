#!/bin/bash

# PM2.5 Web App Startup Script

echo "Starting PM2.5 Web App..."
echo "API Server: http://localhost:5000"
echo "Web App: http://localhost:8000"
echo ""

# Activate virtual environment
source venv/bin/activate

# Start API server
echo "Starting API server..."
python aqi_apis.py > server.log 2>&1 &
API_PID=$!
echo "API Server PID: $API_PID"

# Wait a bit for API server to start
sleep 3

# Start web app server
echo "Starting web app server..."
cd web-app
python3 -m http.server 8000 > ../webapp.log 2>&1 &
WEBAPP_PID=$!
echo "Web App Server PID: $WEBAPP_PID"
cd ..

echo ""
echo "Web app started successfully!"
echo "API Server PID: $API_PID"
echo "Web App PID: $WEBAPP_PID"
echo ""
echo "To stop: make webapp-stop"
echo "To check status: make webapp-status"
echo ""
echo "Press Ctrl+C to stop both servers..."

# Wait for user to stop
trap "echo 'Stopping servers...'; kill $API_PID 2>/dev/null; kill $WEBAPP_PID 2>/dev/null; exit" INT
wait