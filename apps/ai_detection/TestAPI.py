# TestAPI.py

import cv2
import logging
import asyncio
import uvicorn
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
from whatsapp_notifier import WhatsAppNotifier
from config_manager import ConfigManager
from ultralytics import YOLO

class TestAPI:
    def __init__(self, config_path: str = "config/config.yaml"):
        # Load the configuration using your ConfigManager.
        self.config_manager = ConfigManager(config_path)
        self.config = self.config_manager.config

        # Initialize the fire detection model.
        self.fire_model = YOLO(self.config_manager.model_settings['model_path']).to(
            self.config_manager.device_settings
        )

        # Build a notifications configuration dictionary from the full config.
        notifications_config = {
            "chrome": self.config.get("chrome", {}),
            "whatsapp": self.config.get("whatsapp", {}),
            "notification": self.config.get("notification", {})
        }
        # Instantiate the WhatsApp notifier with only the notifications config.
        self.whatsapp_notifier = WhatsAppNotifier(notifications_config)

        self.alert_counter = self.config_manager.notification_settings['initial_alert_counter']
        self.detection_status = {}  # For tracking detection timestamps.
        self.thread_pool = ThreadPoolExecutor(max_workers=4)

        # Create and configure the FastAPI app.
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
            loop = asyncio.get_running_loop()
            # Run model inference in the thread pool.
            results = await loop.run_in_executor(
                self.thread_pool,
                lambda: self.fire_model(frame, conf=self.config_manager.model_settings['confidence_threshold'], stream=True)
            )
            
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
                    if conf > self.config_manager.model_settings['confidence_threshold']:
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
            await self.whatsapp_notifier.send_violation_notification_async(
                alert_id,
                new_detections,
                current_time.strftime("%Y-%m-%d %H:%M:%S"),
                description
            )
        return frame, return_dict

    async def generate_frames(self):
        """
        Capture video frames, process each frame, and yield the encoded frame.
        """
        cap = cv2.VideoCapture(self.config_manager.config.get("video", {}).get("stream_url"))
        if not cap.isOpened():
            logging.error("Error: Couldn't open video file.")
            return

        try:
            while True:
                loop = asyncio.get_running_loop()
                ret, frame = await loop.run_in_executor(self.thread_pool, cap.read)
                if not ret:
                    logging.info("End of video stream.")
                    break

                frame, metadata = await self.process_frame(frame)
                success, buffer = await loop.run_in_executor(self.thread_pool, cv2.imencode, '.jpg', frame)
                if not success:
                    logging.error("Failed to encode frame.")
                    break

                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n\r\n')
                await asyncio.sleep(0.01)
        finally:
            await asyncio.get_running_loop().run_in_executor(self.thread_pool, cap.release)

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
        Initialize the notifier and start its notification worker.
        """
        self.whatsapp_notifier.init_driver(headless=True, silent=True).login()
        asyncio.create_task(self.whatsapp_notifier.start_notification_worker())

    async def shutdown_event(self):
        """
        Shutdown the notifier and thread pool.
        """
        await self.whatsapp_notifier.shutdown()
        self.thread_pool.shutdown(wait=True)
app_instance = TestAPI()
app = app_instance.app
if __name__ == "__main__":
    uvicorn.run("TestAPI:app", host="0.0.0.0", port=8000, reload=True)