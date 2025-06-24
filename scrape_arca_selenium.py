import os
import time
import requests
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# --- CONFIGURACIÓN ---
SEARCH_TERM = "escuela quiteña" 
FOLDER_NAME = SEARCH_TERM.replace(" ", "_").lower()
OUTPUT_FOLDER = os.path.join("raw_images", FOLDER_NAME)
BASE_URL = "https://arcav1.uniandes.edu.co"
SEARCH_PAGE_URL = f"{BASE_URL}/artworks"

# --- FIN DE CONFIGURACIÓN ---

def sanitize_filename(filename):
    return re.sub(r'[\\/*?:"<>|]', "", filename)

def download_current_page_images(driver, wait):
    """Función para descargar todas las imágenes de la página actualmente visible."""
    try:
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.artwork-thumbnail")))
        thumbnail_elements = driver.find_elements(By.CSS_SELECTOR, "div.artwork-thumbnail")
        
        print(f"  Encontradas {len(thumbnail_elements)} imágenes en esta página. Descargando...")
        
        for i, thumb_element in enumerate(thumbnail_elements):
            try:
                img_wrap_div = thumb_element.find_element(By.ID, "img-wrap")
                style_attribute = img_wrap_div.get_attribute('style')
                match = re.search(r"url\(['\"]?(.*?)['\"]?\)", style_attribute)
                if not match: continue

                relative_url = match.group(1)
                image_url = BASE_URL + relative_url

                caption_element = thumb_element.find_element(By.CLASS_NAME, "caption")
                title = caption_element.text.split('\n')[0] or f"img_{int(time.time())}_{i}"
                
                try:
                    artwork_id = thumb_element.find_element(By.TAG_NAME, 'a').get_attribute('href').split('/')[-1]
                    filename = f"{artwork_id}_{sanitize_filename(title).strip().rstrip(',')}.jpg"
                except:
                    filename = f"{sanitize_filename(title).strip().rstrip(',')}_{int(time.time())}_{i}.jpg"

                filepath = os.path.join(OUTPUT_FOLDER, filename)
                
                if os.path.exists(filepath):
                    continue
                
                image_response = requests.get(image_url, stream=True, headers={'User-Agent': 'My-Art-Project-Scraper/5.0-pagination'})
                image_response.raise_for_status()
                with open(filepath, 'wb') as f:
                    for chunk in image_response.iter_content(chunk_size=8192): f.write(chunk)
                
                time.sleep(0.05)

            except Exception as e:
                print(f"    -> Error procesando una miniatura: {e}")
    except TimeoutException:
        print("  -> No se encontraron imágenes en esta página o tardaron demasiado en cargar.")


def download_images_with_pagination(search_term):
    if not os.path.exists(OUTPUT_FOLDER):
        os.makedirs(OUTPUT_FOLDER)
        print(f"Carpeta creada: {OUTPUT_FOLDER}")

    chrome_options = Options()
    # chrome_options.add_argument("--headless")
    chrome_options.add_argument("--log-level=3") 
    service = Service() 
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    try:
        print(f"Abriendo navegador y yendo a: {SEARCH_PAGE_URL}")
        driver.get(SEARCH_PAGE_URL)
        wait = WebDriverWait(driver, 20)
        
        print(f"Buscando el término: '{search_term}'")
        search_box = wait.until(EC.presence_of_element_located((By.ID, "search")))
        search_box.send_keys(search_term)
        
        search_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "i.fa-search")))
        driver.execute_script("arguments[0].click();", search_button)
        
        page_number = 1
        while True:
            print(f"\nProcesando Página #{page_number}...")
            wait.until(EC.presence_of_element_located((By.CLASS_NAME, "pagination")))
            
            download_current_page_images(driver, wait)
            
            try:
                next_button_li = driver.find_element(By.CSS_SELECTOR, "li.next:not(.disabled)")
                next_button = next_button_li.find_element(By.TAG_NAME, 'a')
                
                print(f"  Haciendo clic en 'Next →' para ir a la página {page_number + 1}")
                driver.execute_script("arguments[0].click();", next_button)
                
                time.sleep(2)
                page_number += 1
                
            except NoSuchElementException:
                print("\nNo se encontró el botón 'Next →' o está deshabilitado. Se ha llegado a la última página.")
                break

    except Exception as e:
        print(f"Ocurrió un error principal: {e}")
        screenshot_path = "debug_screenshot_fail.png"
        driver.save_screenshot(screenshot_path)
        print(f"Se ha guardado una captura de pantalla en '{screenshot_path}'.")
    
    finally:
        driver.quit()
        if os.path.exists(OUTPUT_FOLDER):
            final_count = len(os.listdir(OUTPUT_FOLDER))
            print(f"\nNavegador cerrado. ¡Proceso terminado! Se han descargado {final_count} imágenes en la carpeta.")
        else:
            print("\nNavegador cerrado. ¡Proceso terminado!")

# --- CORRECCIÓN APLICADA AQUÍ ---
if __name__ == "__main__":
    download_images_with_pagination(SEARCH_TERM)