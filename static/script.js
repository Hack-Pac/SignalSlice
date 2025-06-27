/**
 * SignalSlice Real-time Dashboard
 * Pentagon Pizza Index Monitoring System
 */

/**
 * SignalSlice Monitor Class
 * Main dashboard controller for real-time pizza surveillance
 */
class SignalSliceMonitor {
    constructor() {
        this.isLoading = false;
        this.chart = null;
        this.map = null;
        this.activityData = [];
        this.scanCount = 0;
        this.anomalyCount = 0;
        this.lastUpdateTime = new Date();
        this.lastScanTime = null;        this.socket = null;
        this.pizzaIndex = 3.42;
        this.gayBarIndex = 6.58;
        this.activeLocations = 127;
        this.lastActivityTimestamp = null;
        
        // MEMORY OPTIMIZATION: Improved throttling and limits
        this.lastActivityUpdate = 0;
        this.activityUpdateCooldown = 500; // Increased from 100ms to 500ms
        this.maxActivityItems = 10; // Reduced from 15 to 10
        this.maxChartPoints = 15; // Reduced from 20 to 15
        
        // MEMORY: Use WeakMap for temporary data caching
        this.tempDataCache = new WeakMap();
        
        this.init();
    }    init() {
        // Hide loading overlay immediately and show main content
        this.hideLoadingOverlay();
        this.updateSystemTime();
        
        // Add initial test activity to verify feed is working
        console.log('Testing activity feed...');
        this.addActivityItem('INIT', 'SignalSlice dashboard loading...', 'normal');
        this.addActivityItem('TEST', 'Testing activity feed functionality', 'success');
        
        this.initializeChart();
        this.initializeMap();
        this.setupEventListeners();
        
        // Start HTTP polling immediately (fallback approach)
        this.startHttpPolling();
        
        // Connect to backend after everything else is set up
        setTimeout(() => {
            this.connectToBackend();
        }, 500);
    }
    
    hideLoadingOverlay() {
        const overlay = document.getElementById('loading-overlay');
        if (overlay) {
            overlay.style.display = 'none';
        }
    }
      showScanningAnimation() {
        const overlay = document.getElementById('loading-overlay');
        if (overlay) {
            overlay.style.display = 'flex';
            overlay.style.opacity = '1';
        }
    }
    
    hideScanningAnimation() {
        const overlay = document.getElementById('loading-overlay');
        if (overlay) {
            overlay.style.display = 'none';
        }
    }    connectToBackend() {
        // Wait for SocketIO to be fully loaded
        if (typeof io === 'undefined') {
            console.warn('⚠️ SocketIO not loaded yet, retrying in 1 second...');
            setTimeout(() => this.connectToBackend(), 1000);
            return;
        }
        
        try {
            console.log('Attempting to connect to SocketIO...');
            // Connect to Flask-SocketIO backend
            this.socket = io({
                transports: ['polling', 'websocket'],
                upgrade: true,
                timeout: 10000,
                forceNew: true
            });
            
            // Handle connection events
            this.socket.on('connect', () => {
                console.log('✅ Successfully connected to SignalSlice backend');
                console.log('Socket ID:', this.socket.id);
                this.addActivityItem('CONNECT', 'Connected to real-time data stream', 'success');
            });
            
            this.socket.on('connect_error', (error) => {
                console.error('❌ SocketIO connection error:', error);
                this.addActivityItem('ERROR', `Connection failed: ${error.message || error}`, 'critical');
            });
              this.socket.on('disconnect', () => {
                console.log('❌ Disconnected from backend');
                this.addActivityItem('DISCONNECT', 'Connection to data stream lost', 'critical');
            });
            
            // Add timeout to detect if connection never happens
            setTimeout(() => {
                if (!this.socket.connected) {
                    console.warn('⚠️ SocketIO connection not established after 5 seconds');
                    this.addActivityItem('ERROR', 'Failed to connect to backend - check server status', 'critical');
                }
            }, 5000);
            
            // Handle real-time updates from backend
            this.socket.on('initial_state', (data) => {
                this.handleInitialState(data);
            });
            
            this.socket.on('activity_update', (activity) => {
                this.handleActivityUpdate(activity);
            });
            
                    this.socket.on('pizza_index_update', (data) => {
            this.handlePizzaIndexUpdate(data);
        });
        
        this.socket.on('gay_bar_index_update', (data) => {
            this.handleGayBarIndexUpdate(data);
        });
            
            this.socket.on('scan_stats_update', (stats) => {
                this.handleScanStatsUpdate(stats);
            });
            
            this.socket.on('anomaly_detected', (anomaly) => {
                this.handleAnomalyDetected(anomaly);
            });
            
            this.socket.on('scanning_start', () => {
                this.showScanningAnimation();
            });
            
            this.socket.on('scanning_complete', () => {
                this.hideScanningAnimation();
                this.updateLastScanTime();
            });
              } catch (error) {
            console.error('Failed to connect to backend:', error);
            this.addActivityItem('ERROR', 'Failed to connect to backend - falling back to polling', 'warning');
            this.startHttpPolling();
        }
    }
    
