# AGENTS.md

## Build/Lint/Test Commands
- Install dependencies: `pip install -r requirements.txt`
- Run app: `python app.py` or `make start`
- Stop app: `make stop`
- Restart app: `make restart`
- No explicit lint commands found; use `flake8` or `black` if installed
- No tests present; for single test, use `pytest` if added (e.g., `pytest tests/test_specific.py`)

## Code Style Guidelines
- Imports: Standard library first, then third-party (e.g., flask), then local modules
- Formatting: 4-space indentation, consistent spacing around operators
- Naming: snake_case for functions/variables (e.g., load_settings), CamelCase for classes (e.g., SEN0460)
- Types: No explicit type hints; use dicts/lists for data structures
- Error Handling: Use try-except blocks for external calls (e.g., requests, sensor reads)
- Logging: Use app.logger for Flask; format as in app.py
- No Cursor or Copilot rules found in codebase

## Coding Agent Instructions
- After every code change, perform end-to-end testing from UI to backend:
  - Start the application using `python app.py` or `make start`
  - Test UI functionality: Access http://localhost:5000/ and verify the index page loads with device info and settings
  - Test backend API endpoints: Use curl to query /api/data, /api/settings, /api/graph_data, etc., and verify JSON responses (e.g., `curl http://localhost:5000/api/data`)
  - Test data flow: Update settings via POST to /api/settings and confirm changes persist and affect /api/data responses
  - Check logs: Review app.log and sensor.log for errors after tests
  - Stop the application using `make stop` or Ctrl+C