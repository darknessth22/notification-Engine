# WhatsApp API Gateway - Complete Dockerized Solution

A fully Dockerized system that enables WhatsApp messaging through Python using the Baileys library (Node.js) under the hood. This solution provides a clean REST API for sending WhatsApp messages, images, and media programmatically.

## 🎯 What This Solution Provides

This is a comprehensive WhatsApp automation gateway that combines:
1. **Node.js server using Baileys** for WhatsApp Web automation
2. **Python FastAPI wrapper** that provides a clean REST API
3. **Single Docker container** running both services with supervisord
4. **Persistent authentication** with volume mounting for QR code sessions
5. **Auto-reconnection** capabilities for stable WhatsApp connection
6. **Image and media sending** support with file uploads and URL-based sending
7. **Complete testing utilities** and examples for easy integration

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    Docker Container                         │
│                                                             │
│  ┌─────────────────────┐    ┌─────────────────────────────┐ │
│  │   Python FastAPI    │    │      Node.js Server         │ │
│  │   (Port: 8000)      │◄──┤      (Baileys Library)      │ │
│  │                     │    │      (Port: 3000)           │ │
│  │ • REST API          │    │ • WhatsApp Web Connection   │ │
│  │ • Request Forwarding│    │ • QR Code Authentication    │ │
│  │ • Error Handling    │    │ • Message Sending           │ │
│  │ • Health Monitoring │    │ • Media File Handling       │ │
│  │ • Image Processing  │    │ • Auto-reconnection         │ │
│  └─────────────────────┘    └─────────────────────────────┘ │
│                                                             │
│              Managed by supervisord                         │
│              Persistent auth: /app/auth_info                │
└─────────────────────────────────────────────────────────────┘
```

## 📁 Complete File Structure & Purpose

### 🚀 Core Application Files

#### `whatsapp-server.js` - Baileys WhatsApp Server
**The heart of WhatsApp communication**
- Connects to WhatsApp Web using the latest Baileys v6.6.0 library
- Handles QR code generation and authentication flow
- Manages WhatsApp session state and auto-reconnection
- Processes text messages, images, videos, audio, and documents
- Provides REST API endpoints for message sending
- Validates and formats phone numbers automatically
- Includes comprehensive error handling and logging

**API Endpoints:**
- `GET /health` - Server health and connection status
- `GET /status` - Detailed WhatsApp connection information  
- `POST /send-message` - Send text messages
- `POST /send-image` - Send images with file upload
- `POST /send-image-url` - Send images from URLs

#### `python_api.py` - FastAPI Gateway
**Clean Python interface to the Baileys server**
- FastAPI-based REST API with automatic documentation
- Forwards requests to Node.js Baileys server internally
- Comprehensive error handling with detailed responses
- Health monitoring of both Python and Node.js services
- Pydantic models for request/response validation
- Async HTTP client for efficient communication
- Support for text messages, file uploads, and URL-based media

**API Endpoints:**
- `GET /` - API information and documentation
- `GET /health` - Complete system health check
- `GET /status` - Detailed status of both services
- `POST /send` - Send WhatsApp text messages
- `POST /send-image` - Upload and send image files
- `POST /send-image-url` - Send images from URLs
- `POST /test-connection` - Test connectivity to Baileys server

### 🐳 Docker & Container Files

#### `Dockerfile` - Multi-Service Container Build
**Creates a single container running both services**
- Uses Node.js 20 as base image for better crypto support
- Installs Python 3, pip, and system dependencies
- Installs supervisord for multi-process management
- Sets up proper working directories and permissions
- Installs all Node.js and Python dependencies
- Exposes ports 3000 (Node.js) and 8000 (Python)
- Includes health checks for container monitoring

#### `docker-compose.yml` - Container Orchestration
**Simplifies deployment and volume management**
- Builds and runs the WhatsApp gateway container
- Creates persistent volume for WhatsApp authentication data
- Maps container ports to host (8000 for API access)
- Sets up environment variables for production
- Configures restart policies and health checks
- Mounts logs directory for easy log access
- Handles graceful container shutdown

#### `supervisord.conf` - Process Management
**Manages both Node.js and Python processes in one container**
- Runs Node.js Baileys server and Python FastAPI simultaneously
- Automatic restart of services if they crash
- Separate log files for each service
- Process monitoring and status reporting
- Graceful shutdown handling
- Configurable restart policies and retry limits

#### `entrypoint.sh` - Container Initialization
**Sets up the container environment on startup**
- Creates necessary directories for logs and authentication
- Sets proper file permissions for WhatsApp auth storage
- Initializes logging infrastructure
- Starts supervisord to manage both services
- Provides startup status information

### 📦 Dependencies & Configuration

#### `package.json` - Node.js Dependencies
**Defines all Node.js packages and scripts**
- **@whiskeysockets/baileys**: Latest WhatsApp Web library (v6.6.0)
- **express**: Web server framework for REST API
- **cors**: Cross-origin request handling
- **multer**: File upload handling for images/media
- **qrcode-terminal**: QR code display in terminal
- **pino**: High-performance logging

#### `requirements.txt` - Python Dependencies
**Defines all Python packages for the FastAPI server**
- **fastapi**: Modern web framework for Python APIs
- **uvicorn**: ASGI server for running FastAPI
- **httpx**: Async HTTP client for internal communication
- **pydantic**: Data validation and serialization
- **python-multipart**: File upload support
- **aiofiles**: Async file operations

### 🧪 Testing & Utility Files

#### `test_client.py` - Comprehensive Testing Suite
**Complete testing utility for all API functionality**
- Health check testing for both services
- WhatsApp connection status monitoring
- Single message sending with validation
- Bulk messaging capabilities for multiple messages
- Interactive messaging mode for real-time testing
- Auto messaging with configurable intervals
- Error handling and retry mechanisms

#### `send_test_message.py` - Simple Message Sender
**Quick utility for sending test messages**
- Command-line interface for sending messages
- Phone number validation and formatting
- Connection status checking before sending
- Detailed success/error reporting
- Support for command-line arguments or interactive input

#### `image_sender.py` - Media Testing Utility
**Specialized tool for testing image and media sending**
- Send images from local files
- Send images from URLs
- Create sample test images programmatically
- Support for captions and metadata
- File type validation and error handling
- Batch image sending capabilities

### 🔧 Setup & Deployment Files

#### `setup.sh` - Automated Setup Script
**One-command deployment script**
- Checks Docker installation and status
- Builds the Docker container automatically
- Starts all services with docker-compose
- Displays service status and health information
- Provides next steps and useful commands
- Shows all available API endpoints

### 📁 Additional Directories

#### `logs/` - Service Logs
- `baileys-server.log` - Node.js Baileys server logs
- `python-api.log` - Python FastAPI server logs
- `supervisord.log` - Process management logs

#### `config/` - Configuration Files
- Contains YAML configuration files for various settings

#### `src/` - Source Code Modules
- Additional Python modules and utilities
- Configuration management
- WhatsApp notification handlers

#### `models/` - AI Models
- Contains machine learning models for fire/smoke detection
- Used for automated alert systems

#### `video/` & `downloaded_images/` - Media Storage
- Sample videos and images for testing
- Downloaded media files from WhatsApp
- Temporary storage for processed files

## 🚀 Quick Start Guide

### Prerequisites
- Docker and Docker Compose installed
- Port 8000 available on your system
- WhatsApp mobile app for QR code scanning

### 1. Clone and Setup
```bash
git clone <your-repo>
cd "notification Engine"
chmod +x setup.sh
./setup.sh
```

### 2. Watch for QR Code
```bash
# Monitor container logs to see QR code
sudo docker compose logs -f whatsapp-gateway

