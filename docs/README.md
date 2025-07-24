# Notification Engine - WhatsApp Integration System

A comprehensive, production-ready notification system that combines AI-powered fire/smoke detection with automated WhatsApp messaging capabilities. This system provides a complete dockerized solution for real-time alerts and notifications.

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                             Notification Engine                                 │
│                                                                                 │
│  ┌─────────────────────┐    ┌─────────────────────┐    ┌─────────────────────┐ │
│  │   AI Detection      │    │   WhatsApp Gateway  │    │    Configuration    │ │
│  │   (Port: 8001)      │    │                     │    │      Manager        │ │
│  │                     │    │ ┌─────────────────┐ │    │                     │ │
│  │ • Fire/Smoke Model  │────┤ │ Python FastAPI  │ │    │ • YAML Config      │ │
│  │ • Video Processing  │    │ │ (Port: 3051)    │ │    │ • Environment Vars │ │
│  │ • Alert Generation  │    │ └─────────────────┘ │    │ • Logging Setup    │ │
│  │ • TestAPI Endpoints │    │         │           │    │                     │ │
│  │                     │    │ ┌─────────────────┐ │    │                     │ │
│  │                     │    │ │ Node.js Baileys │ │    │                     │ │
│  │                     │    │ │ (Port: 3050)    │ │    │                     │ │
│  │                     │    │ └─────────────────┘ │    │                     │ │
│  └─────────────────────┘    └─────────────────────┘    └─────────────────────┘ │
│                                                                                 │
│                           ┌─────────────────────────────┐                      │
│                           │      Docker Container       │                      │
│                           │                             │                      │
│                           │ • Supervisord Management    │                      │
│                           │ • Persistent Authentication │                      │
│                           │ • Volume Mounting           │                      │
│                           │ • Health Monitoring         │                      │
│                           └─────────────────────────────┘                      │
└─────────────────────────────────────────────────────────────────────────────────┘
```

## 🚀 Key Features

### AI Detection Engine
- **Fire/Smoke Detection**: Advanced YOLO-based model for real-time fire and smoke detection
- **Video Stream Processing**: Support for live video streams and recorded files
- **Configurable Thresholds**: Adjustable confidence levels for detection accuracy
- **Alert Management**: Intelligent alert generation with deduplication and timing controls

### WhatsApp Integration
- **Baileys Library**: Latest WhatsApp Web automation using @whiskeysockets/baileys v6.6.0
- **Multi-Format Support**: Send text messages, images, videos, and documents
- **Persistent Sessions**: QR code authentication with session persistence
- **Auto-Reconnection**: Robust connection management with automatic reconnection
- **Rate Limiting**: Built-in protection against spam and rate limits

### Containerized Architecture
- **Docker Compose**: Single-command deployment with docker-compose
- **Supervisord Management**: Multi-process container running both Node.js and Python services
- **Volume Persistence**: Persistent WhatsApp authentication and log storage
- **Health Monitoring**: Built-in health checks and monitoring capabilities

## 📁 Project Structure

```
notification-Engine/
├── 📦 Core Application
│   ├── apps/
│   │   ├── ai_detection/
│   │   │   ├── TestAPI.py              # AI detection API server
│   │   │   └── model/                  # AI model files
│   │   └── whatsapp_gateway/
│   │       ├── whatsapp-server.js      # Node.js Baileys server
│   │       ├── python_api.py           # Python FastAPI bridge
│   │       └── package.json            # Node.js dependencies
│   │
├── 🐳 Docker Configuration
│   ├── Dockerfile                      # Multi-service container definition
│   ├── docker-compose.yml              # Container orchestration
│   ├── supervisord.conf                # Process management
│   ├── entrypoint.sh                   # Container initialization
│   └── requirements.txt                # Python dependencies
│   
├── ⚙️ Configuration
│   ├── config/
│   │   └── config.yaml                 # Main configuration file
│   └── logs/                           # Application logs
│   
├── 📚 Documentation
│   ├── README.md                       # This file
│   └── WHATSAPP_DEPLOYMENT.md          # Deployment guide
│   
└── 📁 Data & Models
    ├── data/                           # Video files and outputs
    └── models/                         # AI detection models
