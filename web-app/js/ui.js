/**
 * UI update module for PM2.5 sensor dashboard
 */

class UIDashboard {
    constructor() {
        this.aqiBreakpoints = {
            good: { min: 0, max: 50, color: '#00e400', category: 'Good' },
            moderate: { min: 51, max: 100, color: '#ffff00', category: 'Moderate' },
            unhealthySensitive: { min: 101, max: 150, color: '#ff7e00', category: 'Unhealthy for Sensitive Groups' },
            unhealthy: { min: 151, max: 200, color: '#ff0000', category: 'Unhealthy' },
            veryUnhealthy: { min: 201, max: 300, color: '#8f3f97', category: 'Very Unhealthy' },
            hazardous: { min: 301, max: 500, color: '#7e0023', category: 'Hazardous' }
        };

        this.pmMaxValues = {
            pm1_0: 50,
            pm2_5: 100,
            pm10: 200
        };
    }

    /**
     * Update the entire dashboard with sensor data
     * @param {Object} data - Sensor data from API
     */
    updateDashboard(data) {
        this.updateAQIDisplay(data);
        this.updatePMValues(data);
        this.updateParticleChart(data);
        this.updateStatusIndicators(data);
        this.updateTimestamps(data);
    }

    /**
     * Update AQI display with color coding and category
     * @param {Object} data - Sensor data
     */
    updateAQIDisplay(data) {
        const aqiValue = Math.round(data.aqi);
        const category = this.getAQICategory(aqiValue);
        const color = this.getAQIColor(aqiValue);

        // Update AQI circle
        const aqiCircle = document.getElementById('aqi-circle');
        const aqiValueEl = document.getElementById('aqi-value');
        const aqiCategoryEl = document.querySelector('.aqi-category');

        aqiCircle.style.backgroundColor = color;
        aqiValueEl.textContent = aqiValue;
        aqiCategoryEl.textContent = category.category;

        // Update health recommendation
        const recommendation = this.getHealthRecommendation(category.category);
        document.getElementById('health-recommendation').textContent = recommendation;

        // Update PM2.5 level
        document.getElementById('pm25-level').textContent = `${data.pm2_5.toFixed(1)} µg/m³`;

        // Update sensor status
        const statusEl = document.getElementById('sensor-status');
        statusEl.textContent = data.status;
        statusEl.className = `breakdown-value status-${data.status.toLowerCase().replace(' ', '-')}`;
    }

    /**
     * Update PM value displays and progress bars
     * @param {Object} data - Sensor data
     */
    updatePMValues(data) {
        const pmTypes = [
            { key: 'pm1_0', id: 'pm1', max: this.pmMaxValues.pm1_0 },
            { key: 'pm2_5', id: 'pm25', max: this.pmMaxValues.pm2_5 },
            { key: 'pm10', id: 'pm10', max: this.pmMaxValues.pm10 }
        ];

        pmTypes.forEach(({ key, id, max }) => {
            const value = data[key];
            const percentage = Math.min((value / max) * 100, 100);

            // Update value display
            document.getElementById(`${id}-value`).textContent = value.toFixed(1);

            // Update progress bar
            const barEl = document.getElementById(`${id}-bar`);
            barEl.style.width = `${percentage}%`;
            barEl.style.backgroundColor = this.getPMBarColor(percentage);
        });
    }

    /**
     * Update particle size distribution chart
     * @param {Object} data - Sensor data
     */
    updateParticleChart(data) {
        const chartContainer = document.getElementById('particles-chart');
        chartContainer.innerHTML = '';

        if (!data.particles) {
            chartContainer.innerHTML = '<div class="no-data">Particle data not available</div>';
            return;
        }

        const particles = [
            { key: '0.3um', label: '0.3-0.5 µm', color: '#e3f2fd' },
            { key: '0.5um', label: '0.5-1.0 µm', color: '#bbdefb' },
            { key: '1.0um', label: '1.0-2.5 µm', color: '#90caf9' },
            { key: '2.5um', label: '2.5-5.0 µm', color: '#64b5f6' },
            { key: '5.0um', label: '5.0-10 µm', color: '#42a5f5' },
            { key: '10um', label: '>10 µm', color: '#2196f3' }
        ];

        // Find max value for scaling
        const maxValue = Math.max(...particles.map(p => data.particles[p.key] || 0));

        particles.forEach(particle => {
            const value = data.particles[particle.key] || 0;
            const height = maxValue > 0 ? (value / maxValue) * 100 : 0;

            const bar = document.createElement('div');
            bar.className = 'particle-bar';
            bar.style.height = `${height}%`;
            bar.style.backgroundColor = particle.color;
            bar.setAttribute('aria-label', `${particle.label}: ${value} particles/0.1L`);

            const valueLabel = document.createElement('div');
            valueLabel.className = 'particle-value';
            valueLabel.textContent = value;

            bar.appendChild(valueLabel);
            chartContainer.appendChild(bar);
        });
    }

