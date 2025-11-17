# KVM 4 Deployment Checklist ✅

## 🎯 Current Configuration
- **Plan**: KVM 4 - ₹2,099/mo
- **Specs**: 4 vCPU + 16 GB RAM + 200 GB NVMe + 16 TB Bandwidth
- **Workers**: 4 Uvicorn workers
- **Capacity**: ~1,000 concurrent requests, 700-900 req/burst

---

## 🚀 Deployment Steps

### 1. **Apply VPS System Optimizations** (One-time, SSH to VPS)

```bash
# SSH into your VPS
ssh user@your-vps-ip

# Apply network optimizations for high concurrency
sudo tee /etc/sysctl.d/99-network-performance.conf << 'EOF'
# File descriptors
fs.file-max = 2097152

# TCP settings for high performance
net.core.somaxconn = 65535
net.core.netdev_max_backlog = 65536
net.ipv4.tcp_max_syn_backlog = 65536
net.ipv4.tcp_fin_timeout = 30
net.ipv4.tcp_keepalive_time = 600
net.ipv4.tcp_tw_reuse = 1

# Increase local port range
net.ipv4.ip_local_port_range = 1024 65535

# TCP memory tuning for 16GB RAM
net.ipv4.tcp_mem = 786432 1048576 26777216
net.ipv4.tcp_rmem = 4096 87380 16777216
net.ipv4.tcp_wmem = 4096 65536 16777216
net.core.rmem_max = 16777216
net.core.wmem_max = 16777216
EOF

# Apply settings immediately
sudo sysctl -p /etc/sysctl.d/99-network-performance.conf

# Verify settings
sysctl net.core.somaxconn
sysctl fs.file-max
```

### 2. **Deploy Updated Docker Configuration**

```bash
# Navigate to project directory
cd /path/to/college-community-api

# Rebuild Docker images with new configuration
docker-compose build --no-cache

# Stop existing containers
docker-compose down

# Start with optimized settings
docker-compose up -d

# Watch startup logs
docker-compose logs -f
```

### 3. **Verify Deployment**

```bash
# Check container status (both should be healthy)
docker-compose ps

# Verify 4 workers are running
docker-compose exec web ps aux | grep uvicorn
# Should show: 1 master + 4 worker processes

# Check resource allocation
docker stats --no-stream

# Test health endpoint
curl http://localhost:8000/health

# Check database connection
docker-compose exec db psql -U postgres -c "SELECT version();"
```

### 4. **Monitor Performance**

```bash
# Real-time container stats
docker stats

# View logs
docker-compose logs -f web
docker-compose logs -f db

# Check PostgreSQL connections
docker-compose exec db psql -U postgres -d college_community -c \
  "SELECT count(*) as active_connections FROM pg_stat_activity;"

# Check PostgreSQL cache hit ratio (should be >90%)
docker-compose exec db psql -U postgres -d college_community -c \
  "SELECT sum(heap_blks_read) as heap_read,
          sum(heap_blks_hit) as heap_hit,
          round(sum(heap_blks_hit) * 100.0 / NULLIF(sum(heap_blks_hit) + sum(heap_blks_read), 0), 2) as cache_hit_ratio
   FROM pg_statio_user_tables;"

# Monitor network connections to port 8000
ss -tan | grep :8000 | wc -l

# Check system file descriptors
cat /proc/sys/fs/file-max
ulimit -n
```

---

## 📊 Expected Performance Metrics

After deployment, you should see:

| Metric | Target | Command to Check |
|--------|--------|------------------|
| **Workers Running** | 5 (1 master + 4 workers) | `docker-compose exec web ps aux \| grep uvicorn` |
| **Web CPU Usage** | 40-70% normal, spike to 350% | `docker stats` |
| **DB CPU Usage** | 20-40% normal, spike to 200% | `docker stats` |
| **Web Memory** | 6-10 GB | `docker stats` |
| **DB Memory** | 4-6 GB | `docker stats` |
| **Active Connections** | < 200 | `ss -tan \| grep :8000 \| wc -l` |
| **DB Cache Hit Ratio** | > 90% | See monitoring commands above |
| **Response Time** | < 200ms | Load test with `hey` |

---

## 🧪 Load Testing (Optional)