```

## 🔧 Component Details

### 1. WhatsApp Gateway Services

#### Node.js Baileys Server (`whatsapp-server.js`)
**Purpose**: Core WhatsApp Web automation server
**Port**: 3050
**Technology**: Node.js with Express.js

**Key Features**:
- WhatsApp Web connection using Baileys library
- QR code generation and authentication
- Message sending (text, images, videos, documents)
- Connection state management and auto-reconnection
- RESTful API endpoints for communication

**Dependencies** (`package.json`):
```json
{
  "dependencies": {
    "@whiskeysockets/baileys": "^6.6.0",  // WhatsApp Web API
    "express": "^4.18.2",                // Web server framework
    "qrcode-terminal": "^0.12.0",        // QR code display
    "pino": "^8.16.1",                   // High-performance logging
    "cors": "^2.8.5",                    // Cross-origin requests
    "multer": "^1.4.5-lts.1"             // File upload handling
  }
}
```

**API Endpoints**:
```javascript
GET  /health              // Server health check
GET  /status              // WhatsApp connection status
POST /send-message        // Send text messages
POST /send-image          // Send images with file upload
POST /send-video          // Send videos with file upload
POST /send-document       // Send documents
```

#### Python FastAPI Bridge (`python_api.py`)
**Purpose**: Clean Python interface to Baileys server
**Port**: 3051
**Technology**: FastAPI with async support

**Key Features**:
- RESTful API with automatic OpenAPI documentation
- Async HTTP client for communication with Baileys server
- Request validation using Pydantic models
- Comprehensive error handling and logging
- Health monitoring of both services

**Dependencies** (`requirements.txt`):
```python
fastapi==0.104.1          # Modern web framework
uvicorn[standard]==0.24.0 # ASGI server
httpx==0.25.2             # Async HTTP client
pydantic==2.5.0           # Data validation
python-multipart==0.0.6   # File upload support
aiofiles==23.2.1          # Async file operations
PyYAML==6.0.1             # Configuration parsing
```

**API Endpoints**:
```python
GET  /                    # API information
GET  /health              # System health check
GET  /status              # Detailed service status
POST /send                # Send WhatsApp messages
POST /send-image          # Send images via URL or upload
POST /test-connection     # Test Baileys connectivity
```

### 2. AI Detection Engine

#### TestAPI Server (`TestAPI.py`)
**Purpose**: AI-powered fire and smoke detection with WhatsApp integration
**Port**: 8001
**Technology**: FastAPI with computer vision models

**Key Features**:
- YOLO-based fire and smoke detection
- Real-time video stream processing
- Configurable detection thresholds
- Automatic alert generation and deduplication
- Integration with WhatsApp gateway for notifications

**Main Endpoints**:
```python
GET  /video_feed                    # Live video stream
GET  /config_status                 # Configuration status
POST /send-video-to-whatsapp        # Send video alerts
POST /send-image-to-whatsapp        # Send image alerts  
POST /send-message-to-whatsapp      # Send text alerts
```

### 3. Docker Infrastructure

#### Dockerfile - Multi-Service Container
**Base Image**: node:20-bullseye
**Purpose**: Single container running both Node.js and Python services

**Build Process**:
```dockerfile
# System dependencies installation
RUN apt-get update && apt-get install -y \
    python3 python3-pip supervisor curl

# Node.js dependencies
COPY apps/whatsapp_gateway/package*.json ./
RUN npm install --production

# Python dependencies  
COPY requirements.txt ./
RUN pip3 install -r requirements.txt

# Application files
COPY apps/whatsapp_gateway/ ./
COPY config/ ./config/
COPY supervisord.conf entrypoint.sh ./

# Expose ports: 3050 (Node.js), 3051 (Python)
EXPOSE 3050 3051
```

#### Docker Compose - Orchestration
**File**: `docker-compose.yml`
**Purpose**: Complete system deployment and management

**Configuration**:
```yaml
services:
  whatsapp-gateway:
    build: .
    ports:
      - "3051:3051"  # Python FastAPI
      - "3050:3050"  # Node.js Baileys
    volumes:
      - whatsapp_auth:/app/auth_info    # Persistent WhatsApp auth
      - ./logs:/app/logs                # Log access
      - ./config:/app/config            # Configuration
    environment:
      - NODE_ENV=production
      - PYTHONUNBUFFERED=1
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3051/health"]
```

#### Supervisord - Process Management
**File**: `supervisord.conf`
**Purpose**: Manage multiple processes within single container

**Configuration**:
```ini
[program:baileys-server]
command=node whatsapp-server.js
directory=/app
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/baileys-server.log

[program:python-api]
command=python3 python_api.py
directory=/app
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/python-api.log
```

### 4. Configuration Management

#### Main Configuration (`config/config.yaml`)
**Purpose**: Centralized configuration for all services

**Structure**:
```yaml
# AI Model Configuration
model:
  fire_detection:
    path: "models/firesmoke_v4-8m_20241223.pt"
    confidence_threshold: 0.5

