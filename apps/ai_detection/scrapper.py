import os
import time
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options

# Update this path to your ChromeDriver
DRIVER_PATH = "/home/dark/chromedriver-linux64/chromedriver"  # Replace with the correct path

# Function to fetch image URLs
def fetch_image_urls(query, max_links, wd, sleep_time=2):
    search_url = f"https://www.google.com/search?q={query}&tbm=isch"
    wd.get(search_url)
    
    image_urls = set()
    image_count = 0
    results_start = 0

    while image_count < max_links:
        wd.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(sleep_time)
        
        thumbnails = wd.find_elements(By.CSS_SELECTOR, "img.Q4LuWd")
        print(f"Found {len(thumbnails)} thumbnails.")

        for img in thumbnails[results_start:]:
            try:
                wd.execute_script("arguments[0].scrollIntoView();", img)
                wd.execute_script("arguments[0].click();", img)
                time.sleep(sleep_time)
            except Exception as e:
                print(f"Error clicking image: {e}")
                continue

            images = wd.find_elements(By.CSS_SELECTOR, "img.n3VNCb")
            for full_img in images:
                src = full_img.get_attribute("src")
                if src and src.startswith("http"):
                    image_urls.add(src)
            
            image_count = len(image_urls)
            if image_count >= max_links:
                break

        results_start = len(thumbnails)

    return image_urls

# Function to download images
def download_image(folder, url, count):
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        file_path = os.path.join(folder, f"image_{count}.jpg")

        with open(file_path, "wb") as f:
            f.write(response.content)
        print(f"Downloaded: {url}")

    except Exception as e:
        print(f"Error downloading {url}: {e}")

# Main execution
if __name__ == "__main__":
    search_term = "Qatar license plate"
    max_images = 10
    download_folder = "downloaded_images"

    if not os.path.exists(download_folder):
        os.makedirs(download_folder)

    chrome_options = Options()
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")

    service = Service(DRIVER_PATH)
    wd = webdriver.Chrome(service=service, options=chrome_options)

    try:
        print(f"Fetching image URLs for '{search_term}'...")
        urls = fetch_image_urls(search_term, max_images, wd)
        print(f"Found {len(urls)} images.")
    finally:
        wd.quit()

    for idx, url in enumerate(urls):
        download_image(download_folder, url, idx)

    print("Download complete!")
