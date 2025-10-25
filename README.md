# Air Quality Monitor

This project uses a DFRobot SEN0460 PM2.5 sensor connected to a Raspberry Pi to display real-time air quality index (AQI) via a web interface accessible on the local network.

## Hardware Setup

- Connect the SEN0460 sensor to the Raspberry Pi's I2C pins:
  - VCC to 3.3V or 5V
  - GND to GND
  - SDA to SDA (GPIO 2)
  - SCL to SCL (GPIO 3)

- Enable I2C on the Raspberry Pi:
  ```
  sudo raspi-config
  # Navigate to Interfacing Options > I2C > Enable
  ```

- Check if the sensor is detected:
  ```
  sudo i2cdetect -y 1
  ```
  Look for address 0x19.

## Software Setup

1. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

2. Run the application:
   ```
   python app.py
   ```

3. Access the web interface at `http://<raspberry_pi_ip>:5000`

The page will update every 5 seconds with the latest PM2.5 reading and calculated AQI.

## Files

- `sensor.py`: Sensor interface and AQI calculation
- `app.py`: Flask web server
- `templates/index.html`: Web page template
- `requirements.txt`: Python dependencies