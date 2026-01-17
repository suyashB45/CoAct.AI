# SSL Deployment Instructions

## Quick Setup on Azure VM

### 1. Push Changes to Git
```bash
git add .
git commit -m "Add SSL support with Let's Encrypt"
git push
```

### 2. On Your Azure VM
```bash
# Pull latest changes
cd /path/to/CoAct.AI
git pull

# Edit the script to add your email
nano init-letsencrypt.sh
# Change: email="your-email@example.com" to your actual email

# Make script executable
chmod +x init-letsencrypt.sh

# Run the certificate setup
./init-letsencrypt.sh

# Start all services
docker compose up -d
```

### 3. Verify
```bash
# Check container health
docker ps

# Test HTTPS
curl -I https://coactai.centralindia.cloudapp.azure.com
```

## Testing Without SSL (Local Development)

If you want to test locally without SSL, you can use the HTTP-only version temporarily:

```bash
# Start only frontend and backend (skip certbot)
docker compose up -d frontend backend
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| "Certificate not found" | Run `./init-letsencrypt.sh` first |
| Port 443 blocked | Open port 443 in Azure NSG |
| Rate limit exceeded | Set `staging=1` in script, wait 1 week |
