"""
ARCHIVO: app/utils/frame_extractor.py

DESCRIPCIÓN Y FUNCIONALIDAD:
Toma un archivo de video renderizado (.mp4) y extrae su último fotograma (frame) exacto.
Este fotograma se utilizará como imagen base para la siguiente escena, garantizando 
continuidad espacial y visual estricta (Visual Chaining).
"""

import os
from moviepy.editor import VideoFileClip
from app.utils.logger import get_logger

logger = get_logger("FRAME_EXTRACTOR")

class FrameExtractor:
    
    @staticmethod
    def extract_last_frame(video_path: str, output_image_path: str) -> str:
        """
        Abre el video, busca el último segundo, extrae el frame y lo guarda como PNG.
        Devuelve la ruta de la imagen generada.
        """
        if not os.path.exists(video_path):
            logger.error(f"❌ Error: El video {video_path} no existe.")
            return None
            
        try:
            logger.info(f"🎞️ Extrayendo último frame de {os.path.basename(video_path)}...")
            with VideoFileClip(video_path) as clip:
                # Extraemos el frame en el instante final (restando 0.1s para evitar pantalla negra de fin de clip)
                tiempo_final = max(0, clip.duration - 0.1)
                clip.save_frame(output_image_path, t=tiempo_final)
                
            logger.info(f"   ✅ Frame extraído y guardado en: {output_image_path}")
            return output_image_path
            
        except Exception as e:
            logger.error(f"❌ Error extrayendo frame: {e}")
            return None