# PM2.5 Air Quality API Server

A Flask-based REST API server for reading PM2.5 air quality data from a DFRobot SEN0460 sensor via I2C.

## Features

- Real-time PM2.5, PM1.0, and PM10 measurements
- US EPA Air Quality Index (AQI) calculation
- Particle count data (0.3μm to 10μm)
- Sensor health monitoring and error handling
- 30-second warmup period for accurate readings
- CORS support for web applications
- Comprehensive integration tests

## Quick Start

### Using Make (Recommended)

```bash
# Setup environment and install dependencies
make setup

# Run the server
make run

# Run tests
make test                    # Unit tests
make integration-test        # Integration tests with mocked data
make integration-test-real   # Integration tests with real sensor (requires running server)
```

### Manual Setup

1. Create virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the server:
```bash
python aqi_apis.py
```

The server will start on `http://localhost:5000` with debug mode enabled.

## API Endpoints

### Documentation
- `GET /` - API documentation and endpoint list

### Sensor Data
- `GET /api/sensor/data` - Complete sensor data (all measurements + AQI + health)
- `GET /api/sensor/aqi` - AQI information only
- `GET /api/sensor/pm` - PM measurements only
- `GET /api/sensor/particles` - Particle count data

### Status & Health
- `GET /api/sensor/health` - Sensor health status
- `GET /api/sensor/hardware` - Hardware and system information
- `GET /api/sensor/warmup` - Sensor warmup status

## Example Responses

### AQI Endpoint
```json
{
  "status": "success",
  "timestamp": "2025-10-30 12:00:00",
  "warmup": {
    "warmed_up": true,
    "warmup_time": 30,
    "time_since_warmup": 100.5,
    "message": "Sensor ready for accurate readings"
  },
  "aqi": {
    "value": 75,
    "category": "Moderate",
    "color": "#FFFF00",
    "pm25_used": 25.0
  }
}
```

### Complete Data Endpoint
```json
{
  "status": "success",
  "timestamp": "2025-10-30 12:00:00",
  "warmup": {...},
  "hardware": {...},
  "health": {...},
  "aqi": {...},
  "measurements": {
    "standard_pm": {
      "pm1_0": 10,
      "pm2_5": 20,
      "pm10": 30,
      "unit": "ug/m3",
      "note": "Lab-calibrated values"
    },
    "atmospheric_pm": {
      "pm1_0": 15,
      "pm2_5": 25,
      "pm10": 35,
      "unit": "ug/m3",
      "note": "Real-world conditions (recommended)"
    },
    "particle_count": {
      "0_3um": 256,
      "0_5um": 128,
      "1_0um": 64,
      "2_5um": 32,
      "5_0um": 16,
      "10_0um": 8,
      "unit": "particles per 0.1L"
    }
  }

}
```

## Web Dashboard

A responsive web dashboard is included for monitoring air quality data in real-time.

### Features

- **Real-time AQI Display** with color-coded categories and health recommendations
- **PM Measurements** (PM1.0, PM2.5, PM10) with visual progress bars
- **Particle Distribution Chart** showing size breakdown (0.3μm to 10μm)
- **Sensor Status Indicators** (warmup, data integrity, sensor health)
- **Auto-refresh** every 30 seconds
- **Responsive Design** for mobile, tablet, and desktop
- **Error Handling** with graceful degradation when sensor is unavailable

### Running the Web App

```bash
# Start both API server and web app
make webapp-run

# Check status
make webapp-status

# Stop both servers
make webapp-stop

# View logs
make webapp-logs
```

The web app will be available at:
- **Web Dashboard**: http://localhost:8000
- **API Server**: http://localhost:5000

### Web App Structure

```
web-app/
├── index.html          # Main dashboard HTML
├── css/
│   └── styles.css      # Responsive styles
└── js/
    ├── api.js         # API communication
    ├── ui.js          # UI updates and rendering
    └── app.js         # Main application logic
```

## Testing

### Using Make

```bash
make test                    # Unit tests (AQI calculations)
make integration-test        # Integration tests with mocked data
make integration-test-real   # Real sensor integration tests (requires running server)
```

### Manual Testing

Run the comprehensive test suite:

```bash
source venv/bin/activate
python -m pytest test_api.py -v
```

The test suite includes:
- **Unit tests**: AQI calculation logic (no hardware required)
- **Integration tests**: Real API endpoints with actual sensor hardware (requires connected PM2.5 sensor)
- Error handling scenarios
- Data format and type validation
- Sensor warmup behavior
- CORS support verification

**Note**: Integration tests use real sensor hardware and validate response structure, data types, and reasonable value ranges. Tests always run and will fail if PM2.5 sensor hardware is not available or not responding properly.

### Available Make Commands

Run `make help` to see all available commands:

- `make setup` - Create virtual environment and install dependencies
- `make run` - Start the Flask API server
- `make webapp-run` - Start the complete web app (API server + static files)
- `make webapp-stop` - Stop the complete web app
- `make webapp-status` - Check status of web app servers
- `make webapp-logs` - Show web app logs
- `make test` - Run unit tests
- `make integration-test` - Run integration tests with mocked data
- `make integration-test-real` - Run integration tests with real sensor hardware
- `make clean` - Remove virtual environment and cache files
- `make lint` - Run code linting (requires ruff)
- `make format` - Format code (requires ruff)
- `make prod-run` - Run in production mode with Gunicorn
- `make docker-build` - Build Docker image
- `make docker-run` - Run with Docker

## Hardware Requirements

- DFRobot SEN0460 PM2.5 sensor
- I2C connection (default address: 0x19)
- Raspberry Pi or similar Linux system with I2C support

## Configuration

- **I2C Address**: 0x19 (configurable in code)
- **Warmup Time**: 30 seconds (required for accurate readings)
- **Port**: 5000 (configurable)
- **Host**: 0.0.0.0 (accessible from network)

## AQI Categories

| PM2.5 (μg/m³) | AQI Range | Category | Color |
|---------------|-----------|----------|-------|
| 0.0-12.0 | 0-50 | Good | #00E400 |
| 12.1-35.4 | 51-100 | Moderate | #FFFF00 |
| 35.5-55.4 | 101-150 | Unhealthy for Sensitive Groups | #FF7E00 |
| 55.5-150.4 | 151-200 | Unhealthy | #FF0000 |
| 150.5-250.4 | 201-300 | Very Unhealthy | #8F3F97 |
| 250.5-500.4 | 301-500 | Hazardous | #7E0023 |

## Error Handling

The API provides comprehensive error handling:
- I2C communication failures
- Sensor initialization errors
- Data corruption (checksum validation)
- Invalid endpoint requests
- Sensor warmup warnings

## Production Deployment

For production use, consider:
- Using a WSGI server like Gunicorn
- Implementing rate limiting
- Adding authentication
- Setting up monitoring and logging
- Using HTTPS with SSL certificates

Example with Gunicorn:
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 aqi_apis:app
```