    startHttpPolling() {
        console.log('Starting HTTP polling fallback...');
        this.addActivityItem('FALLBACK', 'Using HTTP polling for updates', 'warning');
        
        // MEMORY OPTIMIZATION: Poll every 15 seconds to reduce memory pressure
        setInterval(() => {
            this.fetchActivityUpdates();
        }, 15000);
        
        // Initial fetch
        this.fetchActivityUpdates();
    }
      async fetchActivityUpdates() {
        try {
            console.log('Fetching activity updates from API...');
            const response = await fetch('/api/activity_feed');
            const data = await response.json();
            
            console.log('Received activity data:', data);
            
            if (data.activity_feed && data.activity_feed.length > 0) {
                console.log(`Found ${data.activity_feed.length} activity items`);
                
                // Check if we have new activities
                const latestActivity = data.activity_feed[0];
                if (!this.lastActivityTimestamp || 
                    latestActivity.timestamp !== this.lastActivityTimestamp) {
                    
                    console.log('Updating activity feed with new data');
                    // Update activity feed with new items
                    this.updateActivityFeedFromData(data.activity_feed);
                    this.lastActivityTimestamp = latestActivity.timestamp;
                } else {
                    console.log('No new activity updates');
                }
            } else {
                console.log('No activity data received');
            }
        } catch (error) {
            console.error('Failed to fetch activity updates:', error);
        }
    }
    
    updateActivityFeedFromData(activities) {
        // MEMORY OPTIMIZATION: Clear existing feed and rebuild with limited data
        const activityList = document.getElementById('activity-feed');
        if (activityList) {
            activityList.innerHTML = '';
            
            // Only take the latest activities up to our limit
            const limitedActivities = activities.slice(0, this.maxActivityItems);
            
            // Add each activity from the server
            limitedActivities.forEach(activity => {
                this.addActivityItemToFeed(activity, false); // Don't animate for bulk updates
            });
            
            // Update internal data array efficiently
            this.activityData = [...limitedActivities];
        }
    }
    
    handleInitialState(data) {
        console.log('📡 Received initial state:', data);
        console.log('📊 Pizza Index from server:', data.pizza_index);
        console.log('🏳️‍🌈 Gay Bar Index from server:', data.gay_bar_index);
        
        // Update dashboard with real initial state
        this.pizzaIndex = data.pizza_index;
        this.gayBarIndex = data.gay_bar_index || 6.58;
        this.activeLocations = data.active_locations;
        this.scanCount = data.scan_count;
        this.anomalyCount = data.anomaly_count;
        
        console.log('🔄 Updating UI elements...');
        // Update UI elements
        this.updatePizzaIndex(this.pizzaIndex);
        this.updateGayBarIndex(this.gayBarIndex);
        this.updateActiveLocations(this.activeLocations);
        
        const scanCountElement = document.getElementById('scan-count');
        const anomalyCountElement = document.getElementById('anomaly-count');
        
        if (scanCountElement) {
            scanCountElement.textContent = this.scanCount;
            console.log('✅ Updated scan count to:', this.scanCount);
        } else {
            console.warn('⚠️ scan-count element not found');
        }
        
        if (anomalyCountElement) {
            anomalyCountElement.textContent = this.anomalyCount;
            console.log('✅ Updated anomaly count to:', this.anomalyCount);
        } else {
            console.warn('⚠️ anomaly-count element not found');
        }
        
        // MEMORY OPTIMIZATION: Load activity feed with limits
        if (data.activity_feed && data.activity_feed.length > 0) {
            // Only load the latest activities up to our limit
            const limitedFeed = data.activity_feed.slice(0, this.maxActivityItems);
            limitedFeed.forEach(activity => {
                this.addActivityItemToFeed(activity);
            });
        }
        
        // Set last scan time
        if (data.last_scan_time && data.last_scan_time !== 'Never') {
            this.lastScanTime = new Date();
            this.updateLastScanTime();
        }
        
        this.updateLastUpdateIndicator();
        
        // MEMORY OPTIMIZATION: Start periodic cleanup
        this.startMemoryCleanup();
        
        // Twitter timeline removed - using simple link instead
    }
    
    // MEMORY OPTIMIZATION: Periodic memory cleanup
    startMemoryCleanup() {
        setInterval(() => {
            this.performMemoryCleanup();
        }, 30000); // Clean up every 30 seconds
    }
    
    performMemoryCleanup() {
        // Force garbage collection of temporary data
        this.tempDataCache = new WeakMap();
        
        // Ensure arrays don't exceed limits
        if (this.activityData.length > this.maxActivityItems) {
            this.activityData.splice(this.maxActivityItems);
        }
        
        // Clean up chart data if it exists
        if (this.chartData) {
            if (this.chartData.timestamps.length > this.maxChartPoints) {
                const excess = this.chartData.timestamps.length - this.maxChartPoints;
                this.chartData.timestamps.splice(0, excess);
                this.chartData.values.splice(0, excess);
                this.chartData.anomalies.splice(0, excess);
            }
        }
        
        // Clean up DOM elements if activity feed has too many children
        const activityList = document.getElementById('activity-feed');
        if (activityList && activityList.children.length > this.maxActivityItems) {
            while (activityList.children.length > this.maxActivityItems) {
                const lastChild = activityList.lastChild;
                if (lastChild) {
                    lastChild.parentNode.removeChild(lastChild);
                }
            }
        }
    }
    
