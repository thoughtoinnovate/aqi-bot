import pytest
import json
import re
from aqi_apis import app, PM25Sensor


# Validation helper functions for real sensor data testing
def validate_response_structure(data, required_keys):
    """Validate that required keys are present in response"""
    for key in required_keys:
        assert key in data, f"Missing required key: {key}"

def validate_data_types(data, type_checks):
    """Validate data types for specific fields"""
    for field_path, expected_type in type_checks.items():
        keys = field_path.split('.')
        value = data
        for key in keys:
            assert key in value, f"Missing key in path {field_path}: {key}"
            value = value[key]
        assert isinstance(value, expected_type), f"Field {field_path} should be {expected_type.__name__}, got {type(value).__name__}"

def validate_value_ranges(data, range_checks):
    """Validate that numeric values are in reasonable ranges"""
    for field_path, (min_val, max_val) in range_checks.items():
        keys = field_path.split('.')
        value = data
        for key in keys:
            value = value[key]
        assert min_val <= value <= max_val, f"Field {field_path} value {value} not in range [{min_val}, {max_val}]"

def validate_timestamp_format(timestamp_str):
    """Validate timestamp string format"""
    # Should match YYYY-MM-DD HH:MM:SS format
    pattern = r'^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$'
    assert re.match(pattern, timestamp_str), f"Timestamp {timestamp_str} does not match expected format"

def validate_aqi_data(aqi_data):
    """Validate AQI data structure and values"""
    required_keys = ['value', 'category', 'color', 'pm25_used']
    validate_response_structure(aqi_data, required_keys)

    type_checks = {
        'value': int,
        'category': str,
        'color': str,
        'pm25_used': (int, float)
    }
    validate_data_types({'aqi': aqi_data}, {'aqi.' + k: v for k, v in type_checks.items()})

    range_checks = {
        'value': (0, 500),
        'pm25_used': (0, 100000)  # Allow higher range for raw sensor readings
    }
    validate_value_ranges({'aqi': aqi_data}, {'aqi.' + k: v for k, v in range_checks.items()})

    # Validate AQI categories
    valid_categories = ["Good", "Moderate", "Unhealthy for Sensitive Groups",
                       "Unhealthy", "Very Unhealthy", "Hazardous", "Beyond AQI"]
    assert aqi_data['category'] in valid_categories, f"Invalid AQI category: {aqi_data['category']}"

    # Validate color format (hex color)
    assert re.match(r'^#[0-9A-Fa-f]{6}$', aqi_data['color']), f"Invalid color format: {aqi_data['color']}"

def validate_pm_measurements(pm_data):
    """Validate PM measurements structure"""
    required_keys = ['pm1_0', 'pm2_5', 'pm10', 'unit', 'note']
    validate_response_structure(pm_data, required_keys)

    type_checks = {
        'pm1_0': (int, float),
        'pm2_5': (int, float),
        'pm10': (int, float),
        'unit': str,
        'note': str
    }
    validate_data_types({'pm': pm_data}, {'pm.' + k: v for k, v in type_checks.items()})

    range_checks = {
        'pm1_0': (0, 100000),  # Allow higher ranges for raw sensor readings
        'pm2_5': (0, 100000),
        'pm10': (0, 100000)
    }
    validate_value_ranges({'pm': pm_data}, {'pm.' + k: v for k, v in range_checks.items()})

def validate_particle_counts(particle_data):
    """Validate particle count data"""
    required_keys = ['0_3um', '0_5um', '1_0um', '2_5um', '5_0um', '10_0um', 'unit']
    validate_response_structure(particle_data, required_keys)

    type_checks = {
        '0_3um': int, '0_5um': int, '1_0um': int, '2_5um': int, '5_0um': int, '10_0um': int,
        'unit': str
    }
    validate_data_types({'particles': particle_data}, {'particles.' + k: v for k, v in type_checks.items()})

    # Particle counts should be non-negative
    for key in ['0_3um', '0_5um', '1_0um', '2_5um', '5_0um', '10_0um']:
        assert particle_data[key] >= 0, f"Particle count {key} should be non-negative"

def validate_warmup_data(warmup_data):
    """Validate warmup status data"""
    required_keys = ['warmed_up', 'warmup_time', 'message']
    validate_response_structure(warmup_data, required_keys)

    type_checks = {
        'warmed_up': bool,
        'warmup_time': int,
        'message': str
    }
    validate_data_types({'warmup': warmup_data}, {'warmup.' + k: v for k, v in type_checks.items()})

    if warmup_data['warmed_up']:
        assert 'time_since_warmup' in warmup_data
        assert isinstance(warmup_data['time_since_warmup'], (int, float))
        assert warmup_data['time_since_warmup'] >= 0
    else:
        required_warming_keys = ['elapsed', 'remaining']
        for key in required_warming_keys:
            assert key in warmup_data, f"Missing key when not warmed up: {key}"
            assert isinstance(warmup_data[key], (int, float))

