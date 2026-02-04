# HTTPS/SSL Deployment Guide

## 🎯 Overview

Complete guide for deploying YKS Hazırlık Platform with HTTPS/SSL encryption using Let's Encrypt certificates and Nginx/Caddy reverse proxy.

## 📋 Prerequisites

- Domain name pointing to your server (e.g., yks.example.com)
- Server with root/sudo access
- Ports 80 and 443 open in firewall
- FastAPI backend running on port 8000
- React frontend running on port 3002 (or static build)

## 🚀 Quick Start - Let's Encrypt + Nginx

### Option 1: Automated Setup with Certbot

#### Step 1: Install Nginx and Certbot

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install nginx certbot python3-certbot-nginx

# CentOS/RHEL
sudo yum install nginx certbot python3-certbot-nginx
```

#### Step 2: Configure Nginx (Initial HTTP Config)

Create [/etc/nginx/sites-available/yks-platform](file:///etc/nginx/sites-available/yks-platform):

```nginx
# Backend API
upstream backend_api {
    server 127.0.0.1:8000;
    keepalive 32;
}

# Frontend (if using separate server)
upstream frontend_app {
    server 127.0.0.1:3002;
    keepalive 32;
}

server {
    listen 80;
    server_name yks.example.com www.yks.example.com;

    # Allow certbot verification
    location /.well-known/acme-challenge/ {
        root /var/www/html;
    }

    # Backend API
    location /api/ {
        proxy_pass http://backend_api;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";

        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Docs
    location /docs {
        proxy_pass http://backend_api;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # Frontend (option 1: proxy to dev server)
    location / {
        proxy_pass http://frontend_app;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    # Frontend (option 2: serve static build)
    # location / {
    #     root /var/www/yks-platform/frontend/dist;
    #     try_files $uri $uri/ /index.html;
    # }
}
```

Enable the site:

```bash
sudo ln -s /etc/nginx/sites-available/yks-platform /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

#### Step 3: Obtain SSL Certificate

```bash
# Obtain certificate and auto-configure nginx
sudo certbot --nginx -d yks.example.com -d www.yks.example.com

# Follow prompts:
# - Enter email address (for renewal notifications)
# - Agree to terms of service
# - Choose whether to redirect HTTP to HTTPS (recommended: yes)
```

**Certbot will automatically**:
- Obtain certificate from Let's Encrypt
- Update nginx configuration with SSL
- Set up HTTP → HTTPS redirect
- Configure auto-renewal

#### Step 4: Verify SSL Configuration

```bash
# Check nginx configuration
sudo nginx -t

# Restart nginx
sudo systemctl restart nginx

# Test auto-renewal
sudo certbot renew --dry-run
```

Visit https://yks.example.com and verify:
- Green padlock in browser
- Valid certificate
- HTTP redirects to HTTPS

### Option 2: Manual SSL Configuration

If certbot doesn't auto-configure, update nginx manually:

```nginx
server {
    listen 80;
    server_name yks.example.com www.yks.example.com;

    # Redirect all HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yks.example.com www.yks.example.com;

    # SSL Certificate
    ssl_certificate /etc/letsencrypt/live/yks.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yks.example.com/privkey.pem;

    # SSL Configuration (Mozilla Intermediate)
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;

    # HSTS (already in backend security headers)
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;

    # SSL Session Cache
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;

    # OCSP Stapling
    ssl_stapling on;
    ssl_stapling_verify on;
    ssl_trusted_certificate /etc/letsencrypt/live/yks.example.com/chain.pem;
    resolver 8.8.8.8 8.8.4.4 valid=300s;
    resolver_timeout 5s;

    # Backend API
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto https;

        # WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";

        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Docs
    location /docs {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-Proto https;
    }

    # Frontend
    location / {
        root /var/www/yks-platform/frontend/dist;
        try_files $uri $uri/ /index.html;

        # Cache static assets
        location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
            expires 1y;
            add_header Cache-Control "public, immutable";
        }
    }

    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_types text/plain text/css text/xml text/javascript application/json application/javascript application/xml+rss;
    gzip_min_length 1000;

    # Security headers (additional to backend)
    add_header X-Frame-Options "DENY" always;
    add_header X-Content-Type-Options "nosniff" always;
}
```

## 🚀 Alternative: Caddy (Automatic HTTPS)

Caddy automatically handles SSL certificates with zero configuration!

### Step 1: Install Caddy

```bash
# Ubuntu/Debian
sudo apt install -y debian-keyring debian-archive-keyring apt-transport-https
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | sudo gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' | sudo tee /etc/apt/sources.list.d/caddy-stable.list
sudo apt update
sudo apt install caddy
```

### Step 2: Configure Caddy

Create `/etc/caddy/Caddyfile`:

```caddy
yks.example.com www.yks.example.com {
    # Automatic HTTPS with Let's Encrypt
    # No certificate configuration needed!

    # Backend API
    reverse_proxy /api/* 127.0.0.1:8000
    reverse_proxy /docs 127.0.0.1:8000

    # Frontend
    root * /var/www/yks-platform/frontend/dist
    file_server

    # SPA routing (try files, fallback to index.html)
    @notStatic {
        not path /api/* /docs /assets/*
        file {
            try_files {path} /index.html
        }
    }
    rewrite @notStatic /index.html

    # Gzip compression
    encode gzip zstd

    # Security headers
    header {
        Strict-Transport-Security "max-age=31536000; includeSubDomains; preload"
        X-Frame-Options "DENY"
        X-Content-Type-Options "nosniff"
        X-XSS-Protection "1; mode=block"
    }

    # Cache static assets
    @static {
        path /assets/* *.js *.css *.png *.jpg *.jpeg *.gif *.ico *.svg *.woff *.woff2
    }
    header @static Cache-Control "public, max-age=31536000, immutable"

    # Logging
    log {
        output file /var/log/caddy/yks-platform.log
        format json
    }
}
```

### Step 3: Start Caddy

```bash
sudo systemctl enable caddy
sudo systemctl start caddy

# Caddy automatically:
# - Obtains SSL certificate
# - Redirects HTTP → HTTPS
# - Renews certificates
# - Handles OCSP stapling
```

## 🔒 SSL/TLS Best Practices

### 1. Use Strong Ciphers

```nginx
# Nginx
ssl_protocols TLSv1.2 TLSv1.3;
ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384;
ssl_prefer_server_ciphers off;
```

### 2. Enable HSTS

```nginx
# Already enabled in backend/core/security_headers.py
# But add to nginx for non-API requests
add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;
```

### 3. OCSP Stapling

```nginx
# Nginx
ssl_stapling on;
ssl_stapling_verify on;
ssl_trusted_certificate /etc/letsencrypt/live/yks.example.com/chain.pem;
```

### 4. Perfect Forward Secrecy

```nginx
# Use ECDHE ciphers (already in config above)
ssl_ciphers ECDHE-...;
```

### 5. HTTP/2 Support

```nginx
# Enable HTTP/2
listen 443 ssl http2;
```

## 🔧 Certificate Renewal

### Automatic Renewal (Certbot)

Certbot sets up auto-renewal via systemd timer:

```bash
# Check renewal timer status
sudo systemctl status certbot.timer

# Test renewal
sudo certbot renew --dry-run

# Force renewal (if needed)
sudo certbot renew --force-renewal
```

### Manual Renewal

```bash
# Renew all certificates
sudo certbot renew

# Reload nginx
sudo systemctl reload nginx
```

### Renewal Monitoring

Add to crontab:

```bash
# Check certificate expiry daily
0 0 * * * certbot renew --quiet --post-hook "systemctl reload nginx"
```

## 🧪 SSL Testing

### Test SSL Configuration

```bash
# Using openssl
openssl s_client -connect yks.example.com:443 -servername yks.example.com

# Check certificate expiry
openssl s_client -connect yks.example.com:443 -servername yks.example.com 2>/dev/null | openssl x509 -noout -dates
```

### Online SSL Testing Tools

1. **SSL Labs**: https://www.ssllabs.com/ssltest/
   - Target grade: A or A+
   - Check for protocol support, cipher strength, certificate issues

2. **Security Headers**: https://securityheaders.com/
   - Verify security headers (HSTS, CSP, X-Frame-Options, etc.)
   - Target grade: A or A+

3. **Mozilla Observatory**: https://observatory.mozilla.org/
   - Comprehensive security scan
   - Target score: 90+

## 📱 Update Application Configuration

### Backend (.env.production)

```bash
# Force HTTPS
ENVIRONMENT=production
ALLOWED_HOSTS=yks.example.com,www.yks.example.com

# CORS with HTTPS
CORS_ORIGINS=https://yks.example.com,https://www.yks.example.com

# Session cookies (secure flag)
SESSION_COOKIE_SECURE=true
SESSION_COOKIE_HTTPONLY=true
SESSION_COOKIE_SAMESITE=lax

# Trust proxy headers
TRUST_PROXY_HEADERS=true
```

### Frontend (.env.production)

```bash
VITE_API_URL=https://yks.example.com/api
VITE_WS_URL=wss://yks.example.com/ws
```

### Update FastAPI to Trust Proxy

Update [backend/main.py](backend/main.py):

```python
from fastapi import FastAPI
from starlette.middleware.trustedhost import TrustedHostMiddleware

app = FastAPI()

# Trust proxy (nginx/caddy)
if os.getenv('ENVIRONMENT') == 'production':
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=[
            'yks.example.com',
            'www.yks.example.com'
        ]
    )
```

## 🔍 Troubleshooting

### Certificate Not Trusted

```bash
# Check certificate chain
openssl s_client -connect yks.example.com:443 -showcerts

# Verify fullchain.pem includes intermediate certs
cat /etc/letsencrypt/live/yks.example.com/fullchain.pem
```

### HTTP Not Redirecting to HTTPS

```bash
# Check nginx redirect config
curl -I http://yks.example.com
# Should see: Location: https://yks.example.com/

# Test redirect
curl -L http://yks.example.com
```

### Mixed Content Warnings

Check browser console for HTTP resources loaded on HTTPS page:

```javascript
// Fix: Update frontend to use HTTPS or relative URLs
// Bad:  http://example.com/api/data
// Good: https://example.com/api/data
// Good: /api/data (relative)
```

### Certificate Renewal Fails

```bash
# Check certbot logs
sudo tail -f /var/log/letsencrypt/letsencrypt.log

# Common issues:
# - Port 80 not accessible (check firewall)
# - Nginx serving wrong config (check sites-enabled)
# - Domain DNS not pointing to server
```

### HSTS Errors

```bash
# Clear HSTS cache in browser:
# Chrome: chrome://net-internals/#hsts → Delete domain
# Firefox: Settings → Privacy → Clear Data → Select "Site settings"
```

## 🎯 Security Checklist

Use this checklist to verify SSL/HTTPS setup:

### Certificate
- [ ] Valid SSL certificate installed
- [ ] Certificate not expired (check `openssl x509 -dates`)
- [ ] Certificate matches domain name
- [ ] Full certificate chain included

### Protocol
- [ ] TLS 1.2 and 1.3 enabled
- [ ] TLS 1.0 and 1.1 disabled
- [ ] HTTP redirects to HTTPS
- [ ] HSTS header present

### Ciphers
- [ ] Strong ciphers only (ECDHE)
- [ ] Weak ciphers disabled (RC4, 3DES)
- [ ] Perfect Forward Secrecy enabled

### Headers
- [ ] Strict-Transport-Security header
- [ ] X-Frame-Options header
- [ ] X-Content-Type-Options header
- [ ] Content-Security-Policy header

### Testing
- [ ] SSL Labs grade A or A+
- [ ] Security Headers grade A or A+
- [ ] No mixed content warnings
- [ ] Certificate auto-renewal working

## 📊 Monitoring SSL

### Certificate Expiry Monitoring

Add to [monitoring/prometheus/alerts/ssl_alerts.yml](monitoring/prometheus/alerts/ssl_alerts.yml):

```yaml
groups:
  - name: ssl_certificate
    interval: 1h
    rules:
      - alert: SSLCertificateExpiringSoon
        expr: ssl_certificate_expiry_days < 30
        for: 1h
        labels:
          severity: warning
        annotations:
          summary: "SSL certificate expiring soon"
          description: "Certificate expires in {{ $value }} days"

      - alert: SSLCertificateExpired
        expr: ssl_certificate_expiry_days < 0
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "SSL certificate EXPIRED"
          description: "Certificate expired {{ $value }} days ago"
```

### Monitor with Script

Create [scripts/check_ssl_expiry.sh](scripts/check_ssl_expiry.sh):

```bash
#!/bin/bash

DOMAIN="yks.example.com"
EXPIRY=$(echo | openssl s_client -servername $DOMAIN -connect $DOMAIN:443 2>/dev/null | openssl x509 -noout -enddate | cut -d= -f2)
EXPIRY_EPOCH=$(date -d "$EXPIRY" +%s)
NOW_EPOCH=$(date +%s)
DAYS_LEFT=$(( ($EXPIRY_EPOCH - $NOW_EPOCH) / 86400 ))

echo "ssl_certificate_expiry_days{domain=\"$DOMAIN\"} $DAYS_LEFT"

if [ $DAYS_LEFT -lt 30 ]; then
    echo "WARNING: Certificate expires in $DAYS_LEFT days!"
    exit 1
fi
```

## 📚 Additional Resources

- [Let's Encrypt Documentation](https://letsencrypt.org/docs/)
- [Nginx SSL Configuration Generator](https://ssl-config.mozilla.org/)
- [Caddy Documentation](https://caddyserver.com/docs/)
- [SSL/TLS Best Practices](https://github.com/ssllabs/research/wiki/SSL-and-TLS-Deployment-Best-Practices)

---

**Last Updated**: 2025-11-04
**Version**: 1.0.0
**Status**: Production Ready ✅
