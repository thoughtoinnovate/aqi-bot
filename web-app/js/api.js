/**
 * API communication module for PM2.5 sensor data
 */

class SensorAPI {
    constructor(baseURL = '') {
        this.baseURL = baseURL;
        this.retryCount = 3;
        this.retryDelay = 1000; // 1 second
    }

    /**
     * Fetch sensor data from the API
     * @returns {Promise<Object>} Sensor data object
     */
    async fetchSensorData() {
        const url = `${this.baseURL}/api/sensor/data`;

        for (let attempt = 1; attempt <= this.retryCount; attempt++) {
            try {
                const response = await fetch(url, {
                    method: 'GET',
                    headers: {
                        'Accept': 'application/json',
                        'Cache-Control': 'no-cache'
                    },
                    signal: AbortSignal.timeout(10000) // 10 second timeout
                });

                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }

                const data = await response.json();
                return this.validateSensorData(data);

            } catch (error) {
                console.warn(`API request attempt ${attempt} failed:`, error.message);

                if (attempt === this.retryCount) {
                    throw new Error(`Failed to fetch sensor data after ${this.retryCount} attempts: ${error.message}`);
                }

                // Wait before retrying
                await new Promise(resolve => setTimeout(resolve, this.retryDelay * attempt));
            }
        }
    }

    /**
     * Validate sensor data structure and types
     * @param {Object} data - Raw sensor data
     * @returns {Object} Validated sensor data
     */
    validateSensorData(data) {
        if (!data || typeof data !== 'object') {
            throw new Error('Invalid data format: expected object');
        }

        // Required fields
        const requiredFields = ['pm1_0', 'pm2_5', 'pm10', 'aqi', 'timestamp', 'status'];
        for (const field of requiredFields) {
            if (!(field in data)) {
                throw new Error(`Missing required field: ${field}`);
            }
        }

        // Type validation
        if (typeof data.pm1_0 !== 'number' || data.pm1_0 < 0) {
            throw new Error('Invalid PM1.0 value');
        }
        if (typeof data.pm2_5 !== 'number' || data.pm2_5 < 0) {
            throw new Error('Invalid PM2.5 value');
        }
        if (typeof data.pm10 !== 'number' || data.pm10 < 0) {
            throw new Error('Invalid PM10 value');
        }
        if (typeof data.aqi !== 'number' || data.aqi < 0 || data.aqi > 500) {
            throw new Error('Invalid AQI value');
        }
        if (typeof data.timestamp !== 'string') {
            throw new Error('Invalid timestamp format');
        }
        if (typeof data.status !== 'string') {
            throw new Error('Invalid status format');
        }

        // Optional particle distribution data
        if (data.particles && typeof data.particles === 'object') {
            const particleKeys = ['0.3um', '0.5um', '1.0um', '2.5um', '5.0um', '10um'];
            for (const key of particleKeys) {
                if (key in data.particles && (typeof data.particles[key] !== 'number' || data.particles[key] < 0)) {
                    console.warn(`Invalid particle count for ${key}`);
                }
            }
        }

        return data;
    }

    /**
     * Test API connectivity
     * @returns {Promise<boolean>} True if API is reachable
     */
    async testConnection() {
        try {
            await this.fetchSensorData();
            return true;
        } catch (error) {
            console.error('API connection test failed:', error.message);
            return false;
        }
    }
}

// Export for use in other modules
window.SensorAPI = SensorAPI;