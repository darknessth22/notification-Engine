# Fire Detection and Notification System

## Overview

This project is an advanced fire and smoke detection system using computer vision and machine learning, with real-time notification capabilities via WhatsApp. The application leverages YOLOv8 for object detection and Selenium for sending automated notifications.


## Prerequisites

### Hardware
- GPU (recommended for faster processing)
- Webcam or video input source

### Software
- Python 3.10+
- CUDA (optional but recommended)
- Chrome/Chromium Browser
- ChromeDriver

## Installation

### 1. Clone the Repository
```bash
git clone https://github.com/yourusername/fire-detection-system.git
cd fire-detection-system
```

### 2. Create Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Download Required Files
- YOLOv8 Fire Detection Model: `FireSmoke3.pt`
- Sample Video: `firedemo.mp4`

## Configuration

### WhatsApp Configuration
1. Ensure Chrome/Chromium is installed
2. Update paths in `whatsapp_notifier.py`:
   - `executable_path`: Path to ChromeDriver
   - `user_data_dir`: Chrome profile directory
   - `PHONE_NUMBER`: Contact for notifications

### Model Configuration
- Adjust detection confidence in `process_frame()` function
- Modify notification thresholds as needed

## Running the Application

### Start the Server
```bash
python gpu.py

```
### Access Endpoints
- Video Feed: `http://localhost:8000/video_feed`
- Metadata: `http://localhost:8000/test`
## Project Structure
```
fire-detection-system/
│
├── TestAPI.py             # Main FastAPI application
├── whatsapp_notifier.py  # WhatsApp notification module
├── FireSmoke3.pt      # YOLOv8 detection model
├── firedemo.mp4       # Sample video input
├── requirements.txt   # Python dependencies
└── README.md          # Project documentation
```

## Dependencies
- FastAPI
- Ultralytics YOLO
- OpenCV
- Selenium
- PyTorch
- uvicorn

## Troubleshooting
- Ensure ChromeDriver version matches Chrome browser
- Check CUDA and GPU drivers
- Verify model file path
- Confirm WhatsApp web login