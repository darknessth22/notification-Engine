# WhatsApp Service Deployment Guide

## Essential Files for New VM Deployment

Copy these files to your new VM to deploy the WhatsApp service:

### Core Docker Files
- `docker-compose.yml` - Main orchestration
- `Dockerfile` - Container build instructions
- `supervisord.conf` - Process management
- `entrypoint.sh` - Container startup script
- `requirements.txt` - Python dependencies

### Application Files
- `apps/whatsapp_gateway/` - Complete WhatsApp service directory
  - `whatsapp-server.js` - Node.js Baileys server
  - `package.json` - Node.js dependencies  
  - `python_api.py` - FastAPI bridge

### Configuration
- `config/config.yaml` - Application configuration

## Quick Deployment Steps

1. **Install Docker & Docker Compose** on the new VM
2. **Copy the essential files** listed above
3. **Run the service**:
   ```bash
   docker-compose up -d
   ```
4. **Scan QR code** for WhatsApp authentication (first time only)

## Service Endpoints
- WhatsApp Server: `http://localhost:3050`
- Python API: `http://localhost:3051`
- Health Check: `http://localhost:3051/health`

## Notes
- The `apps/ai_detection/` folder stays on individual machines (not dockerized)
- Session data is persisted in Docker volumes
- Logs are available in the `logs/` directory
