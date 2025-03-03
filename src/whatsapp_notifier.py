import logging
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import yaml
from typing import Dict, Any
import asyncio

class WhatsAppNotifier:
    def __init__(self, config: dict):
        self.config = config
        chrome_config = self.config.get('chrome', {})
        whatsapp_config = self.config.get('whatsapp', {})
        driver_config = chrome_config.get('driver', {})
        self.executable_path = driver_config.get('executable_path')
        self.chrome_binary_location = driver_config.get('binary_location')
        profile_config = chrome_config.get('profile', {})
        self.user_data_dir = profile_config.get('user_data_dir')
        self.profile_directory = profile_config.get('profile_directory')
        self.contact_name = whatsapp_config.get('contact_name')
        self.whatsapp_driver = None
        self.current_contact = None
        self._validate_config()
        self.notification_queue = asyncio.Queue()
        self.running = False
        logging.basicConfig(level=logging.DEBUG)
        

    def _load_config(self) -> Dict[str, Any]:
        try:
            with open(self.config_path, 'r') as config_file:
                return yaml.safe_load(config_file)
        except Exception as e:
            raise RuntimeError(f"Failed to load configuration from {self.config_path}: {str(e)}")
    
    def _validate_config(self):
        required_fields = {
            'executable_path': 'chrome.driver.executable_path',
            'chrome_binary_location': 'chrome.driver.binary_location',
            'user_data_dir': 'chrome.profile.user_data_dir',
            'profile_directory': 'chrome.profile.profile_directory',
            'contact_name': 'whatsapp.contact_name'
        }
        
        missing_fields = [config_path for attr, config_path in required_fields.items() 
                         if getattr(self, attr) is None]
        
        if missing_fields:
            raise ValueError(f"Missing required configuration fields: {', '.join(missing_fields)}")

    def init_driver(self, headless: bool = True, silent: bool = True):
        chrome_options = Options()
        chrome_options.binary_location = self.chrome_binary_location
        chrome_options.add_argument(f"--user-data-dir={self.user_data_dir}")
        chrome_options.add_argument(f"--profile-directory={self.profile_directory}")
        
        if headless:
            chrome_options.add_argument("--headless=new")
            chrome_options.add_argument("--window-size=1920,1080")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--disable-notifications")
            chrome_options.add_argument("--disable-popup-blocking")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            chrome_options.add_argument("user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        if silent:
            chrome_options.add_experimental_option("excludeSwitches", ["enable-logging"])
        
        service = Service(self.executable_path)
        self.whatsapp_driver = webdriver.Chrome(service=service, options=chrome_options)
        logging.info("WhatsApp Selenium driver initialized.")
        return self

    def login(self):
        if not self.whatsapp_driver:
            raise RuntimeError("WebDriver not initialized. Call init_driver() first.")
        
        self.whatsapp_driver.get("https://web.whatsapp.com/")
        try:
            WebDriverWait(self.whatsapp_driver, 60).until(
                EC.presence_of_element_located((By.XPATH, '//div[@id="side"]'))
            )
            logging.info("WhatsApp logged in successfully!")
        except Exception as e:
            logging.error(f"Error during login: {str(e)}")
        return self

    def send_message(self, contact_name: str, message: str):
        if not self.whatsapp_driver:
            raise RuntimeError("WebDriver not initialized. Call init_driver() first.")

        try:
            if self.current_contact != contact_name:
                search_box = WebDriverWait(self.whatsapp_driver, 5).until(
                    EC.presence_of_element_located((By.XPATH, '//div[@contenteditable="true"][@data-tab="3"]'))
                )
                search_box.clear()
                search_box.send_keys(contact_name + Keys.ENTER)
                self.current_contact = contact_name

            chat_box = WebDriverWait(self.whatsapp_driver, 5).until(
                EC.presence_of_element_located((By.XPATH, '//div[@contenteditable="true"][@data-tab="10"]'))
            )
            
            chat_box.clear()
            lines = message.split('\n')
            for i, line in enumerate(lines):
                chat_box.send_keys(line)
                if i < len(lines) - 1:
                    chat_box.send_keys(Keys.SHIFT + Keys.ENTER)
            
            chat_box.send_keys(Keys.ENTER)
            logging.info(f"Message sent to {contact_name}")
            
        except Exception as e:
            logging.error(f"Error sending message: {str(e)}")
            self.handle_error(e)
                
        return self

    async def start_notification_worker(self):
        self.running = True
        while self.running:
            try:
                notification = await asyncio.wait_for(
                    self.notification_queue.get(),
                    timeout=1.0
                )
                await self._process_notification(notification)
                self.notification_queue.task_done()
                await asyncio.sleep(0.1)
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logging.error(f"Error in notification worker: {str(e)}")
                await asyncio.sleep(1)

    async def _process_notification(self, notification):
        try:
            contact_name = notification.get('contact_name', self.contact_name)
            message = notification['message']
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(None, self.send_message, contact_name, message)
            await asyncio.sleep(0.5)
        except Exception as e:
            logging.error(f"Error processing notification: {str(e)}")

    async def send_violation_notification_async(self, alert_id, violation_types, timestamp, description):
        violation_type_str = ', '.join(violation_types)
        message = (
            "*ALERT NOTIFICATION*\n\n"
            f"Alert ID: {alert_id}\n"
            f"Type: {violation_type_str}\n"
            f"Timestamp: {timestamp}\n"
            f"Description: {description}"
        )
        
        await self.notification_queue.put({
            'contact_name': self.contact_name,
            'message': message
        })

    def handle_error(self, error):
        logging.error(f"Error details: {str(error)}")
        try:
            current_url = self.whatsapp_driver.current_url
            if "web.whatsapp.com" not in current_url:
                logging.error("WhatsApp Web session invalid. Attempting to relogin...")
                self.login()
        except Exception as e:
            logging.error(f"Error in error handler: {str(e)}")

    async def shutdown(self):
        self.running = False
        await self.notification_queue.join()
        if self.whatsapp_driver:
            self.whatsapp_driver.quit()