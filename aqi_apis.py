from flask import Flask, jsonify, request
from flask_cors import CORS
import smbus
import time
import platform
from datetime import datetime
import threading

app = Flask(__name__)
CORS(app)

I2C_ADDRESS = 0x19
WARMUP_TIME = 30  # seconds - sensor needs 30s to stabilize after power-on

class PM25Sensor:
    def __init__(self, address=0x19, bus_number=1):
        self.address = address
        self.warmup_start = time.time()
        self.is_warmed_up = False
        self.warmup_complete_time = None
        try:
            self.bus = smbus.SMBus(bus_number)
            self.error_count = 0
            self.last_successful_read = None
            # Start warmup timer in background
            threading.Thread(target=self._warmup_timer, daemon=True).start()
        except Exception as e:
            print(f"Failed to initialize I2C bus: {e}")
            self.bus = None
    
    def _warmup_timer(self):
        """Background thread to track warmup completion"""
        time.sleep(WARMUP_TIME)
        self.is_warmed_up = True
        self.warmup_complete_time = time.time()
        print(f"Sensor warmup complete after {WARMUP_TIME} seconds")
    
    def get_warmup_status(self):
        """Get current warmup status"""
        if self.is_warmed_up:
            return {
                "warmed_up": True,
                "warmup_time": WARMUP_TIME,
                "time_since_warmup": round(time.time() - self.warmup_complete_time, 1),
                "message": "Sensor ready for accurate readings"
            }
        else:
            elapsed = time.time() - self.warmup_start
            remaining = max(0, WARMUP_TIME - elapsed)
            return {
                "warmed_up": False,
                "warmup_time": WARMUP_TIME,
                "elapsed": round(elapsed, 1),
                "remaining": round(remaining, 1),
                "message": f"Sensor warming up... {round(remaining)}s remaining"
            }
    
    def calculate_aqi_from_pm25(self, pm25):
        """Calculate AQI from PM2.5 using US EPA breakpoints"""
        breakpoints = [
            (0.0, 12.0, 0, 50, "Good", "#00E400"),
            (12.1, 35.4, 51, 100, "Moderate", "#FFFF00"),
            (35.5, 55.4, 101, 150, "Unhealthy for Sensitive Groups", "#FF7E00"),
            (55.5, 150.4, 151, 200, "Unhealthy", "#FF0000"),
            (150.5, 250.4, 201, 300, "Very Unhealthy", "#8F3F97"),
            (250.5, 350.4, 301, 400, "Hazardous", "#7E0023"),
            (350.5, 500.4, 401, 500, "Hazardous", "#7E0023")
        ]
        
        for bp_lo, bp_hi, aqi_lo, aqi_hi, category, color in breakpoints:
            if bp_lo <= pm25 <= bp_hi:
                aqi = ((aqi_hi - aqi_lo) / (bp_hi - bp_lo)) * (pm25 - bp_lo) + aqi_lo
                return {
                    "value": round(aqi),
                    "category": category,
                    "color": color,
                    "pm25_used": pm25
                }
        
        if pm25 > 500.4:
            return {
                "value": 500,
                "category": "Beyond AQI",
                "color": "#7E0023",
                "pm25_used": pm25
            }
        return None
    
    def calculate_checksum(self, data):
        """Validate data integrity"""
        return sum(data[0:30]) & 0xFF
    
    def get_sensor_version(self):
        """Read sensor firmware version"""
        try:
            return self.bus.read_byte_data(self.address, 0x1F)
        except:
            return "unknown"
    
    def get_hardware_info(self):
        """Collect hardware and system information"""
        return {
            "sensor": {
                "model": "DFRobot SEN0460",
                "version": self.get_sensor_version(),
                "i2c_address": hex(self.address),
                "mtbf": ">=5 years",
                "warmup_required": f"{WARMUP_TIME} seconds"
            },
            "system": {
                "hostname": platform.node(),
                "os": platform.system(),
                "release": platform.release(),
                "architecture": platform.machine(),
                "python_version": platform.python_version()
            }
        }
    
    def read_sensor(self):
        """Read all sensor data with error handling"""
        if self.bus is None:
            return {
                "status": "error",
                "error": "I2C bus not initialized"
            }
        
        # Check warmup status
        warmup_status = self.get_warmup_status()
        
        try:
            data = self.bus.read_i2c_block_data(self.address, 0x00, 32)
            
            # Validate checksum
            calculated_checksum = self.calculate_checksum(data)
            received_checksum = (data[30] << 8) | data[31]
            checksum_valid = (calculated_checksum == (received_checksum & 0xFF))
            
            # Extract measurements
            pm1_std = (data[4] << 8) | data[5]
            pm25_std = (data[6] << 8) | data[7]
            pm10_std = (data[8] << 8) | data[9]
            
            pm1_atm = (data[10] << 8) | data[11]
            pm25_atm = (data[12] << 8) | data[13]
            pm10_atm = (data[14] << 8) | data[15]
            
            # Calculate AQI from atmospheric PM2.5
            aqi_data = self.calculate_aqi_from_pm25(pm25_atm)
            
            # Update success tracking
            if checksum_valid:
                self.last_successful_read = time.time()
                self.error_count = 0
            else:
                self.error_count += 1
            
            result = {
                "status": "success",
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "warmup": warmup_status,
                "hardware": self.get_hardware_info(),
                "health": {
                    "status": "healthy" if checksum_valid else "checksum_error",
                    "checksum_valid": checksum_valid,
                    "data_integrity": "ok" if checksum_valid else "corrupted",
                    "sensor_responding": True,
                    "reading_stability": "stable" if pm25_atm < 1000 else "overrange",
                    "total_errors": self.error_count,
                    "last_successful_read": datetime.fromtimestamp(self.last_successful_read).strftime("%Y-%m-%d %H:%M:%S") if self.last_successful_read else None,
                    "accuracy": "accurate" if self.is_warmed_up else "warming_up"
                },
                "aqi": aqi_data,
                "measurements": {
                    "standard_pm": {
                        "pm1_0": pm1_std,
                        "pm2_5": pm25_std,
                        "pm10": pm10_std,
                        "unit": "ug/m3",
                        "note": "Lab-calibrated values"
                    },
                    "atmospheric_pm": {
                        "pm1_0": pm1_atm,
                        "pm2_5": pm25_atm,
                        "pm10": pm10_atm,
                        "unit": "ug/m3",
                        "note": "Real-world conditions (recommended)"
                    },
                    "particle_count": {
                        "0_3um": (data[16] << 8) | data[17],
                        "0_5um": (data[18] << 8) | data[19],
                        "1_0um": (data[20] << 8) | data[21],
                        "2_5um": (data[22] << 8) | data[23],
                        "5_0um": (data[24] << 8) | data[25],
                        "10_0um": (data[26] << 8) | data[27],
                        "unit": "particles per 0.1L"
                    }
                }
            }
            
            # Add warning if not warmed up
            if not self.is_warmed_up:
                result["warning"] = "Sensor still warming up - readings may be inaccurate"
            
            return result
            
        except Exception as e:
            self.error_count += 1
            return {
                "status": "error",
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "warmup": warmup_status,
                "health": {
                    "status": "error",
                    "sensor_responding": False,
                    "total_errors": self.error_count,
                    "error_message": str(e)
                },
                "error": str(e)
            }