    handleActivityUpdate(activity) {
        // PERFORMANCE: Throttle activity updates to prevent DOM spam
        const now = performance.now();
        if (now - this.lastActivityUpdate < this.activityUpdateCooldown) {
            return; // Skip this update if too frequent
        }
        this.lastActivityUpdate = now;
        this.addActivityItemToFeed(activity);
    }
      handlePizzaIndexUpdate(data) {
        console.log('🍕 Pizza index update received:', data);
        console.log('Current pizza index:', this.pizzaIndex, '-> New:', data.value);
        this.pizzaIndex = data.value;
        const isAnomaly = data.change > 10 || data.value > 7; // Consider significant changes as anomalies
        this.updatePizzaIndex(this.pizzaIndex, data.change, isAnomaly);
    }
    
    handleGayBarIndexUpdate(data) {
        console.log('🏳️‍🌈 Gay bar index update received:', data);
        console.log('Current gay bar index:', this.gayBarIndex, '-> New:', data.value);
        this.gayBarIndex = data.value;
        const isAnomaly = data.change > 10 || data.value > 7;
        this.updateGayBarIndex(this.gayBarIndex, data.change, isAnomaly);
    }
    
    handleScanStatsUpdate(stats) {
        console.log('Scan stats update:', stats);
        this.scanCount = stats.scan_count;
        document.getElementById('scan-count').textContent = this.scanCount;
        this.lastScanTime = new Date();
        this.updateLastScanTime();
        
        // Show scan completion notification
        this.showNotification('Scan completed', 'success');
    }
    
    handleAnomalyDetected(anomaly) {
        console.log('Anomaly detected:', anomaly);
        this.anomalyCount = anomaly.anomaly_count;
        document.getElementById('anomaly-count').textContent = this.anomalyCount;
        
        // Update last anomaly time
        const lastAnomalyElement = document.getElementById('last-anomaly');
        if (lastAnomalyElement) {
            lastAnomalyElement.textContent = 'Just now';
        }
        // Show critical notification
        this.showNotification(`🚨 ${anomaly.message}`, 'critical');
        
        // Flash anomaly indicator
        this.flashAnomalyIndicator();
        
        // Add detailed activity item for anomaly
        this.addActivityItem('ANOMALY', `${anomaly.title}: ${anomaly.message}`, 'critical');
        
        // Note: Pizza reports now use real Twitter embed
        
        // Update pizza index with anomaly flag if value increase is significant
        if (this.pizzaIndex < 7) {
            const newIndex = Math.min(10, this.pizzaIndex + 1.5);
            const changePercent = ((newIndex - this.pizzaIndex) / this.pizzaIndex) * 100;
            this.updatePizzaIndex(newIndex, changePercent, true);
        }
    }
      updateSystemTime() {
        const now = new Date();
        const timeString = now.toLocaleString('en-US', {
            timeZone: 'America/New_York',
            hour12: false,
            year: 'numeric',
            month: '2-digit',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit'
        });
        
        const timeElement = document.getElementById('system-time');
        if (timeElement) {
            timeElement.textContent = `EST ${timeString}`;
        }
        // MEMORY OPTIMIZATION: Update every 10 seconds to reduce operations
        setTimeout(() => this.updateSystemTime(), 10000);
    }
    
    triggerManualScan() {
        if (this.socket && this.socket.connected) {
            console.log('Triggering manual scan...');
            this.socket.emit('manual_scan');
            this.addActivityItem('MANUAL', 'Manual scan initiated by user', 'normal');
        } else {
            console.error('Not connected to backend');
            this.addActivityItem('ERROR', 'Cannot trigger scan - not connected to backend', 'critical');
        }
    }
    
