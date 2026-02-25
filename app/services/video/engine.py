import os
import gc
from dotenv import load_dotenv
from moviepy.config import change_settings

# Carga de entorno (PRESERVADO)
load_dotenv()
imagemagick_path = os.getenv("IMAGEMAGICK_BINARY")
if imagemagick_path and os.path.exists(imagemagick_path):
    change_settings({"IMAGEMAGICK_BINARY": imagemagick_path})

from moviepy.editor import concatenate_videoclips, TextClip, CompositeVideoClip
from app.utils.logger import get_logger
from app.config.themes import ThemeConfig
from app.domain.models import VideoOrientation 

# --- SERVICIOS (PRESERVADO) ---
from app.services.editing.timeline_builder import TimelineBuilder
from app.services.editing.audio_engineer import AudioEngineer
from app.services.editing.branding_manager import BrandingManager

logger = get_logger(__name__)

class VideoEngine:
    # 🟢 MODIFICADO: Agregamos draft_mode=False a la firma del constructor
    def __init__(self, config, output_path="output/final_videos", draft_mode=False):
        self.config = config
        self.output_path = output_path
        self.draft_mode = draft_mode  # 🟢 NUEVO: Guardamos el estado
        os.makedirs(output_path, exist_ok=True)
        
        # 🟢 1. DIMENSIONES DINÁMICAS (PRESERVADO)
        if self.config.orientation == VideoOrientation.LANDSCAPE:
            self.width = 1920
            self.height = 1080
            self.resolution = (1920, 1080) 
            logger.info("🎬 VideoEngine: LANDSCAPE (1920x1080)")
        else:
            self.width = 1080
            self.height = 1920
            self.resolution = (1080, 1920) 
            logger.info("🎬 VideoEngine: PORTRAIT (1080x1920)")
            
        self.fps = 24
        
        # 🟢 MODIFICADO: Pasamos draft_mode al TimelineBuilder
        # Esto es vital para que se desactive el Ken Burns
        self.builder = TimelineBuilder(resolution=self.resolution, draft_mode=self.draft_mode)
        
        self.sound_engineer = AudioEngineer(config)
        self.branding = BrandingManager(config, width=self.width, height=self.height)
        
        # Servicio de Subtítulos (Whisper) (PRESERVADO)
        try:
            from app.services.text.subtitle_service import SubtitleService
            self.subs_service = SubtitleService(model_size="base")
        except:
            logger.warning("⚠️ Subtítulos desactivados (Falta Whisper).")
            self.subs_service = None

    def assemble_video(self, script, assets_map, audio_map):
        """
        Método Maestro: Coordina la producción completa.
        """
        # 🟢 NUEVO: Log informativo del modo
        mode_label = "⚡ DRAFT (TURBO)" if self.draft_mode else "🐢 PRO (FINAL)"
        logger.info(f"🎬 [DIRECTOR] Iniciando: {script.title} | Modo: {mode_label}")
        
        try:
            # --- FASE 1: CONSTRUCCIÓN VISUAL ---
            scene_clips = self.builder.build_visual_clips(script, assets_map, audio_map)

            if not scene_clips:
                logger.error("❌ No hay clips visuales válidos.")
                return None

            # --- FASE 2: MONTAJE DEL CUERPO ---
            logger.info("🎞️ Concatenando escenas...")
            body_video = concatenate_videoclips(scene_clips, method="compose", padding=-0.5)

            # --- FASE 3: INGENIERÍA DE AUDIO ---
            body_video = self.sound_engineer.process_full_mix(body_video, script, scene_clips)

            # --- FASE 4: SUBTÍTULOS ---
            if self.subs_service:
                logger.info("📝 Generando subtítulos globales...")
                body_video = self._burn_subtitles(body_video, audio_map, script)

            # --- FASE 5: BRANDING Y EMPAQUETADO ---
            # 🟢 MODIFICADO: Lógica inteligente para saltar intro compleja si es Short O si es Draft
            # (En Draft queremos ver el video rápido, no esperar render de intro)
            should_add_branding = (
                self.config.orientation == VideoOrientation.LANDSCAPE 
                and not self.draft_mode
            )

            if should_add_branding:
                hero_image = assets_map.get(1) or list(assets_map.values())[0]
                master_video = self.branding.package_full_video(
                    body_clip=body_video, 
                    hero_image=hero_image, 
                    title_text=script.title
                )
            else:
                master_video = body_video

            # --- FASE 6: RENDERIZADO ---
            return self._render(master_video, script.title)

        except Exception as e:
            logger.error(f"❌ Error crítico en assemble_video: {e}")
            import traceback
            traceback.print_exc()
            return None

    def _burn_subtitles(self, video_clip, audio_map, script):
        """
        Genera y superpone subtítulos al video completo.
        (MÉTODO PRESERVADO EXACTAMENTE IGUAL)
        """
        try:
            full_subs = []
            current_time = 0.0
            
            fontsize = 80 if self.config.orientation == VideoOrientation.PORTRAIT else 60
            
            for scene in script.scenes:
                audio_path = audio_map.get(scene.id)
                if not audio_path: continue
                
                segments = self.subs_service.transcribe(audio_path)
                
                for seg in segments:
                    start = current_time + seg['start']
                    end = current_time + seg['end']
                    duration = end - start
                    
                    txt = TextClip(
                        txt=seg['text'].upper(),
                        font="Impact",
                        fontsize=fontsize,
                        color="white",
                        stroke_color="black",
                        stroke_width=3,
                        method='caption',
                        size=(int(self.width * 0.8), None)
                    ).set_start(start).set_duration(duration)
                    
                    pos = ("center", 0.75)
                    txt = txt.set_position(pos, relative=True)
                    
                    full_subs.append(txt)
                
                # Estimación de tiempo para avanzar cursor
                from moviepy.editor import AudioFileClip
                scene_dur = AudioFileClip(audio_path).duration
                current_time += (scene_dur + 0.2) 

            if full_subs:
                return CompositeVideoClip([video_clip] + full_subs)
            return video_clip

        except Exception as e:
            logger.warning(f"⚠️ Fallo en subtítulos: {e}")
            return video_clip

    def _render(self, video, title):
        """Renderiza a MP4."""
        clean_title = "".join([c for c in title if c.isalnum() or c in (' ', '_')]).rstrip()
        clean_title = clean_title.replace(" ", "_")
        
        # 🟢 NUEVO: Etiqueta DRAFT en el archivo
        quality_tag = "DRAFT" if self.draft_mode else "FINAL"
        fmt_tag = "SHORT" if self.width < self.height else "LONG"
        
        output_filepath = os.path.join(self.output_path, f"{clean_title[:30]}_{fmt_tag}_{quality_tag}.mp4")
        
        logger.info(f"💾 Renderizando ({quality_tag}): {output_filepath}")
        
        # 🟢 NUEVO: Configuración de velocidad TURBO
        preset = "ultrafast" if self.draft_mode else "medium" # ultrafast es 10x más rápido
        threads = 8 if self.draft_mode else 4
        
        try:
            video.write_videofile(
                output_filepath, 
                fps=self.fps, 
                codec="libx264", 
                audio_codec="aac",
                threads=threads, 
                preset=preset, # <--- LA CLAVE DE LA VELOCIDAD
                ffmpeg_params=["-pix_fmt", "yuv420p"]
            )
            video.close()
            gc.collect()
            return output_filepath
        except Exception as e:
            logger.error(f"❌ Error renderizando: {e}")
            return None