# Initialize sensor globally
sensor = PM25Sensor(address=I2C_ADDRESS)

# API Routes

@app.route('/', methods=['GET'])
def index():
    """API documentation"""
    warmup = sensor.get_warmup_status()
    return jsonify({
        "name": "DFRobot PM2.5 Air Quality API",
        "version": "1.0",
        "location": "Sundar Nagar, HP",
        "warmup_status": warmup,
        "endpoints": {
            "/": "API documentation",
            "/api/sensor/data": "Get complete sensor data (all measurements + AQI + health)",
            "/api/sensor/aqi": "Get AQI information only",
            "/api/sensor/pm": "Get PM measurements only",
            "/api/sensor/health": "Get sensor health status",
            "/api/sensor/hardware": "Get hardware information",
            "/api/sensor/particles": "Get particle count data",
            "/api/sensor/warmup": "Get warmup status"
        }
    })

@app.route('/api/sensor/warmup', methods=['GET'])
def get_warmup_status():
    """Get sensor warmup status"""
    warmup = sensor.get_warmup_status()
    return jsonify({
        "status": "success",
        "warmup": warmup
    })

@app.route('/api/sensor/data', methods=['GET'])
def get_sensor_data():
    """Get complete sensor data"""
    data = sensor.read_sensor()
    return jsonify(data)

