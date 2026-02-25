import os
import time
import json
from google import genai
from google.genai import types
# 🟢 CAMBIO: Importamos VideoScript y los nuevos modelos
from app.domain.models import VideoScript, VideoOrientation, VideoScene, VisualBible
from app.utils.logger import get_logger

# Importamos los prompts
from app.services.brain.prompts.chef_prompt_long import MASTER_CHEF_LONG
from app.services.brain.prompts.chef_prompt_short import MASTER_CHEF_SHORT

logger = get_logger(__name__)

class GeminiService:
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("❌ GEMINI_API_KEY no encontrada en .env")
            
        self.client = genai.Client(api_key=self.api_key)
        
        # Leemos el modelo del .env (Tu Gemini 3 Preview o Flash)
        self.model_name = os.getenv("GEMINI_MODEL_NAME", "gemini-2.0-flash")
        
        logger.info(f"🧠 Cerebro inicializado con modelo: {self.model_name}")

    def _get_prompt_by_orientation(self, topic: str, orientation: VideoOrientation) -> str:
        """Selecciona el prompt adecuado según si es Short o Long."""
        if orientation == VideoOrientation.LANDSCAPE:
            logger.info("📜 Seleccionando Prompt: DOCUMENTAL CIENTÍFICO (Long Form)")
            return MASTER_CHEF_LONG.replace("{{topic}}", topic)
        else:
            logger.info("⚡ Seleccionando Prompt: VIRAL SHORT (TikTok Style)")
            return MASTER_CHEF_SHORT.replace("{{topic}}", topic)

    def generate_script(self, topic: str, orientation: VideoOrientation = VideoOrientation.LANDSCAPE) -> VideoScript:
        """
        Genera el guion con sistema de REINTENTOS y soporte para Biblia Visual.
        """
        logger.info(f"🤖 Procesando tema: '{topic}' ({orientation.name})")

        # 1. Obtener Prompt Correcto
        final_prompt = self._get_prompt_by_orientation(topic, orientation)

        # 2. BUCLE DE REINTENTOS (Solución error 503)
        max_retries = 5
        
        for attempt in range(max_retries):
            try:
                # Intentamos llamar a la API
                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=final_prompt,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        # 🟢 CAMBIO: Pasamos VideoScript que incluye VisualBible
                        response_schema=VideoScript,
                        temperature=0.7, 
                    )
                )

                # Si llegamos aquí, ¡éxito!
                if response.parsed:
                    script = response.parsed
                    # Forzamos la orientación en el objeto final por seguridad
                    script.orientation = orientation
                    logger.info(f"✅ Guion generado exitosamente: '{script.title}' ({len(script.scenes)} escenas)")
                    # 🟢 CORRECCIÓN: Leemos el inventario de utensilios, no el hero_object
                    logger.info(f"   📚 Biblia Visual (Inventario): {script.visual_bible.prop_inventory}")
                    return script
                else:
                    # Intento de parseo manual si falla el automático
                    logger.warning("⚠️ Respuesta sin parsear automáticamente, intentando manual...")
                    # Limpieza básica de JSON markdown
                    text = response.text.replace("```json", "").replace("```", "")
                    return VideoScript.model_validate_json(text)

            except Exception as e:
                error_msg = str(e)
                
                # Detectamos si es un error de "Servidor Ocupado"
                if "503" in error_msg or "overloaded" in error_msg.lower() or "429" in error_msg:
                    wait_time = (2 ** attempt) + 2  # Espera exponencial: 3s, 4s, 6s...
                    logger.warning(f"🚦 Google está saturado (503). Reintentando en {wait_time}s... (Intento {attempt+1}/{max_retries})")
                    time.sleep(wait_time)
                else:
                    # Error crítico (ej: API Key mala, o error de validación de Pydantic)
                    logger.error(f"❌ Error crítico en Gemini: {e}")
                    raise e
        
        # Si fallamos 5 veces seguidas
        logger.error("💀 Se agotaron los reintentos. Google está demasiado ocupado.")
        raise RuntimeError("Gemini Unavailable after retries")