import os
import time
from playwright.sync_api import sync_playwright
from app.utils.logger import get_logger
from app.services.video_automator.grok.config import GrokConfig

logger = get_logger("GROK_BOT")

class GrokAutomator:
    def __init__(self):
        # Cargar todas las sesiones disponibles en data/sessions
        if not os.path.exists(GrokConfig.SESSIONS_DIR):
            os.makedirs(GrokConfig.SESSIONS_DIR)
            
        self.sessions = [
            os.path.join(GrokConfig.SESSIONS_DIR, f) 
            for f in os.listdir(GrokConfig.SESSIONS_DIR) 
            if f.endswith(".json")
        ]
        self.current_index = 0
        os.makedirs(GrokConfig.DOWNLOAD_DIR, exist_ok=True)

    def _get_next_session(self):
        """Rotación circular de cuentas para evitar límites."""
        if not self.sessions: return None
        session = self.sessions[self.current_index]
        self.current_index = (self.current_index + 1) % len(self.sessions)
        return session

    def animate(self, image_path, prompt, scene_id):
        """Intenta generar video probando cuentas si fallan."""
        if not self.sessions:
            logger.error("❌ No hay sesiones de Grok configuradas. Ejecuta auth.py primero.")
            return None

        # Intentamos con cada cuenta disponible antes de rendirnos
        for _ in range(len(self.sessions)):
            session_path = self._get_next_session()
            account_name = os.path.basename(session_path)
            
            logger.info(f"🤖 Grok: Intentando animación con cuenta '{account_name}'...")
            
            video_path = self._run_browser_task(session_path, image_path, prompt, scene_id)
            
            if video_path:
                return video_path # Éxito
            
            logger.warning(f"⚠️ Cuenta '{account_name}' falló. Rotando a la siguiente...")
            time.sleep(2) 

        logger.error("💀 Todas las cuentas de Grok fallaron.")
        return None

    def _run_browser_task(self, session_path, image_path, prompt, scene_id):
        """Lógica interna de Playwright."""
        video_path = None
        
        with sync_playwright() as p:
            try:
                # headless=False para debug inicial (luego cambiar a True)
                browser = p.chromium.launch(headless=False, slow_mo=50) 
                context = browser.new_context(storage_state=session_path)
                page = context.new_page()

                # 1. Navegar a Grok
                logger.info("   🌍 Entrando a Grok...")
                page.goto(GrokConfig.URL_HOME)
                page.wait_for_load_state("networkidle")

                # 2. Subir Imagen
                logger.info("   📤 Subiendo imagen...")
                try:
                    # Intento A: Clic en botón
                    with page.expect_file_chooser(timeout=3000) as fc_info:
                        page.click(GrokConfig.SELECTOR_UPLOAD_BTN)
                    file_chooser = fc_info.value
                    file_chooser.set_files(image_path)
                except:
                    # Intento B: Inyección directa al input (Más robusto)
                    logger.debug("   Botón no encontrado, inyectando en input oculto...")
                    page.set_input_files(GrokConfig.SELECTOR_FILE_INPUT, image_path)

                time.sleep(3) # Esperar preview de imagen

                # 3. Prompt
                logger.info("   ✍️ Enviando prompt...")
                page.fill(GrokConfig.SELECTOR_TEXT_AREA, f"Animate this image: {prompt}")
                page.click(GrokConfig.SELECTOR_SEND_BTN)
                
                # 4. Esperar Video
                logger.info("   ⏳ Esperando renderizado (aprox 60s)...")
                # Esperamos a que aparezca un elemento <video>
                video_element = page.wait_for_selector(
                    GrokConfig.SELECTOR_VIDEO_RESULT, 
                    timeout=GrokConfig.TIMEOUT_GENERATION * 1000
                )

                if not video_element:
                    raise Exception("Timeout esperando video.")

                # 5. Descargar
                # Obtenemos la URL del video del elemento <video src="...">
                video_url = video_element.get_attribute("src")
                
                if not video_url:
                     raise Exception("Video generado pero sin URL (posible blob).")

                logger.info(f"   🔗 Video encontrado. Descargando...")
                
                # Descargar usando requests del navegador (hereda cookies)
                response = page.request.get(video_url)
                filename = f"grok_{scene_id}_{int(time.time())}.mp4"
                final_path = os.path.join(GrokConfig.DOWNLOAD_DIR, filename)

                with open(final_path, "wb") as f:
                    f.write(response.body())

                video_path = final_path
                logger.info(f"   ✅ Video guardado: {final_path}")

            except Exception as e:
                logger.error(f"   ❌ Error navegador: {e}")
                # page.screenshot(path=f"debug_error_scene_{scene_id}.png")

            finally:
                browser.close()
        
        return video_path