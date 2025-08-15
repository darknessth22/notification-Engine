# Notification Engine - Multi-Number WhatsApp Alerts

A clean, production-ready system for AI-powered violation detection with multi-number WhatsApp notifications.

## 🚀 Quick Start

1. **Configure phone numbers** in `config/config.yaml`:
```yaml
whatsapp:
  phone_numbers:
    - "+1234567890"    # Primary number
    - "+0987654321"    # Secondary number
```

2. **Start the system**:
```bash
docker-compose up -d
```

3. **Test multi-number alerts**:
```bash
# Text message test
curl -X POST http://localhost:8001/send-message-to-whatsapp \
  -H "Content-Type: application/json" \
  -d '{"message": "Test alert", "alert_id": "TEST_001"}'

# Image alert test
curl -X POST http://localhost:8001/send-image-to-whatsapp \
  -F "image=@your_image.jpg" \
  -F "caption=Violation detected" \
  -F "alert_id=IMG_001"
```

## 📱 Multi-Number Support

- **Automatic distribution** to all configured phone numbers
- **Individual delivery tracking** with success/failure status
- **Easy scaling** - just add numbers to config and restart
- **Proven reliability** with working file handling for images/videos

## 🏗️ Architecture

- **TestAPI** (Port 8001): AI detection + multi-number logic
- **Python API** (Port 3051): Simple WhatsApp gateway  
- **Baileys Server** (Port 3050): WhatsApp Web connection
- **Clean codebase**: Removed all legacy/unused code

## 📖 Documentation

See `docs/README.md` for complete documentation.