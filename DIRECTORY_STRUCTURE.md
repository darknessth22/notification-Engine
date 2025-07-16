# Directory Structure Documentation

## 📁 Organized Project Structure

```
notification-Engine/
├── 📄 Project Root Files
│   ├── Dockerfile                          # Main container build
│   ├── docker-compose.yml                  # Container orchestration
│   ├── requirements.txt                    # Python dependencies
│   ├── supervisord.conf                    # Process management
│   ├── entrypoint.sh                       # Container startup script
│   ├── setup.sh                           # Automated setup script
│   └── .gitignore                         # Git ignore rules
│
├── 📱 apps/                               # Application modules
│   ├── whatsapp_gateway/                  # WhatsApp messaging service
│   │   ├── whatsapp-server.js             # Baileys Node.js server
│   │   ├── python_api.py                  # FastAPI gateway
│   │   └── package.json                   # Node.js dependencies
│   │
│   └── ai_detection/                      # AI/ML detection system
│       ├── TestAPI.py                     # Detection API server
│       ├── config_manager.py              # Configuration management
│       ├── whatsapp_notifier.py           # Legacy Selenium notifier
│       ├── scrapper.py                    # Data scraping utilities
│       └── models/                        # AI model files
│           └── FireSmoke3.pt              # YOLO fire detection model
│
├── 🛠️ tools/                              # Development and testing tools
│   └── testing/                           # Testing utilities
│       ├── test_client.py                 # Comprehensive API testing
│       ├── send_test_message.py           # Simple message testing
│       └── image_sender.py                # Image/media testing
│
├── 📊 data/                               # Data storage
│   ├── videos/                            # Test video files
│   │   ├── firedemo.mp4
│   │   ├── firedemo2.mp4
│   │   ├── firetest3.mp4
│   │   └── firetest4.mp4
│   ├── images/                            # Image files and uploads
│   │   └── 13527969-d9fc-4479-8f42-00dccf1653dc.png
│   └── violations/                        # Detected violation data
│
├── 📚 docs/                               # Documentation
│   ├── README.md                          # Main project documentation
│   ├── TECHNICAL_DOCS.md                  # Technical implementation details
│   └── LIVE_PROCESSING_OPTIMIZATION.md   # Performance optimization guide
│
├── ⚙️ config/                             # Configuration files
│   └── config.yaml                        # Main configuration
│
├── 📝 logs/                               # Application logs
│   ├── baileys-server.log                # Node.js server logs
│   ├── python-api.log                    # Python API logs
│   └── supervisord.log                   # Process manager logs
│
├── 🗂️ legacy/                             # Deprecated/old code
│   └── (empty - ready for old files)
│
└── 🔧 Development Files
    ├── __pycache__/                       # Python cache
    ├── .vscode/                           # VS Code settings
    └── .git/                              # Git repository
```

## 🎯 Directory Purpose Explanation

### 📱 **apps/** - Application Modules
- **whatsapp_gateway/**: Complete WhatsApp messaging system
  - Baileys Node.js server for WhatsApp Web automation
  - FastAPI Python gateway for REST API
  - Node.js dependencies and configuration

- **ai_detection/**: AI/ML violation detection system
  - YOLO model integration
  - Video processing capabilities
  - Configuration management
  - Legacy notification system

### 🛠️ **tools/** - Development Tools
- **testing/**: All testing utilities in one place
  - Comprehensive API testing suite
  - Simple message testing tools
  - Image/media testing utilities

### 📊 **data/** - Data Storage
- **videos/**: Test and sample video files
- **images/**: Images, uploads, and media files
- **violations/**: Detected violation data and reports

### 📚 **docs/** - Documentation
- Complete project documentation
- Technical implementation details
- Optimization guides and best practices

### ⚙️ **config/** - Configuration
- Centralized configuration management
- YAML configuration files
- Environment-specific settings

### 📝 **logs/** - Logging
- Separated logs for each service
- Persistent logging across container restarts
- Easy debugging and monitoring

## 🔄 Path Updates Required

After reorganization, you'll need to update these paths:

### Docker Configuration
```dockerfile
# In Dockerfile, update copy commands:
COPY apps/whatsapp_gateway/whatsapp-server.js ./
COPY apps/whatsapp_gateway/python_api.py ./
COPY apps/whatsapp_gateway/package.json ./
```

### Docker Compose
```yaml
# In docker-compose.yml, update volume mounts:
volumes:
  - ./data/videos:/app/videos
  - ./data/images:/app/images
  - ./data/violations:/app/violations
```

### Configuration Files
```yaml
# Update paths in config/config.yaml:
model:
  fire_detection:
    path: "apps/ai_detection/models/FireSmoke3.pt"
```

### Testing Scripts
Update import paths in testing tools:
```python
# In tools/testing/test_client.py
API_BASE_URL = "http://localhost:8000"  # No change needed

# In tools/testing/send_test_message.py  
API_URL = "http://localhost:8000"  # No change needed
```

## 🚀 Benefits of This Organization

1. **Modular Structure**: Each app is self-contained
2. **Clear Separation**: Tools, data, docs, and code are separated
3. **Scalability**: Easy to add new apps or services
4. **Maintainability**: Easier to find and update specific components
5. **Development**: Better development workflow with organized tools
6. **Deployment**: Cleaner Docker builds with focused app directories

## 📋 Next Steps

1. Update Dockerfile to copy from new locations
2. Update docker-compose.yml volume mounts
3. Update configuration file paths
4. Test the reorganized structure
5. Update any hardcoded paths in Python/JavaScript files

This organization follows modern project structure best practices and makes the codebase much more maintainable and scalable.
