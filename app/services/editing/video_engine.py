import os
import gc
import sys

# --- CONFIGURACIÓN CRÍTICA PARA WINDOWS (IMAGEMAGICK) ---
# Ajusta esta ruta si tu instalación de ImageMagick está en otro lado
os.environ["IMAGEMAGICK_BINARY"] = r"C:\Program Files\ImageMagick-7.1.2-Q16-HDRI\magick.exe"

# Parches para compatibilidad de librerías antiguas
import PIL.Image
if not hasattr(PIL.Image, 'ANTIALIAS'):
    PIL.Image.ANTIALIAS = PIL.Image.LANCZOS

import asyncio
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
# --------------------------------------------------------

from moviepy.editor import concatenate_videoclips
from app.utils.logger import get_logger
from app.config.themes import ThemeConfig
from app.domain.channel_config import ChannelConfig

# --- LOS TRES ESPECIALISTAS ---
from app.services.editing.timeline_builder import TimelineBuilder
from app.services.editing.audio_engineer import AudioEngineer
from app.services.editing.branding_manager import BrandingManager

logger = get_logger(__name__)

class VideoEngine:
    def __init__(self, config: ChannelConfig, output_path="output/final_videos"):
        self.config = config
        self.output_path = output_path
        os.makedirs(output_path, exist_ok=True)
        
        # Dimensiones estándar (Vertical Short o Horizontal Video se definen en el recorte final)
        # Por ahora trabajamos en HD Vertical safe zone o Full HD
        self.width = 1080
        self.height = 1920
        self.fps = 24
        
        # 1. Constructor de Línea de Tiempo (Visuales)
        self.builder = TimelineBuilder(width=self.width, height=self.height)
        
        # 2. Ingeniero de Sonido (Audio)
        self.sound_engineer = AudioEngineer(config)
        
        # 3. Gerente de Marca (Intros/Outros/Logos)
        self.branding = BrandingManager(config, width=self.width, height=self.height)
        
        # 4. Servicio de Subtítulos (Opcional / Fallback seguro)
        try:
            from app.services.text.subtitle_service import SubtitleService
            self.subs_service = SubtitleService(model_size="base")
            logger.info("✅ Servicio de Subtítulos cargado.")
        except ImportError:
            logger.warning("⚠️ Whisper no instalado. Subtítulos desactivados.")
            self.subs_service = None
        except Exception as e:
            logger.warning(f"⚠️ Error cargando Whisper: {e}")
            self.subs_service = None

    def assemble_video(self, script, assets_map, audio_map):
        """
        Método Maestro: Coordina la producción completa del video.
        """
        logger.info(f"🎬 [DIRECTOR] Iniciando producción: {script.title} para canal {self.config.name}")
        
        try:
            # --- FASE 1: CONSTRUCCIÓN VISUAL (Escena por Escena) ---
            scene_clips = []
            theme = ThemeConfig.get_theme(self.config.theme_name)
            
            for scene in script.scenes:
                # Delegamos la creación del clip al Builder
                clip = self.builder.build_scene_clip(
                    img_path=assets_map.get(scene.id),
                    audio_path=audio_map.get(scene.id),
                    subtitle_service=self.subs_service,
                    theme=theme
                )
                if clip:
                    scene_clips.append(clip)
                else:
                    logger.error(f"❌ Fallo al crear clip para escena {scene.id}")

            if not scene_clips:
                logger.error("❌ No hay escenas válidas para montar el video.")
                return None

            # --- FASE 2: MONTAJE DEL CUERPO (Concatenación) ---
            # Usamos padding negativo (-0.8s) para crear transiciones fluidas (crossfade)
            logger.info("🎞️ Concatenando escenas...")
            body_video = concatenate_videoclips(scene_clips, method="compose", padding=-0.8)

            # --- FASE 3: INGENIERÍA DE AUDIO ---
            # Delegamos la mezcla (Música + SFX + Ducking) al Ingeniero
            body_video = self.sound_engineer.process_full_mix(body_video, script, scene_clips)

            # --- FASE 4: BRANDING Y EMPAQUETADO ---
            # Detectamos la imagen principal (Hero Image) para la intro dinámica
            # Usamos la imagen de la primera escena disponible
            hero_image = assets_map.get(1) or list(assets_map.values())[0]
            
            # Aplicamos Logo y Lower Thirds (Suscríbete)
            body_video = self.branding.apply_watermark(body_video)
            body_video = self.branding.add_lower_third(body_video)
            
            # Agregamos Intro y Outro (Dinámicas o Estáticas según config)
            master_video = self.branding.package_full_video(
                body_clip=body_video, 
                hero_image=hero_image, 
                title_text=script.title
            )

            # --- FASE 5: RENDERIZADO FINAL ---
            return self._render(master_video, script.title)

        except Exception as e:
            logger.error(f"❌ Error crítico en assemble_video: {e}")
            import traceback
            traceback.print_exc()
            return None

    def _render(self, video, title):
        """Renderiza el video final a MP4."""
        # Limpieza del título para el nombre de archivo
        clean_title = "".join([c for c in title if c.isalnum() or c in (' ', '_')]).rstrip()
        clean_title = clean_title.replace(" ", "_")
        
        output_filepath = os.path.join(self.output_path, f"{clean_title[:30]}_MASTER.mp4")
        
        logger.info(f"💾 Renderizando archivo final: {output_filepath}")
        
        try:
            video.write_videofile(
                output_filepath, 
                fps=self.fps, 
                codec="libx264", 
                audio_codec="aac",
                threads=4, 
                preset="ultrafast", # Cambiar a 'medium' para mejor compresión si tienes tiempo
                ffmpeg_params=["-pix_fmt", "yuv420p"]
            )
            
            # Limpieza de memoria
            video.close()
            gc.collect()
            
            logger.info("🎉 ¡Video renderizado exitosamente!")
            return output_filepath
            
        except Exception as e:
            logger.error(f"❌ Error renderizando video: {e}")
            return None