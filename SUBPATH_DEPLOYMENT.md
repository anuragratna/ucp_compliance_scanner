# Deployment: Same Domain Integration

Yes, you can absolutely deploy this on the same domain (`https://openquest.solutions/testAgenticReadiness`). 

To do this, you typically run this Python application on a different port (e.g., `5002`) on your server and use a **Reverse Proxy** (like Nginx or Apache) to route traffic from the specific path `/testAgenticReadiness` to this application.

## 1. Run the Python Application

Ensure the application is running on your server, listening on a local port (e.g., 5002).

```bash
# Using uv (recommended)
cd /path/to/ucp_compliance_scanner
uv run gunicorn --bind 127.0.0.1:5002 --workers 2 --timeout 120 app:app
```

## 2. Configure Your Web Server (Reverse Proxy)

Depending on what software runs your main website (`openquest.solutions`), choose the configuration below.

### Option A: Nginx (Common)

Edit your site's configuration file (usually in `/etc/nginx/sites-available/openquest.solutions`):

```nginx
server {
    listen 80;
    server_name openquest.solutions;

    # ... your existing website config ...

    # Add this block for the scanner
    location /testAgenticReadiness/ {
        # Trailing slash is important to strip the path prefix
        proxy_pass http://127.0.0.1:5002/; 
        
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

**Important**: 
- Note the trailing slash in `location /testAgenticReadiness/`.
- Note the trailing slash in `proxy_pass http://127.0.0.1:5002/;`.
- This tells Nginx: "When a user visits `/testAgenticReadiness/foo`, send the request to `http://localhost:5002/foo`" (stripping the prefix).

### Option B: Apache (httpd)

Edit your VirtualHost configuration:

```apache
<VirtualHost *:80>
    ServerName openquest.solutions

    # ... your existing website config ...

    <Location "/testAgenticReadiness/">
        ProxyPreserveHost On
        ProxyPass http://127.0.0.1:5002/
        ProxyPassReverse http://127.0.0.1:5002/
    </Location>
</VirtualHost>
```

## 3. Persistent Hosting (Systemd)

To ensure the Python app keeps running even if you close the terminal or restart the server, create a system service.

Create `/etc/systemd/system/ucp-scanner.service`:

```ini
[Unit]
Description=UCP Compliance Scanner
After=network.target

[Service]
User=root
WorkingDirectory=/path/to/ucp_compliance_scanner
# Ensure 'uv' or 'gunicorn' is in the path, or use absolute paths for the executable
ExecStart=/path/to/uv run gunicorn --bind 127.0.0.1:5002 --workers 2 app:app
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start it:
```bash
sudo systemctl enable ucp-scanner
sudo systemctl start ucp-scanner
```
