#!/usr/bin/env python3
"""
Test script to send a WhatsApp message using the Python API Gateway
"""
import requests
import json
import sys
from datetime import datetime

API_URL = "http://localhost:8000"

def send_message(phone_number, message):
    """Send a WhatsApp message via the API"""
    
    # Validate phone number format (should start with + and country code)
    if not phone_number.startswith('+'):
        print("❌ Phone number should start with '+' and include country code")
        print("📱 Example: +1234567890 (US), +44234567890 (UK), +91234567890 (India)")
        return False
    
    payload = {
        "phone": phone_number,
        "message": message
    }
    
    print(f"📤 Sending message to {phone_number}...")
    print(f"💬 Message: {message}")
    print(f"⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("-" * 50)
    
    try:
        response = requests.post(
            f"{API_URL}/send",
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ SUCCESS!")
            print(f"📋 Message ID: {result.get('messageId', 'N/A')}")
            print(f"📱 Sent to: {result.get('to', phone_number)}")
            print(f"⏰ Timestamp: {result.get('timestamp', 'N/A')}")
            return True
        else:
            error_data = response.json()
            print(f"❌ FAILED! Status: {response.status_code}")
            print(f"🚨 Error: {error_data.get('detail', 'Unknown error')}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ CONNECTION ERROR: {e}")
        return False
    except Exception as e:
        print(f"❌ UNEXPECTED ERROR: {e}")
        return False

def check_status():
    """Check the API status before sending"""
    try:
        response = requests.get(f"{API_URL}/health", timeout=10)
        if response.status_code == 200:
            health = response.json()
            print("🔍 API Status Check:")
            print(f"   Python API: {'✅ Healthy' if health['status'] == 'healthy' else '❌ Unhealthy'}")
            print(f"   Baileys Server: {'✅ Healthy' if health['baileys_server_healthy'] else '❌ Unhealthy'}")
            print(f"   WhatsApp Connected: {'✅ Yes' if health['baileys_connected'] else '❌ No - Scan QR code!'}")
            print("-" * 50)
            return health['baileys_connected']
        else:
            print("❌ API health check failed!")
            return False
    except Exception as e:
        print(f"❌ Could not check API status: {e}")
        return False

if __name__ == "__main__":
    print("🚀 WhatsApp Message Test Tool")
    print("=" * 50)
    
    # Check status first
    if not check_status():
        print("❌ API not ready. Please scan QR code if needed.")
        sys.exit(1)
    
    # Get phone number
    if len(sys.argv) >= 2:
        phone = sys.argv[1]
    else:
        phone = input("📱 Enter phone number (with country code, e.g., +1234567890): ").strip()
    
    # Get message
    if len(sys.argv) >= 3:
        message = " ".join(sys.argv[2:])
    else:
        message = input("💬 Enter message: ").strip()
    
    if not phone or not message:
        print("❌ Phone number and message are required!")
        sys.exit(1)
    
    # Send the message
    success = send_message(phone, message)
    sys.exit(0 if success else 1)
