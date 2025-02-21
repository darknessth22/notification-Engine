import logging
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import yaml
from typing import Dict, Any
class WhatsAppNotifier:
    def __init__(self, config_path: str = 'config/config.yaml'):
        """
        Initialize WhatsApp Notifier with configuration from YAML file
        
        :param config_path: Path to configuration YAML file
        """
        self.config_path = config_path
        self.config = self._load_config()
        chrome_config = self.config.get('chrome', {})
        whatsapp_config = self.config.get('whatsapp', {})
        driver_config = chrome_config.get('driver', {})
        self.executable_path = driver_config.get('executable_path')
        self.chrome_binary_location = driver_config.get('binary_location')
        profile_config = chrome_config.get('profile', {})
        self.user_data_dir = profile_config.get('user_data_dir')
        self.profile_directory = profile_config.get('profile_directory')
        self.contact_name = whatsapp_config.get('contact_name')
        self.phone_number = whatsapp_config.get('phone_number')
        self.whatsapp_driver = None
        self.current_contact = None
        self._validate_config()
        logging.basicConfig(level=logging.DEBUG)    
    def _load_config(self) -> Dict[str, Any]:
        """
        Load configuration from the specified YAML file
        
        :return: Loaded configuration as a dictionary
        """
        try:
            with open(self.config_path, 'r') as config_file:
                return yaml.safe_load(config_file)
        except Exception as e:
            raise RuntimeError(f"Failed to load configuration from {self.config_path}: {str(e)}")
    
    def _validate_config(self):
        """
        Validate required configuration values
        """
        required_fields = {
            'executable_path': 'chrome.driver.executable_path',
            'chrome_binary_location': 'chrome.driver.binary_location',
            'user_data_dir': 'chrome.profile.user_data_dir',
            'profile_directory': 'chrome.profile.profile_directory',
            'contact_name': 'whatsapp.contact_name'
        }
        
        missing_fields = []
        for attr, config_path in required_fields.items():
            if getattr(self, attr) is None:
                missing_fields.append(config_path)
        
        if missing_fields:
            raise ValueError(f"Missing required configuration fields: {', '.join(missing_fields)}")
   
        
    def init_driver(self, headless: bool = True, silent: bool = True):
        """
        Initialize Selenium WebDriver for WhatsApp with improved headless support
        """
        chrome_options = Options()
        chrome_options.binary_location = self.chrome_binary_location
        
        # Add required user data and profile directories
        chrome_options.add_argument(f"--user-data-dir={self.user_data_dir}")
        chrome_options.add_argument(f"--profile-directory={self.profile_directory}")
        
        # Essential arguments for headless mode
        if headless:
            chrome_options.add_argument("--headless=new")
            chrome_options.add_argument("--window-size=1920,1080")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--disable-notifications")
            chrome_options.add_argument("--disable-popup-blocking")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            chrome_options.add_argument("--disable-web-security")
            chrome_options.add_argument("--allow-running-insecure-content")
            
            # Add user agent
            chrome_options.add_argument("user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        # Additional preferences
        chrome_options.add_experimental_option("prefs", {
            "profile.default_content_setting_values.notifications": 2,
            "profile.default_content_settings.popups": 0,
        })
        
        if silent:
            chrome_options.add_experimental_option("excludeSwitches", ["enable-logging"])
        
        service = Service(self.executable_path)
        self.whatsapp_driver = webdriver.Chrome(service=service, options=chrome_options)
        
        if headless:
            self.whatsapp_driver.set_window_size(1920, 1080)
            self.whatsapp_driver.execute_cdp_cmd('Network.setUserAgentOverride', {
                "userAgent": 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            })
        
        logging.info("WhatsApp Selenium driver initialized.")
        return self

    
    def login(self):
        """
        Log in to WhatsApp Web
        
        :return: Instance of WhatsAppNotifier
        """
        if not self.whatsapp_driver:
            raise RuntimeError("WebDriver not initialized. Call init_driver() first.")
        
        self.whatsapp_driver.get("https://web.whatsapp.com/")
        try:
            WebDriverWait(self.whatsapp_driver, 60).until(
                EC.presence_of_element_located((By.XPATH, '//div[@id="side"]'))
            )
            logging.info("WhatsApp logged in successfully!")
        except Exception as e:
            logging.error("Error during login: " + str(e))
            try:
                logging.error("Page source snippet: " + self.whatsapp_driver.page_source[:500])
            except Exception:
                logging.error("Could not retrieve page source during login.")
        
        return self
    
    def open_contact_chat(self, contact_name):
        """
        Open the chat for the given contact
        
        :param contact_name: Name of the contact to open chat with
        :return: Instance of WhatsAppNotifier
        """
        try:
            search_box = WebDriverWait(self.whatsapp_driver, 30).until(
                EC.presence_of_element_located((By.XPATH, '//div[@contenteditable="true"][@data-tab="3"]'))
            )
            search_box.clear()
            search_box.click()
            search_box.send_keys(contact_name)
            time.sleep(2)

            contact = WebDriverWait(self.whatsapp_driver, 30).until(
                EC.element_to_be_clickable((By.XPATH, f'//span[@title="{contact_name}"]'))
            )
            contact.click()
            time.sleep(2)
            self.current_contact = contact_name
            logging.info(f"Chat for {contact_name} opened successfully.")
        except Exception as e:
            logging.error("Error opening contact chat: " + str(e))
        
        return self
    
    def send_message(self, 
                contact_name, 
                message, 
                search_xpath='//div[@contenteditable="true"][@data-tab="3"]',
                message_box_xpath='//div[@contenteditable="true"][@data-tab="10"]'):
        """
        Send a WhatsApp message as a single message with proper formatting
        """
        if not self.whatsapp_driver:
            raise RuntimeError("WebDriver not initialized. Call init_driver() first.")

        try:
            # Open the chat if it's not already open
            if self.current_contact != contact_name:
                search_box = WebDriverWait(self.whatsapp_driver, 5).until(
                    EC.presence_of_element_located((By.XPATH, search_xpath))
                )
                search_box.clear()
                search_box.send_keys(contact_name + Keys.ENTER)
                
                contact_xpath = f'//span[@title="{contact_name}"]'
                contact = WebDriverWait(self.whatsapp_driver, 2).until(
                    EC.element_to_be_clickable((By.XPATH, contact_xpath))
                )
                contact.click()
                self.current_contact = contact_name

            # Find message box
            chat_box = WebDriverWait(self.whatsapp_driver, 5).until(
                EC.presence_of_element_located((By.XPATH, message_box_xpath))
            )
            
            # Clear any existing text
            chat_box.clear()
            
            # Use Shift+Enter for line breaks within the message
            lines = message.split('\n')
            for i, line in enumerate(lines):
                chat_box.send_keys(line)
                if i < len(lines) - 1:  # Don't add newline after the last line
                    chat_box.send_keys(Keys.SHIFT + Keys.ENTER)
            
            # Send the message
            chat_box.send_keys(Keys.ENTER)
            
            logging.info(f"Message sent to {contact_name}")
            
        except Exception as e:
            logging.error(f"Error sending message: {str(e)}")
            self.handle_error(e)
                
        return self
    

    def send_violation_notification(self, alert_id, violation_types, timestamp, description, contact_name=None):
        """
        Send a violation notification to a specific contact
        
        :param alert_id: Unique alert identifier
        :param violation_types: List of violation types
        :param timestamp: Time of violation
        :param description: Violation description
        :param contact_name: Contact to send notification to (uses configured contact if not specified)
        :return: Instance of WhatsAppNotifier
        """
        if contact_name is None:
            contact_name = self.contact_name
        
        violation_type_str = ', '.join(violation_types)
        message = (
            "*ALERT NOTIFICATION*\n\n"
            f"Alert ID: {alert_id}\n"
            f"Type: {violation_type_str}\n"
            f"Timestamp: {timestamp}\n\n"
            f"{description}"
        )
        
        self.send_message(contact_name, message)
        logging.info(f"Notification for {violation_type_str} sent successfully!")
        
        return self
    
    def handle_error(self, error):
        """
        Handle errors during message sending
        """
        try:
            logging.error("Full error details:")
            logging.error(str(error))
            
            # Get current URL
            current_url = self.whatsapp_driver.current_url
            logging.error(f"Current URL: {current_url}")
            
            # Take screenshot for debugging
            screenshot_path = f"error_screenshot_{int(time.time())}.png"
            self.whatsapp_driver.save_screenshot(screenshot_path)
            logging.error(f"Error screenshot saved to: {screenshot_path}")
            
            # Check if we're still logged in
            if "web.whatsapp.com" not in current_url:
                logging.error("WhatsApp Web session appears to be invalid. Attempting to relogin...")
                self.login()
            
        except Exception as e:
            logging.error(f"Error in error handler: {str(e)}")
            
    def close_driver(self):
        """
        Close the Selenium WebDriver
        
        :return: Instance of WhatsAppNotifier
        """
        if self.whatsapp_driver:
            self.whatsapp_driver.quit()
            logging.info("WhatsApp WebDriver closed.")
        return self