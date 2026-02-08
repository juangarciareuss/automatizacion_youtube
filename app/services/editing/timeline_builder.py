import os
from moviepy.editor import ImageClip, CompositeVideoClip, AudioFileClip, TextClip
from app.services.editing.effects import VisualEffects
from app.utils.logger import get_logger

logger = get_logger(__name__)

class TimelineBuilder:
    def __init__(self, width=1080, height=1920):
        self.width = width
        self.height = height
        # Inicializamos el especialista en efectos visuales
        self.fx = VisualEffects(width=width, height=height)

    def build_scene_clip(self, img_path, audio_path, subtitle_service=None, theme=None):
        """
        Construye un clip de video completo para una escena individual:
        Imagen + Audio + Efecto Ken Burns + Subtítulos (opcional).
        """
        try:
            # 1. Preparar Audio
            if not os.path.exists(audio_path):
                logger.error(f"❌ Audio no encontrado: {audio_path}")
                return None

            audio_clip = AudioFileClip(audio_path)
            # Añadimos un pequeño padding de 0.2s para suavizar cortes
            duration = audio_clip.duration + 0.2

            # 2. Preparar Imagen Base
            if not os.path.exists(img_path):
                logger.error(f"❌ Imagen no encontrada: {img_path}")
                return None

            image_clip = ImageClip(img_path).set_duration(duration)

            # 3. Aplicar Efectos Visuales (Resize + Ken Burns)
            # Ajustamos la imagen para llenar la pantalla (crop to fill)
            image_clip = self.fx.resize_to_fill(image_clip)
            # Aplicamos el movimiento suave (zoom lento)
            image_clip = self.fx.apply_ken_burns(image_clip)
            
            # Sincronizamos imagen con audio
            video_clip = image_clip.set_audio(audio_clip)

            # 4. Gestión de Capas (Video Base + Subtítulos)
            layers = [video_clip]

            # Si hay servicio de subtítulos y tema configurado, los generamos
            if subtitle_service and theme:
                subtitle_clips = self._create_subtitle_clips(subtitle_service, audio_path, theme)
                if subtitle_clips:
                    layers.extend(subtitle_clips)

            # 5. Composición Final de la Escena
            final_scene = CompositeVideoClip(layers, size=(self.width, self.height)).set_duration(duration)
            
            # Aplicamos Crossfade (fundido) para que la unión con la siguiente escena sea suave
            final_scene = self.fx.apply_crossfade(final_scene)

            return final_scene

        except Exception as e:
            logger.error(f"❌ Error construyendo escena (Visual): {e}")
            return None

    def _create_subtitle_clips(self, service, audio_path, theme):
        """Genera los clips de texto para los subtítulos usando el servicio de transcripción."""
        clips = []
        try:
            # Transcribimos el audio localmente
            segments = service.transcribe(audio_path)
            
            for seg in segments:
                # Creamos el clip de texto
                txt_clip = TextClip(
                    txt=seg['text'],
                    font=theme["font"], 
                    fontsize=theme["fontsize"],
                    color=theme["color"], 
                    stroke_color=theme["stroke_color"],
                    stroke_width=theme["stroke_width"], 
                    method='caption', 
                    size=(self.width * 0.8, None) # Ancho máximo del 80% de la pantalla
                ).set_start(seg['start']).set_duration(seg['end'] - seg['start']).set_position(theme["position"])
                
                clips.append(txt_clip)
                
            return clips
        except Exception as e:
            logger.warning(f"⚠️ Fallo generando subtítulos: {e}")
            return []