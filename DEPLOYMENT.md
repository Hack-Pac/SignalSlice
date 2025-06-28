# SignalSlice Production Deployment Guide

## Prerequisites

- Python 3.8+
- PostgreSQL or SQLite database
- Redis (optional, for caching)
- Nginx or Apache (for reverse proxy)

## Environment Setup

1. **Clone the repository**
```bash
git clone <your-repo-url>
cd SignalSlice
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
playwright install chromium
```

4. **Set environment variables (Optional)**
Create a `.env` file if you want Twitter integration:
```
TWITTER_BEARER_TOKEN=<your-twitter-token>
```

No other configuration is required - the app auto-generates necessary keys.

## Security Configuration

1. **Update CORS settings** in `app.py`:
```python
socketio = SocketIO(app, cors_allowed_origins=["https://yourdomain.com"])
```

2. **Update CSP headers** in `app.py` to match your domain

3. **Configure HTTPS** - Always use HTTPS in production

## Database Migration

For production, migrate from CSV to a proper database:
1. Install PostgreSQL
2. Update connection strings
3. Run migration scripts

## Running in Production

### Option 1: Gunicorn with Eventlet
```bash
gunicorn --worker-class eventlet -w 1 --bind 0.0.0.0:5000 app:app
```

### Option 2: Systemd Service
Create `/etc/systemd/system/signalslice.service`:
```ini
[Unit]
Description=SignalSlice Pizza Monitor
After=network.target

[Service]
User=www-data
WorkingDirectory=/path/to/SignalSlice
Environment="PATH=/path/to/venv/bin"
ExecStart=/path/to/venv/bin/gunicorn --worker-class eventlet -w 1 --bind 127.0.0.1:5000 app:app
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable signalslice
sudo systemctl start signalslice
```

## Nginx Configuration

```nginx
server {
    listen 80;
    server_name yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /socket.io {
        proxy_pass http://127.0.0.1:5000/socket.io;
        proxy_http_version 1.1;
        proxy_buffering off;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }
}
```

## Monitoring

1. **Logs**: Check `/var/log/signalslice.log`
2. **Status**: `sudo systemctl status signalslice`
3. **Metrics**: Consider adding Prometheus/Grafana

## Backup

Regular backups of:
- Database
- Configuration files
- Historical data CSVs

## Maintenance

1. **Update dependencies regularly**
2. **Monitor disk space** (CSV files can accumulate)
3. **Implement log rotation**
4. **Set up alerts for anomalies**

## Troubleshooting

- **WebSocket issues**: Ensure Nginx is configured for WebSocket upgrade
- **CORS errors**: Update allowed origins in app.py
- **Memory issues**: Implement data retention policies
- **Performance**: Consider Redis for caching