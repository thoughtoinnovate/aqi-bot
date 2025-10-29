/**
 * Main application logic for PM2.5 sensor dashboard
 */

class PM25Dashboard {
    constructor() {
        this.api = new SensorAPI();
        this.ui = new UIDashboard();
        this.refreshInterval = 30000; // 30 seconds
        this.intervalId = null;
        this.isOnline = false;
        this.lastData = null;

        this.init();
    }

    /**
     * Initialize the application
     */
    async init() {
        console.log('Initializing PM2.5 Dashboard...');

        // Set up event listeners
        this.setupEventListeners();

        // Show loading state
        this.ui.showLoading();

        // Initial data fetch
        await this.refreshData();

        // Start auto-refresh
        this.startAutoRefresh();

        console.log('Dashboard initialized');
    }

    /**
     * Set up event listeners
     */
    setupEventListeners() {
        // Refresh button
        const refreshBtn = document.getElementById('refresh-btn');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => this.handleRefresh());
        }

        // Retry button
        const retryBtn = document.getElementById('retry-btn');
        if (retryBtn) {
            retryBtn.addEventListener('click', () => this.handleRetry());
        }

        // Handle visibility change (pause/resume auto-refresh when tab is hidden)
        document.addEventListener('visibilitychange', () => {
            if (document.hidden) {
                this.stopAutoRefresh();
            } else {
                this.startAutoRefresh();
            }
        });

        // Handle online/offline events
        window.addEventListener('online', () => this.handleConnectionChange(true));
        window.addEventListener('offline', () => this.handleConnectionChange(false));
    }

    /**
     * Handle manual refresh button click
     */
    async handleRefresh() {
        console.log('Manual refresh requested');

        // Disable button temporarily
        const refreshBtn = document.getElementById('refresh-btn');
        const originalText = refreshBtn.querySelector('.btn-text').textContent;
        refreshBtn.disabled = true;
        refreshBtn.querySelector('.btn-text').textContent = 'Refreshing...';

        try {
            await this.refreshData();
        } finally {
            // Re-enable button
            refreshBtn.disabled = false;
            refreshBtn.querySelector('.btn-text').textContent = originalText;
        }
    }

    /**
     * Handle retry button click
     */
    async handleRetry() {
        console.log('Retry requested');
        await this.refreshData();
    }

    /**
     * Handle connection status change
     * @param {boolean} isOnline - New connection status
     */
    handleConnectionChange(isOnline) {
        console.log(`Connection status changed: ${isOnline ? 'online' : 'offline'}`);
        this.isOnline = isOnline;
        this.ui.updateConnectionStatus(isOnline);

        if (isOnline) {
            // Try to refresh data when coming back online
            this.refreshData();
        }
    }

    /**
     * Refresh sensor data
     */
    async refreshData() {
        try {
            console.log('Fetching sensor data...');
            const data = await this.api.fetchSensorData();

            console.log('Data received:', data);
            this.lastData = data;
            this.isOnline = true;

            // Update UI
            this.ui.updateDashboard(data);
            this.ui.showDashboard();
            this.ui.updateConnectionStatus(true);

        } catch (error) {
            console.error('Failed to fetch sensor data:', error);
            this.isOnline = false;

            // Show error state
            this.ui.showError(error.message);
            this.ui.updateConnectionStatus(false);

            // If we have cached data, show it with a warning
            if (this.lastData) {
                console.log('Showing cached data due to error');
                this.ui.updateDashboard(this.lastData);
                this.ui.showDashboard();
                // Could add a visual indicator that data is stale
            }
        }
    }

    /**
     * Start auto-refresh interval
     */
    startAutoRefresh() {
        if (this.intervalId) {
            clearInterval(this.intervalId);
        }

        console.log(`Starting auto-refresh every ${this.refreshInterval / 1000} seconds`);
        this.intervalId = setInterval(() => {
            if (!document.hidden && this.isOnline) {
                this.refreshData();
            }
        }, this.refreshInterval);
    }

    /**
     * Stop auto-refresh interval
     */
    stopAutoRefresh() {
        if (this.intervalId) {
            console.log('Stopping auto-refresh');
            clearInterval(this.intervalId);
            this.intervalId = null;
        }
    }

    /**
     * Test API connection
     * @returns {Promise<boolean>} Connection status
     */
    async testConnection() {
        return await this.api.testConnection();
    }

    /**
     * Get current data
     * @returns {Object|null} Last fetched data
     */
    getCurrentData() {
        return this.lastData;
    }

    /**
     * Check if dashboard is online
     * @returns {boolean} Online status
     */
    isDashboardOnline() {
        return this.isOnline;
    }
}

// Initialize the dashboard when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.dashboard = new PM25Dashboard();
});

// Export for debugging
window.PM25Dashboard = PM25Dashboard;