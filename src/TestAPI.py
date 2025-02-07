import logging
from fastapi import FastAPI, UploadFile, File, WebSocket
from fastapi.responses import HTMLResponse, StreamingResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.requests import Request
from pathlib import Path
import cv2
import uvicorn
from ultralytics import YOLO
from ultralytics.utils.plotting import Annotator, colors
from fastapi.middleware.cors import CORSMiddleware
import numpy as np
from typing import Union, Any
from pydantic import BaseModel
from datetime import datetime
import base64
import torch
from whatsapp_notifier import WhatsAppNotifier
import yaml

with open('config/config.yaml', 'r') as config_file:
    config = yaml.safe_load(config_file)

# Configure logging
logging.basicConfig(
    level=getattr(logging, config.get('logging', {}).get('level', 'DEBUG').upper()),
    filename=config.get('logging', {}).get('file_path', './fire_detection.log')
)

# Model configuration
model_config = config.get('model', {}).get('fire_detection', {})
stream_url = config.get('video', {}).get('stream_url', 'firedemo.mp4')
output_directory = config.get('video', {}).get('output_directory', './output')

# Device configuration
device = torch.device('cuda' if config.get('device', {}).get('prefer_cuda', False) and torch.cuda.is_available() else 'cpu')
print(f'Using device: {device}')

# Load fire detection model
fire_model = YOLO(model_config.get('path', "FireSmoke3.pt")).to(device)
confidence_threshold = model_config.get('confidence_threshold', 0.5)

# Notification settings
alert_counter = config.get('notification', {}).get('initial_alert_counter', 1)
default_priority = config.get('notification', {}).get('default_priority', 'High')

# WhatsApp Notifier
whatsapp_notifier = WhatsAppNotifier('config/config.yaml')

class UnCompressedVideoFrames(BaseModel):
    frame: Any
    timestamp: datetime