    addActivityItem(type, message, level = 'normal') {
        const timestamp = new Date().toLocaleTimeString('en-US', {
            timeZone: 'America/New_York',
            hour12: false
        });
        
        const activity = {
            type: type,
            message: message,
            level: level,
            timestamp: timestamp
        };
        
        this.addActivityItemToFeed(activity);
    }    addActivityItemToFeed(activity, animate = true) {
        const activityList = document.getElementById('activity-feed');
        if (!activityList) {
            console.warn('Activity feed element not found');
            return;
        }
        
        const activityElement = document.createElement('div');
        activityElement.className = `activity-item activity-${activity.level}`;
        
        // Get appropriate icon for activity type
        let icon = '';
        let iconColor = '';
        switch (activity.type) {
            case 'SCAN': 
                icon = '🔍'; 
                iconColor = '#3b82f6';
                break;
            case 'SCRAPE': 
                icon = '📡'; 
                iconColor = '#3b82f6';
                break;
            case 'ANALYZE': 
                icon = '🧠'; 
                iconColor = '#8b5cf6';
                break;
            case 'ANOMALY': 
                icon = '🚨'; 
                iconColor = '#ef4444';
                break;
            case 'CONNECT': 
                icon = '🔗'; 
                iconColor = '#10b981';
                break;
            case 'DISCONNECT': 
                icon = '⚠️'; 
                iconColor = '#f59e0b';
                break;
            case 'MANUAL': 
                icon = '👤'; 
                iconColor = '#6366f1';
                break;
            case 'ERROR': 
                icon = '❌'; 
                iconColor = '#ef4444';
                break;
            case 'INIT': 
                icon = '🛰️'; 
                iconColor = '#3b82f6';
                break;
            case 'SYSTEM': 
                icon = '📊'; 
                iconColor = activity.level === 'warning' ? '#f59e0b' : '#10b981';
                break;
            case 'SUCCESS':
                icon = '✅';
                iconColor = '#10b981';
                break;
            case 'PIZZA':
                icon = '🍕';
                iconColor = '#f59e0b';
                break;
            case 'GAYBAR':
                icon = '🏳️‍🌈';
                iconColor = '#a855f7';
                break;
            default: 
                icon = '📋'; 
                iconColor = '#6b7280';
                break;
        }
        
        // Special styling for critical activities
        let borderStyle = '';
        if (activity.level === 'critical') {
            borderStyle = 'border-left: 4px solid #ef4444;';
        } else if (activity.level === 'success') {
            borderStyle = 'border-left: 4px solid #10b981;';
        } else if (activity.level === 'warning') {
            borderStyle = 'border-left: 4px solid #f59e0b;';
        }
        
        activityElement.innerHTML = `
            <div class="activity-icon" style="color: ${iconColor};">${icon}</div>
            <div class="activity-content">
                <div class="activity-message">${activity.message}</div>
                <div class="activity-meta">
                    <span class="activity-type">${activity.type}</span>
                    <span class="activity-time">${activity.timestamp}</span>
                </div>
            </div>
        `;
          if (borderStyle) {
            activityElement.style.cssText += borderStyle;
        }
        
        // PERFORMANCE: Simplified DOM insertion without complex animations
        activityList.insertBefore(activityElement, activityList.firstChild);
        
        // Simple fade-in if animation requested
        if (animate) {
            activityElement.style.opacity = '0.5';
            setTimeout(() => {
                activityElement.style.opacity = '1';
            }, 50);
        }
          // MEMORY OPTIMIZATION: Keep only limited items and clean up efficiently
        while (activityList.children.length > this.maxActivityItems) {
            const lastChild = activityList.lastChild;
            if (lastChild) {
                // Remove immediately without animation to save memory
                lastChild.parentNode.removeChild(lastChild);
            }
        }
        
        // MEMORY: Store in activity data array with strict limits
        this.activityData.unshift(activity);
        if (this.activityData.length > this.maxActivityItems) {
            // Use splice instead of slice to modify in-place
            this.activityData.splice(this.maxActivityItems);
        }
        
        // Auto-scroll to top if user is near top
        if (activityList.scrollTop < 50) {
            activityList.scrollTop = 0;
        }
    }
    
    updateLastScanTime() {
        if (!this.lastScanTime) return;
        
        const now = new Date();
        const diffInMinutes = Math.floor((now - this.lastScanTime) / 60000);
        
        const scanFrequencyElement = document.getElementById('scan-frequency');
        if (scanFrequencyElement) {
            if (diffInMinutes === 0) {
                scanFrequencyElement.textContent = 'Just completed';
            } else if (diffInMinutes === 1) {
                scanFrequencyElement.textContent = '1 min ago';
            } else {
                scanFrequencyElement.textContent = `${diffInMinutes} min ago`;
            }
        }
    }
    
    flashAnomalyIndicator() {
        const anomalyElement = document.getElementById('anomaly-count');
        if (anomalyElement) {
            anomalyElement.style.animation = 'flash 1s ease-in-out 3';
        }
    }
    
    processNewData(data) {
        this.updatePizzaIndex(data.pizzaIndex);
        
        if (data.hasAnomaly) {
            this.handleAnomaly(data);
        }
        
        // Only add activity for significant changes
        if (Math.random() > 0.7) { // 30% chance of logging
            this.addActivityItem(
                data.hasAnomaly ? 'ANOMALY' : 'UPDATE',
                `${data.busynessData.dataType} data from ${data.busynessData.location}`,
                data.hasAnomaly ? 'warning' : 'normal'
            );
        }
    }
    
    handleAnomaly(data) {
        this.anomalyCount++;
        document.getElementById('anomaly-count').textContent = this.anomalyCount;
        document.getElementById('last-anomaly').textContent = 'Just detected';
        
        this.showAlert(
            'ANOMALY DETECTED',
            `${data.anomalyType} - Pizza Index: ${data.pizzaIndex.toFixed(2)}`
        );
        
        this.addActivityItem(
            'ANOMALY',
            `${data.anomalyType} at ${data.busynessData.location}`,
            'critical'
        );
        
        this.updateThreatLevel(Math.min(90, data.pizzaIndex * 10));
    }
      updatePizzaIndex(value, changePercent = null, isAnomaly = false) {
        console.log(`🍕 updatePizzaIndex called with value: ${value}, change: ${changePercent}`);
        const element = document.getElementById('pizza-index');
        const changeElement = document.getElementById('pizza-change');
        const cardElement = document.getElementById('pizza-index-card');
        
        if (!element) {
            console.error('❌ pizza-index element not found in DOM');
            return;
        } else {
            console.log('✅ Found pizza-index element');
        }
        
        const currentValue = parseFloat(element.textContent) || 0;
        const change = value - currentValue;
        const calculatedChangePercent = changePercent !== null ? changePercent : 
            (currentValue > 0 ? ((change / currentValue) * 100) : 0);
        
        this.animateNumber(element, currentValue, value, 1000);
        
        if (changeElement) {
            changeElement.textContent = `${calculatedChangePercent >= 0 ? '+' : ''}${calculatedChangePercent.toFixed(2)}%`;
            changeElement.className = 'stat-change ' + (calculatedChangePercent >= 0 ? 'positive' : 'negative');
            
            // Special styling for anomalies
            if (isAnomaly) {
                changeElement.style.color = '#ef4444';
                changeElement.style.fontWeight = 'bold';
                setTimeout(() => {
                    changeElement.style.color = '';
                    changeElement.style.fontWeight = '';
                }, 5000);
            }
        }
        
        if (cardElement) {
            cardElement.className = 'stat-card';
            if (isAnomaly) {
                cardElement.classList.add('anomaly-detected');
                setTimeout(() => {
                    cardElement.classList.remove('anomaly-detected');
                }, 5000);
            } else if (value > 7) {
                cardElement.classList.add('critical');
            } else if (value > 5) {
                cardElement.classList.add('warning');
            }
        }
        
        // Update chart with anomaly information
        this.updateChartData(value, isAnomaly, calculatedChangePercent);
        
        // Note: Pizza reports now use real Twitter embed
        
        // Update stored pizza index
        this.pizzaIndex = value;
    }
    
