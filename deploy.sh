#!/usr/bin/env bash
# ==============================================================================
# 🚀 1-Click Deployment Script for Douyin Backend on Oracle Cloud Free / VPS
# Supports: Ubuntu 20.04/22.04/24.04, Debian 11/12, Oracle Linux 8/9
# ==============================================================================

set -e

echo "=========================================================="
echo "  🚀 DOUYIN CONTENT FINDER - CLOUD AUTO DEPLOYMENT"
echo "=========================================================="

# Check Root
if [ "$EUID" -ne 0 ]; then
  echo "❌ Please run as root (use: sudo bash deploy.sh)"
  exit 1
fi

# 1. Update Packages
echo "📦 [1/7] Updating system packages..."
apt-get update -y && apt-get install -y curl wget git ufw iptables-persistent ca-certificates gnupg lsb-release

# 2. Configure Firewall (UFW & Oracle Cloud iptables)
echo "🛡️  [2/7] Configuring Firewall (Ports 22, 80, 443, 8000)..."
# Oracle Cloud Ubuntu images have strict iptables rules by default, we flush and allow required ports
iptables -I INPUT 6 -m state --state NEW -p tcp --dport 80 -j ACCEPT || true
iptables -I INPUT 6 -m state --state NEW -p tcp --dport 443 -j ACCEPT || true
iptables -I INPUT 6 -m state --state NEW -p tcp --dport 8000 -j ACCEPT || true
netfilter-persistent save || true

# Configure UFW
ufw allow 22/tcp
ufw allow 80/tcp
ufw allow 443/tcp
ufw allow 8000/tcp
ufw --force enable

# 3. Install Docker & Docker Compose Plugin
if ! command -v docker &> /dev/null; then
    echo "🐳 [3/7] Installing Docker & Docker Compose..."
    mkdir -p /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg --yes || true
    echo \
      "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
      $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null
    apt-get update -y
    apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
else
    echo "🐳 [3/7] Docker is already installed."
fi

# Enable Docker on Boot
systemctl enable docker
systemctl start docker

# 4. Prepare Directories and .env
echo "⚙️  [4/7] Preparing project directories and configuration..."
mkdir -p uploads data nginx/conf.d certbot/conf certbot/www
chmod -R 777 uploads data

if [ ! -f .env ]; then
    if [ -f .env.example ]; then
        cp .env.example .env
        echo "✅ Created .env from .env.example"
    else
        touch .env
    fi
fi

# 5. Build and Run Docker Containers
echo "🏗️  [5/7] Building and starting containers with Docker Compose..."
docker compose down || true
docker compose up -d --build

# 6. SSL Configuration (If DOMAIN_NAME is provided)
if [ -n "$DOMAIN_NAME" ] && [ "$DOMAIN_NAME" != "" ]; then
    echo "🔒 [6/7] Setting up Let's Encrypt SSL for domain: $DOMAIN_NAME..."
    EMAIL=${ADMIN_EMAIL:-"admin@$DOMAIN_NAME"}
    
    docker compose run --rm certbot certonly --webroot --webroot-path=/var/www/certbot \
        --email "$EMAIL" --agree-tos --no-eff-email -d "$DOMAIN_NAME" || true
    
    if [ -f "certbot/conf/live/$DOMAIN_NAME/fullchain.pem" ]; then
        export DOMAIN_NAME
        envsubst '${DOMAIN_NAME}' < nginx/conf.d/ssl.conf.template > nginx/conf.d/default.conf
        docker compose restart nginx
        echo "✅ SSL Certificate activated successfully for https://$DOMAIN_NAME"
    fi
else
    echo "ℹ️  [6/7] No custom domain specified. Running on HTTP (IP-based access)."
fi

# 7. Health Check
echo "🔍 [7/7] Verifying Backend Health..."
sleep 5
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/v1/settings || echo "000")

PUBLIC_IP=$(curl -s ifconfig.me || curl -s icanhazip.com || echo "your-server-ip")

echo "=========================================================="
if [ "$HTTP_CODE" == "200" ]; then
    echo "🎉 DEPLOYMENT SUCCESSFUL!"
    echo "📍 Backend API URL: http://$PUBLIC_IP:8000"
    echo "📍 Swagger Docs   : http://$PUBLIC_IP:8000/docs"
    if [ -n "$DOMAIN_NAME" ]; then
        echo "🔒 Secure HTTPS URL: https://$DOMAIN_NAME"
    fi
else
    echo "⚠️  Backend returned HTTP $HTTP_CODE. Check logs with: docker compose logs -f"
fi
echo "=========================================================="
