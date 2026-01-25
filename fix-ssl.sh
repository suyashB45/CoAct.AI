#!/bin/bash

# Fix SSL Configuration and Reset
# Run with sudo!

echo "Stopping containers..."
docker compose down --remove-orphans

echo "Cleaning up Certbot directories..."
# Nuke the existing certbot config to ensure a clean slate
rm -rf ./certbot

echo "Creating directory structure..."
mkdir -p ./certbot/conf/live/coact-ai.com
mkdir -p ./certbot/www
mkdir -p ./certbot/conf

# Ensure permissions are open enough for Docker users
chmod -R 777 ./certbot

echo "Downloading TLS parameters..."
curl -s https://raw.githubusercontent.com/certbot/certbot/master/certbot-nginx/certbot_nginx/_internal/tls_configs/options-ssl-nginx.conf > "./certbot/conf/options-ssl-nginx.conf"
curl -s https://raw.githubusercontent.com/certbot/certbot/master/certbot/certbot/ssl-dhparams.pem > "./certbot/conf/ssl-dhparams.pem"

echo "Generating DUMMY certificates for coact-ai.com..."
openssl req -x509 -nodes -newkey rsa:4096 -days 1 \
  -keyout "./certbot/conf/live/coact-ai.com/privkey.pem" \
  -out "./certbot/conf/live/coact-ai.com/fullchain.pem" \
  -subj "/CN=coact-ai.com"

echo "Starting Nginx (frontend)..."
docker compose up -d frontend

echo "Waiting for Nginx to initialize (10s)..."
sleep 10

# Check if Nginx is running
if [ "$(docker inspect -f '{{.State.Running}}' coactai-frontend-1 2>/dev/null)" != "true" ]; then
    echo "⚠️ Nginx failed to start! Checking logs..."
    docker compose logs frontend
    exit 1
fi

echo "✅ Nginx is running with dummy certs."

echo "Testing ACME challenge directory..."
# Create a test file
echo "test-challenge-content" > ./certbot/www/test-challenge
# Try to fetch it via HTTP
CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost/.well-known/acme-challenge/test-challenge)
echo "HTTP Response for challenge file: $CODE"

if [ "$CODE" != "200" ] && [ "$CODE" != "301" ]; then
    # 301 is also okay if it redirects to HTTPS, but we usually want plain HTTP for acme-challenge
    echo "⚠️ Warning: Challenge file check returned $CODE. Certbot might fail."
else
    echo "✅ Challenge file accessible (or redirected properly)."
fi

echo "Removing dummy certificates to prepare for Certbot..."
rm -rf ./certbot/conf/live/coact-ai.com/*

echo "Requesting REAL certificates..."
docker compose run --rm --entrypoint "\
  certbot certonly --webroot -w /var/www/certbot \
    --email coactai@outlook.com \
    -d coact-ai.com -d www.coact-ai.com \
    --rsa-key-size 4096 \
    --agree-tos \
    --no-eff-email \
    --force-renewal" certbot

echo "Restoring permissions..."
chmod -R 777 ./certbot

echo "Reloading Nginx..."
docker compose exec frontend nginx -s reload

echo "=== Done! ==="
echo "Check https://coact-ai.com"
