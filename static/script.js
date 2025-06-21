document.addEventListener('DOMContentLoaded', function() {
    initializeMap();
    
    initializeCharts();
    
    setupEventListeners();
    
    startRealTimeUpdates();
});

function initializeMap() {
    // Pentagon coordinates
    const pentagonCoords = [38.8719, -77.0563];
    
    const map = L.map('map').setView(pentagonCoords, 11);
    
    L.tileLayer('https://tiles.stadiamaps.com/tiles/alidade_smooth_dark/{z}/{x}/{y}{r}.png', {
        attribution: '&copy; <a href="https://stadiamaps.com/">Stadia Maps</a>',
        maxZoom: 18
    }).addTo(map);
    
    // Add Pentagon marker
    const pentagonIcon = L.divIcon({
        className: 'pentagon-marker',
        html: '<div style="background: #dc2626; width: 20px; height: 20px; border-radius: 50%; border: 3px solid white; box-shadow: 0 0 10px rgba(220, 38, 38, 0.8);"></div>',
        iconSize: [20, 20],
        iconAnchor: [10, 10]
    });
    
    L.marker(pentagonCoords, { icon: pentagonIcon })
        .addTo(map)
        .bindPopup('<b>The Pentagon</b><br>Current Activity: HIGH');
    
    // 50-mile radius circle
    L.circle(pentagonCoords, {
        color: '#fbbf24',
        fillColor: '#fbbf24',
        fillOpacity: 0.1,
        radius: 80467 
    }).addTo(map);
    
    generatePizzaLocations(map, pentagonCoords);
}

function generatePizzaLocations(map, center) {
    const pizzaChains = [
        'Domino\'s', 'Pizza Hut', 'Papa John\'s', 'Little Caesars', 
        'Marco\'s Pizza', 'Blaze Pizza', 'Papa Murphy\'s', 'Casey\'s'
    ];
    
    for (let i = 0; i < 127; i++) {
        const angle = Math.random() * 2 * Math.PI;
        const distance = Math.random() * 0.7; // ~50 miles in degrees
        
        const lat = center[0] + (distance * Math.cos(angle));
        const lng = center[1] + (distance * Math.sin(angle));
        
        const activityLevel = Math.random();
        let markerColor, activityText, orderCount;
        
        if (activityLevel > 0.8) {
            markerColor = '#ef4444'; // High activity
            activityText = 'HIGH';
            orderCount = Math.floor(Math.random() * 50) + 20;
        } else if (activityLevel > 0.6) {
            markerColor = '#f59e0b'; // Medium activity
            activityText = 'MEDIUM';
            orderCount = Math.floor(Math.random() * 20) + 5;
        } else {
            markerColor = '#10b981'; // Normal activity
            activityText = 'NORMAL';
            orderCount = Math.floor(Math.random() * 10) + 1;
        }
        
        const pizzaIcon = L.divIcon({
            className: 'pizza-marker',
            html: `<div style="background: ${markerColor}; width: 12px; height: 12px; border-radius: 50%; border: 2px solid white; box-shadow: 0 0 5px rgba(0,0,0,0.5);"></div>`,
            iconSize: [12, 12],
            iconAnchor: [6, 6]
        });
        
        const chain = pizzaChains[Math.floor(Math.random() * pizzaChains.length)];
        
        L.marker([lat, lng], { icon: pizzaIcon })
            .addTo(map)
            .bindPopup(`
                <b>${chain}</b><br>
                Activity: ${activityText}<br>
                Orders (last hour): ${orderCount}<br>
                <small>Last update: ${Math.floor(Math.random() * 15) + 1} min ago</small>
            `);
    }
}