# The QR code will appear in the logs - scan it with WhatsApp mobile app
```

### 3. Verify Connection
```bash
# Check if WhatsApp is connected
curl http://localhost:8000/health

# Check detailed status
curl http://localhost:8000/status
```

### 4. Send Your First Message
```bash
# Using the test script
python3 send_test_message.py "+1234567890" "Hello from WhatsApp API!"

# Using curl
curl -X POST "http://localhost:8000/send" \
     -H "Content-Type: application/json" \
     -d '{"phone": "+1234567890", "message": "Hello World!"}'
```

## 📱 API Usage Examples

### Send Text Message
```bash
curl -X POST "http://localhost:8000/send" \
     -H "Content-Type: application/json" \
     -d '{
       "phone": "+1234567890",
       "message": "Hello from WhatsApp API Gateway!"
     }'
```

### Send Image File
```bash
curl -X POST "http://localhost:8000/send-image" \
     -F "phone=+1234567890" \
     -F "image=@/path/to/image.jpg" \
     -F "caption=Check out this image!"
```

### Send Image from URL
```bash
curl -X POST "http://localhost:8000/send-image-url" \
     -H "Content-Type: application/json" \
     -d '{
       "phone": "+1234567890",
       "imageUrl": "https://example.com/image.jpg",
       "caption": "Image from URL"
     }'
