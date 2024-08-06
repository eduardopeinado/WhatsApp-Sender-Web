import time
import logging
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

driver = None

def init_browser(headless=False):
    global driver
    options = Options()
    if headless:
        options.add_argument('--headless')
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    driver.get("https://web.whatsapp.com")
    return driver

def move_browser_out_of_view(driver):
    driver.set_window_position(-2000, -2000)
    driver.set_window_size(1280, 800)
    driver.execute_script("document.body.style.zoom='60%'")  # Ajustar el zoom al 80%

def get_driver():
    global driver
    if driver is None:
        driver = init_browser(headless=False)
        time.sleep(20)
        move_browser_out_of_view(driver)
    return driver

def close_driver():
    global driver
    if driver:
        driver.quit()
        driver = None
        logging.info("Browser closed successfully.")
