#!/usr/bin/env python3
"""
Real Integration Test for PM2.5 API Server

This script tests all API endpoints with real sensor data.
Make sure the server is running before executing this test.
"""

import requests
import time
import json

BASE_URL = 'http://localhost:5000'

def test_endpoint(name, url):
    """Test a single endpoint"""
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 'success':
                print(f'✅ {name}: OK')
                return True
            else:
                print(f'❌ {name}: Status not success')
                return False
        else:
            print(f'❌ {name}: HTTP {response.status_code}')
            return False
    except Exception as e:
        print(f'❌ {name}: Error - {e}')
        return False

def main():
    """Run all integration tests"""
    print('Testing PM2.5 API with real sensor data...')
    print('=' * 50)

    # Test all endpoints
    endpoints = [
        ('Index', f'{BASE_URL}/'),
        ('Warmup Status', f'{BASE_URL}/api/sensor/warmup'),
        ('Hardware Info', f'{BASE_URL}/api/sensor/hardware'),
        ('Complete Data', f'{BASE_URL}/api/sensor/data'),
        ('AQI Only', f'{BASE_URL}/api/sensor/aqi'),
        ('PM Measurements', f'{BASE_URL}/api/sensor/pm'),
        ('Particle Counts', f'{BASE_URL}/api/sensor/particles'),
        ('Health Status', f'{BASE_URL}/api/sensor/health'),
    ]

    passed = 0
    total = len(endpoints)

    for name, url in endpoints:
        if test_endpoint(name, url):
            passed += 1
        time.sleep(0.1)  # Small delay between requests

    print('=' * 50)
    print(f'Results: {passed}/{total} endpoints working')

    if passed == total:
        print('🎉 All tests passed! Sensor is working correctly.')
        return 0
    else:
        print('⚠️  Some tests failed. Check sensor connection and warmup status.')
        return 1

if __name__ == '__main__':
    exit(main())