```

### Check Health Status
```bash
curl http://localhost:8000/health
```

## 🧪 Testing Tools

### Interactive Test Client
```bash
python3 test_client.py
```
Features:
- Health and status checking
- Single message sending
- Bulk messaging (multiple messages)
- Interactive messaging mode
- Auto messaging with intervals

### Simple Message Sender
```bash
python3 send_test_message.py "+1234567890" "Test message"
```

### Image Sender Utility
```bash
python3 image_sender.py
```
Features:
- Send local image files
- Send images from URLs
- Create and send sample images
- Add captions to images

## 🔧 Management Commands

### View Logs
```bash
# All services
sudo docker compose logs -f

# Python API only
sudo docker compose logs -f whatsapp-gateway | grep python-api

# Baileys server only  
sudo docker compose logs -f whatsapp-gateway | grep baileys-server
```

### Restart Services
```bash
# Restart everything
sudo docker compose restart

# Rebuild and restart
sudo docker compose down
sudo docker compose up --build -d
```

### Stop Services
```bash
sudo docker compose down
```

## 📊 API Endpoints Reference

| Method | Endpoint | Description | Parameters |
|--------|----------|-------------|------------|
| GET | `/` | API information and documentation | None |
| GET | `/health` | System health check | None |
| GET | `/status` | Detailed system status | None |
| POST | `/send` | Send text message | `phone`, `message` |
| POST | `/send-image` | Send image file | `phone`, `image` (file), `caption` (optional) |
| POST | `/send-image-url` | Send image from URL | `phone`, `imageUrl`, `caption` (optional) |
| POST | `/test-connection` | Test Baileys connectivity | None |

## 🔍 Troubleshooting

### Common Issues

#### 1. WhatsApp Not Connected
**Symptoms**: API returns "WhatsApp not connected" errors
**Solution**: 
- Check logs: `sudo docker compose logs -f whatsapp-gateway`
- Look for QR code in logs and scan with WhatsApp mobile app
- Wait for "Connected to WhatsApp" message

#### 2. Port Already in Use
**Symptoms**: Container fails to start with port binding errors
**Solution**:
- Check what's using port 8000: `sudo lsof -i :8000`
- Stop conflicting service or change port in docker-compose.yml

#### 3. Authentication Session Expired
**Symptoms**: Sudden disconnection after working fine
**Solution**:
- WhatsApp sessions expire periodically
- Check logs for disconnection reason
- Re-scan QR code when prompted

#### 4. Image Upload Fails
**Symptoms**: Image sending returns errors
**Solution**:
- Check file size (max 16MB)
- Verify file type (jpg, png, gif, webp supported)
- Ensure proper file permissions

### Log Analysis
```bash
# Check for connection issues
sudo docker compose logs whatsapp-gateway | grep -i "connect\|disconnect\|error"

# Monitor real-time logs
sudo docker compose logs -f whatsapp-gateway

