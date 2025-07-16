# Use Node.js 20 as base image (includes better crypto support)
FROM node:20-bullseye

# Install system dependencies
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    supervisor \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy package files
COPY apps/whatsapp_gateway/package*.json ./
COPY requirements.txt ./

# Install Node.js dependencies
RUN npm install --production

# Install Python dependencies
RUN pip3 install -r requirements.txt

# Copy application files
COPY apps/whatsapp_gateway/whatsapp-server.js ./
COPY apps/whatsapp_gateway/python_api.py ./
COPY supervisord.conf ./
COPY entrypoint.sh ./

# Make entrypoint executable
RUN chmod +x entrypoint.sh

# Create directories for logs and auth
RUN mkdir -p /var/log /var/run /app/auth_info

# Expose ports
EXPOSE 3000 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Set entrypoint
ENTRYPOINT ["./entrypoint.sh"]
