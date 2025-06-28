# 🛰️ SignalSlice

**SignalSlice** is a real-time OSINT-inspired monitoring system that tracks spikes in pizza ordering activity near the Pentagon — known colloquially as the "Pentagon Pizza Index" — to detect potential high-level activity. The system features a professional web dashboard with live activity feeds, anomaly detection, and real-time data visualization.

The motivation for this project comes from the legendary Pentagon Pizza Index, where unusual late-night pizza ordering patterns have historically correlated with significant events. When government facilities order pizza late at night, it typically means staff are working overtime on something important, potentially of national significance.

## 🎯 Live Demo

Access the real-time dashboard at: `http://localhost:5000` (when running locally)

---

## 📦 Project Summary

> 🍕 "Where there’s smoke, there’s fire. Where there’s pizza, there’s a meeting."

This project blends humor with open-source intelligence principles to monitor real-time or simulated pizza order data. By analyzing trends and alerting users to anomalies, SignalSlice offers a lighthearted but insightful window into late-night activity that could signal something bigger.

---

## 🚀 Features

### �️ Real-time Web Dashboard
- **Live Activity Feed**: Stream of all scanner actions (scraping, analyzing, detecting, scheduling)
- **Pentagon Pizza Index**: Real-time index with trend visualization and anomaly highlighting
- **Interactive Map**: Monitoring zone visualization with threat level indicators
- **System Status**: Live monitoring of all system components and data sources
- **Professional UI**: Military-inspired surveillance interface with modern animations

### 🔍 Advanced Monitoring
- **Real-time Data Collection**: Hourly scraping of Google Maps popular times data
- **Live Anomaly Detection**: Statistical analysis comparing current activity to historical baselines
- **Comprehensive Logging**: Detailed activity tracking for every system action
- **Multiple Data Sources**: Google Maps integration with extensible architecture
- **Smart Scheduling**: Automated hourly scans with manual trigger capability

### 📊 Data & Analytics
- **Historical Analysis**: Pattern recognition across years of monitoring data
- **Baseline Modeling**: Day-of-week and hour-specific baseline calculations
- **Anomaly Alerts**: Real-time notifications when unusual patterns are detected
- **Trend Visualization**: Interactive charts showing pizza index over time
- **Export Capabilities**: CSV data export for further analysis

---

## 📡 How It Works

### 🔄 Automated Scanning Process
1. **Hourly Data Collection**: The system automatically scrapes Google Maps popular times data every hour
2. **Live Data Priority**: Prioritizes real-time "Currently X% busy" data over historical patterns
3. **Baseline Comparison**: Compares current activity against day-specific historical averages
4. **Anomaly Detection**: Flags locations with activity 25%+ above expected baseline
5. **Real-time Alerts**: Instantly broadcasts anomalies via web dashboard and activity feed

### 🎯 Detection Algorithm
- **Data Sources**: Google Maps popular times for pizza restaurants within 50-mile radius of Pentagon
- **Baseline Calculation**: Rolling averages based on day-of-week and hour-of-day patterns
- **Threshold Logic**: Configurable sensitivity with 25% default threshold for anomaly detection
- **Confidence Scoring**: Higher confidence for live data vs. historical/predicted data
- **Real-time Processing**: Immediate analysis and broadcasting of results

---

## 🛠️ Development Setup

### Prerequisites
- Python 3.12+ (recommended)
- Node.js (for frontend dependencies, if needed)
- Git

### Quick Start

1. **Clone the repository**
```bash
git clone https://github.com/your-username/signalslice.git
cd signalslice
```

2. **Set up Python virtual environment**
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Install Playwright browsers** (required for web scraping)
```bash
playwright install
```

5. **Run the application**
```bash
python app.py
```

6. **Access the dashboard**
   - Open your browser to `http://localhost:5000`
   - The scanner will start automatically and begin hourly monitoring
   - Manual scans can be triggered from the dashboard

### 🏗️ Project Structure

```
signalslice/
├── app.py                          # Main Flask application with SocketIO
├── run_scanner.py                  # Legacy CLI scanner entry point
├── scheduler.py                    # Legacy scheduler (now integrated into app.py)
├── requirements.txt                # Python dependencies
├── templates/
│   └── index.html                  # Main dashboard HTML
├── static/
│   ├── script.js                   # Dashboard JavaScript (real-time updates)
│   └── style.css                   # Professional surveillance styling
├── scraping/
│   ├── gmapsScrape.py             # Google Maps scraping logic
│   └── gmapsScraper.py            # Alternative scraper implementation
├── script/
│   └── anomalyDetect.py           # Anomaly detection algorithms
└── data/                          # Scraped data and logs
    ├── current_hour_*.csv         # Hourly scan results
    └── signalslice_popular_times.csv  # Historical baseline data
```

### 🔧 Configuration

