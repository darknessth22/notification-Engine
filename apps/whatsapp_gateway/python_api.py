from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
import httpx
import asyncio
import logging
from typing import Optional
import uvicorn
from datetime import datetime
import aiofiles
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="WhatsApp API Gateway",
    description="Python FastAPI wrapper for Baileys WhatsApp automation",
    version="1.0.0"
)

# Configuration
BAILEYS_SERVER_URL = "http://localhost:3000"

# Pydantic models
class SendMessageRequest(BaseModel):
    phone: str
    message: str

class SendImageUrlRequest(BaseModel):
    phone: str
    imageUrl: str
    caption: Optional[str] = None

class SendMessageResponse(BaseModel):
    success: bool
    message: str
    messageId: Optional[str] = None
    to: Optional[str] = None
    timestamp: str

class SendImageResponse(BaseModel):
    success: bool
    message: str
    messageId: Optional[str] = None
    to: Optional[str] = None
    fileName: Optional[str] = None
    fileType: Optional[str] = None
    imageUrl: Optional[str] = None
    timestamp: str

class HealthResponse(BaseModel):
    status: str
    baileys_connected: bool
    baileys_server_healthy: bool
    timestamp: str

# Helper function to check Baileys server health
async def check_baileys_health():
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{BAILEYS_SERVER_URL}/health")
            if response.status_code == 200:
                data = response.json()
                return {
                    "healthy": True,
                    "connected": data.get("connected", False),
                    "qr_required": data.get("qrRequired", True)
                }
    except Exception as e:
        logger.error(f"Failed to check Baileys health: {e}")
    
    return {"healthy": False, "connected": False, "qr_required": True}

