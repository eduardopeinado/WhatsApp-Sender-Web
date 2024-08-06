import os
import time
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# Configuración de logging
logging.basicConfig(filename='debug.log', level=logging.INFO, format='%(asctime)s %(levelname)s:%(message)s')

driver = None  # Definir el driver como global

def init_browser(headless=False):
    global driver
    options = Options()
    if headless:
        options.add_argument('--headless')
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    driver.get("https://web.whatsapp.com")
    return driver

def get_all_files(folder_path):
    if not os.path.isdir(folder_path):
        return []
    files = [os.path.join(folder_path, file) for file in os.listdir(folder_path) if file.lower().endswith(
        ('png', 'jpg', 'jpeg', 'gif', 'bmp', 'tiff', 'pdf', 'doc', 'docx', 'xls', 'xlsx', 'mp4'))]
    return files

def replace_placeholders(message, contact):
    placeholders = ['{nombre}', '[nombre]']
    for placeholder in placeholders:
        if placeholder in message:
            message = message.replace(placeholder, contact.get('first_name', ''))
    return message

def send_message(driver, phone_number, message, attachment_paths, index, total, is_last):
    try:
        # Buscar e ingresar el número de teléfono
        search_box_css = 'div[contenteditable="true"][data-tab="3"]'
        search_box = driver.find_element(By.CSS_SELECTOR, search_box_css)
        search_box.click()
        logging.info("Clicked on search box.")
        time.sleep(2)
        
        search_box.clear()
        for char in phone_number:
            search_box.send_keys(char)
            time.sleep(0.1)  # Tiempo de espera breve entre cada carácter para asegurar la entrada correcta
        logging.info(f"Numero ingresado: {phone_number}")
        time.sleep(2)
        search_box.send_keys(Keys.ENTER)
        logging.info("Pressed ENTER after typing the number.")
        time.sleep(2)  # Esperar a que se abra la conversación

        # Verificar que el cuadro de mensaje esté presente y visible
        wait = WebDriverWait(driver, 10)
        message_box = wait.until(EC.presence_of_element_located((By.XPATH, '//div[@contenteditable="true"][@data-tab="10"]')))
        logging.info("Message box is present.")
        
        # Escribir y enviar el mensaje
        for char in message:
            message_box.send_keys(char)
            time.sleep(0.01)  # Espera para escribir cada carácter en el cuadro de mensaje
        logging.info(f"Mensaje escrito: {message}")
        time.sleep(2)
        message_box.send_keys(Keys.SHIFT, Keys.ENTER)  # Simula presionar Shift + Enter para asegurarse de enviar el mensaje
        message_box.send_keys(Keys.ENTER)
        logging.info("Pressed ENTER to send the message.")
        time.sleep(2)  # Esperar a que se envíe el mensaje

        # Adjuntar archivos si se proporciona una ruta válida
        if attachment_paths:
            for i, file_path in enumerate(attachment_paths):
                logging.info(f"Attaching file: {file_path}")

                # Clic en el botón de adjuntar
                attach_button = wait.until(EC.presence_of_element_located((By.XPATH, '//div[@title="Attach"]')))
                attach_button.click()
                logging.info("Clicked on attach button.")
                time.sleep(2)

                # Seleccionar el tipo de archivo adecuado
                if file_path.lower().endswith(('png', 'jpg', 'jpeg', 'gif', 'bmp', 'tiff', 'mp4')):
                    file_input_xpath = '//input[@accept="image/*,video/mp4,video/3gpp,video/quicktime"]'
                else:
                    file_input_xpath = '//input[@accept="*"]'
                
                file_input = wait.until(EC.presence_of_element_located((By.XPATH, file_input_xpath)))
                file_input.send_keys(file_path)
                logging.info("Selected file to attach.")
                time.sleep(4)  # Esperar a que el archivo se cargue completamente

                # Clic en el botón de enviar
                send_button = wait.until(EC.element_to_be_clickable((By.XPATH, '//span[@data-icon="send"]')))
                send_button.click()
                logging.info("Clicked on send button.")
                time.sleep(4)  # Esperar a que se envíe el archivo

                if is_last and i == len(attachment_paths) - 1:
                    time.sleep(3)  # Delay adicional para el último attachment del último mensaje

        # Escribir el estado en el archivo de texto
        with open('status.txt', 'w') as status_file:
            status_file.write(f"Enviado {index + 1} de {total}\n")

    except Exception as e:
        logging.error(f"Error: {e}")

def move_browser_out_of_view(driver):
    driver.set_window_position(-2000, -2000)  # Mueve la ventana fuera de la vista del usuario
    driver.set_window_size(1280, 800)      # Cambia el tamaño de la ventana

def send_messages_whatsapp(final_text, recipients, folder_path):
    global driver  # Hacer que el driver sea global para mantenerlo abierto
    if driver is None:
        driver = init_browser(headless=False)
        time.sleep(20)  # Esperar a que WhatsApp Web cargue completamente y solicitar autorización del usuario
        logging.info("Browser opened and WhatsApp Web loaded.")
        move_browser_out_of_view(driver)
        logging.info("Browser moved out of view and resized successfully.")

    total_messages = len(recipients)
    sent_count = 0

    try:
        for i, recipient in enumerate(recipients):
            is_last = (sent_count + 1 == total_messages)
            message = replace_placeholders(final_text, recipient)
            attachment_paths = get_all_files(folder_path)  # Obtener todas las rutas de archivos adjuntos
            send_message(driver, recipient['phone'], message, attachment_paths, sent_count, total_messages, is_last)
            sent_count += 1
    except Exception as e:
        logging.error(f"Error during message sending: {e}")
    finally:
        if driver:
            driver.quit()
            driver = None
            logging.info("Browser closed successfully.")