@app.route('/api/sensor/aqi', methods=['GET'])
def get_aqi():
    """Get AQI information only"""
    data = sensor.read_sensor()
    if data["status"] == "success":
        response = {
            "status": "success",
            "timestamp": data["timestamp"],
            "warmup": data["warmup"],
            "aqi": data["aqi"]
        }
        if not sensor.is_warmed_up:
            response["warning"] = "Sensor still warming up - readings may be inaccurate"
        return jsonify(response)
    return jsonify({
        "status": "error",
        "error": data.get("error", "Unable to read sensor")
    }), 500

@app.route('/api/sensor/pm', methods=['GET'])
def get_pm_measurements():
    """Get PM measurements only"""
    data = sensor.read_sensor()
    if data["status"] == "success":
        response = {
            "status": "success",
            "timestamp": data["timestamp"],
            "warmup": data["warmup"],
            "measurements": {
                "standard_pm": data["measurements"]["standard_pm"],
                "atmospheric_pm": data["measurements"]["atmospheric_pm"]
            }
        }
        if not sensor.is_warmed_up:
            response["warning"] = "Sensor still warming up - readings may be inaccurate"
        return jsonify(response)
    return jsonify({
        "status": "error",
        "error": data.get("error", "Unable to read sensor")
    }), 500

@app.route('/api/sensor/health', methods=['GET'])
def get_health():
    """Get sensor health status"""
    data = sensor.read_sensor()
    if data["status"] == "success":
        return jsonify({
            "status": "success",
            "timestamp": data["timestamp"],
            "warmup": data["warmup"],
            "health": data["health"]
        })
    return jsonify({
        "status": "error",
        "health": data.get("health", {}),
        "error": data.get("error", "Unable to read sensor")
    }), 500

@app.route('/api/sensor/hardware', methods=['GET'])
def get_hardware():
    """Get hardware information"""
    hardware_info = sensor.get_hardware_info()
    return jsonify({
        "status": "success",
        "hardware": hardware_info
    })

@app.route('/api/sensor/particles', methods=['GET'])
def get_particle_count():
    """Get particle count data"""
    data = sensor.read_sensor()
    if data["status"] == "success":
        return jsonify({
            "status": "success",
            "timestamp": data["timestamp"],
            "warmup": data["warmup"],
            "particle_count": data["measurements"]["particle_count"]
        })
    return jsonify({
        "status": "error",
        "error": data.get("error", "Unable to read sensor")
    }), 500

@app.errorhandler(404)
def not_found(error):
    return jsonify({
        "status": "error",
        "error": "Endpoint not found"
    }), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        "status": "error",
        "error": "Internal server error"
    }), 500

if __name__ == '__main__':
    print("=" * 70)
    print("DFRobot PM2.5 Air Quality API Server")
    print("Location: Sundar Nagar, HP")
    print("=" * 70)
    print(f"\nSensor warming up for {WARMUP_TIME} seconds...")
    print("Readings during warmup may be inaccurate.\n")
    print("\nAPI Endpoints:")
    print("  http://localhost:5000/")
    print("  http://localhost:5000/api/sensor/data")
    print("  http://localhost:5000/api/sensor/aqi")
    print("  http://localhost:5000/api/sensor/warmup")
    print("\nStarting server...\n")
    app.run(host='0.0.0.0', port=5000, debug=True)
