# Production Environment Setup Guide

## <¯ Overview

This guide walks you through setting up the production environment configuration for the YKS Haz1rl1k Platform. Follow these steps carefully to ensure a secure and properly configured production deployment.

## =Ë Prerequisites

- Python 3.11+ installed
- Access to production database (PostgreSQL)
- Access to production Redis instance
- API keys for external services (YouTube, OpenAI, etc.)
- SSL certificate for HTTPS

## =€ Quick Start

### Step 1: Copy Template

```bash
cd backend
cp .env.production.template .env.production
```

### Step 2: Generate Secrets

Generate secure random secrets for critical security keys:

```bash
# SECRET_KEY (FastAPI session secret, 32+ characters)
python -c "import secrets; print('SECRET_KEY=' + secrets.token_urlsafe(32))"

# JWT_SECRET_KEY (JWT token signing, 32+ characters)
python -c "import secrets; print('JWT_SECRET_KEY=' + secrets.token_urlsafe(32))"

# ENCRYPTION_KEY (Fernet encryption key)
python -c "from cryptography.fernet import Fernet; print('ENCRYPTION_KEY=' + Fernet.generate_key().decode())"

# CSRF_SECRET_KEY (CSRF protection)
python -c "import secrets; print('CSRF_SECRET_KEY=' + secrets.token_urlsafe(32))"
```

**  CRITICAL**: Save these keys securely! Losing them means:
- All existing sessions become invalid
- All JWT tokens become invalid
- All encrypted data becomes unrecoverable

### Step 3: Configure Database

Update the `DATABASE_URL` in `.env.production`:

```bash
# Format:
# postgresql+asyncpg://username:password@host:port/database

# Example:
DATABASE_URL=postgresql+asyncpg://yks_user:StrongPassword123!@production-db.example.com:5432/yks_production

# Connection Pool Settings
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=10
DB_POOL_TIMEOUT=30
DB_POOL_RECYCLE=3600
```

**Production Checklist**:
- [ ] Use strong password (16+ chars, mixed case, numbers, symbols)
- [ ] Enable SSL for database connection
- [ ] Set up read replicas for scalability
- [ ] Configure automated backups (see P0-2)

### Step 4: Configure Redis

Update the `REDIS_URL` in `.env.production`:

```bash
# Format:
# redis://[:password]@host:port/db

# Example with password:
REDIS_URL=redis://:RedisPassword123@production-redis.example.com:6379/0

# Example without password (not recommended):
REDIS_URL=redis://production-redis.example.com:6379/0

# Redis Settings
REDIS_MAX_CONNECTIONS=50
REDIS_SOCKET_TIMEOUT=5
REDIS_SOCKET_CONNECT_TIMEOUT=5
```

### Step 5: Obtain API Keys

#### YouTube Data API v3

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create new project or select existing
3. Enable "YouTube Data API v3"
4. Create credentials ’ API Key
5. Restrict key to YouTube Data API v3
6. Add to `.env.production`:

```bash
YOUTUBE_API_KEY_1=AIzaSyXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
YOUTUBE_API_KEY_2=AIzaSyYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYY  # Backup key
YOUTUBE_API_KEY_3=AIzaSyZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZ  # Second backup
```

**Quota**: 10,000 units/day per key (we use 3 keys for 30,000 total)

#### OpenAI API

