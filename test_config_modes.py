#!/usr/bin/env python3
"""
Test script to demonstrate the image sending configuration options
"""

import yaml
import json

def test_config_modes():
    """Test different configuration modes"""
    
    # Test 1: Images enabled (default)
    print("=== Testing Configuration Modes ===\n")
    
    # Read current config
    with open('config/config.yaml', 'r') as file:
        config = yaml.safe_load(file)
    
    send_images = config.get('whatsapp', {}).get('send_images', True)
    send_videos = config.get('whatsapp', {}).get('send_videos', False)
    recording_enabled = config.get('video', {}).get('recording', {}).get('enabled', False)
    
    print(f"Current configuration:")
    print(f"  send_images: {send_images}")
    print(f"  send_videos: {send_videos}")
    print(f"  recording_enabled: {recording_enabled}")
    
    if send_videos and recording_enabled:
        mode = "Video clips with captions"
    elif send_images:
        mode = "Images with captions"
    else:
        mode = "Text messages only"
    print(f"  Mode: {mode}")
    print()
    
    print("Configuration options:")
    print("1. send_images: true  -> Sends detection images with alert captions")
    print("2. send_images: false -> Sends text messages only")
    print("3. send_videos: true + recording.enabled: true -> Sends video clips")
    print("4. All three modes can be combined for comprehensive alerts")
    print()
    
    print("API Endpoints available:")
    print("- GET /config_status -> Check current configuration")
    print("- GET /video_feed -> Video stream with detections")
    print()
    
    print("To change mode:")
    print("1. Edit config/config.yaml")
    print("2. Set whatsapp.send_images to true or false")
    print("3. Restart the application")

if __name__ == "__main__":
    test_config_modes()