frame_metadata = []
app = FastAPI()
origins = [
    "http://localhost",
    "http://localhost:8080",
    "*",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(level=logging.DEBUG)

def process_frame(frame):
    global alert_counter
    return_dict = {}
    cls_list = []
    bbox_list = []
    conf_list = []
    violation_list = []

    try:
        results = fire_model(frame, conf=0.5, stream=True)
        for r in results:
            boxes = r.boxes
            for box in boxes:
                x1, y1, x2, y2 = box.xyxy[0]
                x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
                conf = float(box.conf[0])
                cls = int(box.cls[0])
                currentClass = fire_model.model.names[cls] if hasattr(fire_model, "model") and hasattr(fire_model.model, "names") else "fire"
                logging.debug(f"Detected: {currentClass} with confidence {conf}")

                if conf > 0.5:
                    cls_list.append(currentClass)
                    bbox_list.append({"x1": x1, "y1": y1, "x2": x2, "y2": y2})
                    conf_list.append(conf)
                    violation_list.append(currentClass)

                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                    cv2.putText(frame, f'{currentClass} {conf:.2f}', (x1, y1 - 10),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)
    except Exception as e:
        logging.error("Error in violation detection: " + str(e))
        return_dict["error"] = str(e)

    return_dict["class_label"] = cls_list
    return_dict["bbox"] = bbox_list
    return_dict["conf"] = conf_list
    return_dict["violation"] = violation_list

    if violation_list:
        current_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        alert_id = f"ALERT{alert_counter:03d}"
        description_text = f"Violations detected: {', '.join(violation_list)}"
        # Use the new WhatsApp Notifier to send async notification
        whatsapp_notifier.send_violation_notification_async(
            alert_id, 
            violation_list, 
            current_timestamp, 
            description_text
        )
        alert_counter += 1

    return frame, return_dict



def read_image_from_bytes(image_bytes: bytes) -> np.ndarray:
    image_array = np.frombuffer(image_bytes, np.uint8)
    image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
    return image

def generate_frames():
    cap = cv2.VideoCapture(stream_url)
    if not cap.isOpened():
        logging.error("Error: Couldn't open video file.")
        return

    while True:
        ret, frame = cap.read()
        if not ret:
            logging.info("End of video stream.")
            break  
        _, metadata = process_frame(frame)

        frame_metadata.append(metadata)

        logging.debug(f"Updated metadata for current frame: {metadata}")

        for bbox, emotion in zip(metadata['bbox'], metadata['violation']):
            x1, y1, x2, y2 = bbox["x1"], bbox["y1"], bbox["x2"], bbox["y2"]
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(frame, emotion, (x1, y1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)
        ret, buffer = cv2.imencode('.jpg', frame)
        if not ret:
            logging.error("Failed to encode frame.")
            break
        frame_bytes = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n\r\n')

    cap.release() 
        
@app.get("/video_feed")
def video_feed():
    """
    Streaming endpoint for video frames.
    """
    return StreamingResponse(generate_frames(), media_type="multipart/x-mixed-replace; boundary=frame")

@app.post("/meta_data")
async def meta_data(frame: UploadFile = File(...)):
    frame_bytes = await frame.read()
    frame = read_image_from_bytes(frame_bytes)
    frame, meta_data = process_frame(frame)
    return JSONResponse({"MetaData": meta_data}, 200)


@app.get("/test")
async def meta_data_text():
    """
    Endpoint to retrieve metadata for all frames processed so far.
    """
    return JSONResponse(content={"frame_metadata": frame_metadata})


class UnCompressedVideoFrames(BaseModel):
    width: int
    height: int
    data: str
    pixelFormat: str


def base64_to_yuv420_to_image(base64_str, width, height):
    try:
        # Decode base64 URL-safe encoded string
        frame_data = base64.urlsafe_b64decode(base64_str)

        # Extract width, height
        width = width
        height = height

        # Calculate the size of Y, U, and V planes
        y_size = width * height
        uv_width = width // 2
        uv_height = height // 2
        uv_size = uv_width * uv_height  # Size of each U or V plane

        # Extract Y, U, and V planes from the decoded data
        y_plane = frame_data[:y_size]  # First part is Y plane
        u_plane = frame_data[y_size:y_size + uv_size]  # Next part is U plane
        v_plane = frame_data[y_size + uv_size:]  # Remaining part is V plane

        # Convert YUV420 frame to a format usable in OpenCV (for example)
        # Reshape Y, U, and V to the correct dimensions
        y_plane = np.frombuffer(y_plane, dtype=np.uint8).reshape((height, width))
        u_plane = np.frombuffer(u_plane, dtype=np.uint8).reshape((uv_height, uv_width))
        v_plane = np.frombuffer(v_plane, dtype=np.uint8).reshape((uv_height, uv_width))

        # Resize U and V planes to match Y plane dimensions
        u_plane_resized = cv2.resize(u_plane, (width, height))
        v_plane_resized = cv2.resize(v_plane, (width, height))

        # Merge Y, U, V planes into a single image
        yuv_image = cv2.merge([y_plane, u_plane_resized, v_plane_resized])

        # Optionally, convert YUV image to BGR for visualization
        bgr_image = cv2.cvtColor(yuv_image, cv2.COLOR_YUV2BGR)
    except Exception as e:
        raise ValueError(f"YUV to BGR conversion failed: {e}")
    
    return bgr_image

@app.post("/test_frame")
async def meta_data_text(request: Request, data: UnCompressedVideoFrames):
    try:
        body = await request.json()  # Get raw request body
        print(body.keys())  # This will show the exact payload received
        print("API FROM PLUGIN HIT")
        print(f"Width: {data.width}, Height: {data.height}")
        print("Length of Encoded Data:", len(data.data))
        print("Base64 Data Sample (first 100 chars):", data.data[:100])
        try:
            frame = base64_to_yuv420_to_image(data.data, data.width, data.height)
            print(type(frame))
            frame, _ = process_frame(frame)
            cv2.imwrite("frame.jpg", frame)

        except Exception as decode_error:
            print(f"Base64 Decoding Error: {decode_error}")
            return JSONResponse({"MetaData": f"Base64 Decoding Error: {decode_error}"}, 500)
        return JSONResponse({"MetaData": "Object Detected"}, 200)
    except Exception as e:
        return JSONResponse({"MetaData": f"Error: {e}"}, 500)

@app.on_event("startup")
def startup_event():
    contact_name = config.get('whatsapp', {}).get('contact_name', 'Fares Voda')
    whatsapp_notifier.init_driver(headless=False, silent=True) \
                      .login() \
                      .open_contact_chat(contact_name)

if __name__ == "__main__":
    uvicorn.run("TestAPI:app", host="0.0.0.0", port=8000, reload=True)