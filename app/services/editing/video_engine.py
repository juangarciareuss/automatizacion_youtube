import os
import gc
import re
import sys

# --- CONFIGURACIÓN BLINDADA DE IMAGEMAGICK ---
# Esto le dice a MoviePy exactamente dónde está el programa.
# Nota: Usamos r"..." para que Windows lea bien las barras invertidas.
os.environ["IMAGEMAGICK_BINARY"] = r"C:\Program Files\ImageMagick-7.1.2-Q16-HDRI\magick.exe"
# ---------------------------------------------

# --- PARCHES VITALES ---
import PIL.Image
if not hasattr(PIL.Image, 'ANTIALIAS'):
    PIL.Image.ANTIALIAS = PIL.Image.LANCZOS

import asyncio
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
# -----------------------

from moviepy.editor import (
    AudioFileClip, ImageClip, TextClip, 
    concatenate_videoclips, CompositeVideoClip
)
from app.domain.models import VideoScript
from app.utils.logger import get_logger
from app.config.themes import ThemeConfig
from app.services.text.subtitle_service import SubtitleService
from app.domain.channel_config import ChannelConfig

# --- ESPECIALISTAS ---
from app.services.editing.effects import VisualEffects       
from app.services.editing.branding_manager import BrandingManager

# Audio Mixer Fallback
sys.path.append(os.getcwd()) 
try:
    from audio_mixer import AudioMixer 
except ImportError:
    class AudioMixer:
        def select_music_by_mood(self, m): return None
        def apply_auto_ducking(self, v, m, **k): return v
        def overlay_sfx(self, b, s, **k): return b

logger = get_logger(__name__)

class VideoEngine:
    def __init__(self, config: ChannelConfig, output_path="output/final_videos"):
        self.output_path = output_path
        os.makedirs(output_path, exist_ok=True)
        
        self.width = 1080
        self.height = 1920
        self.fps = 24
        
        # Guardar Configuración
        self.config = config
        self.theme = ThemeConfig.get_theme(config.theme_name)
        
        # Inicializar Especialistas
        self.fx = VisualEffects(width=self.width, height=self.height)
        
        # Branding con archivos específicos del canal
        self.branding = BrandingManager(
            intro_file=config.intro_file,
            outro_file=config.outro_file,
            logo_file=config.watermark_file,
            sub_file=config.subscribe_file,
            width=self.width, height=self.height
        )
        
        self.audio_mixer = AudioMixer() 
        
        try:
            self.subtitle_service = SubtitleService(model_size="base")
        except:
            self.subtitle_service = None

    def assemble_video(self, script: VideoScript, assets_map: dict, audio_map: dict):
        logger.info(f"🎬 [DIRECTOR] Iniciando montaje: {script.title}")
        scene_clips = []
        
        # 1. Montaje de Escenas
        for scene in script.scenes:
            if scene.id not in assets_map or scene.id not in audio_map: continue
            
            # Construcción Base
            audio_path = audio_map[scene.id]
            img_path = assets_map[scene.id]
            
            audio_clip = AudioFileClip(audio_path)
            duration = audio_clip.duration + 0.2 
            
            # Efectos Visuales
            image_clip = ImageClip(img_path).set_duration(duration)
            image_clip = self.fx.resize_to_fill(image_clip)
            image_clip = self.fx.apply_ken_burns(image_clip)
            video_clip = image_clip.set_audio(audio_clip)

            # Subtítulos
            layers = [video_clip]
            if self.subtitle_service:
                self._add_subtitles(layers, audio_path)

            final_scene = CompositeVideoClip(layers, size=(self.width, self.height)).set_duration(duration)
            final_scene = self.fx.apply_crossfade(final_scene)
            scene_clips.append(final_scene)

        if not scene_clips: return None

        # 2. Concatenar Cuerpo
        body_video = concatenate_videoclips(scene_clips, method="compose", padding=-0.8)

        # 3. Audio Engineering (Música + SFX)
        # Pasamos scene_clips para calcular los tiempos de los SFX
        body_video = self._process_audio(body_video, script, scene_clips)

        # 4. Branding
        body_video = self.branding.apply_watermark(body_video)
        body_video = self.branding.add_lower_third(body_video)

        # 5. Packaging (Intro/Outro)
        master_video = self.branding.package_full_video(body_video)

        # 6. Render
        return self._render_video(master_video, script.title)

    # --- MÉTODOS PRIVADOS ---

    def _add_subtitles(self, layers, audio_path):
        try:
            segments = self.subtitle_service.transcribe(audio_path)
            for seg in segments:
                txt_clip = TextClip(
                    txt=seg['text'],
                    font=self.theme["font"], fontsize=self.theme["fontsize"],
                    color=self.theme["color"], stroke_color=self.theme["stroke_color"],
                    stroke_width=self.theme["stroke_width"], method='caption', 
                    size=(self.width * 0.8, None)
                ).set_start(seg['start']).set_duration(seg['end']-seg['start']).set_position(self.theme["position"])
                layers.append(txt_clip)
        except Exception as e:
            logger.warning(f"⚠️ Error subtítulos: {e}")

    def _process_audio(self, video_clip, script, scene_clips):
        logger.info("🎚️ Mezclando audio...")
        audio = video_clip.audio
        
        # A. Música (Dinámica según Config)
        bg_music = self.audio_mixer.select_music_by_mood(self.config.music_mood)
        if bg_music:
            audio = self.audio_mixer.apply_auto_ducking(audio, bg_music, ducking_vol=0.15)
        
        # B. SFX (Restaurado y Limpio)
        try:
            current_time = 0.0
            # Iteramos sobre las escenas y los clips sincronizados
            for i, scene in enumerate(script.scenes):
                # Verificar que existe el clip correspondiente
                if i >= len(scene_clips): break
                
                scene_dur = scene_clips[i].duration
                
                # Buscar tags [SFX: ...]
                sfx_matches = re.findall(r'\[SFX:\s*(.*?)\]', scene.narration)
                if sfx_matches:
                    total_chars = len(scene.narration)
                    for sfx_name in sfx_matches:
                        # Calcular posición porcentual en el texto
                        match_obj = re.search(r'\[SFX:\s*' + re.escape(sfx_name) + r'\]', scene.narration)
                        if match_obj:
                            percent = match_obj.start() / max(total_chars, 1)
                            # Tiempo absoluto = Inicio de escena + (Porcentaje * Duración escena)
                            sfx_time = current_time + (percent * scene_dur)
                            
                            audio = self.audio_mixer.overlay_sfx(
                                base_audio=audio,
                                sfx_name=sfx_name.strip().lower(),
                                start_time=sfx_time
                            )
                
                # Avanzar el cursor de tiempo
                # Restamos el padding (0.8) que usamos al concatenar, para que el tiempo sea preciso
                current_time += (scene_dur - 0.8)

        except Exception as e:
            logger.warning(f"⚠️ Error insertando SFX: {e}")
        
        return video_clip.set_audio(audio)

    def _render_video(self, video, title):
        clean_title = "".join([c for c in title if c.isalnum() or c in (' ', '_')]).rstrip()
        output_filepath = os.path.join(self.output_path, f"{clean_title[:30]}_MASTER.mp4")
        
        logger.info(f"💾 Renderizando: {output_filepath}")
        video.write_videofile(
            output_filepath, fps=self.fps, codec="libx264", audio_codec="aac",
            threads=4, preset="ultrafast", ffmpeg_params=["-pix_fmt", "yuv420p"]
        )
        try:
            video.close()
            gc.collect()
        except: pass
        return output_filepath