import time
import logging
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def replace_placeholders(message, contact):
    placeholders = ['{nombre}', '[nombre]']
    for placeholder in placeholders:
        if placeholder in message:
            message = message.replace(placeholder, contact.get('first_name', ''))
    return message

def send_message(driver, phone_number, message, attachment_paths, index, total, is_last):
    try:
        search_box_css = 'div[contenteditable="true"][data-tab="3"]'
        wait = WebDriverWait(driver, 20)
        
        logging.info("Esperando la caja de búsqueda...")
        search_box = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, search_box_css)))
        driver.execute_script("arguments[0].click();", search_box)
        logging.info("Hizo clic en la caja de búsqueda.")
        time.sleep(2)
        
        search_box.clear()
        for char in phone_number:
            search_box.send_keys(char)
            time.sleep(0.1)
        logging.info(f"Número ingresado: {phone_number}")
        time.sleep(2)
        search_box.send_keys(Keys.ENTER)
        logging.info("Presionó ENTER después de escribir el número.")
        time.sleep(2)

        logging.info("Esperando la caja de mensaje...")
        message_box = wait.until(EC.presence_of_element_located((By.XPATH, '//div[@contenteditable="true"][@data-tab="10"]')))
        logging.info("La caja de mensaje está presente.")
        
        for char in message:
            message_box.send_keys(char)
            time.sleep(0.01)
        logging.info(f"Mensaje escrito: {message}")
        time.sleep(2)
        message_box.send_keys(Keys.SHIFT, Keys.ENTER)
        message_box.send_keys(Keys.ENTER)
        logging.info("Presionó ENTER para enviar el mensaje.")
        time.sleep(2)

        # Adjuntar archivos si se proporciona una ruta válida
        if attachment_paths:
            for i, file_path in enumerate(attachment_paths):
                logging.info(f"Adjuntando archivo: {file_path}")
                attach_button = wait.until(EC.presence_of_element_located((By.XPATH, '//div[@title="Attach"]')))
                driver.execute_script("arguments[0].click();", attach_button)
                logging.info("Hizo clic en el botón de adjuntar.")
                time.sleep(2)

                if file_path.lower().endswith(('png', 'jpg', 'jpeg', 'gif', 'bmp', 'tiff', 'mp4')):
                    file_input_xpath = '//input[@accept="image/*,video/mp4,video/3gpp,video/quicktime"]'
                else:
                    file_input_xpath = '//input[@accept="*"]'
                
                file_input = wait.until(EC.presence_of_element_located((By.XPATH, file_input_xpath)))
                file_input.send_keys(file_path)
                logging.info("Archivo seleccionado para adjuntar.")
                time.sleep(4)

                # Usar el JSPath proporcionado para el botón de envío
                try:
                    send_button = driver.execute_script("return document.querySelector('#app > div > div.two._aigs > div._aigu > div._aigv._aigz > span > div > div > div > div.x1n2onr6.xyw6214.x78zum5.x1r8uery.x1iyjqo2.xdt5ytf.x1hc1fzr.x6ikm8r.x10wlt62 > div > div.x78zum5.x1c4vz4f.x2lah0s.x1helyrv.x6s0dn4.x1qughib.x178xt8z.x13fuv20.x1nfbk4f.x1y1aw1k.xwib8y2.x1d52u69.xktsk01 > div.x1247r65.xng8ra > div > div')")
                    driver.execute_script("arguments[0].scrollIntoView(true);", send_button)  # Aseguramos que el botón esté en la vista
                    driver.execute_script("arguments[0].click();", send_button)
                    logging.info("Hizo clic en el botón de enviar usando JSPath.")
                except Exception as e:
                    logging.error(f"Error usando JSPath: {e}")

                time.sleep(4)

    except Exception as e:
        logging.error(f"Error: {e}")
