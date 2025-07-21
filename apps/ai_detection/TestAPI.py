# TestAPI.py

import cv2
import logging
import asyncio
import uvicorn
import httpx
import yaml
import os
import time
from datetime import datetime, timedelta
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
from ultralytics import YOLO

class TestAPI:
    def __init__(self, config_path: str = "config/config.yaml"):
        # Load configuration directly
        with open(config_path, 'r') as file:
            self.config = yaml.safe_load(file)
        
        # Initialize the fire detection model
        model_path = self.config['model']['fire_detection']['path']
        self.confidence_threshold = self.config['model']['fire_detection']['confidence_threshold']
        device = "cuda" if self.config.get('device', {}).get('prefer_cuda', False) else "cpu"
        
        self.fire_model = YOLO(model_path).to(device)

        # WhatsApp configuration
        self.whatsapp_config = self.config.get("whatsapp", {})
        self.whatsapp_api_url = self.whatsapp_config.get("api", {}).get("python_server_url", "http://localhost:8000")
        self.send_images = self.whatsapp_config.get("send_images", True)
        self.send_videos = self.whatsapp_config.get("send_videos", False)
        self.send_text = self.whatsapp_config.get("send_text", True)
        
        # Log notification modes
        notification_modes = []
        if self.send_images:
            notification_modes.append("images via endpoint")
        if self.send_videos:
            notification_modes.append("videos via endpoint + auto-recording")
        
        notification_mode = " + ".join(notification_modes) if notification_modes else "no notifications"
        logging.info(f"WhatsApp notification mode: {notification_mode}")
        logging.info("Text messages available via /send-message-to-whatsapp endpoint only")
        
        self.alert_counter = self.config.get("notification", {}).get("initial_alert_counter", 1)
        self.detection_status = {}  # For tracking detection timestamps
        
        # Video recording configuration for testing
        self.is_recording = False
        self.video_writer = None

        # Create and configure the FastAPI app
        self.app = FastAPI()
        self._configure_app()
        self._setup_routes()

    def _configure_app(self):
        from fastapi.middleware.cors import CORSMiddleware
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        logging.basicConfig(level=logging.DEBUG)
        # Register startup and shutdown events.
        self.app.add_event_handler("startup", self.startup_event)
        self.app.add_event_handler("shutdown", self.shutdown_event)

    def _setup_routes(self):
        # Define the video feed endpoint.
        self.app.get("/video_feed")(self.video_feed)
        # Add configuration status endpoint
        self.app.get("/config_status")(self.get_config_status)
        
        # Production endpoints for external systems
        self.app.post("/send-video-to-whatsapp")(self.send_video_to_whatsapp_endpoint)
        self.app.post("/send-image-to-whatsapp")(self.send_image_to_whatsapp_endpoint)
        self.app.post("/send-message-to-whatsapp")(self.send_message_to_whatsapp_endpoint)

    async def get_config_status(self):
        """Get current configuration settings"""
        return {
            "send_images": self.send_images,
            "send_videos": self.send_videos,
            "send_text": self.send_text,
            "confidence_threshold": self.confidence_threshold,
            "phone_number": self.whatsapp_config.get("phone_number"),
            "whatsapp_api_url": self.whatsapp_api_url,
            "recording_active": self.is_recording,
            "alert_counter": self.alert_counter,
            "available_endpoints": [
                "POST /send-video-to-whatsapp",
                "POST /send-image-to-whatsapp", 
                "POST /send-message-to-whatsapp"
            ],
            "timestamp": datetime.now().isoformat()
        }

    async def send_video_to_whatsapp_endpoint(self, request: Request):
        """
        Endpoint to receive video files and send them to WhatsApp
        Expected: multipart/form-data with 'video' file and optional 'caption', 'alert_id'
        """
        try:
            form = await request.form()
            video_file = form.get("video")
            caption = form.get("caption", "🚨 Violation Video Alert")
            alert_id = form.get("alert_id", f"ALERT{int(time.time())}")
            
            if not video_file:
                return {"success": False, "message": "No video file provided"}
            
            phone_number = self.whatsapp_config.get("phone_number")
            if not phone_number:
                return {"success": False, "message": "No phone number configured"}
            
            logging.info(f"Received video to send: {video_file.filename}")
            
            # Send video to WhatsApp
            async with httpx.AsyncClient(timeout=120.0) as client:
                files = {
                    'video': (video_file.filename, await video_file.read(), 'video/mp4')
                }
                data = {
                    'phone': phone_number,
                    'caption': f"{caption}\n📍 Alert ID: {alert_id}"
                }
                
                response = await client.post(
                    f"{self.whatsapp_api_url}/send-video",
                    files=files,
                    data=data
                )
            
            if response.status_code == 200:
                result = response.json()
                if result.get("success"):
                    logging.info(f"Video sent successfully via endpoint: {alert_id}")
                    return {"success": True, "message": "Video sent successfully", "alert_id": alert_id}
                else:
                    error_msg = result.get('message', 'Unknown error')
                    logging.error(f"Failed to send video: {error_msg}")
                    return {"success": False, "message": f"WhatsApp API error: {error_msg}"}
            else:
                logging.error(f"WhatsApp API HTTP error: {response.status_code}")
                return {"success": False, "message": f"HTTP error: {response.status_code}"}
                
        except Exception as e:
            logging.error(f"Error in send_video_to_whatsapp_endpoint: {e}")
            return {"success": False, "message": f"Server error: {str(e)}"}

    async def send_image_to_whatsapp_endpoint(self, request: Request):
        """
        Endpoint to receive image files and send them to WhatsApp
        Expected: multipart/form-data with 'image' file and optional 'caption', 'alert_id'
        """
        try:
            form = await request.form()
            image_file = form.get("image")
            caption = form.get("caption", "🚨 Violation Image Alert")
            alert_id = form.get("alert_id", f"ALERT{int(time.time())}")
            
            if not image_file:
                return {"success": False, "message": "No image file provided"}
            
            phone_number = self.whatsapp_config.get("phone_number")
            if not phone_number:
                return {"success": False, "message": "No phone number configured"}
            
            logging.info(f"Received image to send: {image_file.filename}")
            
            # Send image to WhatsApp
            async with httpx.AsyncClient(timeout=60.0) as client:
                files = {
                    'image': (image_file.filename, await image_file.read(), 'image/jpeg')
                }
                data = {
                    'phone': phone_number,
                    'caption': f"{caption}\n📍 Alert ID: {alert_id}"
                }
                
                response = await client.post(
                    f"{self.whatsapp_api_url}/send-image",
                    files=files,
                    data=data
                )
            
            if response.status_code == 200:
                result = response.json()
                if result.get("success"):
                    logging.info(f"Image sent successfully via endpoint: {alert_id}")
                    return {"success": True, "message": "Image sent successfully", "alert_id": alert_id}
                else:
                    error_msg = result.get('message', 'Unknown error')
                    logging.error(f"Failed to send image: {error_msg}")
                    return {"success": False, "message": f"WhatsApp API error: {error_msg}"}
            else:
                logging.error(f"WhatsApp API HTTP error: {response.status_code}")
                return {"success": False, "message": f"HTTP error: {response.status_code}"}
                
        except Exception as e:
            logging.error(f"Error in send_image_to_whatsapp_endpoint: {e}")
            return {"success": False, "message": f"Server error: {str(e)}"}

    async def send_message_to_whatsapp_endpoint(self, request: Request):
        """
        Endpoint to send text messages directly to WhatsApp API
        Expected: JSON with 'message' and optional 'alert_id'
        """
        try:
            data = await request.json()
            message = data.get("message")
            alert_id = data.get("alert_id", f"ALERT{int(time.time())}")
            
            if not message:
                return {"success": False, "message": "No message provided"}
            
            phone_number = self.whatsapp_config.get("phone_number")
            if not phone_number:
                return {"success": False, "message": "No phone number configured"}
            
            logging.info(f"Received message to send directly to WhatsApp: {alert_id}")
            
            # Send message directly to WhatsApp API
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.whatsapp_api_url}/send",
                    json={
                        "phone": phone_number,
                        "message": f"{message}\n📍 Alert ID: {alert_id}"
                    }
                )
            
            if response.status_code == 200:
                result = response.json()
                if result.get("success"):
                    logging.info(f"Message sent successfully directly to WhatsApp: {alert_id}")
                    return {"success": True, "message": "Message sent successfully", "alert_id": alert_id}
                else:
                    error_msg = result.get('message', 'Unknown error')
                    logging.error(f"Failed to send message to WhatsApp: {error_msg}")
                    return {"success": False, "message": f"WhatsApp API error: {error_msg}"}
            else:
                logging.error(f"WhatsApp API HTTP error: {response.status_code}")
                return {"success": False, "message": f"HTTP error: {response.status_code}"}
                
        except Exception as e:
            logging.error(f"Error in send_message_to_whatsapp_endpoint: {e}")
            return {"success": False, "message": f"Server error: {str(e)}"}

    def start_recording(self, frame):
        """Start recording video when violation is detected"""
        try:
            if not self.is_recording:
                # Create output directory
                os.makedirs("data/videos/violations", exist_ok=True)
                
                # Generate alert ID
                alert_id = f"ALERT{self.alert_counter:03d}"
                
                # Check for existing files with same alert number and remove them
                violations_dir = "data/videos/violations"
                for filename in os.listdir(violations_dir):
                    if filename.startswith(f"violation_{alert_id}_") and filename.endswith(".mp4"):
                        existing_file = os.path.join(violations_dir, filename)
                        os.remove(existing_file)
                        logging.info(f"Removed existing file: {filename}")
                
                # Generate new filename with current timestamp
                timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                filename = f"violation_{alert_id}_{timestamp}.mp4"
                filepath = f"data/videos/violations/{filename}"
                
                # Set up video writer
                height, width = frame.shape[:2]
                fourcc = cv2.VideoWriter_fourcc(*'mp4v')
                self.video_writer = cv2.VideoWriter(filepath, fourcc, 20.0, (width, height))
                
                self.is_recording = True
                logging.info(f"Started recording: {filename}")
                return filepath
        except Exception as e:
            logging.error(f"Error starting recording: {e}")
            return None

    def stop_recording(self):
        """Stop recording and save the video"""
        try:
            if self.is_recording and self.video_writer:
                self.video_writer.release()
                self.is_recording = False
                logging.info("Recording stopped and saved")
                return True
        except Exception as e:
            logging.error(f"Error stopping recording: {e}")
        return False

    async def auto_stop_recording(self, duration: float, video_path: str, alert_id: str):
        """Automatically stop recording after specified duration and send to WhatsApp"""
        await asyncio.sleep(duration)
        
        # Stop recording
        if self.stop_recording():
            # Wait a moment for file to be fully written
            await asyncio.sleep(0.5)
            
            # Check if file exists and send it
            if os.path.exists(video_path):
                logging.info(f"Auto-sending recorded video: {video_path}")
                await self.send_recorded_video_to_whatsapp(video_path, alert_id)
            else:
                logging.error(f"Recorded video file not found: {video_path}")

    async def send_recorded_video_to_whatsapp(self, video_path: str, alert_id: str):
        """Send the recorded video to WhatsApp using the endpoint (for testing)"""
        try:
            if not os.path.exists(video_path):
                logging.error(f"Recorded video file not found: {video_path}")
                return False
            
            # Extract filename for caption
            filename = os.path.basename(video_path)
            caption = f"🚨 Recorded Violation Video - {alert_id}\n📹 File: {filename}\n📍 Location: Security Camera"
            
            # Use the endpoint to send video (same as AI engine will do)
            logging.info(f"Sending recorded video via endpoint: {video_path}")
            
            async with httpx.AsyncClient(timeout=120.0) as client:
                with open(video_path, 'rb') as video_file:
                    files = {
                        'video': (filename, video_file, 'video/mp4')
                    }
                    data = {
                        'caption': caption,
                        'alert_id': alert_id
                    }
                    
                    # Call our own endpoint
                    response = await client.post(
                        "http://localhost:8001/send-video-to-whatsapp",
                        files=files,
                        data=data
                    )
            
            if response.status_code == 200:
                result = response.json()
                if result.get("success"):
                    logging.info(f"Recorded video sent successfully via endpoint: {alert_id}")
                    return True
                else:
                    logging.error(f"Failed to send recorded video via endpoint: {result.get('message')}")
            else:
                logging.error(f"Endpoint error for recorded video: {response.status_code}")
                
        except Exception as e:
            logging.error(f"Error sending recorded video via endpoint: {e}")
        
        return False

    async def save_and_send_violation_image(self, frame, alert_id: str):
        """Save violation detection frame and send to WhatsApp using endpoint"""
        try:
            # Create output directory
            os.makedirs("data/images/violations", exist_ok=True)
            
            # Check for existing files with same alert number and remove them
            violations_dir = "data/images/violations"
            for filename in os.listdir(violations_dir):
                if filename.startswith(f"violation_{alert_id}_") and filename.endswith((".jpg", ".jpeg", ".png")):
                    existing_file = os.path.join(violations_dir, filename)
                    os.remove(existing_file)
                    logging.info(f"Removed existing image file: {filename}")
            
            # Generate filename with timestamp
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            filename = f"violation_{alert_id}_{timestamp}.jpg"
            filepath = f"data/images/violations/{filename}"
            
            # Save the detection frame
            success = cv2.imwrite(filepath, frame)
            if success:
                logging.info(f"Saved violation image: {filename}")
                
                # Send image via endpoint (same as AI engine will do)
                caption = f"🚨 Violation Detection Image - {alert_id}\n📸 File: {filename}\n📍 Location: Security Camera"
                
                async with httpx.AsyncClient(timeout=60.0) as client:
                    with open(filepath, 'rb') as image_file:
                        files = {
                            'image': (filename, image_file, 'image/jpeg')
                        }
                        data = {
                            'caption': caption,
                            'alert_id': alert_id
                        }
                        
                        # Call our own endpoint
                        response = await client.post(
                            "http://localhost:8001/send-image-to-whatsapp",
                            files=files,
                            data=data
                        )
                
                if response.status_code == 200:
                    result = response.json()
                    if result.get("success"):
                        logging.info(f"Violation image sent successfully via endpoint: {alert_id}")
                        return True
                    else:
                        logging.error(f"Failed to send violation image via endpoint: {result.get('message')}")
                else:
                    logging.error(f"Endpoint error for violation image: {response.status_code}")
            else:
                logging.error(f"Failed to save violation image: {filepath}")
                
        except Exception as e:
            logging.error(f"Error saving and sending violation image: {e}")
        
        return False

    async def process_frame(self, frame):
        """
        Process a frame using the fire model, draw detections, and send a notification if needed.
        """
        return_dict = {
            "class_label": [],
            "bbox": [],
            "conf": [],
            "violation": []
        }

        try:
            # Run model inference directly
            results = self.fire_model(frame, conf=self.confidence_threshold, stream=True)
            
            for r in results:
                boxes = r.boxes
                for box in boxes:
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    conf = float(box.conf[0])
                    cls = int(box.cls[0])
                    current_class = (
                        self.fire_model.model.names[cls]
                        if hasattr(self.fire_model, "model") and hasattr(self.fire_model.model, "names")
                        else "fire"
                    )
                    if conf > self.confidence_threshold:
                        return_dict["class_label"].append(current_class)
                        return_dict["bbox"].append({"x1": x1, "y1": y1, "x2": x2, "y2": y2})
                        return_dict["conf"].append(conf)
                        return_dict["violation"].append(current_class)
                        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                        cv2.putText(frame, f'{current_class} {conf:.2f}', (x1, y1 - 10),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)
        except Exception as e:
            logging.error(f"Error in violation detection: {str(e)}")
            return_dict["error"] = str(e)

        current_time = datetime.now()
        current_detected = set(return_dict["violation"])
        new_detections = []

        # Update detection status and determine new detections.
        for violation in current_detected:
            if violation not in self.detection_status:
                self.detection_status[violation] = current_time
                new_detections.append(violation)
            else:
                elapsed = (current_time - self.detection_status[violation]).total_seconds()
                if elapsed >= 10:
                    self.detection_status[violation] = current_time
                    new_detections.append(violation)

        for violation in list(self.detection_status.keys()):
            if violation not in current_detected:
                elapsed = (current_time - self.detection_status[violation]).total_seconds()
                if elapsed >= 10:
                    del self.detection_status[violation]

        # Send a notification if new detections were found.
        if new_detections:
            alert_id = f"ALERT{self.alert_counter:03d}"
            self.alert_counter += 1
            description = "Violation(s) detected: " + ", ".join(new_detections)
            logging.info(f"New violations detected: {new_detections}, Alert ID: {alert_id}")
            
            # Save and send violation image if enabled
            if self.send_images:
                asyncio.create_task(self.save_and_send_violation_image(frame.copy(), alert_id))
            
            # Start recording for testing purposes
            if self.send_videos and not self.is_recording:
                video_path = self.start_recording(frame)
                if video_path:
                    # Record for 5 seconds then stop and send to WhatsApp
                    asyncio.create_task(self.auto_stop_recording(5.0, video_path, alert_id))
        
        # Continue recording if active
        if self.is_recording and self.video_writer:
            self.video_writer.write(frame)
            
        return frame, return_dict

    async def generate_frames(self):
        """
        Capture video frames, process each frame, and yield the encoded frame.
        """
        cap = cv2.VideoCapture(self.config.get("video", {}).get("stream_url"))
        if not cap.isOpened():
            logging.error("Error: Couldn't open video file.")
            return

        try:
            while True:
                ret, frame = cap.read()
                if not ret:
                    logging.info("End of video stream.")
                    break

                frame, metadata = await self.process_frame(frame)
                success, buffer = cv2.imencode('.jpg', frame)
                if not success:
                    logging.error("Failed to encode frame.")
                    break

                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n\r\n')
                await asyncio.sleep(0.01)
        finally:
            cap.release()

    async def video_feed(self, request: Request):
        """
        Endpoint for streaming video frames.
        """
        return StreamingResponse(
            self.generate_frames(),
            media_type="multipart/x-mixed-replace; boundary=frame"
        )

    async def startup_event(self):
        """
        Check WhatsApp API connection on startup.
        """
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.whatsapp_api_url}/health")
                if response.status_code == 200:
                    health_data = response.json()
                    if health_data.get("baileys_connected"):
                        logging.info("WhatsApp API is connected and ready")
                    else:
                        logging.warning("WhatsApp API is running but not connected. QR code scan may be required.")
                else:
                    logging.error("WhatsApp API is not responding")
        except Exception as e:
            logging.error(f"Failed to check WhatsApp API status: {e}")

    async def shutdown_event(self):
        """
        Cleanup on shutdown.
        """
        logging.info("Shutting down TestAPI")
app_instance = TestAPI()
app = app_instance.app
if __name__ == "__main__":
    uvicorn.run("TestAPI:app", host="0.0.0.0", port=8001, reload=True)