function initializeCharts() {
    const indexCtx = document.getElementById('indexChart').getContext('2d');
    const indexData = generateTimeSeriesData(24);
    
    new Chart(indexCtx, {
        type: 'line',
        data: {
            labels: indexData.labels,
            datasets: [{
                label: 'Pizza Index',
                data: indexData.values,
                borderColor: '#fbbf24',
                backgroundColor: 'rgba(251, 191, 36, 0.1)',
                fill: true,
                tension: 0.4
            }, {
                label: 'Baseline',
                data: Array(24).fill(4.2),
                borderColor: '#94a3b8',
                borderDash: [5, 5],
                fill: false
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    labels: { color: '#f8fafc' }
                }
            },
            scales: {
                x: { 
                    ticks: { color: '#94a3b8' },
                    grid: { color: '#334155' }
                },
                y: { 
                    ticks: { color: '#94a3b8' },
                    grid: { color: '#334155' }
                }
            }
        }
    });
    
    // Order Distribution Chart
    const distCtx = document.getElementById('distributionChart').getContext('2d');
    
    new Chart(distCtx, {
        type: 'doughnut',
        data: {
            labels: ['Domino\'s', 'Pizza Hut', 'Papa John\'s', 'Others'],
            datasets: [{
                data: [35, 28, 20, 17],
                backgroundColor: ['#dc2626', '#fbbf24', '#2563eb', '#10b981'],
                borderWidth: 2,
                borderColor: '#0f172a'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: { color: '#f8fafc' }
                }
            }
        }
    });
}

function generateTimeSeriesData(hours) {
    const labels = [];
    const values = [];
    const now = new Date();
    
    for (let i = hours - 1; i >= 0; i--) {
        const time = new Date(now.getTime() - i * 60 * 60 * 1000);
        labels.push(time.getHours().toString().padStart(2, '0') + ':00');
        
        // Generate realistic pizza index data with spike
        let value = 3 + Math.random() * 2;
        if (i < 3) { // Recent spike
            value += Math.random() * 4;
        }
        values.push(value);
    }
    
    return { labels, values };
}

function setupEventListeners() {
    const fabButton = document.getElementById('fab-main');
    const fabMenu = document.querySelector('.fab-menu');
    
    fabButton.addEventListener('click', () => {
        fabMenu.style.display = fabMenu.style.display === 'flex' ? 'none' : 'flex';
    });
    
    document.querySelectorAll('[data-period]').forEach(button => {
        button.addEventListener('click', (e) => {
            document.querySelectorAll('[data-period]').forEach(b => b.classList.remove('active'));
            e.target.classList.add('active');
            // Update chart data based on period
            const period = e.target.dataset.period;
            console.log('Updating chart for period:', period);
        });
    });
    
    document.getElementById('refresh-map').addEventListener('click', () => {
        console.log('Refreshing map data...');
        showNotification('Map data refreshed', 'success');
    });
    
    document.getElementById('toggle-heatmap').addEventListener('click', () => {
        console.log('Toggling heatmap...');
        showNotification('Heatmap toggled', 'info');
    });
    
    document.querySelectorAll('.nav-link').forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            document.querySelectorAll('.nav-link').forEach(l => l.classList.remove('active'));
            e.target.classList.add('active');
        });
    });
}

function startRealTimeUpdates() {
    setInterval(() => {
        updatePizzaIndex();
        updateLastUpdateTime();
    }, 30000);
    
    // Update last update time every minute
    setInterval(updateLastUpdateTime, 60000);
}

function updatePizzaIndex() {
    const indexElement = document.getElementById('pizza-index');
    const currentValue = parseFloat(indexElement.textContent);
    
    const change = (Math.random() - 0.5) * 0.5;
    const newValue = Math.max(0, currentValue + change);
    
    indexElement.textContent = newValue.toFixed(2);
    
    indexElement.style.transform = 'scale(1.1)';
    setTimeout(() => {
        indexElement.style.transform = 'scale(1)';
    }, 200);
}

function updateLastUpdateTime() {
    const element = document.getElementById('last-update');
    const times = ['1min', '2min', '3min', '1min', '2min'];
    element.textContent = times[Math.floor(Math.random() * times.length)];
}

// Utility functions
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.textContent = message;
    notification.style.cssText = `
        position: fixed;
        top: 100px;
        right: 20px;
        background: var(--bg-darker);
        color: var(--text-light);
        padding: 15px 20px;
        border-radius: 8px;
        border: 1px solid var(--border-gray);
        box-shadow: 0 4px 20px rgba(0,0,0,0.3);
        z-index: 10000;
        animation: slideIn 0.3s ease;
    `;
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.remove();
    }, 3000);
}

// Add CSS animation for notifications
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from { transform: translateX(100%); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
    }
`;
document.head.appendChild(style);