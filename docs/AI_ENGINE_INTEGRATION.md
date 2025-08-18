# WhatsApp Notification Engine - AI Integration Guide

## Quick Integration

### 1. Configuration (`config/config.yaml`)

```yaml
app:
  notifications:
    enabled: true
    settings:
      providers:
        whatsapp:
          enabled: true
          api:
            python_server_url: "http://localhost:3051"
          phone_numbers:
            - "+201025939307"
            - "+201553641192"
          send_images: true
          send_videos: true
          send_text: true
      initial_alert_counter: 1
```

### 2. AI Engine Class Setup

```python
        # WhatsApp configuration
        self.whatsapp_config = self.config['app']['notifications']['settings']['providers']['whatsapp']
        self.whatsapp_api_url = self.whatsapp_config.get("api", {}).get("python_server_url", "http://localhost:3051")
        self.send_images = self.whatsapp_config.get("send_images", True)
        self.send_videos = self.whatsapp_config.get("send_videos", False)
        self.send_text = self.whatsapp_config.get("send_text", True)
        
        # Phone numbers
        self.phone_numbers = self.whatsapp_config.get("phone_numbers", [])
        if not self.phone_numbers:
            single_phone = self.whatsapp_config.get("phone_number")
            if single_phone:
                self.phone_numbers = [single_phone]
        
        logging.info(f"Configured {len(self.phone_numbers)} phone numbers: {self.phone_numbers}")
        
        self.alert_counter = self.config['app']['notifications']['settings'].get("initial_alert_counter", 1)
        
    def _setup_routes(self):
        """Configure WhatsApp endpoints"""
        self.app.post("/send-image-to-whatsapp")(self.send_image_to_whatsapp_endpoint)
        self.app.post("/send-video-to-whatsapp")(self.send_video_to_whatsapp_endpoint)
        self.app.post("/send-message-to-whatsapp")(self.send_message_to_whatsapp_endpoint)
```

### 3. WhatsApp Endpoints

#### Send Image
Accepts an image file via multipart/form-data and sends it to all configured WhatsApp numbers with a caption.
**Expects**: `image` (file), `caption` (optional text), `alert_id` (optional)
**Sends**: Image message to WhatsApp Gateway → `POST /send-image`

```python
async def send_image_to_whatsapp_endpoint(self, request: Request):
    try:
        form = await request.form()
        image_file = form.get("image")
        caption = form.get("caption", "🚨 AI Detection Alert")
        alert_id = form.get("alert_id", f"ALERT{int(time.time())}")
        
        if not image_file or not self.phone_numbers:
            return {"success": False, "message": "Missing image or phone numbers"}
        
        # Read image once
        image_content = await image_file.read()
        
        # Send to all phone numbers
        results = []
        success_count = 0
        
        for phone_number in self.phone_numbers:
            try:
                async with httpx.AsyncClient(timeout=60.0) as client:
                    files = {'image': (image_file.filename, image_content, 'image/jpeg')}
                    data = {'phone': phone_number, 'caption': f"{caption}\n📍 Alert ID: {alert_id}"}
                    
                    response = await client.post(f"{self.whatsapp_api_url}/send-image", files=files, data=data)
                
                if response.status_code == 200 and response.json().get("success"):
                    success_count += 1
                    results.append({"phone": phone_number, "status": "success"})
                    logging.info(f"✅ Image sent to {phone_number}")
                else:
                    results.append({"phone": phone_number, "status": "failed"})
                    logging.error(f"❌ Failed to send image to {phone_number}")
                    
            except Exception as e:
                results.append({"phone": phone_number, "status": "failed", "error": str(e)})
                logging.error(f"❌ Exception sending image to {phone_number}: {e}")
        
        return {
            "success": success_count > 0,
            "message": f"Image sent to {success_count}/{len(self.phone_numbers)} numbers",
            "alert_id": alert_id,
            "results": results
        }
        
    except Exception as e:
        logging.error(f"Error in send_image_to_whatsapp_endpoint: {e}")
        return {"success": False, "message": f"Server error: {str(e)}"}
```

