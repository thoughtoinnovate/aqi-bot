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