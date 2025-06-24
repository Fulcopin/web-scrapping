import os
import requests
from bs4 import BeautifulSoup
import time
import urllib.parse

# --- CONFIGURACIÓN ---
# Cambia esto para el artista que quieras descargar
ARTIST_NAME = "fernando-botero" 
BASE_URL = f"https://www.wikiart.org/en/{ARTIST_NAME}/all-works/text-list"
OUTPUT_FOLDER = os.path.join("raw_images", "botero")

# --- FIN DE CONFIGURACIÓN ---

def download_images_from_wikiart():
    """
    Descarga todas las imágenes de un artista desde WikiArt.
    """
    if not os.path.exists(OUTPUT_FOLDER):
        os.makedirs(OUTPUT_FOLDER)
        print(f"Carpeta creada: {OUTPUT_FOLDER}")

    print(f"Obteniendo lista de obras desde: {BASE_URL}")
    
    try:
        response = requests.get(BASE_URL, headers={'User-Agent': 'My-Cool-Scraper/1.0'})
        response.raise_for_status() # Lanza un error si la petición falla
    except requests.exceptions.RequestException as e:
        print(f"Error al acceder a la página principal: {e}")
        return

    soup = BeautifulSoup(response.content, 'html.parser')
    
    # Encontrar la lista de pinturas. La estructura de la web puede cambiar.
    # Inspecciona la web con las herramientas de desarrollador de tu navegador.
    painting_links = soup.select('ul.painting-list-text a')
    
    if not painting_links:
        print("No se encontraron enlaces de pinturas. La estructura de la web pudo haber cambiado.")
        return

    print(f"Se encontraron {len(painting_links)} obras. Empezando la descarga...")

    for i, link in enumerate(painting_links):
        painting_page_url = "https://www.wikiart.org" + link['href']
        
        try:
            # Pequeña pausa para no sobrecargar el servidor
            time.sleep(1) 
            
            print(f"[{i+1}/{len(painting_links)}] Accediendo a la página de la obra: {link.text.strip()}")
            painting_page_response = requests.get(painting_page_url, headers={'User-Agent': 'My-Cool-Scraper/1.0'})
            painting_page_response.raise_for_status()
            
            painting_soup = BeautifulSoup(painting_page_response.content, 'html.parser')
            
            # Encontrar la URL de la imagen en alta resolución
            image_tag = painting_soup.select_one('div.wiki-layout-artist-image-wrapper img')
            
            if not image_tag or not image_tag.has_attr('src'):
                print(f"  -> No se encontró la etiqueta de imagen para '{link.text.strip()}'. Saltando.")
                continue

            image_url = image_tag['src']
            
            # Limpiar el nombre del archivo
            filename = f"{i+1:03d}_{urllib.parse.quote_plus(link.text.strip().replace(' ', '_'))}.jpg"
            filepath = os.path.join(OUTPUT_FOLDER, filename)

            # Descargar la imagen
            image_response = requests.get(image_url, stream=True)
            image_response.raise_for_status()
            
            with open(filepath, 'wb') as f:
                for chunk in image_response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            print(f"  -> Descargada y guardada como: {filename}")

        except requests.exceptions.RequestException as e:
            print(f"  -> Error descargando la obra '{link.text.strip()}': {e}")
        except Exception as e:
            print(f"  -> Ocurrió un error inesperado: {e}")

    print("\n¡Descarga completada!")


if __name__ == "__main__":
    download_images_from_wikiart()