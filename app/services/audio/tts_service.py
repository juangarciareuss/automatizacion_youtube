import os
import asyncio
import edge_tts
from app.domain.models import Scene
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
def run_tts_sync(service: TTSService, scenes: list[Scene]) -> dict:
    """
    Ejecuta la generación de audio en un bucle de eventos (Sync -> Async).
    Retorna un diccionario {scene_id: audio_path}
    """
    audio_map = {}
    
    async def _process_batch():
        tasks = []
        for scene in scenes:
            # --- CORRECCIÓN AQUÍ: Usamos narrative_text ---
            if scene.narrative_text: 
                filename = f"scene_{scene.id}.mp3"
                # Creamos la tarea asíncrona
                task = service.generate_audio(scene.narrative_text, filename)
                tasks.append((scene.id, task))
        
        # Ejecutamos todas las tareas en paralelo
        results = await asyncio.gather(*[t[1] for t in tasks])
        
        # Mapeamos resultados
        for i, path in enumerate(results):
            scene_id = tasks[i][0]
            if path:
                audio_map[scene_id] = path
                logger.info(f"✅ Audio generado: Escena {scene_id}")

    try:
        # Truco para correr Async dentro de Sync en scripts
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
        loop.run_until_complete(_process_batch())
        return audio_map

    except Exception as e:
        logger.error(f"❌ Fallo crítico en TTS Batch: {e}")
        return None