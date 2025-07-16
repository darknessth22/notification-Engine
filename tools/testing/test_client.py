import requests
import json
import time

# Configuration
API_BASE_URL = "http://localhost:8000"

def test_health():
    """Test the health endpoint"""
    print("🔍 Testing health endpoint...")
    try:
        response = requests.get(f"{API_BASE_URL}/health")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200
    except requests.exceptions.RequestException as e:
        print(f"❌ Health check failed: {e}")
        return False

def test_status():
    """Test the status endpoint"""
    print("\n🔍 Testing status endpoint...")
    try:
        response = requests.get(f"{API_BASE_URL}/status")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"❌ Status check failed: {e}")
        return None

def send_test_message(phone_number, message):
    """Send a test WhatsApp message"""
    print(f"\n📱 Sending test message to {phone_number}...")
    
    payload = {
        "phone": phone_number,
        "message": message
    }
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/send",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 200:
            print("✅ Message sent successfully!")
            return True
        else:
            print("❌ Failed to send message")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
        return False

def wait_for_whatsapp_connection(max_wait_time=300):
    """Wait for WhatsApp to connect (after QR scan)"""
    print("\n⏳ Waiting for WhatsApp connection...")
    print("Please scan the QR code shown in the container logs")
    
    start_time = time.time()
    while time.time() - start_time < max_wait_time:
        try:
            response = requests.get(f"{API_BASE_URL}/status")
            if response.status_code == 200:
                data = response.json()
                if data.get("baileys_server", {}).get("whatsapp_connected", False):
                    print("✅ WhatsApp connected successfully!")
                    return True
                elif data.get("baileys_server", {}).get("qr_code_required", True):
                    print("📱 QR code required - check container logs for QR code")
        except:
            pass
        
        time.sleep(10)  # Check every 10 seconds
    
    print("❌ Timeout waiting for WhatsApp connection")
    return False

def send_multiple_messages():
    """Send multiple messages with options"""
    print("\n📱 MULTIPLE MESSAGE SENDING")
    print("=" * 50)
    
    # Get phone number
    phone = input("Enter phone number (with country code, e.g., +1234567890): ").strip()
    if not phone:
        phone = "+201025939307"  # Default for testing
        print(f"Using default phone: {phone}")
    
    print("\nChoose messaging mode:")
    print("1. Interactive mode (type messages one by one)")
    print("2. Bulk mode (send predefined messages)")
    print("3. Auto mode (send messages at intervals)")
    
    choice = input("Enter your choice (1-3): ").strip()
    
    if choice == "1":
        interactive_messaging(phone)
    elif choice == "2":
        bulk_messaging(phone)
    elif choice == "3":
        auto_messaging(phone)
    else:
        print("❌ Invalid choice!")

def interactive_messaging(phone):
    """Interactive messaging - type messages one by one"""
    print(f"\n💬 Interactive messaging to {phone}")
    print("Type 'quit' or 'exit' to stop")
    print("-" * 30)
    
    message_count = 0
    while True:
        message = input("\n📝 Enter message: ").strip()
        
        if message.lower() in ['quit', 'exit', 'stop']:
            print(f"👋 Stopped after sending {message_count} messages")
            break
        
        if not message:
            print("❌ Empty message. Please type something or 'quit' to exit.")
            continue
        
        # Add timestamp to message
        timestamped_message = f"{message}\n\n📅 Sent at: {time.strftime('%Y-%m-%d %H:%M:%S')}"
        
        if send_test_message(phone, timestamped_message):
            message_count += 1
            print(f"✅ Message #{message_count} sent successfully!")
        else:
            print("❌ Failed to send message. Continue? (y/n): ", end="")
            if input().lower() != 'y':
                break
        
        # Small delay to avoid rate limiting
        time.sleep(1)

