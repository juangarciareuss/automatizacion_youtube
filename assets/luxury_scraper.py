import os
import time
import requests
from playwright.sync_api import sync_playwright
from PIL import Image
from io import BytesIO
from app.domain.models import Scene, AssetSource
from app.utils.logger import get_logger

logger = get_logger(__name__)

class LuxuryScraper:
    def __init__(self, download_path="output/temp"):
        self.download_path = download_path
        os.makedirs(download_path, exist_ok=True)
        # User Agent para parecer un navegador Chrome real de Windows
        self.user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

    def fetch_assets(self, scenes: list[Scene]) -> dict:
        """
        Recibe una lista de Escenas, busca las imágenes visuales necesarias 
        y retorna un diccionario {scene_id: path_to_image}.
        """
        assets_map = {}
        
        with sync_playwright() as p:
            # Lanzamos el navegador en modo HEADLESS (Invisible/Servidor)
            browser = p.chromium.launch(headless=True) 
            context = browser.new_context(user_agent=self.user_agent)
            
            for scene in scenes:
                # Solo activamos si la fuente es Scraper (Google Images)
                if scene.visual_source == AssetSource.GOOGLE_IMAGES:
                    logger.info(f"🤖 Robot buscando assets para: '{scene.visual_search_term}'")
                    
                    image_path = self._scrape_google_image(context, scene.visual_search_term, scene.id)
                    
                    if image_path:
                        assets_map[scene.id] = image_path
                    else:
                        logger.warning(f"⚠️ No se encontró imagen para escena {scene.id}. Usando placeholder.")
                        # Aquí podrías poner una lógica de fallback (ej. color negro)
            
            browser.close()
            
        return assets_map

    def _scrape_google_image(self, context, query: str, scene_id: int):
        """Lógica dura del robot para extraer la imagen HD."""
        page = context.new_page()
        
        # Búsqueda en DuckDuckGo Images (Más amigable con bots que Google directo)
        # O Google Images con parámetros safe search desactivados
        search_url = f"https://www.google.com/search?q={query}&tbm=isch&tbs=isz:l" # isz:l fuerza imágenes GRANDES
        
        try:
            page.goto(search_url)
            page.wait_for_load_state("networkidle")

            # Click en la primera imagen para que cargue la versión HD en el panel lateral
            # (Selectores CSS pueden cambiar, esto requiere mantenimiento en una granja real)
            # Estrategia robusta: Tomar la primera imagen que sea > 600px de ancho
            
            # Simulamos scroll para cargar
            page.evaluate("window.scrollTo(0, 1000)")
            time.sleep(1) # Pequeña espera técnica

            # Extraemos URLs de imágenes candidatas
            # Este selector busca etiquetas img que tengan src http
            images = page.query_selector_all("img")
            
            best_url = None
            for img in images:
                src = img.get_attribute("src") or img.get_attribute("data-src")
                if src and "http" in src and "encrypt" not in src: # Evitar thumbnails encriptados pequeños
                    # En un sistema real, aquí verificaríamos el tamaño real antes de descargar
                    best_url = src
                    break
            
            if best_url:
                return self._download_and_verify(best_url, scene_id)
                
        except Exception as e:
            logger.error(f"❌ Error scraping {query}: {e}")
            return None
        finally:
            page.close()

    def _download_and_verify(self, url: str, scene_id: int):
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                img = Image.open(BytesIO(response.content))
                width, height = img.size
                
                # REGLA DE CALIDAD: Si es muy chica, es basura.
                if width < 800 or height < 600:
                    logger.warning(f"⚠️ Imagen rechazada por baja resolución: {width}x{height}")
                    return None
                
                # Guardar
                ext = img.format.lower()
                filename = f"scene_{scene_id}.{ext}"
                filepath = os.path.join(self.download_path, filename)
                
                # Convertir a RGB si es necesario (evita errores con PNGs transparentes en MoviePy)
                if img.mode in ("RGBA", "P"):
                    img = img.convert("RGB")
                    filepath = os.path.join(self.download_path, f"scene_{scene_id}.jpg")
                    img.save(filepath, "JPEG", quality=95)
                else:
                    img.save(filepath)
                
                return filepath
        except Exception as e:
            logger.error(f"Error descargando imagen: {e}")
            return None