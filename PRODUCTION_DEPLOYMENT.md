# Production Deployment Guide

## 🚀 Deploying College Community API to Production

This guide covers how to deploy your college community API to production with proper database initialization and schema management.

### 📋 Prerequisites

1. **Production Server** (Ubuntu/CentOS/AWS/Digital Ocean)
2. **PostgreSQL Database** (Local or cloud service like AWS RDS, Google Cloud SQL)
3. **Docker & Docker Compose** (recommended) or Python 3.11+
4. **Domain name and SSL certificate** (for HTTPS)
5. **Reverse proxy** (Nginx recommended)

### 🗄️ Database Setup Options

#### Option 1: Fresh Production Database (Recommended)

```bash
# 1. Create the database schema only (no test data)
python create_schema.py

# 2. Initialize with minimal production data
python init_production_db.py --sample-college --admin-user

# 3. Verify setup
python db_manager.py health-check
```

#### Option 2: Migrate from Development

```bash
# 1. Backup development database
python db_manager.py backup

# 2. Export development data (optional)
python db_manager.py export-data

# 3. Set up production database
python create_schema.py

# 4. Import data (if needed)
# Edit exported JSON to remove test data, then restore
```

#### Option 3: Complete Clean Setup

```bash
# 1. Drop and recreate everything
python create_schema.py --drop --force

# 2. Create fresh schema
python create_schema.py

# 3. Set up production data
python init_production_db.py --admin-user
```

### 🔧 Environment Configuration

1. **Copy environment template:**
   ```bash
   cp .env.production.example .env
   ```

2. **Configure production settings:**
   ```bash
   # Edit .env file with your production values
   nano .env
   ```

3. **Essential variables to change:**
   - `DATABASE_URL`: Your production PostgreSQL URL
   - `SECRET_KEY`: Generate a secure 32+ character key
   - `OPENAI_API_KEY`: Your OpenAI API key (if using AI features)
   - `CORS_ORIGINS`: Your frontend domain(s)

### 🐳 Docker Deployment (Recommended)

#### 1. Production Docker Compose

Create `docker-compose.production.yml`:

```yaml
version: '3.8'

services:
  web:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:password@db:5432/college_community
      - SECRET_KEY=your-production-secret-key
    depends_on:
      - db
    volumes:
      - ./uploads:/app/uploads
      - ./logs:/app/logs
    restart: unless-stopped

  db:
    image: postgres:15
    environment:
      POSTGRES_DB: college_community
      POSTGRES_USER: your_db_user
      POSTGRES_PASSWORD: your_db_password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - web
    restart: unless-stopped

volumes:
  postgres_data:
```

#### 2. Build and Deploy

```bash
# Build production image
docker-compose -f docker-compose.production.yml build

# Start services
docker-compose -f docker-compose.production.yml up -d

# Initialize database
docker-compose -f docker-compose.production.yml exec web python create_schema.py
docker-compose -f docker-compose.production.yml exec web python init_production_db.py --admin-user
```

### 🖥️ Manual Deployment (Without Docker)

#### 1. Install Dependencies

```bash
# Install Python dependencies
pip install -r requirements.txt

# Install PostgreSQL client (for backups)
sudo apt-get install postgresql-client  # Ubuntu/Debian
sudo yum install postgresql             # CentOS/RHEL
```

#### 2. Set up Database

```bash
# Create PostgreSQL database
sudo -u postgres createdb college_community
sudo -u postgres createuser -P your_db_user

# Grant permissions
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE college_community TO your_db_user;"
```

#### 3. Initialize Application

```bash
# Set environment variables
export DATABASE_URL="postgresql://user:password@localhost/college_community"
export SECRET_KEY="your-production-secret-key"

# Create database schema
python create_schema.py

# Initialize with production data
python init_production_db.py --admin-user

# Start application
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### 🔒 Security Configuration

#### 1. Nginx Reverse Proxy

Create `/etc/nginx/sites-available/college-api`:

```nginx
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;

    ssl_certificate /path/to/your/certificate.crt;
    ssl_certificate_key /path/to/your/private.key;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /uploads/ {
        alias /path/to/uploads/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

#### 2. SSL Certificate (Let's Encrypt)

```bash
# Install certbot
sudo apt-get install certbot python3-certbot-nginx

# Get SSL certificate
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com
```

### 📊 Monitoring and Maintenance

#### 1. Health Checks

```bash
# Check database health
python db_manager.py health-check

# Check API health
curl https://yourdomain.com/health
```

#### 2. Backup Strategy

```bash
# Create automated backup script
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
python db_manager.py backup
aws s3 cp backup_*.sql s3://your-backup-bucket/
```

#### 3. Log Monitoring

```bash
# View application logs
tail -f /app/logs/app.log

# View nginx logs
tail -f /var/log/nginx/access.log
tail -f /var/log/nginx/error.log
```

### 🔄 Database Migrations

For future schema changes:

```bash
# 1. Create migration script
python create_migration.py add_new_feature

# 2. Test migration on staging
python migrate.py --dry-run

# 3. Backup before migration
python db_manager.py backup

# 4. Run migration
python migrate.py
```

### 📱 Frontend Integration

Your frontend can now connect to:
- **API Base URL**: `https://yourdomain.com`
- **Authentication**: JWT tokens via `/auth/login`
- **File uploads**: `/files/upload`
- **Real-time alerts**: `/alerts` endpoints

### 🚨 Troubleshooting

#### Common Issues:

1. **Database Connection Failed**
   ```bash
   # Check database status
   sudo systemctl status postgresql
   
   # Test connection
   psql -h localhost -U your_user -d college_community
   ```

2. **Permission Denied for Uploads**
   ```bash
   # Fix upload permissions
   sudo chown -R www-data:www-data /path/to/uploads
   sudo chmod -R 755 /path/to/uploads
   ```

3. **CORS Errors**
   - Update `CORS_ORIGINS` in `.env`
   - Restart the application

4. **SSL Certificate Issues**
   ```bash
   # Renew certificate
   sudo certbot renew
   ```

### 🎯 Performance Optimization

1. **Database Indexing**: Already optimized in models
2. **Connection Pooling**: Configure in `DATABASE_URL`
3. **Caching**: Add Redis for session management
4. **CDN**: Use CloudFlare for static assets
5. **Load Balancing**: Use multiple app instances

### 📋 Production Checklist

- [ ] Database initialized and tested
- [ ] Environment variables configured
- [ ] SSL certificate installed
- [ ] Nginx reverse proxy configured
- [ ] Backup strategy implemented
- [ ] Monitoring set up
- [ ] Security headers configured
- [ ] CORS properly configured
- [ ] File upload limits set
- [ ] Log rotation configured
- [ ] Admin user created
- [ ] Health checks working
- [ ] Documentation updated

### 🎉 Success!

Your College Community API is now running in production! 🚀

**Next steps:**
1. Connect your Flutter frontend
2. Set up monitoring alerts
3. Configure automated backups
4. Add more colleges and users
5. Monitor performance and scale as needed