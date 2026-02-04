import whisper
import os
from app.utils.logger import get_logger

logger = get_logger(__name__)

class SubtitleService:
    def __init__(self, model_size="base"):
        """
        model_size: 'tiny', 'base', 'small', 'medium', 'large'.
        'base' es el equilibrio perfecto entre velocidad y precisión para español.
        """
        logger.info(f"👂 Cargando modelo Whisper ({model_size})... (Esto puede tardar la primera vez)")
        try:
            # Whisper descarga el modelo automáticamente si no existe
            self.model = whisper.load_model(model_size)
            logger.info("✅ Oído Biónico (Whisper) listo.")
        except Exception as e:
            logger.error(f"❌ Error cargando Whisper. ¿Instalaste ffmpeg? {e}")
            raise e

    def transcribe(self, audio_path: str):
        """
        Genera los subtítulos con tiempos exactos.
        Retorna una lista de segmentos: [{'start': 0.5, 'end': 2.0, 'text': 'Hola'}, ...]
        """
        if not os.path.exists(audio_path):
            logger.error(f"❌ No encuentro el audio: {audio_path}")
            return []

        logger.info(f"🎙️ Transcribiendo audio: {audio_path}...")
        
        # Transcripción mágica
        # fp16=False es necesario si no tienes una GPU NVIDIA de última generación, 
        # evita errores en CPUs normales.
        result = self.model.transcribe(audio_path, fp16=False)
        
        segments = result["segments"]
        
        logger.info(f"✅ Transcripción completada: {len(segments)} líneas detectadas.")
        
        # Limpieza básica de datos para facilitar el uso
        clean_segments = []
        for s in segments:
            clean_segments.append({
                "start": s["start"],
                "end": s["end"],
                "text": s["text"].strip()
            })
            
        return clean_segments