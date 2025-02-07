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
import tempfile
import yaml

class WhatsAppNotifier:
    def __init__(self, config_path='config.yaml'):
        """
        Initialize WhatsApp Notifier with configuration from YAML file
        
        :param config_path: Path to configuration YAML file
        """
        # Load configuration
        with open(config_path, 'r') as config_file:
            config = yaml.safe_load(config_file)
        
        # Extract WhatsApp and Chrome configurations
        chrome_config = config.get('chrome', {})
        whatsapp_config = config.get('whatsapp', {})
        
        # Set configuration parameters
        self.executable_path = chrome_config.get('driver', {}).get('executable_path', '/usr/bin/chromedriver')
        self.user_data_dir = chrome_config.get('profile', {}).get('user_data_dir', '/home/dark/chrome_profile')
        self.profile_directory = chrome_config.get('profile', {}).get('profile_directory', 'Default')
        self.contact_name = whatsapp_config.get('contact_name', 'Default Contact')
        self.phone_number = whatsapp_config.get('phone_number', '')
        
        # Chrome binary location
        self.chrome_binary_location = chrome_config.get('driver', {}).get('binary_location', '/usr/bin/chromium-browser')
        
        self.whatsapp_driver = None
        self.current_contact = None
        self.send_lock = threading.Lock()
        
        # Configure logging
        logging.basicConfig(level=logging.DEBUG)
        
    def init_driver(self, headless=True, silent=True):
        """
        Initialize Selenium WebDriver for WhatsApp
        
        :param headless: Run Chrome in headless mode
        :param silent: Suppress logging
        """
        chrome_options = Options()
        chrome_options.binary_location = self.chrome_binary_location
        
        if headless:
            temp_profile_dir = tempfile.mkdtemp(prefix="chrome_profile_headless_")
            chrome_options.add_argument(f"--user-data-dir={temp_profile_dir}")
            chrome_options.add_argument("--profile-directory=Default")
        else:
            chrome_options.add_argument(f"--user-data-dir={self.user_data_dir}")
            chrome_options.add_argument(f"--profile-directory={self.profile_directory}")
        
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--start-maximized")
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
        
        service = Service(self.executable_path)
        self.whatsapp_driver = webdriver.Chrome(service=service, options=chrome_options)
        logging.info("WhatsApp Selenium driver initialized.")
        
        return self
    
    def login(self):
        """
        Log in to WhatsApp Web
        """
        if not self.whatsapp_driver:
            raise RuntimeError("WebDriver not initialized. Call init_driver() first.")
        
        self.whatsapp_driver.get("https://web.whatsapp.com/")
        try:
            # Wait for the WhatsApp chat sidebar to appear (indicating a successful login)
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
        Send a WhatsApp message to the specified contact
        
        :param contact_name: Name of the contact
        :param message: Message to send
        :param search_xpath: XPath for search box
        :param message_box_xpath: XPath for message input box
        """
        if not self.whatsapp_driver:
            raise RuntimeError("WebDriver not initialized. Call init_driver() first.")

        # Use a lock to prevent overlapping calls
        with self.send_lock:
            try:
                if self.current_contact != contact_name:
                    search_box = WebDriverWait(self.whatsapp_driver, 30).until(
                        EC.presence_of_element_located((By.XPATH, search_xpath))
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
                    
                message_box = WebDriverWait(self.whatsapp_driver, 30).until(
                    EC.presence_of_element_located((By.XPATH, message_box_xpath))
                )
                message_box.click()

                for line in message.split("\n"):
                    message_box.send_keys(line)
                    message_box.send_keys(Keys.SHIFT, Keys.ENTER)
                message_box.send_keys(Keys.ENTER)
                logging.info(f"Message sent to {contact_name}!")
            except Exception as e:
                logging.error("Error sending message: " + str(e))
                try:
                    logging.error("Page source snippet: " + self.whatsapp_driver.page_source[:500])
                except Exception:
                    logging.error("Could not retrieve page source during message sending.")
        
        return self
    
    def create_notification_message(self, alert_id, alert_type, timestamp, priority, description):
        """
        Create a formatted notification message
        
        :param alert_id: Unique alert identifier
        :param alert_type: Type of alert
        :param timestamp: Time of alert
        :param priority: Alert priority
        :param description: Detailed description
        :return: Formatted message string
        """
        return f"""* *ALERT NOTIFICATION*

Alert ID: {alert_id}
Type: {alert_type}
Timestamp: {timestamp}
Priority: {priority}

Description:
{description}"""
    
    def send_violation_notification(self, alert_id, violation_types, timestamp, description, contact_name=None):
        """
        Send a violation notification to a specific contact
        
        :param alert_id: Unique alert identifier
        :param violation_types: List of violation types
        :param timestamp: Time of violation
        :param description: Violation description
        :param contact_name: Contact to send notification to (uses configured contact if not specified)
        """
        # Use configured contact name if not provided
        if contact_name is None:
            contact_name = self.contact_name
        
        violation_type_str = ', '.join(violation_types)
        message = self.create_notification_message(
            alert_id=alert_id,
            alert_type=violation_type_str,
            timestamp=timestamp,
            priority="High",
            description=description
        )
        
        self.send_message(contact_name, message)
        logging.info(f"Notification for {violation_type_str} sent successfully!")
        
        return self
    
    def send_violation_notification_async(self, alert_id, violation_types, timestamp, description, contact_name="Fares Voda"):
        """
        Send violation notification in a separate thread
        
        :param alert_id: Unique alert identifier
        :param violation_types: List of violation types
        :param timestamp: Time of violation
        :param description: Violation description
        :param contact_name: Contact to send notification to
        """
        thread = threading.Thread(
            target=self.send_violation_notification,
            args=(alert_id, violation_types, timestamp, description, contact_name),
            daemon=True
        )
        thread.start()
        
        return self
    
    def close_driver(self):
        """
        Close the Selenium WebDriver
        """
        if self.whatsapp_driver:
            self.whatsapp_driver.quit()
            logging.info("WhatsApp WebDriver closed.")
        return self