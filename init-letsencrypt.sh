#!/bin/bash

# init-letsencrypt.sh
# Run this script on your Azure VM to obtain SSL certificates

domains=(coact-ai.com www.coact-ai.com)
email="coactai@outlook.com"  # CHANGE THIS to your email
staging=0  # Set to 1 for testing (avoids rate limits)

data_path="./certbot"
rsa_key_size=4096

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}=== Let's Encrypt SSL Certificate Setup ===${NC}"
echo ""

# Check if docker-compose is available
if ! [ -x "$(command -v docker)" ]; then
  echo -e "${RED}Error: docker is not installed.${NC}" >&2
  exit 1
fi

# Create directory structure
echo -e "${YELLOW}Creating certificate directories...${NC}"
mkdir -p "$data_path/conf/live/$domains"
mkdir -p "$data_path/www"

# Check if certificates already exist
if [ -d "$data_path/conf/live/$domains" ] && [ -f "$data_path/conf/live/$domains/fullchain.pem" ]; then
  echo -e "${YELLOW}Existing certificates found. Do you want to replace them? (y/N)${NC}"
  read -r decision
  if [ "$decision" != "Y" ] && [ "$decision" != "y" ]; then
    echo "Keeping existing certificates."
    exit 0
  fi
fi

# Download recommended TLS parameters
echo -e "${YELLOW}Downloading recommended TLS parameters...${NC}"
curl -s https://raw.githubusercontent.com/certbot/certbot/master/certbot-nginx/certbot_nginx/_internal/tls_configs/options-ssl-nginx.conf > "$data_path/conf/options-ssl-nginx.conf"
curl -s https://raw.githubusercontent.com/certbot/certbot/master/certbot/certbot/ssl-dhparams.pem > "$data_path/conf/ssl-dhparams.pem"

# Create dummy certificates for initial nginx startup
echo -e "${YELLOW}Creating dummy certificates for nginx startup...${NC}"
openssl req -x509 -nodes -newkey rsa:$rsa_key_size -days 1 \
  -keyout "$data_path/conf/live/$domains/privkey.pem" \
  -out "$data_path/conf/live/$domains/fullchain.pem" \
  -subj "/CN=localhost" 2>/dev/null

# Start nginx with dummy certificates
echo -e "${YELLOW}Starting nginx...${NC}"
docker compose up -d frontend

# Wait for nginx to start
echo "Waiting for nginx to start..."
sleep 5

# Delete dummy certificates
echo -e "${YELLOW}Removing dummy certificates...${NC}"
rm -rf "$data_path/conf/live/$domains"

# Request real certificates
echo -e "${GREEN}Requesting Let's Encrypt certificates for $domains...${NC}"

# Select staging or production
if [ $staging != "0" ]; then
  staging_arg="--staging"
  echo -e "${YELLOW}Using STAGING environment (test mode)${NC}"
else
  staging_arg=""
  echo -e "${GREEN}Using PRODUCTION environment${NC}"
fi

docker compose run --rm --entrypoint "\
  certbot certonly --webroot -w /var/www/certbot \
    $staging_arg \
    --email $email \
    --rsa-key-size $rsa_key_size \
    --agree-tos \
    --no-eff-email \
    --force-renewal \
    -d ${domains[0]} -d ${domains[1]}" certbot

# Check if certificate was obtained
if [ -f "$data_path/conf/live/$domains/fullchain.pem" ]; then
  echo -e "${GREEN}✅ SSL certificates obtained successfully!${NC}"
  echo ""
  echo -e "${GREEN}Restarting nginx to use new certificates...${NC}"
  docker compose restart frontend
  echo ""
  echo -e "${GREEN}=== Setup Complete ===${NC}"
  echo -e "Your site is now available at: ${GREEN}https://${domains[0]}${NC}"
else
  echo -e "${RED}❌ Failed to obtain certificates.${NC}"
  echo "Check the certbot logs above for details."
  exit 1
fi