# Check specific service logs
sudo docker compose exec whatsapp-gateway cat /var/log/baileys-server.log
sudo docker compose exec whatsapp-gateway cat /var/log/python-api.log
```

## 🔒 Security Considerations

- **Authentication**: WhatsApp sessions are stored in persistent Docker volumes
- **Phone Numbers**: Always include country codes (+1, +44, etc.)
- **Rate Limiting**: WhatsApp has built-in rate limits - avoid spam
- **Network Security**: Consider using nginx proxy for production
- **Data Privacy**: Messages are sent directly through WhatsApp servers

## 🚀 Production Deployment

### Environment Variables
```yaml
# docker-compose.yml additions for production
environment:
  - NODE_ENV=production
  - PYTHONUNBUFFERED=1
  - API_PORT=8000
  - BAILEYS_PORT=3000
```

### Nginx Reverse Proxy
```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### Auto-Restart on Boot
```bash
# Add to systemd or use Docker restart policies
sudo docker compose up -d --restart unless-stopped
```

## 📚 Integration Examples

### Python Integration
```python
import requests

def send_whatsapp_message(phone, message):
    response = requests.post(
        "http://localhost:8000/send",
        json={"phone": phone, "message": message}
    )
    return response.json()

# Usage
result = send_whatsapp_message("+1234567890", "Hello from Python!")
```

### Node.js Integration
```javascript
const axios = require('axios');

async function sendWhatsAppMessage(phone, message) {
    const response = await axios.post('http://localhost:8000/send', {
        phone: phone,
        message: message
    });
    return response.data;
}

// Usage
sendWhatsAppMessage('+1234567890', 'Hello from Node.js!');
```

### Webhook Integration
```python
# Flask webhook example
from flask import Flask, request
import requests

app = Flask(__name__)

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.json
    # Send WhatsApp notification
    requests.post('http://localhost:8000/send', json={
        'phone': data['phone'],
        'message': f"Alert: {data['message']}"
    })
    return 'OK'
```

## 📈 Monitoring & Analytics

### Health Monitoring
```bash
# Set up monitoring with curl checks
#!/bin/bash
while true; do
    curl -s http://localhost:8000/health | jq '.baileys_connected'
    sleep 30
done
```

### Message Analytics
- Monitor logs for message success/failure rates
- Track connection uptime
- Monitor resource usage with `docker stats`

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Test thoroughly with the provided test scripts
4. Submit a pull request with detailed description

## 📝 License

MIT License - feel free to use in personal and commercial projects.

## 🆘 Support

For issues and support:
1. Check the troubleshooting section above
2. Review container logs for error details
3. Verify WhatsApp connection status
4. Check that all dependencies are properly installed

---

**Built with ❤️ using Baileys, FastAPI, and Docker**
**Purpose**: Get everything running with a single command
**What it does**:
- Checks if Docker is running
- Builds the container
- Starts services in background
- Shows service status
- Provides next steps and useful commands

### Additional Files

#### 11. `.gitignore` - Version Control
```gitignore
# Excludes sensitive and temporary files from git
```
**Important exclusions**:
- `auth_info/` - WhatsApp authentication data
- `node_modules/` - Node.js dependencies
- `__pycache__/` - Python cache files
- `logs/` - Application logs

## 🚀 Quick Start Guide

### Step 1: Run the Setup
```bash
# Make the script executable and run it
chmod +x setup.sh
./setup.sh
```

### Step 2: Authenticate WhatsApp
```bash
# Watch for the QR code in logs
docker-compose logs -f whatsapp-gateway
```
1. Look for the QR code in the terminal output
2. Open WhatsApp on your phone
3. Go to Settings → Linked Devices → Link a Device
4. Scan the QR code displayed in the terminal

### Step 3: Test the API
```bash
# Run the test client
python test_client.py
```

## 📡 API Usage Examples

### Basic Message Sending
```python
import requests

# Send a simple message
response = requests.post("http://localhost:8000/send", json={
    "phone": "+1234567890",
    "message": "Hello from WhatsApp API Gateway!"
})

print(response.json())
# Output: {"success": true, "message": "Message sent successfully", ...}
```