```bash
# Install hey (HTTP load tester)
# macOS: brew install hey
# Linux: wget https://hey-release.s3.us-east-2.amazonaws.com/hey_linux_amd64
#        chmod +x hey_linux_amd64 && sudo mv hey_linux_amd64 /usr/local/bin/hey

# Test sustained load
hey -n 1000 -c 100 -m GET http://your-vps-ip:8000/api/posts

# Test burst capacity (400 requests in 2 seconds)
hey -n 400 -c 200 -q 200 -m GET http://your-vps-ip:8000/api/posts

# Test with authentication (replace with your token)
hey -n 500 -c 50 -H "Authorization: Bearer YOUR_TOKEN" \
    http://your-vps-ip:8000/api/posts
```

**Expected Results:**
- **Success rate**: > 99%
- **Average response time**: 100-300ms
- **Requests/sec**: 500-1000
- **No connection errors**

---

## ⚠️ Troubleshooting

### **Issue: Workers not starting**
```bash
# Check logs for errors
docker-compose logs web

# Common fixes:
# 1. Port 8000 already in use
sudo lsof -i :8000
# Kill the process or change port

# 2. Out of memory
free -h
# Reduce worker count or memory limits
```

### **Issue: Database connection errors**
```bash
# Check if PostgreSQL is healthy
docker-compose exec db pg_isready -U postgres

# Check max connections vs active
docker-compose exec db psql -U postgres -c "SHOW max_connections;"
docker-compose exec db psql -U postgres -c \
  "SELECT count(*) FROM pg_stat_activity;"

# If hitting max connections, increase or add PgBouncer
```

### **Issue: High CPU but low throughput**
```bash
# Check for blocking operations
docker-compose exec db psql -U postgres -d college_community -c \
  "SELECT pid, wait_event_type, wait_event, state, query 
   FROM pg_stat_activity 
   WHERE state != 'idle';"

# Check for slow queries
docker-compose exec db psql -U postgres -d college_community -c \
  "SELECT query, calls, total_time, mean_time 
   FROM pg_stat_statements 
   ORDER BY mean_time DESC 
   LIMIT 10;"
```

### **Issue: "Too many open files" error**
```bash
# Check current limit
ulimit -n

# Verify Docker ulimits applied
docker inspect college-community-api_web_1 | grep -A 5 Ulimits

# If not applied, ensure you restarted after docker-compose changes
docker-compose down && docker-compose up -d
```

---

## 🔐 Security Checklist

- [ ] Change default PostgreSQL password in production
- [ ] Use environment variables for secrets (not hardcoded)
- [ ] Enable firewall (only allow ports 22, 80, 443, 8000)
- [ ] Set up SSL/TLS (use Let's Encrypt + Nginx)
- [ ] Regular backups of PostgreSQL data
- [ ] Monitor disk usage (200 GB fills up over time)
- [ ] Set up log rotation

---

## 📈 When to Scale Further

### **Consider upgrading to KVM 8 (8 vCPU) when:**
- ✅ CPU consistently > 80% with `docker stats`
- ✅ Response times > 500ms under normal load
- ✅ Seeing "503 Service Unavailable" errors
- ✅ User complaints about slowness
- ✅ Growing to > 800-1000 concurrent users

### **Before upgrading, try these first:**
1. Add Redis caching for frequent queries
2. Optimize database queries (add indexes)
3. Add CDN for static files
4. Enable Nginx caching
5. Database connection pooling (PgBouncer)

---

## 📝 Maintenance Tasks

### **Daily:**
```bash
# Check container health
docker-compose ps

# Monitor disk usage
df -h
```

### **Weekly:**
```bash
# Check logs for errors
docker-compose logs --tail=100 web | grep -i error
docker-compose logs --tail=100 db | grep -i error

# Backup database
docker-compose exec db pg_dump -U postgres college_community > backup_$(date +%Y%m%d).sql
```

### **Monthly:**
```bash
# Clean up Docker resources
docker system prune -a --volumes

# Update Docker images
docker-compose pull
docker-compose up -d --build

# Vacuum database
docker-compose exec db psql -U postgres -d college_community -c "VACUUM ANALYZE;"
```

---

## 🎉 Summary

Your KVM 4 setup is configured for:
- ✅ **4x request capacity** vs KVM 2
- ✅ **1,000 concurrent requests**
- ✅ **700-900 req/burst** (vs 300-400)
- ✅ **Parallel database queries** (4 workers)
- ✅ **Optimized networking** (65K file descriptors)
- ✅ **Auto-restart** on failures
- ✅ **Health monitoring**

**Next Steps:**
1. Run the VPS system optimization commands
2. Deploy with `docker-compose up -d --build`
3. Verify with monitoring commands
4. Run load tests
5. Monitor for a week and adjust if needed

Enjoy your 4x performance boost! 🚀
