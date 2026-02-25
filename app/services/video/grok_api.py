"""
ARCHIVO: app/services/video/grok_api.py

DESCRIPCIÓN:
Motor de animación con Selenium.
Versión Humanoide Optimizada: Incluye sanitización estricta de saltos de línea
para evitar el bug de los "múltiples Enter" y descarga directa por inyección JS.
"""

import os
import time
import shutil
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from app.utils.logger import get_logger

logger = get_logger("GROK_API")

class GrokVideoGenerator:
    def __init__(self, debug_port=9222):
        self.debug_port = debug_port
        self.output_dir = os.path.abspath("output/final_videos")
        os.makedirs(self.output_dir, exist_ok=True)
        
        self.system_downloads = str(Path.home() / "Downloads")

    def _connect_to_chrome(self):
        chrome_options = Options()
        chrome_options.add_experimental_option("debuggerAddress", f"127.0.0.1:{self.debug_port}")
        return webdriver.Chrome(options=chrome_options)

    def _limpiar_basura_descargas(self):
        """Elimina archivos abortados menores a 1MB antes de empezar."""
        try:
            for f in os.listdir(self.system_downloads):
                if f.endswith('.mp4') or f.endswith('.crdownload'):
                    ruta = os.path.join(self.system_downloads, f)
                    if os.path.exists(ruta) and os.path.getsize(ruta) < 1000000:
                        try: os.remove(ruta)
                        except: pass
        except Exception as e:
            logger.warning(f"   ⚠️ No se pudo limpiar la basura inicial: {e}")

    def animate_image(self, image_path: str, prompt: str, scene_id: str) -> str:
        logger.info(f"🎬 [GROK CDP] Iniciando Animación para Escena {scene_id} (Modo Tiempo Fijo)...")
        
        imagen_absoluta = os.path.abspath(image_path)
        if not os.path.exists(imagen_absoluta):
            logger.error(f"❌ Error: La imagen no existe en la ruta {imagen_absoluta}")
            return None
        
        self._limpiar_basura_descargas()

        driver = None
        try:
            driver = self._connect_to_chrome()
            wait = WebDriverWait(driver, 15)
            
            # 1. HARD RESET
            logger.info("   🧹 Limpiando interfaz...")
            driver.get("https://grok.com/imagine")
            time.sleep(4) 

            # 2. SUBIR IMAGEN
            logger.info(f"   📤 Subiendo imagen de la escena {scene_id}...")
            try:
                file_input = wait.until(EC.presence_of_element_located((By.XPATH, '//input[@type="file"]')))
                file_input.send_keys(imagen_absoluta)
                logger.info("   ⏳ Esperando 8s a que la interfaz procese la imagen...")
                time.sleep(8) 
            except Exception:
                logger.warning("   ⚠️ Input oculto. Intervención manual requerida (15s)...")
                time.sleep(15)
            
            # 3. ESCRIBIR PROMPT (SANITIZADO)
            # 🟢 CORRECCIÓN: Destruir saltos de línea para evitar Enters accidentales
            prompt_limpio = prompt.replace('\n', ' ').replace('\r', ' ').strip()
            prompt_completo = f"Animate this image: {prompt_limpio}, ultra-hyperrealistic, physically accurate fluid dynamics, 4k resolution"
            logger.info(f"   ✍️ Escribiendo prompt...")
            
            input_box = wait.until(EC.presence_of_element_located((By.XPATH, '//*[@contenteditable="true"] | //textarea')))
            
            actions = ActionChains(driver)
            actions.move_to_element(input_box).click().send_keys(prompt_completo).perform()
            time.sleep(1.5)
            
            # 4. ENVIAR (UN SOLO ENTER ESTRICTO)
            logger.info("   🚀 Ejecutando envío mediante 1 solo ENTER...")
            actions = ActionChains(driver)
            actions.send_keys(Keys.ENTER).perform()
            
            # 5. BARRERA DE TIEMPO FIJO
            logger.info("   ⏳ Iniciando cronómetro de renderizado estricto (90 segundos)...")
            time.sleep(90)
            logger.info("   ⏳ Tiempo cumplido. Asumiendo renderizado finalizado.")
            
            # 6. DESCARGA DIRECTA POR INYECCIÓN JS (Bypass de botones)
            logger.info("   📥 Extrayendo URL del video directamente del DOM...")
            ruta_final = os.path.join(os.path.abspath("output/temp_assets"), f"scene_{scene_id}_grok.mp4")
            mp4_files_before = set([f for f in os.listdir(self.system_downloads) if f.endswith('.mp4')])

            try:
                # Inyectamos Javascript para forzar la descarga sin usar botones de la interfaz
                descarga_forzada = driver.execute_script("""
                    let videos = document.querySelectorAll('video');
                    if(videos.length === 0) return false;
                    
                    let lastVideo = videos[videos.length - 1];
                    let src = lastVideo.src || (lastVideo.querySelector('source') ? lastVideo.querySelector('source').src : null);
                    
                    if(src) {
                        let a = document.createElement('a');
                        a.href = src;
                        a.download = 'grok_generated_video.mp4';
                        document.body.appendChild(a);
                        a.click();
                        document.body.removeChild(a);
                        return true;
                    } else {
                        // Fallback: Si no hay src directo, clic en el último botón SVG
                        let container = lastVideo.parentElement.parentElement.parentElement;
                        if (container) {
                            let btns = container.querySelectorAll('button');
                            if(btns.length > 0) {
                                btns[btns.length - 1].click();
                                return true;
                            }
                        }
                    }
                    return false;
                """)

                if not descarga_forzada:
                    logger.error("❌ No se detectó ninguna etiqueta de video para descargar.")
                    return None
                
                download_timeout = 60
                start_time = time.time()
                downloaded_file = None
                
                logger.info(f"   ⏳ Esperando archivo en: {self.system_downloads}...")
                while time.time() - start_time < download_timeout:
                    current_mp4_files = set([f for f in os.listdir(self.system_downloads) if f.endswith('.mp4')])
                    new_files = current_mp4_files - mp4_files_before
                    
                    if new_files:
                        temp_file = list(new_files)[0]
                        candidate_file = os.path.join(self.system_downloads, temp_file)
                        
                        if not any(f.endswith('.crdownload') for f in os.listdir(self.system_downloads)):
                            # Filtro estricto: Mayor a 1 MB
                            if os.path.exists(candidate_file) and os.path.getsize(candidate_file) > 1000000: 
                                downloaded_file = candidate_file
                                break
                            else:
                                if os.path.exists(candidate_file):
                                    logger.warning("   ⚠️ Archivo inválido detectado (< 1MB). Borrando...")
                                    try: os.remove(candidate_file)
                                    except: pass
                    time.sleep(1)

                if downloaded_file:
                    # Estabilizador
                    last_size = -1
                    for _ in range(10):
                        current_size = os.path.getsize(downloaded_file)
                        if current_size == last_size and current_size > 0:
                            break
                        last_size = current_size
                        time.sleep(1)

                    if os.path.exists(ruta_final):
                        os.remove(ruta_final)
                    
                    shutil.move(downloaded_file, ruta_final)
                    
                    tamano_mb = os.path.getsize(ruta_final) / (1024 * 1024)
                    logger.info(f"   ✅ Video movido y guardado exitosamente en temp_assets ({tamano_mb:.2f} MB): {ruta_final}")
                    return ruta_final
                else:
                     logger.error(f"   ❌ Fallo de validación de descarga tras extracción JS.")
                     return None

            except Exception as e:
                logger.error(f"   ❌ Error en anclaje de descarga: {e}")
                return None
                
        except Exception as e:
            logger.error(f"💥 Error crítico en Selenium: {e}")
            return None
        finally:
            if driver:
                driver = None