from flask import Blueprint, jsonify, request, make_response
import json
import sqlite3
from sensor import SEN0460, calculate_aqi
from database import insert_reading, get_data, export_data
from config import load_settings, save_settings, get_location

api = Blueprint('api', __name__)

sensor = SEN0460()

@api.route('/data')
def data():
    try:
        settings = load_settings()
        sensor.awake()
        import time
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
    except Exception as e:
        return jsonify({'error': f'Sensor error: {str(e)}'})

@api.route('/settings', methods=['GET', 'POST'])
def settings_api():
    if request.method == 'POST':
        data = request.get_json()
        save_settings(data)
        return jsonify({'status': 'saved'})
    else:
        return jsonify(load_settings())

@api.route('/graph_data')
def graph_data():
    param = request.args.get('param', 'aqi')
    range_type = request.args.get('range', 'day')
    location = request.args.get('location', None)
    data = get_data(param, range_type, location)
    return jsonify(data)

@api.route('/locations')
def get_locations():
    conn = sqlite3.connect('air_quality.db')
    c = conn.cursor()
    c.execute('SELECT DISTINCT location FROM readings')
    locations = [row[0] for row in c.fetchall()]
    conn.close()
    return jsonify(locations)

@api.route('/export')
def export():
    format_type = request.args.get('format', 'json')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    location = request.args.get('location')
    data = export_data(start_date, end_date, location)
    if format_type == 'csv':
        from io import StringIO
        import csv
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