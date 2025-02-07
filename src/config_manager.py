"""
ConfigManager: Manages configuration settings for the application, 
including model, video, notification, WhatsApp, and Chrome driver settings.
"""

from pathlib import Path
import logging
import yaml
import torch
from typing import Dict, Any

class ConfigManager:
    def __init__(self, config_path= 'config/config.yaml'):
        """
        Initialize configuration manager

        :param config_path: Path to the YAML configuration file
        """
        self.config_path = config_path
        self.config = self._load_config()
        self._setup_logging()
        
    def _load_config(self) -> Dict[str, Any]:
        """
        Load configuration from a YAML file

        :return: Configuration data as a dictionary
        """
        try:
            with open(self.config_path, 'r') as config_file:
                return yaml.safe_load(config_file)
        except Exception as e:
            raise RuntimeError(f"Failed to load configuration from {self.config_path}: {str(e)}")
    
    def _setup_logging(self) -> None:
        """
        Configure logging based on settings in the configuration file
        """
        logging_config = self.config.get('logging', {})
        logging.basicConfig(
            level=getattr(logging, logging_config.get('level', 'DEBUG').upper()),
            filename=logging_config.get('file_path', './fire_detection.log')
        )
    
    @property
    def model_settings(self) -> Dict[str, Any]:
        """
        Model-related settings. 
        Includes model path and confidence threshold.
        """
        fire_detection = self.config.get('model', {}).get('fire_detection', {})
        return {
            'model_path': fire_detection.get('path'),
            'confidence_threshold': fire_detection.get('confidence_threshold')
        }
    
    @property
    def video_settings(self) -> Dict[str, Any]:
        """
        Video-related settings.
        Includes stream URL and output directory.
        """
        video_config = self.config.get('video', {})
        return {
            'stream_url': video_config.get('stream_url'),
            'output_directory': video_config.get('output_directory')
        }
    
    @property
    def device_settings(self) -> torch.device:
        """
        Device configuration (CPU or CUDA).
        Prefer CUDA if available and configured.
        """
        use_cuda = (
            self.config.get('device', {}).get('prefer_cuda', False) 
            and torch.cuda.is_available()
        )
        return torch.device('cuda' if use_cuda else 'cpu')
    
    @property
    def notification_settings(self) -> Dict[str, Any]:
        """
        Notification-related settings.
        Includes initial alert counter and default priority.
        """
        notification_config = self.config.get('notification', {})
        return {
            'initial_alert_counter': notification_config.get('initial_alert_counter'),
            'default_priority': notification_config.get('default_priority')
        }
    
    @property
    def server_settings(self) -> Dict[str, Any]:
        """
        Server-related settings.
        Includes host, port, and reload configuration.
        """
        server_config = self.config.get('server', {})
        return {
            'host': server_config.get('host'),
            'port': server_config.get('port'),
            'reload': server_config.get('reload')
        }
    
    @property
    def whatsapp_settings(self) -> Dict[str, Any]:
        """
        WhatsApp-related settings.
        Fetches contact name and phone number from configuration.
        """
        whatsapp_config = self.config.get('whatsapp', {})
        return {
            'contact_name': whatsapp_config.get('contact_name'),
            'phone_number': whatsapp_config.get('phone_number')
        }
    
    @property
    def chrome_settings(self) -> Dict[str, Any]:
        """
        Chrome-related settings.
        Includes driver and profile configurations.
        """
        chrome_config = self.config.get('chrome', {})
        return {
            'driver': chrome_config.get('driver', {}),
            'profile': chrome_config.get('profile', {})
        }