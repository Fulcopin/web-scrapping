import os
import requests
import time
import re

# --- CONFIGURACIÓN ---
# Debes encontrar estos valores para cada autor que quieras descargar.
# Ejemplo para Beatriz González:
AUTHOR_ID = 784
# Usa un nombre corto y sin espacios para la carpeta.
AUTHOR_NAME_FOLDER = "escuela-quiteña" 

BASE_API_URL = "https://arcav1.uniandes.edu.co/api/artworks"
OUTPUT_FOLDER = os.path.join("raw_images", AUTHOR_NAME_FOLDER)
# --- FIN DE CONFIGURACIÓN ---

def sanitize_filename(filename):
    """
    Limpia un string para que sea un nombre de archivo válido.
    """
    return re.sub(r'[\\/*?:"<>|]', "", filename)

def download_images_from_arca(author_id):
    """
    Descarga todas las imágenes de un autor específico desde la API de ARCA.
    """
    if not os.path.exists(OUTPUT_FOLDER):
        os.makedirs(OUTPUT_FOLDER)
        print(f"Carpeta creada: {OUTPUT_FOLDER}")

    current_page = 1
    total_downloaded = 0

    while True:
        # Construir la URL de la API para la página actual
        api_url = f"{BASE_API_URL}?page={current_page}&author_show={author_id}"
        print(f"\nObteniendo datos de la página {current_page} desde: {api_url}")

        try:
            # Hacemos la petición a la API, simulando ser un navegador
            response = requests.get(api_url, headers={'User-Agent': 'My-Art-Project-Scraper/1.0'})
            response.raise_for_status() # Lanza un error si la petición falla (e.g., 404, 500)
            
            data = response.json()
            artworks = data.get('data', [])

            if not artworks:
                print("No se encontraron más obras. Finalizando.")
                break

            print(f"Se encontraron {len(artworks)} obras en esta página. Empezando descarga...")

            for artwork in artworks:
                artwork_id = artwork.get('id')
                title = artwork.get('title', 'sin-titulo')
                image_info = artwork.get('image')

                if not image_info or 'large' not in image_info:
                    print(f"  -> La obra '{title}' (ID: {artwork_id}) no tiene imagen. Saltando.")
                    continue
                
                # Usamos la imagen 'large' para mejor calidad
                image_url = image_info['large']
                
                # Crear un nombre de archivo limpio y único
                safe_title = sanitize_filename(title)[:50] # Truncamos a 50 chars
                filename = f"{artwork_id}_{safe_title}.jpg"
                filepath = os.path.join(OUTPUT_FOLDER, filename)

                try:
                    # Descargar la imagen
                    image_response = requests.get(image_url, stream=True)
                    image_response.raise_for_status()
                    
                    with open(filepath, 'wb') as f:
                        for chunk in image_response.iter_content(chunk_size=8192):
                            f.write(chunk)
                    
                    print(f"  -> Descargada: {filename}")
                    total_downloaded += 1
                
                except requests.exceptions.RequestException as img_e:
                    print(f"  -> Error descargando la imagen para '{title}': {img_e}")

                # Pausa breve para ser respetuosos con el servidor
                time.sleep(0.5)

            # Comprobar si hemos llegado a la última página
            last_page = data.get('last_page', 1)
            if current_page >= last_page:
                print("\nSe ha alcanzado la última página.")
                break
            
            # Pasar a la siguiente página
            current_page += 1

        except requests.exceptions.RequestException as e:
            print(f"Error al contactar la API: {e}")
            break
        except ValueError: # Se dispara si la respuesta no es un JSON válido
            print("Error: La respuesta del servidor no fue un JSON válido.")
            break

    print(f"\n¡Descarga completada! Total de imágenes guardadas: {total_downloaded}")


if __name__ == "__main__":
    download_images_from_arca(AUTHOR_ID)