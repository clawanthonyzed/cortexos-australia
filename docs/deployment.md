# Deployment Guide

Full production deployment on Ubuntu 22.04 VPS. Estimated time: 30–45 minutes.

---

## Prerequisites

- Ubuntu 22.04 LTS VPS (minimum: 4 vCPU, 8GB RAM, 80GB SSD)
- Domain name pointing to VPS IP (A record for `cortexos.yourdomain.com` and `api.cortexos.yourdomain.com` and `langfuse.cortexos.yourdomain.com`)
- SSH access as root or a sudo user
- GitHub repository with your CortexOS code

---

## 1. Initial Server Setup

```bash
# Update packages
apt update && apt upgrade -y

# Install essentials
apt install -y \
  curl \
  git \
  unzip \
  ufw \
  fail2ban \
  htop \
  ncdu

# Create a non-root deploy user (optional but recommended)
adduser deploy
usermod -aG sudo docker deploy

# Harden SSH: disable password auth (only if you have SSH key configured)
# Edit /etc/ssh/sshd_config:
#   PasswordAuthentication no
#   PermitRootLogin prohibit-password
# systemctl restart sshd

# Configure firewall
ufw default deny incoming
ufw default allow outgoing
ufw allow ssh
ufw allow 80/tcp
ufw allow 443/tcp
ufw enable

# Install fail2ban
systemctl enable fail2ban
systemctl start fail2ban
```

---

## 2. Install Docker and Docker Compose

```bash
# Add Docker's GPG key
curl -fsSL https://download.docker.com/linux/ubuntu/gpg \
  | gpg --dearmor -o /usr/share/keyrings/docker.gpg

# Add Docker repository
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker.gpg] \
  https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" \
  > /etc/apt/sources.list.d/docker.list

# Install Docker
apt update
apt install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# Start and enable Docker
systemctl enable docker
systemctl start docker

# Verify
docker --version
docker compose version
```

---

## 3. Clone Repository

```bash
# Create project directory
mkdir -p /opt/cortexos
cd /opt/cortexos

# Clone
git clone https://github.com/your-org/cortexos.git .

# Or if private, use deploy token:
# git clone https://oauth2:GITHUB_TOKEN@github.com/your-org/cortexos.git .
```

---

## 4. Configure .env

```bash
cd /opt/cortexos
cp .env.example .env
nano .env  # or vim .env
```

Fill in all required values. Generate secrets:

```bash
# Generate each of these separately:
openssl rand -hex 32   # → SECRET_KEY
openssl rand -hex 32   # → LANGFUSE_NEXTAUTH_SECRET
openssl rand -hex 32   # → LANGFUSE_SALT

# Generate strong passwords
openssl rand -base64 24   # → POSTGRES_PASSWORD
openssl rand -base64 24   # → NEO4J_PASSWORD
```

**Required values to set before starting:**
- `POSTGRES_PASSWORD` — strong random password
- `NEO4J_PASSWORD` — strong random password
- `SECRET_KEY` — 32+ char hex string
- `ANTHROPIC_API_KEY` — your Anthropic API key
- `LANGFUSE_NEXTAUTH_SECRET` — 32+ char hex string
- `LANGFUSE_SALT` — 32+ char hex string
- `ENVIRONMENT=production`

**Set production URLs:**
```env
NEXT_PUBLIC_API_URL=https://api.cortexos.yourdomain.com
NEXT_PUBLIC_WS_URL=wss://api.cortexos.yourdomain.com
CORS_ORIGINS=https://cortexos.yourdomain.com
```

Protect the .env file:
```bash
chmod 600 /opt/cortexos/.env
```

---

## 5. Configure Traefik

Update domain names in both Traefik config and docker-compose.prod.yml:

```bash
# Replace all occurrences of the placeholder domain
sed -i 's/cortexos.yourdomain.com/cortexos.youractual.domain/g' \
  traefik/traefik.yml \
  traefik/dynamic.yml \
  docker-compose.prod.yml

# Set your email for Let's Encrypt notifications
sed -i 's/admin@yourdomain.com/your@email.com/g' traefik/traefik.yml
```

Create the ACME certificate storage file with correct permissions:

```bash
mkdir -p /opt/cortexos/traefik/letsencrypt
touch /opt/cortexos/traefik/letsencrypt/acme.json
chmod 600 /opt/cortexos/traefik/letsencrypt/acme.json
```

Update `docker-compose.prod.yml` to mount the letsencrypt directory:

```yaml
traefik:
  volumes:
    - /var/run/docker.sock:/var/run/docker.sock:ro
    - ./traefik/traefik.yml:/traefik.yml:ro
    - ./traefik/dynamic.yml:/dynamic.yml:ro
    - ./traefik/letsencrypt:/letsencrypt  # persistent cert storage
```

---

## 6. Start Production Stack

```bash
cd /opt/cortexos

# Pull all base images first (faster initial start)
docker compose -f docker-compose.yml -f docker-compose.prod.yml pull

# Build application images
docker compose -f docker-compose.yml -f docker-compose.prod.yml build

# Start all services
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Verify all containers are running
docker compose -f docker-compose.yml -f docker-compose.prod.yml ps
```

