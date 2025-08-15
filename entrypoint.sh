#!/bin/bash

# Create log directories
mkdir -p /var/log
mkdir -p /var/run
mkdir -p /app/logs

# Create auth_info directory for WhatsApp authentication
mkdir -p /app/auth_info
chown -R root:root /app/auth_info

echo "🚀 Starting WhatsApp Gateway Services..."
echo "⏰ $(date): Container startup initiated"
echo "📱 Baileys Server: http://localhost:3050"
echo "🐍 Python API: http://localhost:3051"

# Start supervisord to manage both services
exec /usr/bin/supervisord -c /app/supervisord.conf
