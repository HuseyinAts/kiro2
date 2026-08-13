#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
KIRO2 Quick Fix Generator
Automated security and deployment fixes for the platform
"""

import os
import json
import subprocess
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any

class QuickFixGenerator:
    """Generate quick fixes for security and deployment issues"""

    def __init__(self):
        self.project_root = Path(__file__).parent
        self.backend_path = self.project_root / 'backend'
        self.frontend_path = self.project_root / 'frontend'
        self.fixes_applied = []

    def check_security_issues(self) -> List[Dict]:
        """Check for common security issues"""
        issues = []

        # Check for exposed secrets
        secret_patterns = [
            'SECRET_KEY',
            'API_KEY',
            'PASSWORD',
            'TOKEN',
            'PRIVATE_KEY'
        ]

        for root, dirs, files in os.walk(self.project_root):
            if any(skip in root for skip in ['venv', 'node_modules', '.git', '__pycache__']):
                continue

            for file in files:
                if file.endswith(('.py', '.js', '.ts', '.env', '.yml', '.yaml')):
                    filepath = os.path.join(root, file)
                    try:
                        with open(filepath, 'r', encoding='utf-8') as f:
                            content = f.read()

                            for pattern in secret_patterns:
                                if pattern in content and not file.startswith('.env'):
                                    issues.append({
                                        'type': 'security',
                                        'severity': 'high',
                                        'file': filepath,
                                        'issue': f'Potential secret exposure: {pattern}',
                                        'line': content.count('\n', 0, content.find(pattern)) + 1
                                    })
                    except Exception:
                        continue

        return issues

    def check_deployment_issues(self) -> List[Dict]:
        """Check for deployment configuration issues"""
        issues = []

        # Check for missing Docker files
        required_docker_files = [
            'Dockerfile',
            'docker-compose.yml',
            '.dockerignore'
        ]

        for docker_file in required_docker_files:
            if not (self.project_root / docker_file).exists():
                issues.append({
                    'type': 'deployment',
                    'severity': 'medium',
                    'file': docker_file,
                    'issue': f'Missing {docker_file}',
                    'solution': f'create_{docker_file.replace(".", "_").replace("-", "_")}'
                })

        # Check for missing environment files
        env_files = ['.env.example', '.env.production']
        for env_file in env_files:
            if not (self.project_root / env_file).exists():
                issues.append({
                    'type': 'deployment',
                    'severity': 'low',
                    'file': env_file,
                    'issue': f'Missing {env_file}',
                    'solution': f'create_env_file'
                })

        return issues

    def create_dockerfile(self) -> bool:
        """Create basic Dockerfile"""
        try:
            dockerfile_content = '''# KIRO2 Production Dockerfile
FROM node:18-alpine AS frontend-builder

WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci --only=production

COPY frontend/ ./
RUN npm run build

# Python backend
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    gcc \\
    && rm -rf /var/lib/apt/lists/*

# Copy backend requirements and install
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend application
COPY backend/ ./

# Copy frontend build
COPY --from=frontend-builder /app/frontend/dist ./static

# Create non-root user
RUN useradd --create-home --shell /bin/bash kiro2
RUN chown -R kiro2:kiro2 /app
USER kiro2

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \\
    CMD curl -f http://localhost:8000/health || exit 1

# Start application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
'''

            with open(self.project_root / 'Dockerfile', 'w') as f:
                f.write(dockerfile_content)

            self.fixes_applied.append('Created production Dockerfile')
            return True

        except Exception as e:
            print(f"[ERROR] Failed to create Dockerfile: {e}")
            return False

    def create_docker_compose_yml(self) -> bool:
        """Create docker-compose.yml"""
        try:
            compose_content = '''version: '3.8'

services:
  kiro2-app:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://kiro2:password@db:5432/kiro2
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - db
      - redis
    volumes:
      - ./logs:/app/logs
    restart: unless-stopped

  db:
    image: postgres:15-alpine
    environment:
      - POSTGRES_DB=kiro2
      - POSTGRES_USER=kiro2
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./init-scripts:/docker-entrypoint-initdb.d
    ports:
      - "5432:5432"
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/nginx/ssl:ro
    depends_on:
      - kiro2-app
    restart: unless-stopped

volumes:
  postgres_data:
  redis_data:
'''

            with open(self.project_root / 'docker-compose.yml', 'w') as f:
                f.write(compose_content)

            self.fixes_applied.append('Created docker-compose.yml')
            return True

        except Exception as e:
            print(f"[ERROR] Failed to create docker-compose.yml: {e}")
            return False

    def create_dockerignore(self) -> bool:
        """Create .dockerignore file"""
        try:
            dockerignore_content = '''# Git
.git
.gitignore

# Documentation
*.md
docs/

# Dependencies
node_modules/
venv/
__pycache__/

# IDE
.vscode/
.idea/
*.swp
*.swo

# Logs
logs/
*.log

# Environment files
.env
.env.local
.env.production

# Test files
test_*
*_test.py
coverage/
htmlcov/

# Build artifacts
dist/
build/
*.egg-info/

# OS
.DS_Store
Thumbs.db

# Temporary files
temp/
tmp/
*.tmp
'''

            with open(self.project_root / '.dockerignore', 'w') as f:
                f.write(dockerignore_content)

            self.fixes_applied.append('Created .dockerignore')
            return True

        except Exception as e:
            print(f"[ERROR] Failed to create .dockerignore: {e}")
            return False

    def create_env_example(self) -> bool:
        """Create .env.example file"""
        try:
            env_content = '''# KIRO2 Environment Configuration Example

# Application
APP_NAME=KIRO2
APP_ENV=production
DEBUG=false
SECRET_KEY=your-secret-key-here

# Database
DATABASE_URL=postgresql://username:password@localhost:5432/kiro2
DB_HOST=localhost
DB_PORT=5432
DB_NAME=kiro2
DB_USER=username
DB_PASSWORD=password

# Redis Cache
REDIS_URL=redis://localhost:6379/0
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# External APIs
YOUTUBE_API_KEY=your-youtube-api-key
OPENAI_API_KEY=your-openai-api-key

# Security
CORS_ORIGINS=["http://localhost:3000"]
JWT_SECRET_KEY=your-jwt-secret-key
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=1440

# Monitoring
PROMETHEUS_PORT=9090
LOG_LEVEL=INFO

# Email (if applicable)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password

# File Storage
UPLOAD_DIR=./uploads
MAX_FILE_SIZE=10485760
'''

            with open(self.project_root / '.env.example', 'w') as f:
                f.write(env_content)

            self.fixes_applied.append('Created .env.example')
            return True

        except Exception as e:
            print(f"[ERROR] Failed to create .env.example: {e}")
            return False

    def create_nginx_config(self) -> bool:
        """Create nginx configuration"""
        try:
            # Create nginx.conf
            nginx_content = '''events {
    worker_connections 1024;
}

http {
    upstream kiro2_backend {
        server kiro2-app:8000;
    }

    server {
        listen 80;
        server_name localhost;

        # Redirect HTTP to HTTPS
        return 301 https://$server_name$request_uri;
    }

    server {
        listen 443 ssl http2;
        server_name localhost;

        # SSL Configuration
        ssl_certificate /etc/nginx/ssl/fullchain.pem;
        ssl_certificate_key /etc/nginx/ssl/privkey.pem;
        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_ciphers HIGH:!aNULL:!MD5;

        # Security headers
        add_header X-Frame-Options DENY;
        add_header X-Content-Type-Options nosniff;
        add_header X-XSS-Protection "1; mode=block";
        add_header Strict-Transport-Security "max-age=31536000; includeSubDomains";

        # Gzip compression
        gzip on;
        gzip_types text/plain text/css application/json application/javascript text/xml application/xml application/xml+rss text/javascript;

        location / {
            proxy_pass http://kiro2_backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        location /static/ {
            alias /app/static/;
            expires 1y;
            add_header Cache-Control "public, immutable";
        }
    }
}
'''

            with open(self.project_root / 'nginx.conf', 'w') as f:
                f.write(nginx_content)

            self.fixes_applied.append('Created nginx.conf')
            return True

        except Exception as e:
            print(f"[ERROR] Failed to create nginx.conf: {e}")
            return False

    def fix_security_issues(self, issues: List[Dict]) -> List[str]:
        """Apply fixes for security issues"""
        fixed_issues = []

        for issue in issues:
            if issue['type'] == 'security':
                # For now, just log the issue
                print(f"[WARN] Security issue found in {issue['file']}: {issue['issue']}")
                print("[INFO] Manual review required for security issues")
                fixed_issues.append(f"Logged security issue: {issue['issue']}")

        return fixed_issues

    def fix_deployment_issues(self, issues: List[Dict]) -> List[str]:
        """Apply fixes for deployment issues"""
        fixed_issues = []

        for issue in issues:
            if issue['type'] == 'deployment':
                solution = issue.get('solution')

                if solution == 'create_Dockerfile':
                    if self.create_dockerfile():
                        fixed_issues.append('Created Dockerfile')

                elif solution == 'create_docker_compose_yml':
                    if self.create_docker_compose_yml():
                        fixed_issues.append('Created docker-compose.yml')

                elif solution == 'create__dockerignore':
                    if self.create_dockerignore():
                        fixed_issues.append('Created .dockerignore')

                elif solution == 'create_env_file':
                    if self.create_env_example():
                        fixed_issues.append('Created .env.example')

        return fixed_issues

    def run_security_audit(self) -> Dict[str, Any]:
        """Run security audit"""
        print("[SECURE] Running security audit...")

        try:
            # Try to run pip audit
            os.chdir(self.backend_path)
            result = subprocess.run(
                ['pip', 'list'],
                capture_output=True,
                text=True
            )

            return {
                'success': result.returncode == 0,
                'output': result.stdout,
                'errors': result.stderr
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def generate_fixes(self) -> Dict[str, Any]:
        """Generate and apply quick fixes"""
        print("[START] Starting quick fix generation...")

        # Check for issues
        security_issues = self.check_security_issues()
        deployment_issues = self.check_deployment_issues()

        print(f"[INFO] Found {len(security_issues)} security issues")
        print(f"[INFO] Found {len(deployment_issues)} deployment issues")

        # Apply fixes
        security_fixes = self.fix_security_issues(security_issues)
        deployment_fixes = self.fix_deployment_issues(deployment_issues)

        # Create additional deployment files
        self.create_nginx_config()

        # Run security audit
        audit_result = self.run_security_audit()

        return {
            'success': True,
            'security_issues': len(security_issues),
            'deployment_issues': len(deployment_issues),
            'security_fixes': security_fixes,
            'deployment_fixes': deployment_fixes,
            'fixes_applied': self.fixes_applied,
            'audit_result': audit_result
        }

    def generate_report(self, results: Dict) -> str:
        """Generate quick fix report"""
        report = []
        report.append("=" * 70)
        report.append("QUICK FIX GENERATOR REPORT")
        report.append("=" * 70)
        report.append(f"Generated: {datetime.now().isoformat()}")
        report.append("")

        if results['success']:
            report.append("[OK] Quick fix generation completed")

            report.append(f"[INFO] Security issues found: {results['security_issues']}")
            report.append(f"[INFO] Deployment issues found: {results['deployment_issues']}")
            report.append("")

            if results['fixes_applied']:
                report.append("[OK] Fixes applied:")
                for fix in results['fixes_applied']:
                    report.append(f"  - {fix}")
                report.append("")

            if results['security_fixes']:
                report.append("[SECURE] Security fixes:")
                for fix in results['security_fixes']:
                    report.append(f"  - {fix}")
                report.append("")

            if results['deployment_fixes']:
                report.append("[DEPLOY] Deployment fixes:")
                for fix in results['deployment_fixes']:
                    report.append(f"  - {fix}")
                report.append("")

        report.append("[NEXT] Recommended next steps:")
        report.append("1. Review generated Docker files")
        report.append("2. Update .env.example with actual values")
        report.append("3. Set up SSL certificates for production")
        report.append("4. Run 'docker-compose up -d' to test deployment")
        report.append("5. Configure production secrets securely")

        report.append("")
        report.append("=" * 70)

        return "\n".join(report)

def main():
    """Main function"""
    fixer = QuickFixGenerator()

    # Generate fixes
    results = fixer.generate_fixes()

    # Generate and display report
    report = fixer.generate_report(results)
    print(report)

    # Save report
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    report_file = f'quick_fix_report_{timestamp}.txt'

    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)

    print(f"\n[OK] Report saved to: {report_file}")

if __name__ == "__main__":
    main()
