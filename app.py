from flask import Flask, render_template
import socket
import platform
import logging
from database import init_db
from config import load_settings, get_location
from api import api

# Configure logging to file
logging.basicConfig(filename='app.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Configure werkzeug logger to also log to file
werkzeug_logger = logging.getLogger('werkzeug')
werkzeug_logger.setLevel(logging.INFO)
handler = logging.FileHandler('app.log')
handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
werkzeug_logger.addHandler(handler)

app = Flask(__name__)
app.register_blueprint(api, url_prefix='/api')
init_db()

@app.route('/')
def index():
    hostname = socket.gethostname()
    ip = socket.gethostbyname(hostname)
    settings = load_settings()
    location = settings.get('manual_location', '') or get_location()
    device_info = {
        'hostname': hostname,
        'ip': ip,
        'platform': platform.platform(),
        'sensor_model': 'DFRobot SEN0460 PM2.5 Laser Sensor',
        'location': location
    }
    return render_template('index.html', device_info=device_info, settings=settings)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)