### Advanced Usage with Error Handling
```python
import requests
import time

class WhatsAppAPI:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
    
    def check_connection(self):
        """Check if WhatsApp is connected"""
        try:
            response = requests.get(f"{self.base_url}/status")
            if response.status_code == 200:
                data = response.json()
                return data.get("baileys_server", {}).get("whatsapp_connected", False)
        except:
            return False
        return False
    
    def send_message(self, phone, message):
        """Send a WhatsApp message"""
        if not self.check_connection():
            return {"success": False, "error": "WhatsApp not connected"}
        
        try:
            response = requests.post(f"{self.base_url}/send", json={
                "phone": phone,
                "message": message
            })
            return response.json()
        except Exception as e:
            return {"success": False, "error": str(e)}

# Usage
api = WhatsAppAPI()
result = api.send_message("+1234567890", "Hello World!")
print(result)
```

### Bulk Message Sending
```python
import requests
import time

def send_bulk_messages(contacts, message, delay=2):
    """Send messages to multiple contacts"""
    results = []
    
    for contact in contacts:
        try:
            response = requests.post("http://localhost:8000/send", json={
                "phone": contact,
                "message": message
            })
            results.append({
                "contact": contact,
                "success": response.status_code == 200,
                "response": response.json()
            })
            print(f"✅ Sent to {contact}")
            time.sleep(delay)  # Rate limiting
        except Exception as e:
            results.append({
                "contact": contact,
                "success": False,
                "error": str(e)
            })
            print(f"❌ Failed to send to {contact}: {e}")
    
    return results

# Example usage
contacts = ["+1234567890", "+0987654321", "+1122334455"]
message = "🤖 Automated message from our system!"
results = send_bulk_messages(contacts, message)
```

## 🔧 Configuration & Customization

### Environment Variables
You can customize behavior through environment variables in `docker-compose.yml`:

```yaml
environment:
  - NODE_ENV=production          # Node.js environment
  - PYTHONUNBUFFERED=1          # Python output buffering
  - LOG_LEVEL=info              # Logging level
```

### Port Configuration
Default ports:
- **8000**: Python FastAPI (main API - expose this externally)
- **3000**: Node.js Baileys server (internal communication)

To change ports, modify `docker-compose.yml`:
```yaml
ports:
  - "8080:8000"  # Change external port to 8080
  - "3001:3000"  # Change Node.js port to 3001
```

### Persistent Data
WhatsApp authentication is stored in a Docker volume:
```yaml
volumes:
  - whatsapp_auth:/app/auth_info  # Persistent authentication
  - ./logs:/var/log               # Access logs from host
```

## 📊 Monitoring & Troubleshooting

### Health Checks
```bash
# Check container health
docker-compose ps

# API health check
curl http://localhost:8000/health

# Detailed status
curl http://localhost:8000/status
```

### Log Monitoring
```bash
# All services
docker-compose logs -f

# Python API only
docker-compose logs -f whatsapp-gateway | grep python-api

# Baileys server only
docker-compose logs -f whatsapp-gateway | grep baileys-server

# Inside container
docker-compose exec whatsapp-gateway tail -f /var/log/python-api.log
docker-compose exec whatsapp-gateway tail -f /var/log/baileys-server.log
```

### Common Issues & Solutions

#### 1. QR Code Not Appearing
```bash
# Check if Baileys server is running
docker-compose logs whatsapp-gateway | grep "QR CODE"

# If no QR code, restart the container
docker-compose restart
```

#### 2. WhatsApp Connection Lost
```bash
# Check connection status
curl http://localhost:8000/status

# Restart services
docker-compose restart

# If persistent, clear auth and re-authenticate
docker volume rm notification-engine_whatsapp_auth
docker-compose restart
```

#### 3. Port Conflicts
```bash
# Check what's using the ports
lsof -i :8000
lsof -i :3000

# Stop conflicting services or change ports in docker-compose.yml
```

#### 4. Container Won't Start
```bash
# Check Docker daemon
docker info

# Check container logs
docker-compose logs

# Rebuild container
docker-compose down
docker-compose build --no-cache
docker-compose up
```

## 🔄 Extending the System

### Adding Media Support
To extend for images and documents, you would add to `whatsapp-server.js`:

```javascript
// Future enhancement: media support
app.post('/send-media', async (req, res) => {
    const { phone, mediaUrl, caption, mediaType } = req.body;
    
    // Download media
    // Send via Baileys
    // Return response
});
```

