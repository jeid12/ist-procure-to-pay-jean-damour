# Deployment Guide

This guide covers deploying the Procure-to-Pay backend to various production environments.

## Pre-Deployment Checklist

- [ ] Set `DEBUG=False` in production
- [ ] Configure strong `SECRET_KEY`
- [ ] Set proper `ALLOWED_HOSTS`
- [ ] Configure PostgreSQL database
- [ ] Set up file storage (S3 or similar)
- [ ] Configure CORS for frontend domain
- [ ] Enable HTTPS
- [ ] Set up monitoring and logging
- [ ] Configure backup strategy

## Environment Variables for Production

Create a `.env` file with:

```env
# Security
SECRET_KEY=your-very-strong-secret-key-here
DEBUG=False
ALLOWED_HOSTS=your-domain.com,www.your-domain.com

# Database
POSTGRES_DB=p2p_production
POSTGRES_USER=p2p_user
POSTGRES_PASSWORD=secure-password-here
POSTGRES_HOST=your-db-host
POSTGRES_PORT=5432

# CORS
CORS_ALLOWED_ORIGINS=https://your-frontend-domain.com
```

## Deployment Options

### 1. Heroku

```bash
# Install Heroku CLI
heroku login

# Create app
heroku create your-p2p-app

# Add PostgreSQL
heroku addons:create heroku-postgresql:hobby-dev

# Set environment variables
heroku config:set SECRET_KEY=your-secret-key
heroku config:set DEBUG=False
heroku config:set ALLOWED_HOSTS=your-app.herokuapp.com

# Deploy
git push heroku main

# Run migrations
heroku run python manage.py migrate

# Create superuser
heroku run python manage.py createsuperuser

# Collect static files
heroku run python manage.py collectstatic --noinput
```

### 2. DigitalOcean/AWS EC2

#### Step 1: Setup Server

```bash
# SSH into server
ssh root@your-server-ip

# Update system
apt update && apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Install Docker Compose
apt install docker-compose -y
```

#### Step 2: Deploy Application

```bash
# Clone repository
git clone your-repository-url /opt/p2p-backend
cd /opt/p2p-backend

# Create .env file
nano .env
# Add production environment variables

# Create production docker-compose
nano docker-compose.prod.yml
```

```yaml
version: '3.8'

services:
  db:
    image: postgres:15-alpine
    volumes:
      - postgres_data:/var/lib/postgresql/data
    environment:
      - POSTGRES_DB=${POSTGRES_DB}
      - POSTGRES_USER=${POSTGRES_USER}
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
    restart: always
    networks:
      - p2p-network

  web:
    build: .
    command: gunicorn core.wsgi:application --bind 0.0.0.0:8000 --workers 4
    volumes:
      - media_data:/app/media
      - static_data:/app/staticfiles
    environment:
      - DEBUG=False
      - SECRET_KEY=${SECRET_KEY}
      - ALLOWED_HOSTS=${ALLOWED_HOSTS}
      - POSTGRES_DB=${POSTGRES_DB}
      - POSTGRES_USER=${POSTGRES_USER}
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
      - POSTGRES_HOST=db
      - POSTGRES_PORT=5432
    depends_on:
      - db
    restart: always
    networks:
      - p2p-network

  nginx:
    image: nginx:alpine
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - static_data:/app/staticfiles:ro
      - media_data:/app/media:ro
      - ./certbot/conf:/etc/letsencrypt:ro
      - ./certbot/www:/var/www/certbot:ro
    ports:
      - "80:80"
      - "443:443"
    depends_on:
      - web
    restart: always
    networks:
      - p2p-network

volumes:
  postgres_data:
  media_data:
  static_data:

networks:
  p2p-network:
    driver: bridge
```

#### Step 3: Configure Nginx

```bash
nano nginx.conf
```

```nginx
events {
    worker_connections 1024;
}

http {
    upstream web {
        server web:8000;
    }

    server {
        listen 80;
        server_name your-domain.com www.your-domain.com;
        
        location /.well-known/acme-challenge/ {
            root /var/www/certbot;
        }
        
        location / {
            return 301 https://$host$request_uri;
        }
    }

    server {
        listen 443 ssl;
        server_name your-domain.com www.your-domain.com;
        
        ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
        ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;
        
        client_max_body_size 10M;
        
        location /static/ {
            alias /app/staticfiles/;
        }
        
        location /media/ {
            alias /app/media/;
        }
        
        location / {
            proxy_pass http://web;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }
    }
}
```

#### Step 4: Install SSL Certificate

```bash
# Install Certbot
apt install certbot python3-certbot-nginx -y

# Get certificate
certbot --nginx -d your-domain.com -d www.your-domain.com

# Or manually
mkdir -p certbot/conf certbot/www
docker-compose run --rm certbot certonly --webroot --webroot-path /var/www/certbot/ -d your-domain.com
```

#### Step 5: Start Application

```bash
# Build and start
docker-compose -f docker-compose.prod.yml up -d --build

# View logs
docker-compose -f docker-compose.prod.yml logs -f

# Run migrations
docker-compose -f docker-compose.prod.yml exec web python manage.py migrate

# Create superuser
docker-compose -f docker-compose.prod.yml exec web python manage.py createsuperuser

# Collect static files
docker-compose -f docker-compose.prod.yml exec web python manage.py collectstatic --noinput
```

### 3. AWS Elastic Beanstalk

#### Step 1: Install EB CLI

```bash
pip install awsebcli
```

