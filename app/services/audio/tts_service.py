import os
import asyncio
import edge_tts
import re  # <--- IMPORTANTE: Necesario para limpiar el texto
from app.domain.models import Scene
from app.utils.logger import get_logger

logger = get_logger(__name__)

class TTSService:
    def __init__(self, download_path="output/temp_audio"):
        self.download_path = download_path
        os.makedirs(download_path, exist_ok=True)
        # Voces recomendadas para inglés (calidad documental):
        # en-US-ChristopherNeural (Masculina, profunda)
        # en-US-RogerNeural (Masculina, seria)
        # en-US-AriaNeural (Femenina, profesional)
        self.voice = "en-US-ChristopherNeural"

    async def generate_audio(self, text: str, scene_id: int) -> str:
        try:
            # --- LIMPIEZA AGRESIVA (NUEVO) ---
            # 1. Elimina todo lo que esté entre corchetes: [SFX...], [Music...], [Action...]
            clean_text = re.sub(r'\[.*?\]', '', text)
            
            # 2. Elimina todo lo que esté entre paréntesis (por si acaso): (whispering), (pause)
            clean_text = re.sub(r'\(.*?\)', '', clean_text)
            
            # 3. Elimina espacios dobles que quedan al borrar
            clean_text = re.sub(r'\s+', ' ', clean_text).strip()
            # ---------------------------------

            if not clean_text:
                logger.warning(f"⚠️ La escena {scene_id} quedó vacía tras limpiar.")
                return None

            # Usamos self.voice que viene configurada desde el main
            communicate = edge_tts.Communicate(clean_text, self.voice, rate="+15%")
            
            filename = f"audio_scene_{scene_id}.mp3"
            filepath = os.path.join(self.download_path, filename)
            
            await communicate.save(filepath)
            
            logger.info(f"   🔊 Audio Escena {scene_id} generado (Limpio)")
            return filepath
        except Exception as e:
            logger.error(f"❌ Error generando audio escena {scene_id}: {e}")
            return None

def run_tts_sync(tts_service: TTSService, scenes: list) -> dict:
    """Helper para correr la función asíncrona desde el main síncrono"""
    audio_map = {}
    
    # Parche para Windows (Loop de eventos)
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    for scene in scenes:
        if scene.narration:
            # Usamos el loop existente para ejecutar la tarea
            path = loop.run_until_complete(tts_service.generate_audio(scene.narration, scene.id))
            if path:
                audio_map[scene.id] = path
                
    return audio_map