    updateGayBarIndex(value, changePercent = null, isAnomaly = false) {
        console.log(`🏳️‍🌈 updateGayBarIndex called with value: ${value}, change: ${changePercent}`);
        const element = document.getElementById('gay-bar-index');
        const changeElement = document.getElementById('gay-bar-change');
        const cardElement = document.getElementById('gay-bar-index-card');
        
        if (!element) {
            console.error('❌ gay-bar-index element not found in DOM');
            return;
        } else {
            console.log('✅ Found gay-bar-index element');
        }
        
        const currentValue = parseFloat(element.textContent) || 0;
        const change = value - currentValue;
        const calculatedChangePercent = changePercent !== null ? changePercent : 
            (currentValue > 0 ? ((change / currentValue) * 100) : 0);
        this.animateNumber(element, currentValue, value, 1000);
        
        if (changeElement) {
            changeElement.textContent = `${calculatedChangePercent >= 0 ? '+' : ''}${calculatedChangePercent.toFixed(2)}%`;
            changeElement.className = 'stat-change ' + (calculatedChangePercent >= 0 ? 'positive' : 'negative');
            
            // Special styling for anomalies - for gay bars, high value is anomalous
            if (isAnomaly) {
                changeElement.style.color = '#ef4444';
                changeElement.style.fontWeight = 'bold';
                setTimeout(() => {
                    changeElement.style.color = '';
                    changeElement.style.fontWeight = '';
                }, 5000);
            }
        }
        
        if (cardElement) {
            cardElement.className = 'stat-card';
            if (isAnomaly) {
                cardElement.classList.add('anomaly-detected');
                setTimeout(() => {
                    cardElement.classList.remove('anomaly-detected');
                }, 5000);
            } else if (value > 7) {
                cardElement.classList.add('critical');
            } else if (value > 5) {
                cardElement.classList.add('warning');
            }
        }
        
        // Note: Pizza reports now use real Twitter embed
        
        // Update stored gay bar index
        this.gayBarIndex = value;
    }
    
