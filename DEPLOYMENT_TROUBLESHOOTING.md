# SignalSlice WebSocket Deployment Troubleshooting

## Current Issue: WebSocket Connection Refused

The error `NS_ERROR_WEBSOCKET_CONNECTION_REFUSED` indicates that the WebSocket connection cannot be established.

## Quick Diagnostic Commands

Run these commands on your server to diagnose the issue:

```bash
# 1. Check if Gunicorn is running
ps aux | grep gunicorn

# 2. Check if app is listening on port 6003
sudo netstat -tlnp | grep 6003

# 3. Check Gunicorn logs
tail -f logs/gunicorn.log

# 4. Test local connection
curl http://localhost:6003/socket.io/?EIO=4&transport=polling

# 5. Check Nginx error logs
sudo tail -f /var/log/nginx/error.log
```

## Common Issues and Solutions

### 1. Gunicorn Not Running
If Gunicorn isn't running or crashes immediately:
```bash
# Run Gunicorn in foreground to see errors
gunicorn --worker-class eventlet -w 1 --bind 127.0.0.1:6003 wsgi:app
```

### 2. Missing Dependencies
Ensure eventlet is installed:
```bash
pip install eventlet flask-socketio gunicorn
```

### 3. Nginx Configuration Not Applied
```bash
# Test Nginx config
sudo nginx -t

# Reload Nginx
sudo nginx -s reload
```

### 4. Firewall Blocking WebSocket
```bash
# Check if port 443 is open
sudo ufw status
```

### 5. SSL Certificate Issues
Make sure your SSL certificates are properly configured in nginx.conf

## Manual Test Deployment

Try this simplified deployment approach:

```bash
# 1. Stop everything
pkill -f gunicorn
pkill -f "python.*app.py"

# 2. Create a test script
cat > test_deploy.py << 'EOF'
from app import app, socketio
import logging

logging.basicConfig(level=logging.INFO)

if __name__ == "__main__":
    socketio.run(app, host='0.0.0.0', port=6003, debug=False)
EOF

# 3. Run directly with Python first
python test_deploy.py

# 4. Test WebSocket connection locally
curl -i http://localhost:6003/socket.io/?EIO=4&transport=polling
```

## Alternative Nginx Configuration

If the current configuration doesn't work, try this simplified version:

```nginx
location /socket.io {
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header Host $http_host;
    proxy_set_header X-NginX-Proxy false;

    proxy_pass http://127.0.0.1:6003;
    proxy_redirect off;

    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
}
```

## Verification Steps

After deployment, verify:

1. **Backend is running**: `curl http://localhost:6003/api/status`
2. **Socket.IO endpoint works**: `curl http://localhost:6003/socket.io/?EIO=4&transport=polling`
3. **Nginx proxies correctly**: `curl https://signalslice.sebastianalexis.com/api/status`
4. **WebSocket upgrade headers**: Use browser dev tools Network tab to check headers

## Emergency Fallback

If WebSocket still doesn't work, Socket.IO will fall back to HTTP long-polling automatically. The app will still function but with slightly higher latency.

## Need More Help?

Check the specific error in:
- Gunicorn logs: `logs/gunicorn.log`
- Nginx error logs: `/var/log/nginx/error.log`
- Browser console for JavaScript errors

The issue is typically one of:
- Process not running on expected port
- Nginx configuration not reloaded
- SSL/proxy header issues
- Missing Python dependencies