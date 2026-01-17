#!/bin/bash
# Auto-renew SSL certificates every 90 days
# Run this script via cron on your Azure VM

# Renew certificates
certbot renew --quiet

# Reload nginx to pick up new certificates
cd /path/to/CoAct.AI
docker compose exec frontend nginx -s reload

echo "$(date): Certificate renewal check completed" >> /var/log/certbot-renew.log