    /**
     * Update status indicators
     * @param {Object} data - Sensor data
     */
    updateStatusIndicators(data) {
        // Warmup status
        const warmupEl = document.getElementById('warmup-status');
        const isWarming = data.status === 'warming';
        warmupEl.innerHTML = `
            <div class="status-icon">${isWarming ? '⏳' : '✅'}</div>
            <div class="status-text">${isWarming ? 'Warming up...' : 'Ready'}</div>
        `;

        // Data integrity
        const integrityEl = document.getElementById('data-integrity');
        const hasValidData = data.pm2_5 >= 0 && data.aqi >= 0;
        integrityEl.innerHTML = `
            <div class="status-icon">${hasValidData ? '✅' : '❌'}</div>
            <div class="status-text">${hasValidData ? 'Valid' : 'Invalid data'}</div>
        `;

        // Sensor health
        const healthEl = document.getElementById('sensor-health');
        const isHealthy = data.status === 'ready' || data.status === 'measuring';
        healthEl.innerHTML = `
            <div class="status-icon">${isHealthy ? '❤️' : '💔'}</div>
            <div class="status-text">${isHealthy ? 'Healthy' : 'Check sensor'}</div>
        `;

        // Last update
        const updateEl = document.getElementById('last-update');
        const timeAgo = this.getTimeAgo(data.timestamp);
        updateEl.innerHTML = `
            <div class="status-icon">🕐</div>
            <div class="status-text">${timeAgo}</div>
        `;
    }

    /**
     * Update timestamps throughout the UI
     * @param {Object} data - Sensor data
     */
    updateTimestamps(data) {
        const timestamp = new Date(data.timestamp);
        const formatted = timestamp.toLocaleString();

        document.getElementById('aqi-timestamp').textContent = `Last updated: ${formatted}`;
    }

    /**
     * Get AQI category based on value
     * @param {number} aqi - AQI value
     * @returns {Object} Category info
     */
    getAQICategory(aqi) {
        for (const [key, category] of Object.entries(this.aqiBreakpoints)) {
            if (aqi >= category.min && aqi <= category.max) {
                return category;
            }
        }
        return this.aqiBreakpoints.hazardous; // Default to hazardous for >500
    }

    /**
     * Get AQI color based on value
     * @param {number} aqi - AQI value
     * @returns {string} Hex color
     */
    getAQIColor(aqi) {
        return this.getAQICategory(aqi).color;
    }

    /**
     * Get health recommendation based on AQI category
     * @param {string} category - AQI category
     * @returns {string} Health recommendation
     */
    getHealthRecommendation(category) {
        const recommendations = {
            'Good': 'Air quality is satisfactory. Enjoy outdoor activities.',
            'Moderate': 'Air quality is acceptable. Sensitive individuals should consider limiting prolonged outdoor exertion.',
            'Unhealthy for Sensitive Groups': 'Members of sensitive groups may experience health effects. Consider reducing outdoor activities.',
            'Unhealthy': 'Everyone may begin to experience health effects. Sensitive groups should avoid outdoor activities.',
            'Very Unhealthy': 'Health alert: everyone may experience more serious health effects. Avoid outdoor activities.',
            'Hazardous': 'Health warnings of emergency conditions. Everyone should avoid all outdoor activities.'
        };
        return recommendations[category] || 'Check air quality guidelines for your area.';
    }

    /**
     * Get color for PM progress bars based on percentage
     * @param {number} percentage - Percentage filled
     * @returns {string} Color
     */
    getPMBarColor(percentage) {
        if (percentage < 25) return '#00e400'; // Good
        if (percentage < 50) return '#ffff00'; // Moderate
        if (percentage < 75) return '#ff7e00'; // Unhealthy for sensitive
        return '#ff0000'; // Unhealthy+
    }

    /**
     * Get human-readable time ago string
     * @param {string} timestamp - ISO timestamp
     * @returns {string} Time ago string
     */
    getTimeAgo(timestamp) {
        const now = new Date();
        const time = new Date(timestamp);
        const diffMs = now - time;
        const diffMins = Math.floor(diffMs / 60000);
        const diffHours = Math.floor(diffMins / 60);
        const diffDays = Math.floor(diffHours / 24);

        if (diffMins < 1) return 'Just now';
        if (diffMins < 60) return `${diffMins}m ago`;
        if (diffHours < 24) return `${diffHours}h ago`;
        return `${diffDays}d ago`;
    }

    /**
     * Show loading skeleton
     */
    showLoading() {
        document.getElementById('loading-skeleton').classList.remove('hidden');
        document.getElementById('dashboard').classList.add('hidden');
        document.getElementById('error-state').classList.add('hidden');
    }

    /**
     * Show dashboard content
     */
    showDashboard() {
        document.getElementById('loading-skeleton').classList.add('hidden');
        document.getElementById('dashboard').classList.remove('hidden');
        document.getElementById('error-state').classList.add('hidden');
    }

    /**
     * Show error state
     * @param {string} message - Error message
     */
    showError(message = 'Unable to connect to the air quality sensor. Please check your connection and try again.') {
        document.getElementById('loading-skeleton').classList.add('hidden');
        document.getElementById('dashboard').classList.add('hidden');
        document.getElementById('error-state').classList.remove('hidden');

        const errorText = document.querySelector('.error-state p');
        if (errorText) {
            errorText.textContent = message;
        }
    }

    /**
     * Update connection status indicator
     * @param {boolean} isOnline - Connection status
     */
    updateConnectionStatus(isOnline) {
        const statusEl = document.getElementById('connection-status');
        const statusDot = statusEl.querySelector('.status-dot');
        const statusText = statusEl.querySelector('.status-text');

        if (isOnline) {
            statusDot.className = 'status-dot status-online';
            statusText.textContent = 'Online';
        } else {
            statusDot.className = 'status-dot status-offline';
            statusText.textContent = 'Offline';
        }
    }
}

// Export for use in other modules
window.UIDashboard = UIDashboard;