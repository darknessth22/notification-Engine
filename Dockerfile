# WhatsApp Gateway Services - Core notification engine
FROM node:20-bullseye

# Install system dependencies for WhatsApp services
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    supervisor \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy package files and install Node.js dependencies
COPY apps/whatsapp_gateway/package*.json ./
RUN npm install --production

# Install Python dependencies for API bridge
COPY requirements.txt ./
RUN pip3 install -r requirements.txt

# Copy WhatsApp gateway application files
COPY apps/whatsapp_gateway/whatsapp-server.js ./
COPY apps/whatsapp_gateway/python_api.py ./
COPY config/ ./config/
COPY supervisord.conf ./
COPY entrypoint.sh ./

# Make entrypoint executable
RUN chmod +x entrypoint.sh

# Create directories for logs and auth
RUN mkdir -p /var/log /var/run /app/auth_info /app/logs

# Expose ports for WhatsApp services only
EXPOSE 3050 3051

# Health check for WhatsApp services
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:3051/health || exit 1

# Set entrypoint
ENTRYPOINT ["./entrypoint.sh"]