### Adding Webhook Support
For incoming message handling:

```javascript
// Add to whatsapp-server.js
sock.ev.on('messages.upsert', async (m) => {
    // Forward incoming messages to webhook URL
    // Useful for chatbots and automated responses
});
```

### Adding Group Messaging
```javascript
// Group message support
app.post('/send-group', async (req, res) => {
    const { groupId, message } = req.body;
    await sock.sendMessage(groupId, { text: message });
});
```

## 🛡️ Security Best Practices

1. **Network Security**: Only expose port 8000 externally
2. **Authentication**: Store auth data in secure volumes
3. **Rate Limiting**: Implement rate limiting for production
4. **Environment Variables**: Use `.env` files for sensitive config
5. **HTTPS**: Use reverse proxy (nginx) for HTTPS in production

## 🚀 Production Deployment

For production use:

1. **Use environment variables** for configuration
2. **Set up reverse proxy** (nginx) for HTTPS
3. **Implement rate limiting** to prevent abuse
4. **Monitor logs** and set up alerting
5. **Regular backups** of auth_info volume
6. **Update dependencies** regularly for security

## 📋 Command Reference

```bash
# Development
./setup.sh                          # Initial setup
python test_client.py              # Test the API
docker-compose logs -f             # Watch logs

# Management
docker-compose up -d               # Start in background
docker-compose down                # Stop services
docker-compose restart             # Restart services
docker-compose ps                  # Check status

# Troubleshooting
docker-compose build --no-cache    # Rebuild container
docker volume ls                   # List volumes
docker volume rm <volume_name>     # Remove volume (clears auth)
```

## 📝 Summary

This solution provides exactly what you requested:

✅ **Node.js Baileys server** for WhatsApp automation  
✅ **Python FastAPI wrapper** for clean REST API  
✅ **Single Docker container** with supervisord  
✅ **Persistent authentication** via volumes  
✅ **Auto-reconnection** on disconnect  
✅ **QR code authentication** in terminal  
✅ **Complete code examples** and testing  
✅ **Production-ready** with proper error handling  

The system is modular, extensible, and ready for production use. You can easily add media support, webhooks, group messaging, and other features as needed.

**Ready to send WhatsApp messages programmatically! 🚀**
   ```bash
   docker-compose logs -f whatsapp-gateway
   ```

2. **Scan the QR code** with your WhatsApp mobile app (Settings → Linked Devices → Link a Device)

3. **Wait for connection confirmation** in the logs

### 3. Test the API

```bash
# Check health
curl http://localhost:8000/health

# Check status
curl http://localhost:8000/status

# Send a message
curl -X POST http://localhost:8000/send \
  -H "Content-Type: application/json" \
  -d '{
    "phone": "+1234567890",
    "message": "Hello from WhatsApp API Gateway!"
  }'
```

## 📡 API Endpoints

### Python FastAPI (Port 8000)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | API information |
| `GET` | `/health` | Health check |
| `GET` | `/status` | Detailed status |
| `POST` | `/send` | Send WhatsApp message |
| `POST` | `/test-connection` | Test Baileys connection |

### Node.js Baileys Server (Port 3000)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Server health |
| `GET` | `/status` | WhatsApp status |
| `POST` | `/send-message` | Direct message sending |

## 🐍 Python Usage Examples

### Basic Message Sending

```python
import requests

# Send a simple message
response = requests.post("http://localhost:8000/send", json={
    "phone": "+1234567890",
    "message": "Hello World!"
})

print(response.json())
```

### Advanced Usage with Error Handling

```python
import requests
import time

class WhatsAppClient:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
    
    def wait_for_connection(self, timeout=300):
        """Wait for WhatsApp to connect"""
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                response = requests.get(f"{self.base_url}/status")
                if response.status_code == 200:
                    data = response.json()
                    if data.get("baileys_server", {}).get("whatsapp_connected"):
                        return True
            except:
                pass
            time.sleep(10)
        return False
    
    def send_message(self, phone, message):
        """Send a WhatsApp message"""
        try:
            response = requests.post(f"{self.base_url}/send", json={
                "phone": phone,
                "message": message
            })
            return response.json()
        except Exception as e:
            return {"success": False, "error": str(e)}

# Usage
client = WhatsAppClient()

# Wait for connection (after QR scan)
if client.wait_for_connection():
    result = client.send_message("+1234567890", "Hello from Python!")
    print(result)
else:
    print("Failed to connect to WhatsApp")
```