#### Step 2: Initialize EB

```bash
eb init -p python-3.11 p2p-backend --region us-east-1
```

#### Step 3: Create Environment

```bash
eb create p2p-production
```

#### Step 4: Configure Database

- Create RDS PostgreSQL instance in AWS Console
- Set environment variables:

```bash
eb setenv SECRET_KEY=your-secret-key \
  DEBUG=False \
  POSTGRES_DB=p2p_db \
  POSTGRES_USER=postgres \
  POSTGRES_PASSWORD=your-password \
  POSTGRES_HOST=your-rds-endpoint.amazonaws.com
```

#### Step 5: Deploy

```bash
eb deploy
```

## Post-Deployment Tasks

### 1. Run Migrations

```bash
# Heroku
heroku run python manage.py migrate

# Docker
docker-compose exec web python manage.py migrate

# EB
eb ssh
cd /var/app/current
source /var/app/venv/*/bin/activate
python manage.py migrate
```

### 2. Create Superuser

```bash
# Heroku
heroku run python manage.py createsuperuser

# Docker
docker-compose exec web python manage.py createsuperuser

# EB
eb ssh
cd /var/app/current
source /var/app/venv/*/bin/activate
python manage.py createsuperuser
```

### 3. Collect Static Files

```bash
# Heroku (automatic)
# Already handled by Heroku

# Docker
docker-compose exec web python manage.py collectstatic --noinput

# EB
eb ssh
cd /var/app/current
source /var/app/venv/*/bin/activate
python manage.py collectstatic --noinput
```

### 4. Setup File Storage (S3)

Update `settings.py`:

```python
# Install boto3
# pip install boto3 django-storages

INSTALLED_APPS += ['storages']

# S3 Configuration
AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
AWS_STORAGE_BUCKET_NAME = os.getenv('AWS_STORAGE_BUCKET_NAME')
AWS_S3_REGION_NAME = os.getenv('AWS_S3_REGION_NAME', 'us-east-1')

# Static files
STATICFILES_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'

# Media files
DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
```

## Monitoring & Maintenance

### 1. Setup Logging

Use external logging service like:
- Sentry for error tracking
- Loggly for log aggregation
- CloudWatch for AWS deployments

### 2. Database Backups

```bash
# Manual backup
docker-compose exec db pg_dump -U postgres p2p_db > backup.sql

# Restore
docker-compose exec -T db psql -U postgres p2p_db < backup.sql

# Automated backups (cron job)
0 2 * * * cd /opt/p2p-backend && docker-compose exec -T db pg_dump -U postgres p2p_db > /backups/p2p_$(date +\%Y\%m\%d).sql
```

### 3. Health Checks

Create `healthcheck.sh`:

```bash
#!/bin/bash
response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/auth/login/)
if [ $response -eq 200 ]; then
    echo "Health check passed"
    exit 0
else
    echo "Health check failed"
    exit 1
fi
```

### 4. Monitoring Endpoints

Add to Django:

```python
# views.py
from django.http import JsonResponse
from django.db import connection

def health_check(request):
    try:
        connection.ensure_connection()
        return JsonResponse({'status': 'healthy', 'database': 'connected'})
    except Exception as e:
        return JsonResponse({'status': 'unhealthy', 'error': str(e)}, status=500)
```

## Scaling

### Horizontal Scaling

```yaml
# docker-compose.prod.yml
web:
  deploy:
    replicas: 3
    resources:
      limits:
        cpus: '0.5'
        memory: 512M
```

### Load Balancing

Use:
- AWS Application Load Balancer
- Nginx load balancing
- Kubernetes for orchestration

## Security Best Practices

1. **Use HTTPS only**
2. **Enable HSTS** (HTTP Strict Transport Security)
3. **Configure CORS properly**
4. **Rate limiting** (django-ratelimit)
5. **SQL injection protection** (Django ORM does this)
6. **XSS protection** (Django templates do this)
7. **CSRF protection** (enabled by default)
8. **Secure headers** (django-security)

## Troubleshooting

### Application won't start
```bash
# Check logs
docker-compose logs web

# Check database connection
docker-compose exec web python manage.py dbshell
```

### Static files not loading
```bash
# Collect static files
docker-compose exec web python manage.py collectstatic --noinput

# Check nginx configuration
docker-compose exec nginx nginx -t
```

### Database migration errors
```bash
# Show migrations
docker-compose exec web python manage.py showmigrations

# Fake migration (if needed)
docker-compose exec web python manage.py migrate --fake

# Reset migrations (CAUTION)
docker-compose exec web python manage.py migrate --fake p2p zero
docker-compose exec web python manage.py migrate
```

## Performance Optimization

1. **Database indexing** - Already configured in models
2. **Query optimization** - Use select_related and prefetch_related
3. **Caching** - Add Redis for caching
4. **CDN** - Use CloudFront or similar for static files
5. **Database connection pooling** - Use pgbouncer

## Maintenance Mode

Create `maintenance.html` and configure nginx:

```nginx
location / {
    if (-f /var/www/maintenance.html) {
        return 503;
    }
    proxy_pass http://web;
}

error_page 503 @maintenance;
location @maintenance {
    root /var/www;
    rewrite ^(.*)$ /maintenance.html break;
}
```

## Support

For deployment issues:
- Check logs: `docker-compose logs`
- Review settings: `core/settings.py`
- Database status: `docker-compose exec db pg_isready`
- Django shell: `docker-compose exec web python manage.py shell`
