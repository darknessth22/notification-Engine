# TestAPI.py

import cv2
import logging
import asyncio
import uvicorn
import httpx
import yaml
import os
from datetime import datetime
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
        
        self.alert_counter = self.config.get("notification", {}).get("initial_alert_counter", 1)
        self.detection_status = {}  # For tracking detection timestamps

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

    async def send_whatsapp_notification(self, alert_id: str, violations: list, timestamp: str, description: str, detection_frame=None):
        """
        Send WhatsApp notification using Baileys API with optional detection frame
        """
        try:
            phone_number = self.whatsapp_config.get("phone_number")
            if not phone_number:
                logging.error("No phone number configured for WhatsApp notifications")
                return False

            # Create notification message
            message = f"🚨 {alert_id} - Fire/Smoke Detection Alert\n\n"
            message += f"⚠️ {description}\n"
            message += f"🕐 Time: {timestamp}\n"
            message += f"📍 Location: Security Camera\n\n"
            message += "Please take immediate action!"

            # If detection frame is provided, save it and send as image
            if detection_frame is not None:
                # Ensure data directory exists
                os.makedirs("data/images", exist_ok=True)
                
                # Save the detection frame
                image_filename = f"detection_{alert_id}_{timestamp.replace(':', '-').replace(' ', '_')}.jpg"
                image_path = f"data/images/{image_filename}"
                
                # Save frame to file
                success = cv2.imwrite(image_path, detection_frame)
                if not success:
                    logging.error(f"Failed to save detection image: {image_path}")
                    return False

                # Send image with caption via Baileys API
                async with httpx.AsyncClient(timeout=60.0) as client:
                    with open(image_path, 'rb') as image_file:
                        files = {
                            'image': (image_filename, image_file, 'image/jpeg')
                        }
                        data = {
                            'phone': phone_number,
                            'caption': message
                        }
                        
                        response = await client.post(
                            f"{self.whatsapp_api_url}/send-image",
                            files=files,
                            data=data
                        )
                
                if response.status_code == 200:
                    result = response.json()
                    if result.get("success"):
                        logging.info(f"WhatsApp image notification sent successfully: {alert_id}")
                        return True
                    else:
                        logging.error(f"Failed to send WhatsApp image notification: {result.get('message')}")
                        return False
                else:
                    logging.error(f"WhatsApp API error: {response.status_code} - {response.text}")
                    return False
            else:
                # Send text message only
                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.post(
                        f"{self.whatsapp_api_url}/send",
                        json={
                            "phone": phone_number,
                            "message": message
                        }
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        if result.get("success"):
                            logging.info(f"WhatsApp notification sent successfully: {alert_id}")
                            return True
                        else:
                            logging.error(f"Failed to send WhatsApp notification: {result.get('message')}")
                            return False
                    else:
                        logging.error(f"WhatsApp API error: {response.status_code} - {response.text}")
                        return False

        except httpx.TimeoutException:
            logging.error("Timeout while sending WhatsApp notification")
            return False
        except Exception as e:
            logging.error(f"Error sending WhatsApp notification: {str(e)}")
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
            # Run model inference directly (no threading)
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
            
            # Create a copy of the frame for notification (to avoid modification)
            notification_frame = frame.copy()
            
            await self.send_whatsapp_notification(
                alert_id,
                new_detections,
                current_time.strftime("%Y-%m-%d %H:%M:%S"),
                description,
                notification_frame
            )
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