import os
import sys
import asyncio
import edge_tts
from typing import List, Dict
# 🟢 CAMBIO: Importamos VideoScene en lugar de Scene
from app.domain.models import VideoScene
from app.utils.logger import get_logger

logger = get_logger(__name__)

class TTSService:
    def __init__(self, download_path: str = "output/temp_audio"):
        self.download_path = download_path
        os.makedirs(self.download_path, exist_ok=True)
        
        # Voz por defecto (rápida y clara para Shorts)
        self.voice = "en-US-ChristopherNeural" 

    async def generate_audio(self, text: str, filename: str) -> str:
        """Genera un archivo de audio MP3 usando Edge TTS."""
        try:
            communicate = edge_tts.Communicate(text, self.voice)
            file_path = os.path.join(self.download_path, filename)
            
            await communicate.save(file_path)
            return file_path
        except Exception as e:
            logger.error(f"❌ Error generando TTS: {e}")
            return None

# --- WRAPPER SÍNCRONO PARA USAR EN MAIN.PY ---
def run_tts_sync(service: TTSService, scenes: List[VideoScene]) -> Dict[int, str]:
    """
    Ejecuta la generación de audio en un bucle de eventos (Sync -> Async).
    Retorna un diccionario {scene_id: audio_path}
    """
    # 🟢 FIX CRÍTICO PARA WINDOWS (PRESERVADO):
    # aiohttp/aiodns requieren SelectorEventLoop, pero Windows usa Proactor por defecto.
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    audio_map = {}
    
    async def _process_batch():
        tasks = []
        for scene in scenes:
            if scene.narrative_text: 
                filename = f"audio_scene_{scene.id}.mp3"
                # Creamos la tarea asíncrona
                task = service.generate_audio(scene.narrative_text, filename)
                tasks.append((scene.id, task))
        
        if not tasks:
            logger.warning("⚠️ No hay escenas con texto para narrar.")
            return []

        # Ejecutamos todas las tareas en paralelo
        logger.info(f"🎙️ Iniciando síntesis paralela para {len(tasks)} escenas...")
        results = await asyncio.gather(*[t[1] for t in tasks])
        
        # Mapeamos resultados
        for i, path in enumerate(results):
            scene_id = tasks[i][0]
            if path:
                audio_map[scene_id] = path
                logger.info(f"   ✅ Audio generado: Escena {scene_id}")
            else:
                logger.error(f"   ❌ Falló audio: Escena {scene_id}")

    try:
        # Gestión robusta del Event Loop
        try:
            loop = asyncio.get_event_loop()
            if loop.is_closed():
                raise RuntimeError("Loop closed")
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
        loop.run_until_complete(_process_batch())
        return audio_map

    except Exception as e:
        logger.error(f"❌ Fallo crítico en TTS Batch: {e}")
        return {}