Wait 60–90 seconds for services to initialise. Check:

```bash
# Check logs for errors
docker compose -f docker-compose.yml -f docker-compose.prod.yml logs --tail=50

# Check specific service
docker compose -f docker-compose.yml -f docker-compose.prod.yml logs backend
```

---

## 7. Database Migrations

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml \
  exec -T backend alembic upgrade head
```

Seed default data (first deploy only):

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml \
  exec -T backend python -m app.scripts.seed
```

---

## 8. Setting Up GitHub Actions Secrets

In your GitHub repository → Settings → Secrets and variables → Actions → New repository secret:

| Secret | Value |
|--------|-------|
| `VPS_HOST` | Your VPS IP address |
| `VPS_SSH_KEY` | Contents of your SSH private key (`cat ~/.ssh/id_rsa`) |
| `VPS_PORT` | SSH port (default: `22`) |
| `CODECOV_TOKEN` | From codecov.io (optional) |

Test the deployment workflow manually:
- GitHub Actions → "Deploy to Production" → Run workflow

---

## 9. Backup Strategy

### Automated daily backups via cron

```bash
# Create backup directory
mkdir -p /opt/cortexos/backups

# Create backup script
cat > /opt/cortexos/scripts/backup-cron.sh << 'EOF'
#!/bin/bash
set -e

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/opt/cortexos/backups"
COMPOSE_FILE="-f /opt/cortexos/docker-compose.yml -f /opt/cortexos/docker-compose.prod.yml"

# Dump PostgreSQL
docker compose $COMPOSE_FILE exec -T postgres \
  pg_dump -U cortexos cortexos \
  | gzip > "$BACKUP_DIR/postgres_$TIMESTAMP.sql.gz"

# Keep only last 30 days of backups
find "$BACKUP_DIR" -name "*.sql.gz" -mtime +30 -delete

echo "Backup completed: $BACKUP_DIR/postgres_$TIMESTAMP.sql.gz"
EOF

chmod +x /opt/cortexos/scripts/backup-cron.sh

# Schedule daily at 2am
(crontab -l 2>/dev/null; echo "0 2 * * * /opt/cortexos/scripts/backup-cron.sh >> /var/log/cortexos-backup.log 2>&1") | crontab -
```

### Restore from backup

```bash
# List available backups
ls -lh /opt/cortexos/backups/

# Restore (replace TIMESTAMP with the backup you want)
gunzip -c /opt/cortexos/backups/postgres_TIMESTAMP.sql.gz | \
  docker compose -f docker-compose.yml -f docker-compose.prod.yml \
  exec -T postgres psql -U cortexos cortexos
```

---

## 10. Monitoring Setup

### Basic health check cron

```bash
cat > /opt/cortexos/scripts/health-check.sh << 'EOF'
#!/bin/bash
URL="https://api.cortexos.yourdomain.com/health"
EXPECTED_STATUS=200

HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$URL")

if [ "$HTTP_STATUS" != "$EXPECTED_STATUS" ]; then
  echo "$(date): HEALTH CHECK FAILED — HTTP $HTTP_STATUS" >> /var/log/cortexos-health.log
  # Add alerting here (e.g., curl a webhook)
fi
EOF

chmod +x /opt/cortexos/scripts/health-check.sh

# Run every 5 minutes
(crontab -l 2>/dev/null; echo "*/5 * * * * /opt/cortexos/scripts/health-check.sh") | crontab -
```

### View container resource usage

```bash
docker stats --no-stream
```

### Check disk usage

```bash
df -h
du -sh /opt/cortexos/backups/
docker system df
```

---

## Updating CortexOS

```bash
cd /opt/cortexos

# Pull latest code
git pull origin main

# Rebuild and restart (uses docker-compose.prod.yml automatically via GitHub Actions)
# Or manually:
make build-prod
make up-prod

# Run any new migrations
docker compose -f docker-compose.yml -f docker-compose.prod.yml \
  exec -T backend alembic upgrade head
```

---

## Troubleshooting

### Container won't start

```bash
# View detailed logs
docker compose -f docker-compose.yml -f docker-compose.prod.yml logs backend

# Check if port is already in use
ss -tlnp | grep :443
```

### SSL certificate not issuing

- Ensure DNS A records are pointing to your VPS IP
- Ensure ports 80 and 443 are open in UFW
- Check Traefik logs: `docker compose logs traefik`
- Verify `acme.json` has `chmod 600`

### Database connection refused

```bash
# Check postgres is healthy
docker compose ps postgres
docker compose logs postgres

# Connect manually to verify
docker compose exec postgres psql -U cortexos cortexos -c "SELECT 1;"
```

### Out of disk space

```bash
# Clean Docker resources
docker system prune -f
docker image prune -f

# Clean old backups
find /opt/cortexos/backups -name "*.sql.gz" -mtime +7 -delete
```