#### Send Video
Accepts a video file via multipart/form-data and sends it to all configured WhatsApp numbers with a caption.
**Expects**: `video` (file), `caption` (optional text), `alert_id` (optional)
**Sends**: Video message to WhatsApp Gateway → `POST /send-video`

```python
async def send_video_to_whatsapp_endpoint(self, request: Request):
    try:
        form = await request.form()
        video_file = form.get("video")
        caption = form.get("caption", "🚨 AI Detection Video")
        alert_id = form.get("alert_id", f"ALERT{int(time.time())}")
        
        if not video_file or not self.phone_numbers:
            return {"success": False, "message": "Missing video or phone numbers"}
        
        # Read video once
        video_content = await video_file.read()
        
        # Send to all phone numbers
        results = []
        success_count = 0
        
        for phone_number in self.phone_numbers:
            try:
                async with httpx.AsyncClient(timeout=120.0) as client:
                    files = {'video': (video_file.filename, video_content, 'video/mp4')}
                    data = {'phone': phone_number, 'caption': f"{caption}\n📍 Alert ID: {alert_id}"}
                    
                    response = await client.post(f"{self.whatsapp_api_url}/send-video", files=files, data=data)
                
                if response.status_code == 200 and response.json().get("success"):
                    success_count += 1
                    results.append({"phone": phone_number, "status": "success"})
                    logging.info(f"✅ Video sent to {phone_number}")
                else:
                    results.append({"phone": phone_number, "status": "failed"})
                    logging.error(f"❌ Failed to send video to {phone_number}")
                    
            except Exception as e:
                results.append({"phone": phone_number, "status": "failed", "error": str(e)})
                logging.error(f"❌ Exception sending video to {phone_number}: {e}")
        
        return {
            "success": success_count > 0,
            "message": f"Video sent to {success_count}/{len(self.phone_numbers)} numbers",
            "alert_id": alert_id,
            "results": results
        }
        
    except Exception as e:
        logging.error(f"Error in send_video_to_whatsapp_endpoint: {e}")
        return {"success": False, "message": f"Server error: {str(e)}"}
```

#### Send Message
Accepts a text message via JSON and sends it to all configured WhatsApp numbers.
**Expects**: `message` (text), `alert_id` (optional)
**Sends**: Text message to WhatsApp Gateway → `POST /send`

```python
async def send_message_to_whatsapp_endpoint(self, request: Request):
    try:
        data = await request.json()
        message = data.get("message")
        alert_id = data.get("alert_id", f"ALERT{int(time.time())}")
        
        if not message or not self.phone_numbers:
            return {"success": False, "message": "Missing message or phone numbers"}
        
        # Send to all phone numbers
        results = []
        success_count = 0
        
        for phone_number in self.phone_numbers:
            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.post(
                        f"{self.whatsapp_api_url}/send",
                        json={"phone": phone_number, "message": f"{message}\n📍 Alert ID: {alert_id}"}
                    )
                
                if response.status_code == 200 and response.json().get("success"):
                    success_count += 1
                    results.append({"phone": phone_number, "status": "success"})
                    logging.info(f"✅ Message sent to {phone_number}")
                else:
                    results.append({"phone": phone_number, "status": "failed"})
                    logging.error(f"❌ Failed to send message to {phone_number}")
                    
            except Exception as e:
                results.append({"phone": phone_number, "status": "failed", "error": str(e)})
                logging.error(f"❌ Exception sending message to {phone_number}: {e}")
        
        return {
            "success": success_count > 0,
            "message": f"Message sent to {success_count}/{len(self.phone_numbers)} numbers",
            "alert_id": alert_id,
            "results": results
        }
        
    except Exception as e:
        logging.error(f"Error in send_message_to_whatsapp_endpoint: {e}")
        return {"success": False, "message": f"Server error: {str(e)}"}
```