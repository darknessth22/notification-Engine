import logging
from fastapi import FastAPI, UploadFile, File, WebSocket
from fastapi.responses import HTMLResponse, StreamingResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.requests import Request
import shutil
from pathlib import Path
import cv2
import os
import csv
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
import pywhatkit as kit  # For sending WhatsApp notifications
import logging
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import threading

# --- Global Variables & Model Initialization ---
# Global alert counter (starts at 1 and increases for every new violation notification)
alert_counter = 1
PHONE_NUMBER = "+201553641192"
send_lock = threading.Lock()

# Load the YOLO fire detection model (ensure the model file path is correct)
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
print(f'Using device: {device}')
fire_model = YOLO("FireSmoke3.pt").to(device)

# --- FastAPI App Setup ---
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
stream_url = "firedemo.mp4" 

logging.basicConfig(level=logging.DEBUG)
whatsapp_driver = None
current_contact = None
def open_contact_chat(contact_name):
    """Open the chat for the given contact if not already open."""
    global whatsapp_driver, current_contact
    try:
        # Locate the search box and type the contact name.
        search_box = WebDriverWait(whatsapp_driver, 30).until(
            EC.presence_of_element_located((By.XPATH, '//div[@contenteditable="true"][@data-tab="3"]'))
        )
        search_box.clear()
        search_box.click()
        search_box.send_keys(contact_name)
        time.sleep(2)  # Allow search results to populate

        # Click on the contact in the search results.
        contact = WebDriverWait(whatsapp_driver, 30).until(
            EC.element_to_be_clickable((By.XPATH, f'//span[@title="{contact_name}"]'))
        )
        contact.click()
        time.sleep(2)  # Allow the chat to load
        current_contact = contact_name
        logging.info(f"Chat for {contact_name} opened successfully.")
    except Exception as e:
        logging.error("Error opening contact chat: " + str(e))
        
def init_whatsapp(executable_path, user_data_dir, profile_directory="Default", headless=True, silent=True):
    global whatsapp_driver
    chrome_options = Options()
    chrome_options.binary_location = "/usr/bin/chromium-browser"
    
    # Use a temporary directory for headless mode or a persistent one otherwise.
    if headless:
        import tempfile
        temp_profile_dir = tempfile.mkdtemp(prefix="chrome_profile_headless_")
        chrome_options.add_argument(f"--user-data-dir={temp_profile_dir}")
        chrome_options.add_argument("--profile-directory=Default")
    else:
        chrome_options.add_argument(f"--user-data-dir={user_data_dir}")
        chrome_options.add_argument(f"--profile-directory={profile_directory}")
    
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--start-maximized")
    
    # Let Chrome choose a remote debugging port automatically.
    chrome_options.add_argument("--remote-debugging-port=0")
    
    if headless:
        chrome_options.add_argument("--headless=new")
        chrome_options.add_argument("window-size=1920,1080")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-features=VizDisplayCompositor")
    
    if silent:
        chrome_options.add_experimental_option("excludeSwitches", ["enable-logging"])
    
    service = Service(executable_path)
    whatsapp_driver = webdriver.Chrome(service=service, options=chrome_options)
    logging.info("WhatsApp Selenium driver initialized.")
    