#### Environment Variables
```bash
# Optional: Create .env file for configuration
FLASK_ENV=development
FLASK_DEBUG=False
SCAN_INTERVAL_MINUTES=60           # Hourly scans (default)
ANOMALY_THRESHOLD_PERCENT=25       # 25% above baseline triggers alert
```

#### Adding New Monitoring Locations
Edit `scraping/gmapsScrape.py` and add Google Maps URLs to the `RESTAURANT_URLS` list:

```python
RESTAURANT_URLS = [
    "https://maps.app.goo.gl/KqSr8hH5GV4ZGJP27",  # Default location
    "https://maps.app.goo.gl/YOUR_NEW_LOCATION",   # Add your URLs here
    # ... more locations
]
```

### 🧪 Development Commands

#### Run Development Server
```bash
python app.py
# Dashboard: http://localhost:5000
# API Status: http://localhost:5000/api/status
# Activity Feed: http://localhost:5000/api/activity_feed
```

#### Manual Scanner (CLI mode)
```bash
python run_scanner.py
```

#### Trigger Manual Scan
```bash
# Via browser:
http://localhost:5000/api/trigger_scan

# Via curl:
curl http://localhost:5000/api/trigger_scan
```

#### Test Anomaly Detection
```bash
cd script
python anomalyDetect.py
```

### 📊 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Main dashboard |
| `/api/status` | GET | System status and statistics |
| `/api/activity_feed` | GET | Current activity feed |
| `/api/trigger_scan` | GET | Trigger manual scan |
| `/api/start_scanner` | GET | Start automated scanner |
| `/api/stop_scanner` | GET | Stop automated scanner |

### 🔌 WebSocket Events

| Event | Direction | Description |
|-------|-----------|-------------|
| `connect` | Client → Server | Client connects to dashboard |
| `initial_state` | Server → Client | Initial dashboard data |
| `activity_update` | Server → Client | New activity feed item |
| `anomaly_detected` | Server → Client | Anomaly alert |
| `scanning_start` | Server → Client | Scan cycle begins |
| `scanning_complete` | Server → Client | Scan cycle ends |
| `manual_scan` | Client → Server | Trigger manual scan |

---

## 🤝 Contributing

### Development Workflow

1. **Fork and clone** the repository
2. **Create a feature branch**: `git checkout -b feature/amazing-feature`
3. **Set up development environment** following the setup guide above
4. **Make your changes** with proper testing
5. **Run the application** to ensure everything works
6. **Commit your changes**: `git commit -m 'Add amazing feature'`
7. **Push to the branch**: `git push origin feature/amazing-feature`
8. **Open a Pull Request**

### Code Style
- **Python**: Follow PEP 8 guidelines
- **JavaScript**: Use ES6+ features, consistent indentation
- **HTML/CSS**: Maintain professional surveillance theme
- **Comments**: Document complex logic and API integrations

### Testing
- Test manual and automatic scanning
- Verify real-time dashboard updates
- Ensure anomaly detection works correctly
- Check cross-browser compatibility

---

## 📈 Roadmap

### Immediate Improvements
- [ ] Email notification system for anomaly alerts
- [ ] Historical data visualization with longer time ranges
- [ ] Mobile-responsive dashboard design
- [ ] Additional data sources (Yelp, delivery apps)

### Advanced Features
- [ ] Machine learning-based anomaly detection
- [ ] Multi-location correlation analysis
- [ ] Webhook integrations (Discord, Slack)
- [ ] Advanced statistical modeling
- [ ] Geographic heat map visualization

---

## ⚖️ Legal & Ethics

This project is for **educational and research purposes only**. All data is collected from publicly available sources (Google Maps popular times). Users are responsible for:

- Respecting rate limits and terms of service
- Using data ethically and responsibly
- Not using the system for actual surveillance or malicious purposes
- Understanding that correlations do not imply causation

---

## 📄 License

MIT License - see LICENSE file for details

---

## 🙏 Acknowledgments
- Inspired by the legendary Pentagon Pizza Index OSINT technique
- Built with Flask, SocketIO, Playwright, and modern web technologies
- Thanks to the open-source community for the amazing tools and libraries

## 🔧 Technology Stack

### Backend
- **Flask**: Web framework and API server
- **Flask-SocketIO**: Real-time WebSocket communication
- **Playwright**: Automated browser for web scraping
- **Pytz**: Timezone handling for EST operations
- **Python 3.12+**: Core runtime environment

### Frontend
- **HTML5**: Semantic markup with modern features
- **CSS3**: Professional surveillance-style theming with animations
- **JavaScript ES6+**: Real-time dashboard functionality
- **Chart.js**: Data visualization and trend analysis
- **Leaflet**: Interactive mapping components
- **Socket.IO Client**: Real-time communication with backend

### Data & Storage
- **CSV Files**: Structured data storage for historical analysis
- **JSON APIs**: Real-time data exchange format
- **Google Maps**: Primary data source for popular times

---

*Stay vigilant! 🍕🛰️*











