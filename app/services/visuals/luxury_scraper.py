import os
import time
import random
import base64
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
        # User Agent de Chrome real (Windows)
        self.user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"

    def fetch_assets(self, scenes: list[Scene]) -> dict:
        assets_map = {}
        
        with sync_playwright() as p:
            logger.info("👀 Abriendo navegador (Modo Ingeniería)...")
            # headless=False para que veas trabajar al robot
            browser = p.chromium.launch(headless=False) 
            
            context = browser.new_context(
                user_agent=self.user_agent,
                viewport={'width': 1280, 'height': 800},
                locale='en-US' # Forzar inglés para resultados más relevantes
            )
            
            for scene in scenes:
                if scene.visual_source == AssetSource.GOOGLE_IMAGES:
                    logger.info(f"🔎 Buscando escena {scene.id}: '{scene.visual_search_term}'")
                    
                    try:
                        image_path = self._scrape_robust(context, scene.visual_search_term, scene.id)
                        
                        if image_path:
                            assets_map[scene.id] = image_path
                            logger.info(f"✅ ÉXITO: Asset {scene.id} guardado en {image_path}")
                        else:
                            logger.error(f"❌ FRACASO: No se pudo conseguir imagen válida para escena {scene.id}")
                    
                    except Exception as e:
                        logger.error(f"💥 Excepción crítica en escena {scene.id}: {e}")
                    
                    time.sleep(1.5) # Respiro para evitar bloqueos
            
            browser.close()
            
        return assets_map

    def _scrape_robust(self, context, query: str, scene_id: int):
        page = context.new_page()
        # Usamos BING Images con filtro de tamaño GRANDE explícito (isz:l) si fuera posible, 
        # pero primero vamos genérico para asegurar resultados.
        search_url = f"https://www.bing.com/images/search?q={query}&first=1"
        
        try:
            page.goto(search_url, timeout=20000)
            
            # Esperar carga inicial
            try:
                page.wait_for_selector('img.mimg', state='visible', timeout=6000)
            except:
                logger.warning("   ⚠️ Timeout esperando selector específico, intentando genérico...")

            # Scroll agresivo para triggerear lazy loading
            page.evaluate("window.scrollTo(0, 1000)")
            time.sleep(2)

            # ESTRATEGIA: Recolectar candidatos
            # Bing usa la clase 'mimg' para los thumbnails del grid.
            images = page.query_selector_all('img.mimg')
            
            if not images:
                # Fallback: intentar cualquier imagen si falla el selector mimg
                images = page.query_selector_all('img')

            logger.info(f"   👁️ Candidatos encontrados: {len(images)}")
            
            # PROCESO DE SELECCIÓN Y DESCARGA
            attempts = 0
            max_attempts = 25 # Intentar con los primeros 25 resultados
            
            for img in images:
                if attempts >= max_attempts:
                    break
                
                attempts += 1
                
                # Prioridad 1: src (URL normal)
                # Prioridad 2: data-src (Lazy load)
                src = img.get_attribute('src') or img.get_attribute('data-src')
                
                if not src:
                    continue

                # ANÁLISIS DEL CANDIDATO
                if src.startswith('http'):
                    # TÉCNICA PRO: Descargar usando el contexto del navegador (JS Fetch)
                    # Esto evita errores 403 Forbidden
                    is_valid = self._download_via_browser(page, src, scene_id)
                    if is_valid: 
                        page.close()
                        return is_valid
                        
                elif src.startswith('data:image'):
                    # TÉCNICA PRO: Limpieza agresiva de Base64
                    is_valid = self._save_base64_robust(src, scene_id)
                    if is_valid:
                        page.close()
                        return is_valid
            
            logger.warning(f"   ⚠️ Se revisaron {attempts} imágenes y ninguna pasó el control de calidad.")

        except Exception as e:
            logger.error(f"   ❌ Error en navegación: {e}")
            if not page.is_closed():
                page.close()
            return None
            
        if not page.is_closed():
            page.close()
        return None

    def _download_via_browser(self, page, url: str, scene_id: int):
        """
        Usa el motor de Chrome para descargar la imagen y devolverla a Python en Base64.
        Bypassea protecciones anti-bot de headers.
        """
        try:
            # Inyectamos JS para fetchear la imagen como blob y convertirla a base64
            # Esto usa las cookies/sesión de la página actual.
            js_script = """
            async (url) => {
                const response = await fetch(url);
                const blob = await response.blob();
                return new Promise((resolve) => {
                    const reader = new FileReader();
                    reader.onloadend = () => resolve(reader.result);
                    reader.readAsDataURL(blob);
                });
            }
            """
            # Ejecutamos el JS
            base64_data = page.evaluate(js_script, url)
            
            # Ahora procesamos ese base64 limpio
            return self._save_base64_robust(base64_data, scene_id, source_url=url)

        except Exception as e:
            # Fallo común: CORS o imagen bloqueda
            # No logueamos error crítico para no ensuciar, solo pasamos al siguiente
            return None

    def _save_base64_robust(self, data_str: str, scene_id: int, source_url="base64_direct"):
        try:
            # 1. Limpieza de cabecera
            if 'base64,' in data_str:
                _, encoded = data_str.split('base64,', 1)
            else:
                encoded = data_str

            # 2. Limpieza de caracteres sucios (Newlines, espacios)
            encoded = encoded.strip().replace('\n', '').replace('\r', '').replace(' ', '+')

            # 3. Corrección de Padding (Matemática pura)
            missing_padding = len(encoded) % 4
            if missing_padding:
                encoded += '=' * (4 - missing_padding)

            # 4. Decodificación
            data = base64.b64decode(encoded)
            img = Image.open(BytesIO(data))
            
            return self._process_and_save(img, scene_id, source_url)
            
        except Exception as e:
            # logger.debug(f"Error decodificando candidato: {e}")
            return None

    def _process_and_save(self, img: Image.Image, scene_id: int, source_type: str):
        width, height = img.size
        
        # FILTRO DE CALIDAD AJUSTADO PARA MVP
        # Aceptamos 150px porque Bing thumbnails a veces reportan tamaños pequeños
        # pero son suficientes para probar el flujo.
        if width < 150 or height < 150:
            # logger.warning(f"   🗑️ Rechazada por pequeña ({width}x{height})")
            return None

        filepath = os.path.join(self.download_path, f"scene_{scene_id}.jpg")
        
        try:
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")
                
            img.save(filepath, "JPEG", quality=95)
            # logger.info(f"   💾 Guardada: {width}x{height} (Fuente: {source_type[:15]}...)")
            return filepath
        except Exception as e:
            logger.error(f"Error guardando archivo: {e}")
            return None