# WhatsApp Service URLs
whatsapp:
  api:
    python_server_url: "http://localhost:3051"
    baileys_server_url: "http://localhost:3050"
  phone_number: "+1234567890"
  send_images: true
  send_videos: true
  send_text: true

# Server Configuration
server:
  host: "0.0.0.0"
  port: 8001
  reload: false

# Logging Configuration
logging:
  level: "INFO"
  file_path: "logs/fire_detection.log"

# Notification Settings
notification:
  initial_alert_counter: 1
  default_priority: "High"
```

## 🚀 Quick Start Guide

### Prerequisites
- Docker and Docker Compose installed
- Ports 3050, 3051, and 8001 available
- WhatsApp mobile app for QR code scanning

### 1. Clone and Setup
```bash
# Clone the repository
git clone https://github.com/darknessth22/notification-Engine.git
cd "notification Engine"

# Make scripts executable
chmod +x entrypoint.sh
```

### 2. Deploy with Docker Compose
```bash
# Build and start all services
docker-compose up -d --build

# Monitor logs for QR code
docker-compose logs -f whatsapp-gateway
```

### 3. WhatsApp Authentication
1. **Watch for QR Code**: Monitor the logs until QR code appears
2. **Scan QR Code**: Open WhatsApp → Settings → Linked Devices → Link a Device
3. **Confirm Connection**: Wait for "Connected to WhatsApp" message in logs

### 4. Verify Services
```bash
# Check all service health
curl http://localhost:3051/health

# Check AI detection API
curl http://localhost:8001/config_status

# Test WhatsApp messaging
curl -X POST "http://localhost:3051/send" \
     -H "Content-Type: application/json" \
     -d '{"phone": "+1234567890", "message": "Hello from Notification Engine!"}'
```

## 📱 API Usage Examples

### Send WhatsApp Messages
```python
import requests

# Send text message
response = requests.post("http://localhost:3051/send", json={
    "phone": "+1234567890",
    "message": "Alert: Fire detected in building A!"
})

# Send image with caption
with open("alert_image.jpg", "rb") as f:
    files = {"image": f}
    data = {
        "phone": "+1234567890",
        "caption": "🚨 Fire Detection Alert - Building A"
    }
    response = requests.post("http://localhost:3051/send-image", 
                           files=files, data=data)
```

### AI Detection Integration
```python
import requests

# Send fire detection alert
alert_data = {
    "video": open("fire_detected.mp4", "rb"),
    "caption": "🔥 FIRE DETECTED - Immediate attention required!",
    "alert_id": "FIRE_001_2025"
}

response = requests.post("http://localhost:8001/send-video-to-whatsapp", 
                        files={"video": alert_data["video"]},
                        data={"caption": alert_data["caption"], 
                              "alert_id": alert_data["alert_id"]})
```

## 🔧 Configuration Options

### Environment Variables
```bash
# Docker environment variables
NODE_ENV=production              # Node.js environment
PYTHONUNBUFFERED=1              # Python output buffering
LOG_LEVEL=INFO                  # Application log level
```

### Port Configuration
- **3050**: Node.js Baileys WhatsApp server
- **3051**: Python FastAPI gateway  
- **8001**: AI detection API server

### WhatsApp Settings
```yaml
whatsapp:
  phone_number: "+1234567890"    # Destination phone number
  send_images: true              # Enable image alerts
  send_videos: true              # Enable video alerts
  send_text: true                # Enable text alerts
```

## 📊 Monitoring and Logging

### Service Health Checks
```bash
# Container health
docker-compose ps

# Individual service health
curl http://localhost:3051/health
curl http://localhost:8001/config_status

# Detailed system status
curl http://localhost:3051/status
```

### Log Management
```bash
# View all logs
docker-compose logs -f

# WhatsApp service logs
docker-compose logs -f whatsapp-gateway

# AI detection logs
tail -f logs/fire_detection.log

# Individual service logs inside container
docker-compose exec whatsapp-gateway cat /var/log/baileys-server.log
docker-compose exec whatsapp-gateway cat /var/log/python-api.log
```

### Performance Monitoring
```bash
# Container resource usage
docker stats