def validate_health_data(health_data):
    """Validate health status data"""
    required_keys = ['status', 'checksum_valid', 'data_integrity', 'sensor_responding',
                    'reading_stability', 'total_errors', 'accuracy']
    validate_response_structure(health_data, required_keys)

    type_checks = {
        'status': str,
        'checksum_valid': bool,
        'data_integrity': str,
        'sensor_responding': bool,
        'reading_stability': str,
        'total_errors': int,
        'accuracy': str
    }
    validate_data_types({'health': health_data}, {'health.' + k: v for k, v in type_checks.items()})

    assert health_data['total_errors'] >= 0, "Total errors should be non-negative"

def validate_hardware_data(hardware_data):
    """Validate hardware information"""
    required_keys = ['sensor', 'system']
    validate_response_structure(hardware_data, required_keys)

    sensor_keys = ['model', 'version', 'i2c_address', 'mtbf', 'warmup_required']
    validate_response_structure(hardware_data['sensor'], sensor_keys)

    system_keys = ['hostname', 'os', 'release', 'architecture', 'python_version']
    validate_response_structure(hardware_data['system'], system_keys)


@pytest.fixture
def client():
    """Create test client"""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client





class TestAPIEndpoints:
    """Test all API endpoints with real sensor hardware (requires connected PM2.5 sensor)"""



    def test_index_endpoint(self, client):
        """Test the index endpoint returns API documentation"""
        response = client.get('/')
        assert response.status_code == 200
        data = json.loads(response.data)

        # Validate basic API info
        assert data["name"] == "DFRobot PM2.5 Air Quality API"
        assert data["version"] == "1.0"
        assert data["location"] == "Sundar Nagar, HP"
        assert "endpoints" in data

        # Validate endpoints are listed
        required_endpoints = ["/", "/api/sensor/data", "/api/sensor/aqi", "/api/sensor/warmup"]
        for endpoint in required_endpoints:
            assert endpoint in data["endpoints"], f"Missing endpoint: {endpoint}"

        # Validate warmup status structure
        assert "warmup_status" in data
        validate_warmup_data(data["warmup_status"])

    def test_warmup_endpoint(self, client):
        """Test warmup endpoint returns valid warmup status"""
        response = client.get('/api/sensor/warmup')
        assert response.status_code == 200
        data = json.loads(response.data)

        assert data["status"] == "success"
        assert "warmup" in data
        validate_warmup_data(data["warmup"])

    def test_data_endpoint(self, client):
        """Test data endpoint response structure"""
        response = client.get('/api/sensor/data')
        assert response.status_code in [200, 500]

        data = json.loads(response.data)

        # Validate basic response structure
        assert "status" in data
        assert data["status"] in ["success", "error"]
        assert "timestamp" in data

        validate_timestamp_format(data["timestamp"])

        if data["status"] == "success":
            # Validate successful response structure
            assert "warmup" in data
            assert "hardware" in data
            assert "health" in data
            assert "measurements" in data

            # Validate each data section
            validate_warmup_data(data["warmup"])
            validate_hardware_data(data["hardware"])
            validate_health_data(data["health"])

            # Validate measurements
            assert "standard_pm" in data["measurements"]
            assert "atmospheric_pm" in data["measurements"]
            assert "particle_count" in data["measurements"]

            validate_pm_measurements(data["measurements"]["standard_pm"])
            validate_pm_measurements(data["measurements"]["atmospheric_pm"])
            validate_particle_counts(data["measurements"]["particle_count"])

            # Validate AQI if present (may not be present if sensor failed)
            if "aqi" in data and data["aqi"] is not None:
                validate_aqi_data(data["aqi"])
        else:
            # Validate error response structure
            assert "error" in data
            assert isinstance(data["error"], str)

    def test_aqi_endpoint(self, client):
        """Test AQI endpoint with real sensor data"""
        response = client.get('/api/sensor/aqi')
        assert response.status_code in [200, 500]  # May fail if sensor not ready

        data = json.loads(response.data)

        if response.status_code == 200:
            assert data["status"] == "success"
            assert "timestamp" in data
            assert "warmup" in data
            assert "aqi" in data

            validate_timestamp_format(data["timestamp"])
            validate_warmup_data(data["warmup"])

            # AQI may be None if sensor failed
            if data["aqi"] is not None:
                validate_aqi_data(data["aqi"])

            # Check for warmup warning
            if not data["warmup"]["warmed_up"]:
                assert "warning" in data
                assert "warming up" in data["warning"]
            else:
                # May or may not have warning depending on sensor state
                pass
        else:
            # Error response
            assert data["status"] == "error"
            assert "error" in data

    def test_pm_endpoint(self, client):
        """Test PM measurements endpoint with real sensor data"""
        response = client.get('/api/sensor/pm')
        assert response.status_code in [200, 500]

        data = json.loads(response.data)

        if response.status_code == 200:
            assert data["status"] == "success"
            assert "timestamp" in data
            assert "warmup" in data
            assert "measurements" in data

            validate_timestamp_format(data["timestamp"])
            validate_warmup_data(data["warmup"])

            # Validate PM measurements
            assert "standard_pm" in data["measurements"]
            assert "atmospheric_pm" in data["measurements"]

            validate_pm_measurements(data["measurements"]["standard_pm"])
            validate_pm_measurements(data["measurements"]["atmospheric_pm"])

            # Check for warmup warning
            if not data["warmup"]["warmed_up"]:
                assert "warning" in data
        else:
            assert data["status"] == "error"
            assert "error" in data

    def test_health_endpoint(self, client):
        """Test health endpoint with real sensor data"""
        response = client.get('/api/sensor/health')
        assert response.status_code in [200, 500]

        data = json.loads(response.data)

        if response.status_code == 200:
            assert data["status"] == "success"
            assert "timestamp" in data
            assert "warmup" in data
            assert "health" in data

            validate_timestamp_format(data["timestamp"])
            validate_warmup_data(data["warmup"])
            validate_health_data(data["health"])
        else:
            assert data["status"] == "error"
            assert "health" in data  # May still have partial health info
            assert "error" in data

    def test_hardware_endpoint(self, client):
        """Test hardware endpoint"""
        response = client.get('/api/sensor/hardware')
        assert response.status_code == 200
        data = json.loads(response.data)

        assert data["status"] == "success"
        assert "hardware" in data
        validate_hardware_data(data["hardware"])

    def test_particles_endpoint(self, client):
        """Test particle count endpoint with real sensor data"""
        response = client.get('/api/sensor/particles')
        assert response.status_code in [200, 500]

        data = json.loads(response.data)

        if response.status_code == 200:
            assert data["status"] == "success"
            assert "timestamp" in data
            assert "warmup" in data
            assert "particle_count" in data

            validate_timestamp_format(data["timestamp"])
            validate_warmup_data(data["warmup"])
            validate_particle_counts(data["particle_count"])
        else:
            assert data["status"] == "error"
            assert "error" in data


