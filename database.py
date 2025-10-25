import sqlite3
import json
from datetime import datetime, timedelta

DB_FILE = 'air_quality.db'

def init_db():
    with sqlite3.connect(DB_FILE) as conn:
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS readings (
            id INTEGER PRIMARY KEY,
            timestamp TEXT,
            location TEXT,
            pm1 REAL,
            pm25 REAL,
            pm10 REAL,
            aqi INTEGER,
            particles TEXT
        )''')
        conn.commit()

def insert_reading(location, pm1, pm25, pm10, aqi, particles):
    with sqlite3.connect(DB_FILE) as conn:
        c = conn.cursor()
        timestamp = datetime.now().isoformat()
        particles_json = json.dumps(particles)
        c.execute('INSERT INTO readings (timestamp, location, pm1, pm25, pm10, aqi, particles) VALUES (?, ?, ?, ?, ?, ?, ?)',
                   (timestamp, location, pm1, pm25, pm10, aqi, particles_json))
        conn.commit()

def get_data(param, range_type, location=None):
    with sqlite3.connect(DB_FILE) as conn:
        c = conn.cursor()
        now = datetime.now()
        if range_type == 'hour':
            start = now - timedelta(hours=24)
        elif range_type == 'day':
            start = now - timedelta(days=7)
        elif range_type == 'week':
            start = now - timedelta(weeks=4)
        elif range_type == 'month':
            start = now - timedelta(days=365)
        else:  # year or all
            start = datetime.min

        query = f'SELECT timestamp, {param}, location FROM readings WHERE timestamp >= ?'
        params = [start.isoformat()]
        if location:
            query += ' AND location = ?'
            params.append(location)

        c.execute(query, params)
        rows = c.fetchall()

    # Group by time unit
    data = {}
    for ts, value, loc in rows:
        dt = datetime.fromisoformat(ts)
        if range_type == 'hour':
            key = dt.strftime('%H:00')
        elif range_type == 'day':
            key = dt.strftime('%Y-%m-%d')
        elif range_type == 'week':
            key = f'Week {dt.isocalendar()[1]}'
        elif range_type == 'month':
            key = dt.strftime('%Y-%m')
        else:
            key = dt.strftime('%Y')

        if key not in data:
            data[key] = []
        data[key].append((value, loc))

    # Average values
    averaged = {}
    for time_key, value_loc_list in data.items():
        total = sum(v for v, l in value_loc_list)
        avg_value = total / len(value_loc_list)
        # Use the location of the first reading for that time (assuming same location per time)
        loc = value_loc_list[0][1] if value_loc_list else 'Unknown'
        averaged[time_key] = {'value': avg_value, 'location': loc}
    return [{'time': k, 'value': v['value'], 'location': v['location']} for k, v in sorted(averaged.items())]

def export_data(start_date=None, end_date=None, location=None):
    with sqlite3.connect(DB_FILE) as conn:
        c = conn.cursor()
        query = 'SELECT timestamp, location, pm1, pm25, pm10, aqi, particles FROM readings WHERE 1=1'
        params = []
        if start_date:
            query += ' AND timestamp >= ?'
            params.append(start_date)
        if end_date:
            query += ' AND timestamp <= ?'
            params.append(end_date)
        if location:
            query += ' AND location = ?'
            params.append(location)
        query += ' ORDER BY timestamp'
        c.execute(query, params)
        rows = c.fetchall()
    data = []
    for row in rows:
        ts, loc, pm1, pm25, pm10, aqi, particles_json = row
        particles = json.loads(particles_json) if particles_json else {}
        data.append({
            'timestamp': ts,
            'location': loc,
            'pm1': pm1,
            'pm25': pm25,
            'pm10': pm10,
            'aqi': aqi,
            'particles': particles
        })
    return data

def cleanup_old_data(days=365):
    with sqlite3.connect(DB_FILE) as conn:
        c = conn.cursor()
        cutoff = (datetime.now() - timedelta(days=days)).isoformat()
        c.execute('DELETE FROM readings WHERE timestamp < ?', (cutoff,))
        conn.commit()