@app.get("/")
async def root():
    return {
        "message": "WhatsApp API Gateway",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "send": "/send",
            "send_image": "/send-image",
            "send_image_url": "/send-image-url",
            "status": "/status"
        }
    }

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Check the health of both Python API and Baileys server"""
    baileys_health = await check_baileys_health()
    
    return HealthResponse(
        status="healthy",
        baileys_connected=baileys_health["connected"],
        baileys_server_healthy=baileys_health["healthy"],
        timestamp=datetime.now().isoformat()
    )

@app.get("/status")
async def get_status():
    """Get detailed status information"""
    baileys_health = await check_baileys_health()
    
    return {
        "python_api": {
            "status": "running",
            "version": "1.0.0"
        },
        "baileys_server": {
            "healthy": baileys_health["healthy"],
            "whatsapp_connected": baileys_health["connected"],
            "qr_code_required": baileys_health["qr_required"]
        },
        "timestamp": datetime.now().isoformat()
    }

@app.post("/send", response_model=SendMessageResponse)
async def send_message(request: SendMessageRequest):
    """Send a WhatsApp message via Baileys server"""
    try:
        # Validate input
        if not request.phone or not request.message:
            raise HTTPException(
                status_code=400,
                detail="Phone number and message are required"
            )

        # Check if Baileys server is healthy first
        baileys_health = await check_baileys_health()
        if not baileys_health["healthy"]:
            raise HTTPException(
                status_code=503,
                detail="Baileys server is not responding"
            )

        if not baileys_health["connected"]:
            raise HTTPException(
                status_code=503,
                detail="WhatsApp is not connected. Please scan QR code first."
            )

        # Forward request to Baileys server
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{BAILEYS_SERVER_URL}/send-message",
                json={
                    "phone": request.phone,
                    "message": request.message
                }
            )

            if response.status_code == 200:
                data = response.json()
                logger.info(f"Message sent successfully to {request.phone}")
                
                return SendMessageResponse(
                    success=data["success"],
                    message=data["message"],
                    messageId=data.get("messageId"),
                    to=data.get("to"),
                    timestamp=data["timestamp"]
                )
            else:
                error_data = response.json()
                raise HTTPException(
                    status_code=response.status_code,
                    detail=error_data.get("error", "Failed to send message")
                )

    except httpx.TimeoutException:
        logger.error("Timeout while sending message to Baileys server")
        raise HTTPException(
            status_code=504,
            detail="Request timeout while sending message"
        )
    except httpx.RequestError as e:
        logger.error(f"Request error: {e}")
        raise HTTPException(
            status_code=503,
            detail="Failed to connect to Baileys server"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error"
        )

@app.post("/send-image", response_model=SendImageResponse)
async def send_image(
    phone: str = Form(...),
    image: UploadFile = File(...),
    caption: Optional[str] = Form(None)
):
    """Send an image via WhatsApp"""
    try:
        # Validate input
        if not phone:
            raise HTTPException(
                status_code=400,
                detail="Phone number is required"
            )

        # Check if Baileys server is healthy first
        baileys_health = await check_baileys_health()
        if not baileys_health["healthy"]:
            raise HTTPException(
                status_code=503,
                detail="Baileys server is not responding"
            )

        if not baileys_health["connected"]:
            raise HTTPException(
                status_code=503,
                detail="WhatsApp is not connected. Please scan QR code first."
            )

        # Prepare multipart form data
        files = {"image": (image.filename, await image.read(), image.content_type)}
        data = {"phone": phone}
        if caption:
            data["caption"] = caption

        # Forward request to Baileys server
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{BAILEYS_SERVER_URL}/send-image",
                files=files,
                data=data
            )

            if response.status_code == 200:
                data = response.json()
                logger.info(f"Image sent successfully to {phone}")
                
                return SendImageResponse(
                    success=data["success"],
                    message=data["message"],
                    messageId=data.get("messageId"),
                    to=data.get("to"),
                    fileName=data.get("fileName"),
                    fileType=data.get("fileType"),
                    timestamp=data["timestamp"]
                )
            else:
                error_data = response.json()
                raise HTTPException(
                    status_code=response.status_code,
                    detail=error_data.get("error", "Failed to send image")
                )

    except httpx.TimeoutException:
        logger.error("Timeout while sending image to Baileys server")
        raise HTTPException(
            status_code=504,
            detail="Request timeout while sending image"
        )
    except httpx.RequestError as e:
        logger.error(f"Request error: {e}")
        raise HTTPException(
            status_code=503,
            detail="Failed to connect to Baileys server"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error"
        )

@app.post("/send-image-url", response_model=SendImageResponse)
async def send_image_from_url(request: SendImageUrlRequest):
    """Send an image from URL via WhatsApp"""
    try:
        # Validate input
        if not request.phone or not request.imageUrl:
            raise HTTPException(
                status_code=400,
                detail="Phone number and image URL are required"
            )

        # Check if Baileys server is healthy first
        baileys_health = await check_baileys_health()
        if not baileys_health["healthy"]:
            raise HTTPException(
                status_code=503,
                detail="Baileys server is not responding"
            )

        if not baileys_health["connected"]:
            raise HTTPException(
                status_code=503,
                detail="WhatsApp is not connected. Please scan QR code first."
            )

        # Forward request to Baileys server
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{BAILEYS_SERVER_URL}/send-image-url",
                json={
                    "phone": request.phone,
                    "imageUrl": request.imageUrl,
                    "caption": request.caption
                }
            )

            if response.status_code == 200:
                data = response.json()
                logger.info(f"Image from URL sent successfully to {request.phone}")
                
                return SendImageResponse(
                    success=data["success"],
                    message=data["message"],
                    messageId=data.get("messageId"),
                    to=data.get("to"),
                    imageUrl=data.get("imageUrl"),
                    timestamp=data["timestamp"]
                )
            else:
                error_data = response.json()
                raise HTTPException(
                    status_code=response.status_code,
                    detail=error_data.get("error", "Failed to send image from URL")
                )

    except httpx.TimeoutException:
        logger.error("Timeout while sending image from URL to Baileys server")
        raise HTTPException(
            status_code=504,
            detail="Request timeout while sending image from URL"
        )
    except httpx.RequestError as e:
        logger.error(f"Request error: {e}")
        raise HTTPException(
            status_code=503,
            detail="Failed to connect to Baileys server"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error"
        )

# Additional endpoint for testing
@app.post("/test-connection")
async def test_connection():
    """Test connection to Baileys server"""
    baileys_health = await check_baileys_health()
    return {
        "baileys_server_reachable": baileys_health["healthy"],
        "whatsapp_connected": baileys_health["connected"],
        "qr_code_required": baileys_health["qr_required"],
        "timestamp": datetime.now().isoformat()
    }

if __name__ == "__main__":
    uvicorn.run(
        "python_api:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info"
    )
