#!/bin/bash

# Create log directories
mkdir -p /var/log
mkdir -p /var/run

# Create auth_info directory for WhatsApp authentication
mkdir -p /app/auth_info
chown -R root:root /app/auth_info

echo "🚀 Starting WhatsApp Baileys + Python API Gateway..."
echo "⏰ $(date): Container startup initiated"

# Start supervisord
exec /usr/bin/supervisord -c /app/supervisord.conf
