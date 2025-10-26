from flask import Blueprint, jsonify, request, make_response, current_app
import json
import sqlite3
import time
from sensor import SEN0460, calculate_aqi
from database import insert_reading, get_data, export_data, cleanup_old_data
from config import load_settings, save_settings, get_location

api = Blueprint('api', __name__)

sensor = SEN0460()
sensor_initialized = False
last_reading_time = 0
reading_mode = "realtime"

@api.route('/data')
def data():
    global sensor_initialized, last_reading_time, reading_mode
    try:
        settings = load_settings()
        current_mode = settings.get('reading_mode', 'realtime')
        current_time = int(time.time() * 1000)  # Current time in milliseconds
        
        # For lazy mode, check if we should read (manual trigger only)
        if current_mode == 'lazy':
            # Only read if it's been requested (via /api/read_now endpoint)
            if 'read_now' not in request.args:
                return jsonify({
                    'mode': 'lazy',
                    'message': 'Lazy mode - use Read Now button or /api/read_now',
                    'last_reading': last_reading_time
                })
        
        # Check if enough time has passed for the current mode
        interval = settings.get('custom_interval', 5000)
        if current_time - last_reading_time < interval and current_mode != 'lazy':
            return jsonify({
                'mode': current_mode,
                'message': f'Waiting for next reading in {((interval - (current_time - last_reading_time)) // 1000) + 1} seconds',
                'last_reading': last_reading_time
            })
        
        # Initialize sensor if not already done
        if not sensor_initialized:
            if not sensor.init_sensor():
                return jsonify({'error': 'Failed to initialize sensor'})
            sensor_initialized = True
        
        # Wake sensor and wait for stable reading
        sensor.awake()
        sleep_time = 2 if current_mode == 'realtime' else 3
        time.sleep(sleep_time)
        
        concentrations = sensor.gain_all_concentrations()
        counts = sensor.gain_particle_counts()
        version = sensor.gain_version()
        
        # Put sensor to sleep based on mode
        if settings['power_save'] or current_mode != 'realtime':
            sensor.set_lowpower()
            
        if concentrations['pm25'] is not None:
            aqi = calculate_aqi(concentrations['pm25'])
            location = settings.get('manual_location', '') or get_location()
            insert_reading(location, concentrations['pm1'], concentrations['pm25'], concentrations['pm10'], aqi, counts)
            last_reading_time = current_time
            current_app.logger.info(f"Inserted reading: PM2.5={concentrations['pm25']}, AQI={aqi}, Mode={current_mode}")
            return jsonify({
                'pm1': concentrations['pm1'],
                'pm25': concentrations['pm25'],
                'pm10': concentrations['pm10'],
                'particles': counts,
                'version': version,
                'aqi': aqi,
                'mode': current_mode,
                'next_reading': current_time + interval
            })
        else:
            return jsonify({'error': 'Failed to read sensor - invalid readings'})
    except Exception as e:
        current_app.logger.error(f"Sensor error: {str(e)}")
        return jsonify({'error': f'Sensor error: {str(e)}'})

@api.route('/read_now')
def read_now():
    """Force a reading regardless of mode (for lazy mode)"""
    global last_reading_time, sensor_initialized
    try:
        settings = load_settings()
        
        # Initialize sensor if not already done
        if not sensor_initialized:
            if not sensor.init_sensor():
                return jsonify({'error': 'Failed to initialize sensor'})
            sensor_initialized = True
        
        # Wake sensor and wait for stable reading
        sensor.awake()
        import time
        time.sleep(3)
        
        concentrations = sensor.gain_all_concentrations()
        counts = sensor.gain_particle_counts()
        version = sensor.gain_version()
        
        # Put sensor to sleep after reading
        sensor.set_lowpower()
            
        if concentrations['pm25'] is not None:
            aqi = calculate_aqi(concentrations['pm25'])
            location = settings.get('manual_location', '') or get_location()
            insert_reading(location, concentrations['pm1'], concentrations['pm25'], concentrations['pm10'], aqi, counts)
            last_reading_time = int(time.time() * 1000)
            current_app.logger.info(f"Manual reading: PM2.5={concentrations['pm25']}, AQI={aqi}")
            return jsonify({
                'pm1': concentrations['pm1'],
                'pm25': concentrations['pm25'],
                'pm10': concentrations['pm10'],
                'particles': counts,
                'version': version,
                'aqi': aqi,
                'manual': True
            })
        else:
            return jsonify({'error': 'Failed to read sensor - invalid readings'})
    except Exception as e:
        current_app.logger.error(f"Manual reading error: {str(e)}")
        return jsonify({'error': f'Sensor error: {str(e)}'})

