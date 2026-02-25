import os
import PIL.Image

# --- 🔴 PARCHE CRÍTICO PARA PILLOW 10+ ---
# Esto evita que MoviePy falle con versiones nuevas de librerías de imagen
if not hasattr(PIL.Image, 'ANTIALIAS'):
    PIL.Image.ANTIALIAS = PIL.Image.LANCZOS
# -----------------------------------------

# 🟢 IMPORTAMOS concatenate_videoclips PARA UNIR SUB-FRAGMENTOS
from moviepy.editor import ImageClip, VideoFileClip, AudioFileClip, concatenate_videoclips
from app.utils.logger import get_logger

logger = get_logger(__name__)

class TimelineBuilder:
    def __init__(self, resolution=(1920, 1080), draft_mode=False):
        """
        Inicializa el constructor con la resolución objetivo y el modo.
        resolution: Tupla (ancho, alto). Ej: (1080, 1920) para Shorts.
        draft_mode: Si es True, desactiva efectos pesados para render rápido.
        """
        self.width, self.height = resolution
        self.draft_mode = draft_mode  # 🟢 NUEVO: Guardamos el estado
        self.aspect_ratio = self.width / self.height
        
        mode_str = "⚡ DRAFT (Rápido/Estático)" if draft_mode else "🐢 PRO (Audio-Driven/Dinámico)"
        logger.info(f"🎞️ TimelineBuilder calibrado a: {self.width}x{self.height} | Modo: {mode_str}")

    def build_visual_clips(self, script, assets_map, audio_map):
        """
        [MÉTODO PRINCIPAL]
        Itera sobre el guion y convierte cada escena en un VideoClip.
        """
        visual_clips = []
        logger.info(f"🔨 Construyendo línea de tiempo para {len(script.scenes)} escenas...")

        for scene in script.scenes:
            # 1. Recuperar rutas de archivos (AHORA ES UNA LISTA DE FRAGMENTOS)
            asset_paths = assets_map.get(scene.id)
            audio_path = audio_map.get(scene.id)
            
            # 2. Construir la escena individual (Pasamos el objeto scene completo)
            clip = self._process_single_scene(asset_paths, audio_path, scene)
            
            if clip:
                visual_clips.append(clip)
            else:
                logger.error(f"❌ Escena {scene.id} descartada por falta de assets.")

        return visual_clips

    def _process_single_scene(self, asset_paths, audio_path, scene):
        """
        [LÓGICA INTERNA]
        Crea un clip: Ensambla sub-fragmentos + Recorte Milimétrico + Crop Inteligente + Audio.
        """
        # A. Validación básica (Ahora validamos una lista)
        if not asset_paths or not isinstance(asset_paths, list) or len(asset_paths) == 0:
            logger.warning(f"⚠️ Faltaron assets para Escena {scene.id}. Saltando.")
            return None

        try:
            # B. Gestión del Audio + Pausa ASMR (EL RELOJ MAESTRO)
            if audio_path and os.path.exists(audio_path):
                audio_clip = AudioFileClip(audio_path)
                # 🟢 Tiempo exacto dictado por el Audio + el silencio ordenado por Gemini
                target_duration = audio_clip.duration + scene.asmr_pause
            else:
                logger.warning(f"⚠️ Audio faltante en Escena {scene.id}. Usando default + ASMR.")
                audio_clip = None
                target_duration = 5.0 + scene.asmr_pause

            # C. Crear Clip Base (El Pegamento Digital)
            clips_to_concat = []
            is_video = False

            # Identificamos y pre-cargamos todos los sub-fragmentos de esta escena
            for path in asset_paths:
                if path.lower().endswith(('.mp4', '.mov', '.avi')):
                    is_video = True
                    clips_to_concat.append(VideoFileClip(path))
                else:
                    # Si es una foto (modo draft), la estiramos al tiempo objetivo
                    clips_to_concat.append(ImageClip(path).set_duration(target_duration))

            # Unimos las piezas si hay más de una (Sub-encadenamiento)
            if len(clips_to_concat) > 1:
                base_clip = concatenate_videoclips(clips_to_concat, method="compose")
            else:
                base_clip = clips_to_concat[0]

            # 🟢 EL TIJERETAZO MILIMÉTRICO (Corte exacto, cero loops)
            if base_clip.duration > target_duration:
                base_clip = base_clip.subclip(0, target_duration)

            # D. LÓGICA DE RECORTE INTELIGENTE (SMART CROP)
            # Esto asegura que la imagen/video llene la pantalla sin bandas negras
            img_w, img_h = base_clip.size
            img_ratio = img_w / img_h
            
            if img_ratio > self.aspect_ratio:
                # IMAGEN MÁS ANCHA QUE LA PANTALLA (Landscape en pantalla Portrait)
                new_height = self.height
                new_width = int(new_height * img_ratio)
                base_clip = base_clip.resize(height=new_height)
                
                # Cortamos el exceso de los lados (Centrado)
                x_center = new_width // 2
                base_clip = base_clip.crop(
                    x1=x_center - self.width//2, 
                    y1=0,
                    width=self.width, 
                    height=self.height
                )
            else:
                # IMAGEN MÁS ALTA QUE LA PANTALLA (Portrait en pantalla Landscape o Cuadrada)
                new_width = self.width
                new_height = int(new_width / img_ratio)
                base_clip = base_clip.resize(width=new_width)
                
                # Cortamos el exceso de arriba/abajo (Centrado)
                y_center = new_height // 2
                base_clip = base_clip.crop(
                    x1=0, 
                    y1=y_center - self.height//2, 
                    width=self.width, 
                    height=self.height
                )

            # E. EFECTO KEN BURNS (CONDICIONAL)
            # Solo aplicamos zoom a imágenes estáticas que no estén en modo borrador
            if not self.draft_mode and not is_video:
                base_clip = base_clip.resize(lambda t: 1 + 0.04 * (t / target_duration))
            
            # Siempre centramos para asegurar (especialmente tras el crop)
            base_clip = base_clip.set_position(("center", "center"))

            # F. Integrar Audio
            if audio_clip:
                base_clip = base_clip.set_audio(audio_clip)

            return base_clip

        except Exception as e:
            logger.error(f"❌ Error crítico procesando Escena {scene.id}: {e}")
            import traceback
            traceback.print_exc()
            return None