from flask import Flask, render_template, jsonify, request, make_response
import time
import socket
import platform
import json
import os
import requests
import sqlite3
import csv
from io import StringIO
from sensor import SEN0460, calculate_aqi
from database import init_db, insert_reading, get_data, cleanup_old_data, export_data

app = Flask(__name__)
sensor = SEN0460()
init_db()

SETTINGS_FILE = 'settings.json'

def load_settings():
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, 'r') as f:
            return json.load(f)
    return {"update_interval": 5000, "power_save": True}

def save_settings(settings):
    with open(SETTINGS_FILE, 'w') as f:
        json.dump(settings, f)

def get_location():
    try:
        response = requests.get('https://ipinfo.io/json', timeout=5)
        data = response.json()
        return f"{data.get('city', 'Unknown')}, {data.get('region', 'Unknown')}, {data.get('country', 'Unknown')}"
    except:
        return "Location detection failed"

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

@app.route('/api/data')
def data():
    settings = load_settings()
    sensor.awake()
    time.sleep(1)
    concentrations = sensor.gain_all_concentrations()
    counts = sensor.gain_particle_counts()
    version = sensor.gain_version()
    if settings['power_save']:
        sensor.set_lowpower()
    if concentrations['pm25'] is not None:
        aqi = calculate_aqi(concentrations['pm25'])
        location = settings.get('manual_location', '') or get_location()
        insert_reading(location, concentrations['pm1'], concentrations['pm25'], concentrations['pm10'], aqi, counts)
        return jsonify({
            'pm1': concentrations['pm1'],
            'pm25': concentrations['pm25'],
            'pm10': concentrations['pm10'],
            'particles': counts,
            'version': version,
            'aqi': aqi
        })
    else:
        return jsonify({'error': 'Failed to read sensor'})

@app.route('/api/settings', methods=['GET', 'POST'])
def settings_api():
    if request.method == 'POST':
        data = request.get_json()
        save_settings(data)
        return jsonify({'status': 'saved'})
    else:
        return jsonify(load_settings())

@app.route('/api/graph_data')
def graph_data():
    param = request.args.get('param', 'aqi')
    range_type = request.args.get('range', 'day')
    location = request.args.get('location', None)
    data = get_data(param, range_type, location)
    return jsonify(data)

@app.route('/api/locations')
def get_locations():
    conn = sqlite3.connect('air_quality.db')
    c = conn.cursor()
    c.execute('SELECT DISTINCT location FROM readings')
    locations = [row[0] for row in c.fetchall()]
    conn.close()
    return jsonify(locations)

@app.route('/api/export')
def export():
    format_type = request.args.get('format', 'json')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    location = request.args.get('location')
    data = export_data(start_date, end_date, location)
    if format_type == 'csv':
        si = StringIO()
        writer = csv.DictWriter(si, fieldnames=['timestamp', 'location', 'pm1', 'pm25', 'pm10', 'aqi', 'particles'])
        writer.writeheader()
        for row in data:
            row_copy = row.copy()
            row_copy['particles'] = json.dumps(row_copy['particles'])
            writer.writerow(row_copy)
        output = make_response(si.getvalue())
        output.headers["Content-Disposition"] = "attachment; filename=air_quality_data.csv"
        output.headers["Content-type"] = "text/csv"
        return output
    else:  # json
        return jsonify(data)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)