# Service response times
time curl http://localhost:3051/health
time curl http://localhost:8001/config_status
```

## 🛡️ Security and Production Considerations

### Security Best Practices
- **Network Isolation**: Use Docker networks for service communication
- **Environment Variables**: Store sensitive configuration in environment variables
- **Authentication**: Secure WhatsApp session data in persistent volumes
- **Rate Limiting**: Implement rate limiting for API endpoints
- **HTTPS**: Use reverse proxy (nginx) for HTTPS in production

### Production Deployment
```bash
# Production docker-compose override
cat > docker-compose.prod.yml << EOF
version: '3.8'
services:
  whatsapp-gateway:
    environment:
      - NODE_ENV=production
      - LOG_LEVEL=WARN
    restart: always
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 2G
        reservations:
          cpus: '1.0'
          memory: 1G
EOF

# Deploy to production
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

### Backup and Recovery
```bash
# Backup WhatsApp authentication
docker run --rm -v notification-engine_whatsapp_auth:/data -v $(pwd):/backup ubuntu tar czf /backup/whatsapp_auth_backup.tar.gz -C /data .

# Restore WhatsApp authentication
docker run --rm -v notification-engine_whatsapp_auth:/data -v $(pwd):/backup ubuntu tar xzf /backup/whatsapp_auth_backup.tar.gz -C /data
```

## 🔧 Troubleshooting

### Common Issues

#### 1. WhatsApp Connection Problems
```bash
# Check QR code generation
docker-compose logs whatsapp-gateway | grep -i "qr\|code"

# Reset WhatsApp session
docker volume rm notification-engine_whatsapp_auth
docker-compose restart
```

#### 2. Port Conflicts
```bash
# Check port usage
sudo lsof -i :3050
sudo lsof -i :3051
sudo lsof -i :8001

# Change ports in docker-compose.yml if needed
```

#### 3. Container Startup Issues
```bash
# Check container status
docker-compose ps

# View startup logs
docker-compose logs whatsapp-gateway

# Rebuild container
docker-compose down
docker-compose up --build -d
```

#### 4. AI Model Loading Problems
```bash
# Check model file existence
ls -la apps/ai_detection/model/

# Check AI detection logs
tail -f logs/fire_detection.log

# Test AI API directly
curl http://localhost:8001/config_status
```

### Debug Mode
```bash
# Run in debug mode with console output
docker-compose down
docker-compose up --build

# Enable debug logging
export LOG_LEVEL=DEBUG
docker-compose up --build
```

## 🚀 Development and Extension

### Adding New Features

#### New Detection Models
```python
# Add new model in config/config.yaml
model:
  smoke_detection:
    path: "models/smoke_v2.pt"
    confidence_threshold: 0.6
```

#### Custom Alert Types
```python
# Extend TestAPI.py with new alert endpoints
@app.post("/send-custom-alert")
async def send_custom_alert(request: Request):
    # Custom alert logic
    pass
```

#### Additional WhatsApp Features
```javascript
// Add new endpoints in whatsapp-server.js
app.post('/send-document', async (req, res) => {
    // Document sending logic
});
```

### API Documentation
- **FastAPI Docs**: http://localhost:3051/docs (automatic OpenAPI documentation)
- **Health Endpoints**: Real-time service status monitoring
- **Configuration API**: Dynamic configuration management

## 📈 Performance Optimization

### Resource Allocation
```yaml
# Docker Compose resource limits
deploy:
  resources:
    limits:
      cpus: '2.0'
      memory: 2G
    reservations:
      cpus: '1.0'
      memory: 1G
```

### Caching and Optimization
- **Model Caching**: AI models loaded once and cached in memory
- **Connection Pooling**: HTTP connection reuse for API calls
- **Async Processing**: Non-blocking operations for better throughput

## 🤝 Contributing

### Development Setup
```bash
# Clone repository
git clone https://github.com/darknessth22/notification-Engine.git

# Install development dependencies
cd "notification Engine/apps/whatsapp_gateway"
npm install

# Install Python dependencies
pip install -r requirements.txt

# Run services locally for development
npm run dev                    # Node.js service
python python_api.py          # Python service
python apps/ai_detection/TestAPI.py  # AI detection service
```

### Code Standards
- **JavaScript**: ESLint with Airbnb configuration
- **Python**: Black formatter with PEP 8 standards
- **Docker**: Multi-stage builds and security best practices
- **Documentation**: Comprehensive inline documentation

## 📄 License

MIT License - See LICENSE file for details.

## 🆘 Support

For issues and support:
1. Check the troubleshooting section above
2. Review container logs for error details  
3. Verify all services are running and healthy
4. Ensure WhatsApp connection is established
5. Create an issue on GitHub with detailed error information

---

**Built with ❤️ for real-time notification and alert systems**

**Technologies**: FastAPI • Node.js • Baileys • Docker • YOLO • Computer Vision

**Ready for production deployment! 🚀**