1. Go to [OpenAI Platform](https://platform.openai.com/)
2. Sign in / Create account
3. Navigate to API Keys section
4. Create new secret key
5. Add to `.env.production`:

```bash
OPENAI_API_KEY=[REDACTED_OPENAI_KEY]
OPENAI_MODEL=gpt-4-turbo-preview  # or gpt-3.5-turbo for lower cost
OPENAI_MAX_TOKENS=2000
OPENAI_TEMPERATURE=0.7
```

**Cost Optimization**:
- Use gpt-3.5-turbo for simple tasks (90% cheaper)
- Implement response caching
- Set reasonable max_tokens limits

#### HuggingFace

1. Go to [HuggingFace](https://huggingface.co/)
2. Sign in / Create account
3. Settings ’ Access Tokens
4. Create new token with read access
5. Add to `.env.production`:

```bash
HUGGINGFACE_API_TOKEN=hf_XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
HUGGINGFACE_MODEL=dbmdz/bert-base-turkish-cased
```

#### EBA API (Turkish Education Network)

Contact EBA for production credentials:

```bash
EBA_API_KEY=<CONTACT_EBA_FOR_CREDENTIALS>
EBA_API_SECRET=<CONTACT_EBA_FOR_CREDENTIALS>
EBA_BASE_URL=https://api.eba.gov.tr/v1
```

#### Khan Academy API

1. Contact Khan Academy for institutional access
2. Add credentials:

```bash
KHAN_API_KEY=<CONTACT_KHAN_ACADEMY>
KHAN_API_SECRET=<CONTACT_KHAN_ACADEMY>
KHAN_BASE_URL=https://www.khanacademy.org/api/v1
```

### Step 6: Configure CORS

Update allowed origins for production domain:

```bash
# Single domain:
CORS_ORIGINS=https://yks.example.com

# Multiple domains (comma-separated):
CORS_ORIGINS=https://yks.example.com,https://www.yks.example.com,https://app.yks.example.com

# IMPORTANT: Never use * in production!
# CORS_ORIGINS=*  L WRONG - Security vulnerability
```

### Step 7: Configure Monitoring

#### Sentry (Error Tracking)

1. Go to [Sentry.io](https://sentry.io/)
2. Create new project (Python/FastAPI)
3. Copy DSN
4. Add to `.env.production`:

```bash
SENTRY_DSN=https://abc123def456@o123456.ingest.sentry.io/7891011
SENTRY_ENVIRONMENT=production
SENTRY_TRACES_SAMPLE_RATE=0.1  # 10% of transactions
SENTRY_PROFILES_SAMPLE_RATE=0.1
```

#### Prometheus & Grafana

```bash
PROMETHEUS_ENABLED=true
PROMETHEUS_PORT=9090
PROMETHEUS_MULTIPROC_DIR=/tmp/prometheus_multiproc

GRAFANA_ENABLED=true
GRAFANA_PORT=3000
GRAFANA_ADMIN_PASSWORD=<STRONG_PASSWORD>
```

#### Elasticsearch (Logging)

```bash
ELASTICSEARCH_ENABLED=true
ELASTICSEARCH_HOST=elasticsearch.production.com
ELASTICSEARCH_PORT=9200
ELASTICSEARCH_USERNAME=elastic
ELASTICSEARCH_PASSWORD=<STRONG_PASSWORD>
ELASTICSEARCH_INDEX_PREFIX=yks-logs
```

### Step 8: Configure Email (SMTP)

For sending password reset emails, notifications, etc:

```bash
# Gmail Example:
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=noreply@yourdomain.com
SMTP_PASSWORD=<APP_PASSWORD>  # Use app-specific password
SMTP_FROM_EMAIL=noreply@yourdomain.com
SMTP_FROM_NAME=YKS Haz1rl1k Platformu

# AWS SES Example:
SMTP_HOST=email-smtp.us-east-1.amazonaws.com
SMTP_PORT=587
SMTP_USER=<AWS_SES_SMTP_USERNAME>
SMTP_PASSWORD=<AWS_SES_SMTP_PASSWORD>
```

### Step 9: Configure File Storage (AWS S3)

For storing uploaded files, images, etc:

```bash
AWS_ACCESS_KEY_ID=AKIAXXXXXXXXXXXXXXXX
AWS_SECRET_ACCESS_KEY=XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
AWS_REGION=eu-west-1
AWS_S3_BUCKET=yks-platform-production
AWS_S3_ENDPOINT_URL=https://s3.eu-west-1.amazonaws.com
```

**Bucket Configuration**:
- [ ] Enable versioning
- [ ] Enable server-side encryption (AES-256)
- [ ] Configure lifecycle policies (delete old files)
- [ ] Set up CORS policy for uploads

### Step 10: Security Settings

```bash
# Environment
ENVIRONMENT=production
DEBUG=false  #   MUST be false in production

# Rate Limiting (requests per minute)
RATE_LIMIT_PER_MINUTE=60
RATE_LIMIT_PER_HOUR=1000
RATE_LIMIT_PER_DAY=10000
RATE_LIMIT_BURST=10

# Session Security
SESSION_COOKIE_SECURE=true  # Requires HTTPS
SESSION_COOKIE_HTTPONLY=true
SESSION_COOKIE_SAMESITE=lax
SESSION_MAX_AGE=86400  # 24 hours

# Password Policies
PASSWORD_MIN_LENGTH=8
PASSWORD_REQUIRE_UPPERCASE=true
PASSWORD_REQUIRE_LOWERCASE=true
PASSWORD_REQUIRE_NUMBERS=true
PASSWORD_REQUIRE_SPECIAL=true
```

### Step 11: KVKK Compliance (Turkish Data Protection)

```bash
KVKK_ENABLED=true
KVKK_DATA_RETENTION_DAYS=365
KVKK_CONSENT_REQUIRED=true
KVKK_ENCRYPTION_ENABLED=true
KVKK_AUDIT_LOGGING=true
KVKK_DATA_CONTROLLER_NAME=Your Company Name
KVKK_DATA_CONTROLLER_EMAIL=kvkk@yourdomain.com
KVKK_DATA_CONTROLLER_PHONE=+90xxxxxxxxxx
```

##  Validation

After configuring all values, validate the configuration:

```bash
# Install dependencies if needed
pip install python-dotenv pydantic cryptography

# Run validation
python validate_production_env.py --env-file .env.production
```

**Expected Output**:
```
= Validating Production Environment Configuration


 SECRET_KEY: Valid (32+ chars, good entropy)
 JWT_SECRET_KEY: Valid (32+ chars, good entropy)
 ENCRYPTION_KEY: Valid (Fernet key format)
 DATABASE_URL: Valid (postgresql+asyncpg)
 REDIS_URL: Valid (redis://)
 YOUTUBE_API_KEY_1: Valid (40+ chars)
 OPENAI_API_KEY: Valid (sk-proj- prefix)
 CORS_ORIGINS: Valid (HTTPS URLs)
 SENTRY_DSN: Valid (sentry.io format)


 VALIDATION PASSED - Ready for production!

```

**If validation fails**:
1. Check error messages for specific issues
2. Fix placeholder values
3. Verify API key formats
4. Re-run validation

## = Security Best Practices

### 1. Never Commit .env.production

Add to `.gitignore`:
```bash
.env.production
.env.local
*.env.production*
```

### 2. Use Secret Management

For production deployments, use a secret management service:

- **AWS Secrets Manager**
- **HashiCorp Vault**
- **Azure Key Vault**
- **Google Secret Manager**

### 3. Rotate Secrets Regularly

Schedule for rotating:
- Database passwords: Every 90 days
- API keys: Every 180 days
- Encryption keys: Annually (with data re-encryption)
- JWT secrets: Every 6 months

### 4. Principle of Least Privilege

- Database user should only have necessary permissions
- API keys should be scoped to minimum required access
- Redis should use password authentication

### 5. Monitor Secret Usage

- Enable audit logging for secret access
- Set up alerts for failed authentication attempts
- Monitor for unusual API usage patterns

## =¨ Troubleshooting

### Validation Error: "Contains placeholder"

```bash
L YOUTUBE_API_KEY_1: Contains placeholder
```

**Fix**: Replace `<GOOGLE_CLOUD_API_KEY_1>` with actual API key from Google Cloud Console.

### Validation Error: "Too short"

```bash
L SECRET_KEY: Too short (minimum 32 characters)
```

**Fix**: Generate new secret using:
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### Validation Error: "Invalid pattern"

```bash
L DATABASE_URL: Doesn't match pattern
```

**Fix**: Ensure URL format is: `postgresql+asyncpg://user:pass@host:port/db`

### Database Connection Failed

```bash
asyncpg.exceptions.InvalidPasswordError
```

**Fix**:
1. Verify password doesn't contain special chars that need URL encoding
2. URL-encode password: `urllib.parse.quote_plus(password)`
3. Test connection: `psql "postgresql://user:pass@host:port/db"`

### Redis Connection Timeout

```bash
redis.exceptions.ConnectionError: Error connecting to Redis
```

**Fix**:
1. Verify Redis is running: `redis-cli -h host -p port ping`
2. Check firewall rules
3. Verify REDIS_URL format
4. Test with: `redis-cli -u redis://host:port/0 ping`

## =Ê Performance Tuning

### Database Connection Pool

For high-traffic production (1000+ concurrent users):

```bash
DB_POOL_SIZE=50
DB_MAX_OVERFLOW=20
DB_POOL_TIMEOUT=30
DB_POOL_RECYCLE=1800  # Recycle connections every 30 min
```

For low-traffic production (100-500 concurrent users):

```bash
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=10
DB_POOL_TIMEOUT=30
DB_POOL_RECYCLE=3600
```

### Redis Connection Pool

```bash
REDIS_MAX_CONNECTIONS=100  # High traffic
REDIS_MAX_CONNECTIONS=50   # Medium traffic
REDIS_MAX_CONNECTIONS=20   # Low traffic
```

### Rate Limiting

Adjust based on expected load:

```bash
# Conservative (prevent abuse)
RATE_LIMIT_PER_MINUTE=30
RATE_LIMIT_PER_HOUR=500

# Moderate (balanced)
RATE_LIMIT_PER_MINUTE=60
RATE_LIMIT_PER_HOUR=1000

# Generous (high-traffic platform)
RATE_LIMIT_PER_MINUTE=120
RATE_LIMIT_PER_HOUR=3000
```

## =Ö Next Steps

After environment setup:

1. **P0-2**: Set up database backup strategy ’ See `DATABASE_BACKUP_STRATEGY.md`
2. **P0-3**: Configure HTTPS/SSL ’ See `HTTPS_SSL_SETUP.md`
3. **P0-4**: Set up monitoring alerts ’ See `MONITORING_ALERTS_SETUP.md`
4. **P0-5**: Write critical E2E tests ’ See `E2E_TESTS.md`
5. **P0-6**: Enable config validation strict mode ’ See `CONFIG_VALIDATION.md`

## =Þ Support

If you encounter issues:

1. Check logs: `tail -f logs/production.log`
2. Verify health endpoint: `curl https://yourdomain.com/health`
3. Review validation output
4. Check firewall/security groups
5. Verify DNS resolution

## =Ý Environment Variables Checklist

Use this checklist to ensure all critical variables are set:

### Security (Critical) 
- [ ] SECRET_KEY (32+ chars)
- [ ] JWT_SECRET_KEY (32+ chars)
- [ ] ENCRYPTION_KEY (Fernet format)
- [ ] CSRF_SECRET_KEY (32+ chars)

### Database 
- [ ] DATABASE_URL (production PostgreSQL)
- [ ] DB_POOL_SIZE
- [ ] DB_MAX_OVERFLOW

### Redis 
- [ ] REDIS_URL (production Redis)
- [ ] REDIS_MAX_CONNECTIONS

### External APIs 
- [ ] YOUTUBE_API_KEY_1 (Google Cloud)
- [ ] YOUTUBE_API_KEY_2 (backup)
- [ ] YOUTUBE_API_KEY_3 (backup)
- [ ] OPENAI_API_KEY
- [ ] HUGGINGFACE_API_TOKEN
- [ ] EBA_API_KEY (if using EBA)
- [ ] KHAN_API_KEY (if using Khan Academy)

### CORS 
- [ ] CORS_ORIGINS (HTTPS URLs only)
- [ ] CORS_ALLOW_CREDENTIALS=true

### Monitoring 
- [ ] SENTRY_DSN (error tracking)
- [ ] PROMETHEUS_ENABLED=true
- [ ] ELASTICSEARCH_HOST (optional)

### Email 
- [ ] SMTP_HOST
- [ ] SMTP_PORT
- [ ] SMTP_USER
- [ ] SMTP_PASSWORD
- [ ] SMTP_FROM_EMAIL

### File Storage (Optional)  
- [ ] AWS_ACCESS_KEY_ID
- [ ] AWS_SECRET_ACCESS_KEY
- [ ] AWS_S3_BUCKET

### Security Settings 
- [ ] ENVIRONMENT=production
- [ ] DEBUG=false
- [ ] SESSION_COOKIE_SECURE=true
- [ ] RATE_LIMIT_PER_MINUTE

### KVKK Compliance 
- [ ] KVKK_ENABLED=true
- [ ] KVKK_DATA_CONTROLLER_NAME
- [ ] KVKK_DATA_CONTROLLER_EMAIL

---

**Last Updated**: 2025-11-04
**Version**: 1.0.0
**Status**: Production Ready 