### Bulk Message Sending

```python
import requests
import time

def send_bulk_messages(contacts, message, delay=2):
    """Send message to multiple contacts with delay"""
    results = []
    
    for contact in contacts:
        try:
            response = requests.post("http://localhost:8000/send", json={
                "phone": contact,
                "message": message
            })
            results.append({
                "contact": contact,
                "success": response.status_code == 200,
                "response": response.json()
            })
            print(f"Sent to {contact}: {response.status_code}")
            
            # Add delay between messages
            time.sleep(delay)
            
        except Exception as e:
            results.append({
                "contact": contact,
                "success": False,
                "error": str(e)
            })
    
    return results

# Usage
contacts = ["+1234567890", "+0987654321"]
message = "Bulk message from API Gateway!"
results = send_bulk_messages(contacts, message)
```

## 🔧 Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `NODE_ENV` | `production` | Node.js environment |
| `PYTHONUNBUFFERED` | `1` | Python output buffering |

### Persistent Data

- **WhatsApp Auth**: Stored in `/app/auth_info` (Docker volume)
- **Logs**: Available in `/var/log/` inside container

### Port Configuration

- **Python API**: `8000` (expose this for external access)
- **Node.js Server**: `3000` (internal communication)

## 📊 Monitoring

### Health Checks

```bash
# Container health
docker-compose ps

# API health
curl http://localhost:8000/health

# Detailed status
curl http://localhost:8000/status
```

### Logs

```bash
# All services
docker-compose logs -f

# Python API only
docker-compose exec whatsapp-gateway tail -f /var/log/python-api.log

# Baileys server only
docker-compose exec whatsapp-gateway tail -f /var/log/baileys-server.log
```

## 🔍 Testing

Use the included test client:

```bash
python test_client.py
```

This will:
1. Check service health
2. Wait for WhatsApp connection
3. Send a test message
4. Provide detailed feedback

## 🛡️ Security Considerations

- **Network**: Only expose port 8000 externally
- **Auth Persistence**: Use Docker volumes for auth data
- **Rate Limiting**: Implement rate limiting for production use
- **Environment**: Use environment variables for sensitive config

## 🔄 Future Extensions

### Media Support

```python
# Future: Send image
response = requests.post("http://localhost:8000/send-media", json={
    "phone": "+1234567890",
    "media_url": "https://example.com/image.jpg",
    "caption": "Check this out!"
})
```

### Webhook Integration

```python
# Future: Webhook for incoming messages
@app.post("/webhook/message")
async def handle_incoming_message(message_data: dict):
    # Process incoming WhatsApp messages
    pass
```

### Group Messaging

```python
# Future: Send to groups
response = requests.post("http://localhost:8000/send-group", json={
    "group_id": "group@g.us",
    "message": "Hello group!"
})
```

## 🐛 Troubleshooting

### Common Issues

1. **QR Code Not Appearing**
   ```bash
   docker-compose logs whatsapp-gateway | grep "QR CODE"
   ```

2. **Connection Lost**
   - Check if phone is connected to internet
   - Restart container: `docker-compose restart`

3. **Port Conflicts**
   - Change ports in `docker-compose.yml`
   - Update client URLs accordingly

4. **Authentication Issues**
   - Remove auth volume: `docker volume rm notification-engine_whatsapp_auth`
   - Restart and re-scan QR code

### Debug Mode

```bash
# Run with debug logs
docker-compose down
docker-compose up --build
```

## 📝 License

MIT License - Feel free to modify and distribute.

## 🤝 Contributing

1. Fork the repository
2. Create feature branch
3. Submit pull request

---

**Ready to send WhatsApp messages programmatically! 🚀**