def bulk_messaging(phone):
    """Send multiple predefined messages"""
    print(f"\n📦 Bulk messaging to {phone}")
    
    messages = [
        "🚀 Message 1: Hello from WhatsApp Gateway!",
        "📱 Message 2: This is a bulk message test",
        "💻 Message 3: Your API is working perfectly!",
        "⭐ Message 4: Multiple messages sent successfully",
        "🎉 Message 5: Bulk messaging complete!"
    ]
    
    print(f"📋 Prepared {len(messages)} messages to send")
    confirm = input("Proceed with sending? (y/n): ").strip().lower()
    
    if confirm != 'y':
        print("❌ Bulk messaging cancelled")
        return
    
    success_count = 0
    for i, message in enumerate(messages, 1):
        print(f"\n� Sending message {i}/{len(messages)}...")
        timestamped_message = f"{message}\n\n📅 Sent at: {time.strftime('%Y-%m-%d %H:%M:%S')}"
        
        if send_test_message(phone, timestamped_message):
            success_count += 1
            print(f"✅ Message {i} sent successfully!")
        else:
            print(f"❌ Message {i} failed!")
        
        # Delay between messages to avoid rate limiting
        if i < len(messages):
            print("⏳ Waiting 3 seconds before next message...")
            time.sleep(3)
    
    print(f"\n📊 Bulk messaging complete: {success_count}/{len(messages)} messages sent successfully")

def auto_messaging(phone):
    """Send messages automatically at intervals"""
    print(f"\n🤖 Auto messaging to {phone}")
    
    try:
        interval = int(input("Enter interval between messages (seconds, default 10): ") or "10")
        max_messages = int(input("Enter maximum number of messages (default 5): ") or "5")
    except ValueError:
        print("❌ Invalid input. Using defaults: 10 seconds interval, 5 messages max")
        interval = 10
        max_messages = 5
    
    print(f"⚙️  Configuration:")
    print(f"   📱 Phone: {phone}")
    print(f"   ⏰ Interval: {interval} seconds")
    print(f"   📊 Max messages: {max_messages}")
    
    confirm = input("\nStart auto messaging? (y/n): ").strip().lower()
    if confirm != 'y':
        print("❌ Auto messaging cancelled")
        return
    
    print(f"\n🚀 Starting auto messaging... (Press Ctrl+C to stop)")
    
    message_count = 0
    try:
        while message_count < max_messages:
            message_count += 1
            message = f"🤖 Auto message #{message_count}\n📅 Sent at: {time.strftime('%Y-%m-%d %H:%M:%S')}\n⏰ Interval: {interval}s"
            
            print(f"\n📤 Sending auto message {message_count}/{max_messages}...")
            
            if send_test_message(phone, message):
                print(f"✅ Auto message {message_count} sent successfully!")
            else:
                print(f"❌ Auto message {message_count} failed!")
            
            if message_count < max_messages:
                print(f"⏳ Waiting {interval} seconds for next message...")
                time.sleep(interval)
        
        print(f"\n🎉 Auto messaging complete! Sent {message_count} messages")
        
    except KeyboardInterrupt:
        print(f"\n⏹️  Auto messaging stopped by user. Sent {message_count} messages")

def main():
    """Main testing function"""
    print("�🚀 WhatsApp API Gateway - Test Client")
    print("=" * 50)
    
    # Test health
    if not test_health():
        print("❌ Health check failed. Make sure the container is running.")
        return
    
    # Test status
    status = test_status()
    if not status:
        print("❌ Status check failed.")
        return
    
    # Check if WhatsApp is connected
    if not status.get("baileys_server", {}).get("whatsapp_connected", False):
        print("\n⚠️  WhatsApp is not connected yet.")
        if not wait_for_whatsapp_connection():
            print("❌ Cannot proceed without WhatsApp connection.")
            return
    
    # Choose testing mode
    print("\n" + "=" * 50)
    print("📱 WHATSAPP MESSAGING OPTIONS")
    print("=" * 50)
    print("1. Send single test message")
    print("2. Send multiple messages")
    
    choice = input("\nChoose option (1-2): ").strip()
    
    if choice == "1":
        # Single message test (original functionality)
        print("\n📱 SINGLE MESSAGE TEST")
        print("=" * 30)
        
        phone = input("Enter phone number (with country code, e.g., +1234567890): ").strip()
        if not phone:
            phone = "+201025939307"  # Default for testing
            print(f"Using default phone: {phone}")
        
        test_message = f"🤖 Test message from WhatsApp API Gateway\nTimestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}"
        
        success = send_test_message(phone, test_message)
        
        if success:
            print("\n✅ Single message test passed!")
        else:
            print("\n❌ Single message test failed.")
    
    elif choice == "2":
        send_multiple_messages()
    
    else:
        print("❌ Invalid choice!")

if __name__ == "__main__":
    main()
