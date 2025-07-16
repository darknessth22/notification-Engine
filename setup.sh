#!/bin/bash

# Build and run the WhatsApp API Gateway
echo "🚀 Building WhatsApp API Gateway..."

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

# Build the container
echo "📦 Building Docker container..."
sudo docker compose build

# Start the services
echo "🔄 Starting services..."
sudo docker compose up -d

# Wait a moment for services to start
sleep 5

# Show status
echo "📊 Service status:"
sudo docker compose ps

echo ""
echo "✅ Setup complete!"
echo ""
echo "📱 NEXT STEPS:"
echo "1. Watch for QR code: sudo docker compose logs -f whatsapp-gateway"
echo "2. Scan QR code with WhatsApp mobile app"
echo "3. Test the API: python test_client.py"
echo ""
echo "🌐 API Endpoints:"
echo "- Health: http://localhost:8000/health"
echo "- Status: http://localhost:8000/status"
echo "- Send Message: POST http://localhost:8000/send"
echo ""
echo "🧪 Testing Tools:"
echo "- Comprehensive testing: python tools/testing/test_client.py"
echo "- Simple message test: python tools/testing/send_test_message.py"
echo "- Image testing: python tools/testing/image_sender.py"
echo ""
echo "📋 Useful commands:"
echo "- View logs: sudo docker compose logs -f"
echo "- Stop services: sudo docker compose down"
echo "- Restart: sudo docker compose restart"
