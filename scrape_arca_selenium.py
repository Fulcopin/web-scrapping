import os
import time
import requests
import re
from urllib.parse import quote_plus  # Importante para codificar el término de búsqueda para la URL
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# --- CONFIGURACIÓN ---
# ¡Cambia este término para cada artista que quieras descargar!
SEARCH_TERM = "peru" 
# --- FIN DE CONFIGURACIÓN ---

def sanitize_filename(filename):
    """Limpia una cadena para que sea un nombre de archivo válido."""
    return re.sub(r'[\\/*?:"<>|]', "", filename)

def download_images_on_page(driver, wait, output_folder):
    """Descarga todas las imágenes de la página actual."""
    try:
        # Espera a que al menos una miniatura esté presente
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.artwork-thumbnail")))
        thumbnails = driver.find_elements(By.CSS_SELECTOR, "div.artwork-thumbnail")
        
        if not thumbnails:
            print("  -> No se encontraron miniaturas de imágenes en esta página.")
            return

        print(f"  Encontradas {len(thumbnails)} imágenes. Procediendo a descargar...")
        
        for thumb in thumbnails:
            try:
                # Extraer la URL de la imagen del estilo CSS
                img_wrap_div = thumb.find_element(By.CSS_SELECTOR, "div#img-wrap")
                style_attr = img_wrap_div.get_attribute('style')
                match = re.search(r"url\(['\"]?(.*?)['\"]?\)", style_attr)
                if not match: continue

                image_url = f"https://arcav1.uniandes.edu.co{match.group(1)}"

                # Extraer título y ID para el nombre del archivo
                caption_text = thumb.find_element(By.CLASS_NAME, "caption").text
                title = caption_text.split('\n')[0].strip() or f"sin_titulo_{int(time.time())}"
                
                # Obtener el ID de la obra desde el enlace para un nombre de archivo único
                artwork_id = thumb.find_element(By.TAG_NAME, 'a').get_attribute('href').split('/')[-1]
                filename = f"{artwork_id}_{sanitize_filename(title)}.jpg"
                filepath = os.path.join(output_folder, filename)
                
                if os.path.exists(filepath):
                    print(f"    - Saltando '{filename}' (ya existe).")
                    continue
                
                # Descargar la imagen
                response = requests.get(image_url, stream=True, headers={'User-Agent': 'ArtScraper/1.0'})
                response.raise_for_status()
                with open(filepath, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                
                print(f"    + Descargada '{filename}'.")
                time.sleep(0.1) # Pequeña pausa para no sobrecargar el servidor

            except Exception as e:
                print(f"    ! Error procesando una miniatura: {e}")

    except TimeoutException:
        print("  -> Tiempo de espera agotado. No se encontraron imágenes en la página.")

def run_scraper(search_term):
    # Crear carpetas de salida
    folder_name = search_term.replace(" ", "_").lower()
    output_folder = os.path.join("data", "raw_images", folder_name) # Mejor guardar en data/raw_images
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
        print(f"Directorio creado: {output_folder}")

    # Configuración de Selenium
    chrome_options = Options()
    # chrome_options.add_argument("--headless") # Descomenta para ejecutar sin interfaz gráfica
    chrome_options.add_argument("--log-level=3")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
    service = Service()
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    try:
        # Construir la URL de búsqueda directamente para mayor fiabilidad
        encoded_search_term = quote_plus(search_term)
        search_url = f"https://arcav1.uniandes.edu.co/artworks?utf8=✓&search={encoded_search_term}"
        
        print(f"Navegando directamente a la página de resultados para: '{search_term}'")
        print(f"URL: {search_url}")
        driver.get(search_url)
        wait = WebDriverWait(driver, 15)
        
        page_number = 1
        while True:
            print(f"\n--- Procesando Página #{page_number} ---")
            
            # Esperar a que la paginación esté visible como señal de que la página ha cargado
            wait.until(EC.visibility_of_element_located((By.CLASS_NAME, "pagination")))
            
            download_images_on_page(driver, wait, output_folder)
            
            # Intentar pasar a la siguiente página
            try:
                # Busca el <li> que contiene el botón 'siguiente', asegurándose de que no esté deshabilitado
                next_button_li = driver.find_element(By.CSS_SELECTOR, "li.next:not(.disabled)")
                next_button_a = next_button_li.find_element(By.TAG_NAME, 'a')
                
                print(f"  Pasando a la página {page_number + 1}...")
                
                # Usar JavaScript click es a menudo más fiable
                driver.execute_script("arguments[0].click();", next_button_a)
                
                # Espera explícita para que el contenido de la nueva página cargue
                time.sleep(2) # Pausa estática para permitir que la página se actualice
                
                page_number += 1
                
            except NoSuchElementException:
                print("\n--- Fin del proceso: Se ha llegado a la última página. ---")
                break

    except Exception as e:
        print(f"\n¡ERROR! Ocurrió un error inesperado: {e}")
        screenshot_path = "debug_screenshot.png"
        driver.save_screenshot(screenshot_path)
        print(f"Se ha guardado una captura de pantalla del error en '{screenshot_path}'.")
    
    finally:
        driver.quit()
        final_count = len(os.listdir(output_folder)) if os.path.exists(output_folder) else 0
        print(f"Navegador cerrado. Total de imágenes descargadas para '{search_term}': {final_count}")


if __name__ == "__main__":
    run_scraper(SEARCH_TERM)