def send_whatsapp_message(contact_name, message,
                            search_xpath='//div[@contenteditable="true"][@data-tab="3"]',
                            message_box_xpath='//div[@contenteditable="true"][@data-tab="10"]'):
    """
    Sends a WhatsApp message to the specified contact using the persistent Selenium driver.
    Reuses the open chat if available.
    """
    global whatsapp_driver, current_contact
    if whatsapp_driver is None:
        logging.error("WhatsApp driver is not initialized!")
        return

    # Use a lock to prevent overlapping calls
    with send_lock:
        try:
            # If the current chat is not the desired one, search and select the contact.
            if current_contact != contact_name:
                search_box = WebDriverWait(whatsapp_driver, 30).until(
                    EC.presence_of_element_located((By.XPATH, search_xpath))
                )
                search_box.clear()
                search_box.click()
                search_box.send_keys(contact_name)
                time.sleep(2)  # Allow search results to populate

                contact = WebDriverWait(whatsapp_driver, 30).until(
                    EC.element_to_be_clickable((By.XPATH, f'//span[@title="{contact_name}"]'))
                )
                contact.click()
                time.sleep(2)  # Allow the chat to load

                current_contact = contact_name  # Update global variable

            # Locate the message input box.
            message_box = WebDriverWait(whatsapp_driver, 30).until(
                EC.presence_of_element_located((By.XPATH, message_box_xpath))
            )
            message_box.click()
            # Optional: clear the message input if necessary
            # message_box.clear()
            
            # Type the full message. Use Shift+Enter for line breaks.
            for line in message.split("\n"):
                message_box.send_keys(line)
                message_box.send_keys(Keys.SHIFT, Keys.ENTER)
            # Finally, press Enter to send.
            message_box.send_keys(Keys.ENTER)
            logging.info(f"Message sent to {contact_name}!")
        except Exception as e:
            logging.error("Error sending message: " + str(e))
            try:
                logging.error("Page source snippet: " + whatsapp_driver.page_source[:500])
            except Exception:
                logging.error("Could not retrieve page source during message sending.")

def create_notification_message(alert_id, alert_type, timestamp, priority, description):
    return f"""* *ALERT NOTIFICATION*

Alert ID: {alert_id}
Type: {alert_type}
Timestamp: {timestamp}
Priority: {priority}

Description:
{description}"""

def send_violation_notification(alert_id, violation_types, timestamp, description):
    violation_type_str = ', '.join(violation_types)
    message = create_notification_message(
        alert_id=alert_id,
        alert_type=violation_type_str,
        timestamp=timestamp,
        priority="High",
        description=description
    )
    try:
        CONTACT_NAME = "Fares Voda"
        send_whatsapp_message(CONTACT_NAME, message)
        logging.info(f"Notification for {violation_type_str} sent successfully!")
    except Exception as e:
        logging.error("Error sending notification: " + str(e))

def send_notification_async(alert_id, violation_types, timestamp, description):
    thread = threading.Thread(
        target=send_violation_notification,
        args=(alert_id, violation_types, timestamp, description),
        daemon=True
    )
    thread.start()
    
    
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
        # Offload notification without throttling
        send_notification_async(alert_id, violation_list, current_timestamp, description_text)
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
def login_whatsapp():
    global whatsapp_driver
    whatsapp_driver.get("https://web.whatsapp.com/")
    try:
        # Wait for the WhatsApp chat sidebar to appear (indicating a successful login)
        WebDriverWait(whatsapp_driver, 60).until(
            EC.presence_of_element_located((By.XPATH, '//div[@id="side"]'))
        )
        logging.info("WhatsApp logged in successfully!")
    except Exception as e:
        logging.error("Error during login: " + str(e))
        try:
            logging.error("Page source snippet: " + whatsapp_driver.page_source[:500])
        except Exception:
            logging.error("Could not retrieve page source during login.")

@app.on_event("startup")
def startup_event():
    WHATSAPP_EXECUTABLE_PATH = '/home/dark/work/test/chromedriver-linux64/chromedriver'
    USER_DATA_DIR = '/home/dark/chrome_profile'
    PROFILE_DIRECTORY = "Default"
    # For the initial login, you might use headless=False to scan the QR code.
    init_whatsapp(WHATSAPP_EXECUTABLE_PATH, USER_DATA_DIR, PROFILE_DIRECTORY, headless=False, silent=True)
    login_whatsapp()
    # Open the chat for the target contact.
    open_contact_chat("Fares Voda")

if __name__ == "__main__":
    uvicorn.run("gpu:app", host="0.0.0.0", port=8000, reload=True)