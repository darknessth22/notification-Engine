from fastapi import FastAPI, UploadFile, File
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.concurrency import run_in_threadpool
import cv2
import logging
import asyncio
import uvicorn
from typing import Dict, Any
from datetime import datetime
from whatsapp_notifier import WhatsAppNotifier
from config_manager import ConfigManager
from ultralytics import YOLO
# Initialize configuration and models
config_manager = ConfigManager('config/config.yaml')
fire_model = YOLO(config_manager.model_settings['model_path']).to(config_manager.device_settings)
whatsapp_notifier = WhatsAppNotifier('config/config.yaml')
alert_counter = config_manager.notification_settings['initial_alert_counter']
detection_status: Dict[str, datetime] = {}

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(level=logging.DEBUG)

async def process_frame(frame):
    global alert_counter, detection_status
    return_dict = {
        "class_label": [],
        "bbox": [],
        "conf": [],
        "violation": []
    }

    try:
        results = await run_in_threadpool(
            lambda: fire_model(frame, conf=config_manager.model_settings['confidence_threshold'], stream=True)
        )
        
        for r in results:
            boxes = r.boxes
            for box in boxes:
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                conf = float(box.conf[0])
                cls = int(box.cls[0])
                current_class = (
                    fire_model.model.names[cls]
                    if hasattr(fire_model, "model") and hasattr(fire_model.model, "names")
                    else "fire"
                )

                if conf > config_manager.model_settings['confidence_threshold']:
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

    for violation in current_detected:
        if violation not in detection_status:
            detection_status[violation] = current_time
            new_detections.append(violation)
        else:
            elapsed = (current_time - detection_status[violation]).total_seconds()
            if elapsed >= 10:
                detection_status[violation] = current_time
                new_detections.append(violation)

    for violation in list(detection_status.keys()):
        if violation not in current_detected:
            elapsed = (current_time - detection_status[violation]).total_seconds()
            if elapsed >= 10:
                del detection_status[violation]

    if new_detections:
        alert_id = f"ALERT{alert_counter:03d}"
        alert_counter += 1
        description = "Violation(s) detected: " + ", ".join(new_detections)
        
        await whatsapp_notifier.send_violation_notification_async(
            alert_id,
            new_detections,
            current_time.strftime("%Y-%m-%d %H:%M:%S"),
            description
        )
    
    return frame, return_dict

async def generate_frames():
    cap = cv2.VideoCapture(config_manager.video_settings['stream_url'])
    if not cap.isOpened():
        logging.error("Error: Couldn't open video file.")
        return

    try:
        while True:
            ret, frame = await run_in_threadpool(cap.read)
            if not ret:
                logging.info("End of video stream.")
                break

            frame, metadata = await process_frame(frame)

            success, buffer = await run_in_threadpool(cv2.imencode, '.jpg', frame)
            if not success:
                logging.error("Failed to encode frame.")
                break

            yield (b'--frame\r\n'
                  b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n\r\n')

            await asyncio.sleep(0.01)

    finally:
        await run_in_threadpool(cap.release)

@app.get("/video_feed")
async def video_feed():
    return StreamingResponse(
        generate_frames(),
        media_type="multipart/x-mixed-replace; boundary=frame"
    )

@app.on_event("startup")
async def startup_event():
    whatsapp_notifier.init_driver(headless=True, silent=True).login()
    asyncio.create_task(whatsapp_notifier.start_notification_worker())

@app.on_event("shutdown")
async def shutdown_event():
    await whatsapp_notifier.shutdown()

if __name__ == "__main__":
    uvicorn.run("TestAPI:app", host="0.0.0.0", port=8000, reload=True)