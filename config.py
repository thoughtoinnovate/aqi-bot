import json
import os
import requests

SETTINGS_FILE = 'settings.json'

def load_settings():
    defaults = {
        "update_interval": 5000, 
        "power_save": True, 
        "manual_location": "",
        "reading_mode": "realtime",  # realtime, less_aggressive, lazy
        "custom_interval": 5000  # Custom interval in milliseconds
    }
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, 'r') as f:
            loaded = json.load(f)
        defaults.update(loaded)
    return defaults

def save_settings(settings):
    with open(SETTINGS_FILE, 'w') as f:
        json.dump(settings, f)

def get_location():
    try:
        response = requests.get('https://ipinfo.io/json', timeout=5)
        data = response.json()
        return f"{data.get('city', 'Unknown')}, {data.get('region', 'Unknown')}, {data.get('country', 'Unknown')}"
    except Exception as e:
        return "Location detection failed"