class TestErrorHandling:
    """Test error handling scenarios"""

    def test_invalid_endpoint(self, client):
        """Test 404 error for invalid endpoint"""
        response = client.get('/api/sensor/invalid')
        assert response.status_code == 404
        data = json.loads(response.data)

        assert data["status"] == "error"
        assert data["error"] == "Endpoint not found"
        assert isinstance(data["error"], str)

    def test_error_response_format(self, client):
        """Test that error responses have consistent format"""
        # Test with an endpoint that might fail
        response = client.get('/api/sensor/aqi')

        data = json.loads(response.data)

        # Should always have status field
        assert "status" in data
        assert data["status"] in ["success", "error"]

        # If error, should have error field
        if data["status"] == "error":
            assert "error" in data
            assert isinstance(data["error"], str)


class TestAQICalculation:
    """Unit tests for AQI calculation logic (no hardware required)"""

    def test_aqi_calculation_good_air_quality(self):
        """Test AQI calculation for good air quality"""
        sensor = PM25Sensor()
        result = sensor.calculate_aqi_from_pm25(10.0)
        
        assert result["value"] == 42  # Interpolated AQI
        assert result["category"] == "Good"
        assert result["color"] == "#00E400"
        assert result["pm25_used"] == 10.0

    def test_aqi_calculation_moderate(self):
        """Test AQI calculation for moderate air quality"""
        sensor = PM25Sensor()
        result = sensor.calculate_aqi_from_pm25(25.0)
        
        assert result["value"] == 78  # Interpolated AQI
        assert result["category"] == "Moderate"
        assert result["color"] == "#FFFF00"

    def test_aqi_calculation_unhealthy(self):
        """Test AQI calculation for unhealthy air quality"""
        sensor = PM25Sensor()
        result = sensor.calculate_aqi_from_pm25(100.0)
        
        assert result["value"] == 174  # Interpolated AQI
        assert result["category"] == "Unhealthy"
        assert result["color"] == "#FF0000"

    def test_aqi_calculation_beyond_aqi(self):
        """Test AQI calculation for values beyond AQI scale"""
        sensor = PM25Sensor()
        result = sensor.calculate_aqi_from_pm25(600.0)
        
        assert result["value"] == 500  # Capped at 500
        assert result["category"] == "Beyond AQI"
        assert result["color"] == "#7E0023"

    def test_checksum_calculation(self):
        """Test checksum calculation"""
        sensor = PM25Sensor()
        test_data = [i for i in range(32)]  # Simple test data
        checksum = sensor.calculate_checksum(test_data)
        
        expected_checksum = sum(test_data[0:30]) & 0xFF
        assert checksum == expected_checksum


if __name__ == '__main__':
    pytest.main([__file__, '-v'])