    updateActiveLocations(count) {
        const element = document.getElementById('active-locations');
        if (element) {
            this.animateNumber(element, 
                              parseInt(element.textContent) || 0, 
                              count, 800);
        }
    }
      animateNumber(element, start, end, duration) {
        if (!element) return;
        
        // PERFORMANCE: Use requestAnimationFrame instead of setInterval
        const startTime = performance.now();
        
        const animate = (currentTime) => {
            const elapsed = currentTime - startTime;
            const progress = Math.min(elapsed / duration, 1);
            
            const current = start + (end - start) * progress;
            
            // Format number appropriately
            if (Number.isInteger(end)) {
                element.textContent = Math.round(current);
            } else {
                element.textContent = current.toFixed(2);
            }
            
            if (progress < 1) {
                requestAnimationFrame(animate);
            }
        };
        
        requestAnimationFrame(animate);
        
        // PERFORMANCE: Reduced visual feedback - no transform scale
        element.style.color = '#fbbf24';
        setTimeout(() => {
            element.style.color = '';
        }, 200); // Reduced duration
    }      initializeChart() {
        const ctx = document.getElementById('realtime-chart');
        if (!ctx) {
            console.warn('Chart canvas element not found');
            return;
        }
        
        // MEMORY OPTIMIZATION: Initialize chart data tracking with strict limits
        this.chartData = {
            timestamps: [],
            values: [],
            anomalies: [], // Track anomaly points
            maxPoints: this.maxChartPoints // Use configurable limit
        };
        
        // Initialize with current pizza index
        const now = new Date();
        this.chartData.timestamps.push(now);
        this.chartData.values.push(this.pizzaIndex);
        this.chartData.anomalies.push(false);
        
        // PERFORMANCE: Simplified chart configuration
        this.chart = new Chart(ctx.getContext('2d'), {
            type: 'line',
            data: {
                labels: [this.formatTimeLabel(now)],
                datasets: [{
                    label: 'Pizza Index',
                    data: [this.pizzaIndex],
                    borderColor: '#3b82f6',
                    backgroundColor: 'rgba(59, 130, 246, 0.1)',
                    fill: false, // Reduced fill for performance
                    tension: 0.2, // Reduced tension
                    pointRadius: 3, // Fixed point size for performance
                    pointBackgroundColor: '#3b82f6',
                    pointBorderColor: '#2563eb',
                    pointHoverRadius: 5
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: {
                    intersect: false // Improved hover performance
                },
                plugins: {
                    legend: {
                        labels: { color: '#d1d5db' }
                    }
                },
                scales: {
                    x: { 
                        ticks: { color: '#6b7280' },
                        grid: { color: '#374151' }
                    },
                    y: { 
                        ticks: { 
                            color: '#6b7280'
                        },
                        grid: { color: '#374151' },
                        min: 0,
                        max: 10
                    }
                },
                animation: {
                    duration: 500, // Reduced animation duration
                    easing: 'easeInOut'
                }
            }
        });
    }
      formatTimeLabel(timestamp) {
        return timestamp.toLocaleTimeString('en-US', { 
            hour12: false, 
            hour: '2-digit', 
            minute: '2-digit' 
        });
    }
    
    updateChartData(newValue, isAnomaly = false, changePercent = 0) {
        if (!this.chart) return;
        
        const now = new Date();
        const timeLabel = this.formatTimeLabel(now);
        
        // Add new data point
        this.chartData.timestamps.push(now);
        this.chartData.values.push(newValue);
        this.chartData.anomalies.push(isAnomaly);
        
        // Update chart data
        this.chart.data.labels.push(timeLabel);
        this.chart.data.datasets[0].data.push(newValue);
        
        // MEMORY OPTIMIZATION: Keep only the last maxPoints with efficient cleanup
        if (this.chartData.timestamps.length > this.chartData.maxPoints) {
            // Remove multiple items at once to reduce operations
            const removeCount = this.chartData.timestamps.length - this.chartData.maxPoints;
            this.chartData.timestamps.splice(0, removeCount);
            this.chartData.values.splice(0, removeCount);
            this.chartData.anomalies.splice(0, removeCount);
            this.chart.data.labels.splice(0, removeCount);
            this.chart.data.datasets[0].data.splice(0, removeCount);
        }
        
        // PERFORMANCE: Reduced chart update animation
        this.chart.update({ duration: 200 });
        
        // Flash chart if anomaly (simplified)
        if (isAnomaly) {
            this.flashChart();
        }
    }
    
    flashChart() {
        const chartContainer = document.querySelector('.chart-container');
        if (chartContainer) {
            // PERFORMANCE: Simplified flash effect - just add/remove class
            chartContainer.classList.add('anomaly-flash');
            
            setTimeout(() => {
                chartContainer.classList.remove('anomaly-flash');
            }, 1500); // Reduced duration
        }
    }
    
    generateTimeLabels(count) {
        const labels = [];
        const now = new Date();
        
        for (let i = count - 1; i >= 0; i--) {
            const time = new Date(now.getTime() - i * 60000);
            labels.push(time.toLocaleTimeString('en-US', { 
                hour12: false, 
                hour: '2-digit', 
                minute: '2-digit' 
            }));
        }
        
        return labels;
    }
    
    generateChartData(count) {
        const data = [];
        const baseValue = 3.42; // Start near current index
        for (let i = 0; i < count; i++) {
            let value = baseValue + (Math.random() - 0.5) * 2;
            if (i > count - 4 && Math.random() > 0.7) value += Math.random() * 3; // Recent activity
            data.push(Math.max(0, value));
        }
        return data;
    }
    
      initializeMap() {
        const mapElement = document.getElementById('surveillance-map');
        if (!mapElement) {
            console.warn('Map container element not found');
            return;
        }
        
        const pentagonCoords = [38.8719, -77.0563];
        
        try {
            this.map = L.map('surveillance-map', {
                zoomControl: false,
                attributionControl: false
            }).setView(pentagonCoords, 10);
            
            L.tileLayer('https://tiles.stadiamaps.com/tiles/alidade_smooth_dark/{z}/{x}/{y}{r}.png', {
                attribution: '',
                maxZoom: 18
            }).addTo(this.map);
            
            const pentagonIcon = L.divIcon({
                className: 'pentagon-marker',
                html: `<div style="
                    background: #ef4444; 
                    width: 16px; 
                    height: 16px; 
                    border-radius: 50%; 
                    border: 2px solid white; 
                    box-shadow: 0 0 20px rgba(239, 68, 68, 0.8);
                    animation: pulse 2s infinite;
                "></div>`,
                iconSize: [16, 16],
                iconAnchor: [8, 8]
            });
            
            L.marker(pentagonCoords, { icon: pentagonIcon })
                .addTo(this.map)
                .bindPopup('<b>THE PENTAGON</b><br>Classification: TOP SECRET');
            
            L.circle(pentagonCoords, {
                color: '#3b82f6',
                fillColor: '#3b82f6',
                fillOpacity: 0.05,
                radius: 80467,
                weight: 2,
                opacity: 0.6
            }).addTo(this.map);
            
            // MEMORY OPTIMIZATION: Surveillance points generation completely removed to save memory
        } catch (error) {
            console.error('Error initializing map:', error);
            this.addActivityItem('ERROR', 'Failed to initialize surveillance map', 'critical');
        }
    }
    
    // MEMORY OPTIMIZATION: Removed generateSurveillancePoints() entirely to prevent memory bloat
    // Original method generated 127 DOM elements with complex styling causing memory issues
    
    generateInitialActivity() {
        // MEMORY OPTIMIZATION: Reduced initial activities to prevent memory buildup
        const activities = [
            { type: 'INIT', message: 'Surveillance system online - 127 locations monitored', level: 'normal' },
            { type: 'CONNECT', message: 'Real-time data feeds established', level: 'normal' },
            { type: 'SCAN', message: 'Google Maps API: 127 active locations confirmed', level: 'normal' }
        ];
        
        activities.forEach((activity, index) => {
            setTimeout(() => {
                this.addActivityItem(activity.type, activity.message, activity.level);
            }, index * 500); // Increased delay to reduce rapid DOM updates
        });
    }
    
    // MEMORY OPTIMIZATION: Removed duplicate addActivityItem method - using the optimized version above
    
    updateThreatLevel(percentage) {
        const fill = document.getElementById('threat-fill');
        const text = document.getElementById('threat-level-text');
        
        if (fill) {
            fill.style.width = `${Math.min(percentage, 100)}%`;
        }
        
        if (text) {
            if (percentage < 30) {
                text.textContent = 'LOW';
                text.className = 'text-success';
            } else if (percentage < 70) {
                text.textContent = 'MODERATE';
                text.className = 'text-warning';
            } else {
                text.textContent = 'HIGH';
                text.className = 'text-critical';
            }
        }
    }
    updateLastUpdateIndicator() {
        const element = document.getElementById('last-update');
        if (!element) return;
        
        const now = new Date();
        const diffInMinutes = Math.floor((now - this.lastUpdateTime) / 60000);
        
        if (diffInMinutes === 0) {
            element.textContent = 'Just now';
        } else if (diffInMinutes === 1) {
            element.textContent = '1 min ago';
        } else {
            element.textContent = `${diffInMinutes} min ago`;
        }
    }
    
    showAlert(title, message) {
        const banner = document.getElementById('alert-banner');
        const titleEl = document.getElementById('alert-title');
        const messageEl = document.getElementById('alert-message');
        const timestampEl = document.getElementById('alert-timestamp');
        
        if (banner && titleEl && messageEl && timestampEl) {
            titleEl.textContent = title;
            messageEl.textContent = message;
            timestampEl.textContent = new Date().toLocaleTimeString('en-US', { 
                hour12: false, 
                hour: '2-digit', 
                minute: '2-digit'
            });
            
            banner.style.display = 'block';
            
            // Auto-hide after 10 seconds
            setTimeout(() => {
                banner.style.display = 'none';
            }, 10000);
        }
    }
    
    showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.textContent = message;
        notification.style.cssText = `
            position: fixed;
            top: 100px;
            right: 20px;
            background: var(--bg-panel);
            color: var(--text-primary);
            padding: 15px 20px;
            border-radius: 8px;
            border: 1px solid var(--border-primary);
            box-shadow: 0 4px 20px rgba(0,0,0,0.3);
            z-index: 10000;
            animation: slideIn 0.3s ease;
        `;
        
        document.body.appendChild(notification);
        
        setTimeout(() => {
            notification.style.animation = 'slideOut 0.3s ease';
            setTimeout(() => notification.remove(), 300);
        }, 3000);
    }
      setupEventListeners() {
        // Chart period controls
        document.querySelectorAll('[data-period]').forEach(button => {
            button.addEventListener('click', (e) => {
                document.querySelectorAll('[data-period]').forEach(b => b.classList.remove('active'));
                e.target.classList.add('active');
                
                const period = e.target.dataset.period;
                this.updateChartPeriod(period);
            });
        });
        
        // Map controls
        const centerBtn = document.getElementById('center-pentagon');
        if (centerBtn) {
            centerBtn.addEventListener('click', () => {
                if (this.map) {
                    this.map.setView([38.8719, -77.0563], 10);
                    this.showNotification('Map centered on Pentagon', 'info');
                }
            });
        }
        
        const heatmapBtn = document.getElementById('toggle-heatmap');
        if (heatmapBtn) {
            heatmapBtn.addEventListener('click', () => {
                this.showNotification('Heatmap view toggled', 'info');
            });
        }
        
          // Add manual scan button to map controls
        const mapControls = document.querySelector('.map-controls');
        if (mapControls) {
            const scanBtn = document.createElement('button');
            scanBtn.textContent = 'Manual Scan';
            scanBtn.className = 'btn btn-sm';
            scanBtn.onclick = () => this.triggerManualScan();
            mapControls.appendChild(scanBtn);
        }
    }
    
    updateChartPeriod(period) {
        if (!this.chart) return;
        let labelCount, dataCount;
        switch (period) {
            case '1h':
                labelCount = dataCount = 60;
                break;
            case '6h':
                labelCount = dataCount = 72;
                break;
            case '24h':
                labelCount = dataCount = 96;
                break;
            default:
                labelCount = dataCount = 20;
        }
        
        this.chart.data.labels = this.generateTimeLabels(labelCount);
        this.chart.data.datasets[0].data = this.generateChartData(dataCount);
        this.chart.data.datasets[1].data = Array(dataCount).fill(5);
        this.chart.update();
    }
    
    
    getRandomAnomalyType() {
        const types = [
            "Busier than usual",
            "Significant spike detected", 
            "Pattern deviation",
            "Above baseline threshold"
        ];
        return types[Math.floor(Math.random() * types.length)];
    }
    
    // PIZZA REPORTS: Initialize and manage tweet-like updates
    initializePizzaReports() {
        this.tweetTemplates = [
            "🚨 ALERT: Unusual spike detected at {location}. Pizza Index: {index}. #PentagonPizza #SecurityMonitoring",
            "📊 Weekly Analysis: Pizza Index averaged {index} this week. All parameters normal. #DataIntelligence",
            "🏳️‍🌈 Gay Bar Index update: Currently at {gayIndex} - {status}. Correlation analysis ongoing. #DataIntelligence",
            "🔍 Anomaly detected: {anomalyType} at {location}. Investigating patterns. #PizzaSurveillance",
            "✅ System check: All {count} locations reporting normal activity. Pizza Index stable at {index}. #StatusUpdate"
        ];
        
        // Update tweets when significant events occur
        this.lastTweetTime = Date.now();
        this.tweetCooldown = 300000; // 5 minutes between tweets
    }
    
    // Generate and add new tweets based on dashboard activity
    addPizzaReport(type, data = {}) {
        const now = Date.now();
        if (now - this.lastTweetTime < this.tweetCooldown) {
            return; // Too soon for another tweet
        }
        
        let tweetContent = '';
        const timeAgo = this.getRandomTimeAgo();
        
        switch (type) {
            case 'anomaly':
                tweetContent = `🚨 ALERT: Anomaly detected! Pizza Index spiked to ${this.pizzaIndex.toFixed(1)}. Unusual activity patterns observed. #PentagonPizza #Alert`;
                break;
            case 'pizza_update':
                tweetContent = `📊 Pizza Index update: ${this.pizzaIndex.toFixed(1)} (${data.change >= 0 ? '+' : ''}${data.change.toFixed(1)}%). ${this.getPizzaStatus(this.pizzaIndex)} #PizzaIndex`;
                break;
            case 'gay_bar_update':
                tweetContent = `🏳️‍🌈 Gay Bar Index: ${this.gayBarIndex.toFixed(1)} - ${this.getGayBarStatus(this.gayBarIndex)}. Monitoring correlation patterns. #DataIntelligence`;
                break;
            case 'system':
                tweetContent = `✅ System Status: Monitoring ${this.activeLocations} locations. Pizza Index: ${this.pizzaIndex.toFixed(1)}. All systems operational. #StatusUpdate`;
                break;
        }
        
        if (tweetContent) {
            this.insertTweet(tweetContent, timeAgo);
            this.lastTweetTime = now;
        }
    }
    
    getPizzaStatus(index) {
        if (index > 7) return "CRITICAL LEVELS";
        if (index > 5) return "ELEVATED";
        if (index > 3) return "MODERATE";
        return "NORMAL";
    }
    
    getGayBarStatus(index) {
        if (index > 8) return "significantly quieter than usual";
        if (index > 6) return "below normal activity";
        if (index > 4) return "moderate activity levels";
        return "high activity detected";
    }
    
    getRandomTimeAgo() {
        const times = ['2m', '5m', '12m', '25m', '1h', '2h', '3h'];
        return times[Math.floor(Math.random() * times.length)];
    }
    
    insertTweet(content, timeAgo) {
        const tweetsContainer = document.getElementById('tweets-container');
        if (!tweetsContainer) return;
        
        const tweetElement = document.createElement('div');
        tweetElement.className = 'tweet-card';
        tweetElement.innerHTML = `
            <div class="tweet-header">
                <div class="tweet-avatar">🍕</div>
                <div class="tweet-info">
                    <div class="tweet-name">Pentagon Pizza Report</div>
                    <div class="tweet-handle">@PenPizzaReport</div>
                </div>
                <div class="tweet-time">${timeAgo}</div>
            </div>
            <div class="tweet-content">${content}</div>
            <div class="tweet-metrics">
                <span class="tweet-likes">🔄 ${Math.floor(Math.random() * 20)}</span>
                <span class="tweet-retweets">❤️ ${Math.floor(Math.random() * 50)}</span>
            </div>
        `;
        
        // Insert at the top
        tweetsContainer.insertBefore(tweetElement, tweetsContainer.firstChild);
        
        // Fade in effect
        tweetElement.style.opacity = '0';
        setTimeout(() => {
            tweetElement.style.opacity = '1';
            tweetElement.style.transition = 'opacity 0.3s ease';
        }, 100);
        
        // Keep only latest 5 tweets
        while (tweetsContainer.children.length > 5) {
            tweetsContainer.removeChild(tweetsContainer.lastChild);
        }
    }
    
    // Twitter embed functionality removed - using simple link instead
}
// Initialize the dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new SignalSliceMonitor();
});

// Global CSS animations for notifications
const notificationStyles = document.createElement('style');
notificationStyles.textContent = `
    @keyframes slideIn {
        from { transform: translateX(100%); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
    }
    
    @keyframes slideOut {
        from { transform: translateX(0); opacity: 1; }
        to { transform: translateX(100%); opacity: 0; }
    }
    
    .notification.success {
        border-left: 4px solid var(--success-green);
    }
    
    .notification.info {
        border-left: 4px solid var(--primary-blue);
    }
    
    .notification.critical {
        border-left: 4px solid var(--danger-red);
    }
`;
document.head.appendChild(notificationStyles);
