@api.route('/settings', methods=['GET', 'POST'])
def settings_api():
    if request.method == 'POST':
        data = request.get_json()
        
        # Validate and set custom interval based on mode
        mode = data.get('reading_mode', 'realtime')
        if mode == 'realtime':
            # Realtime mode: 5s, 10s, 20s, 40s, 60s
            interval_map = {'5': 5000, '10': 10000, '20': 20000, '40': 40000, '60': 60000}
            data['custom_interval'] = interval_map.get(data.get('interval', '5'), 5000)
        elif mode == 'less_aggressive':
            # Less aggressive mode: 5min, 10min, 30min, 1h, 2h, 4h, 8h, 24h
            interval_map = {
                '5': 300000,      # 5 minutes
                '10': 600000,     # 10 minutes  
                '30': 1800000,    # 30 minutes
                '60': 3600000,    # 1 hour
                '120': 7200000,   # 2 hours
                '240': 14400000,  # 4 hours
                '480': 28800000,  # 8 hours
                '1440': 86400000  # 24 hours
            }
            data['custom_interval'] = interval_map.get(data.get('interval', '5'), 300000)
        elif mode == 'lazy':
            # Lazy mode: no automatic readings
            data['custom_interval'] = 0
        
        save_settings(data)
        return jsonify({'status': 'saved', 'settings': data})
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
    with sqlite3.connect('air_quality.db') as conn:
        c = conn.cursor()
        c.execute('SELECT DISTINCT location FROM readings')
        locations = [row[0] for row in c.fetchall()]
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

@api.route('/readings')
def readings():
    limit = int(request.args.get('limit', 50))
    offset = int(request.args.get('offset', 0))
    location = request.args.get('location')
    with sqlite3.connect('air_quality.db') as conn:
        c = conn.cursor()
        query = 'SELECT id, timestamp, location, pm1, pm25, pm10, aqi FROM readings WHERE 1=1'
        params = []
        if location:
            query += ' AND location = ?'
            params.append(location)
        query += ' ORDER BY timestamp DESC LIMIT ? OFFSET ?'
        params.extend([limit, offset])
        c.execute(query, params)
        rows = c.fetchall()
    data = []
    for row in rows:
        id_, ts, loc, pm1, pm25, pm10, aqi = row
        data.append({
            'id': id_,
            'timestamp': ts,
            'location': loc,
            'pm1': pm1,
            'pm25': pm25,
            'pm10': pm10,
            'aqi': aqi
        })
    return jsonify(data)

@api.route('/cleanup', methods=['POST'])
def cleanup():
    days = int(request.get_json().get('days', 365))
    cleanup_old_data(days)
    return jsonify({'status': 'cleaned'})

@api.route('/logs')
def logs():
    try:
        with open('app.log', 'r') as f:
            lines = f.readlines()
        parsed_logs = []
        if not lines:
            parsed_logs = [{'timestamp': 'N/A', 'level': 'INFO', 'message': 'No logs available yet'}]
        else:
            for line in lines[-100:]:  # last 100 lines
                line = line.strip()
                if ' - ' in line:
                    parts = line.split(' - ', 2)
                    if len(parts) >= 2:
                        timestamp = parts[0]
                        level = parts[1] if len(parts) > 2 else 'INFO'
                        message = parts[2] if len(parts) > 2 else parts[1]
                        parsed_logs.append({'timestamp': timestamp, 'level': level, 'message': message})
                    else:
                        parsed_logs.append({'timestamp': 'N/A', 'level': 'INFO', 'message': line})
                else:
                    parsed_logs.append({'timestamp': 'N/A', 'level': 'INFO', 'message': line})
        return jsonify(parsed_logs)
    except Exception as e:
        return jsonify({'error': str(e)})