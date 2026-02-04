import os
from moviepy.editor import VideoFileClip, ImageClip, CompositeVideoClip, concatenate_videoclips
from app.utils.logger import get_logger

logger = get_logger(__name__)

class BrandingManager:
    def __init__(self, intro_file, outro_file, logo_file, sub_file, assets_path="assets/branding", width=1080, height=1920):
        self.assets_path = assets_path
        self.width = width
        self.height = height
        
        # Guardamos la configuración específica
        self.intro_file = intro_file
        self.outro_file = outro_file
        self.logo_file = logo_file
        self.sub_file = sub_file

    def _load_asset(self, filename):
        if not filename: return None
        path = os.path.join(self.assets_path, filename)
        if os.path.exists(path):
            return path
        return None

    def apply_watermark(self, video_clip):
        logo_path = self._load_asset(self.logo_file)
        if not logo_path: return video_clip

        logger.info(f"🎨 Aplicando Logo: {self.logo_file}")
        
        # --- CORRECCIÓN AQUÍ ---
        # Usamos .margin() en lugar de .set_margin()
        logo = (ImageClip(logo_path)
                .resize(width=150)
                .margin(top=50, right=50, opacity=0) # <--- CAMBIO CLAVE
                .set_position(("right", "top"))
                .set_duration(video_clip.duration)
                .set_opacity(0.8))
        
        return CompositeVideoClip([video_clip, logo])

    def add_lower_third(self, video_clip):
        sub_path = self._load_asset(self.sub_file)
        if not sub_path: return video_clip

        logger.info(f"🎨 Añadiendo Animación: {self.sub_file}")
        start_t = 5
        
        if sub_path.endswith(".mov"):
            sub_clip = VideoFileClip(sub_path, has_mask=True).resize(width=700)
        else:
            sub_clip = ImageClip(sub_path).resize(width=700).set_duration(4)
        
        sub_clip = sub_clip.set_start(start_t).set_position(("center", 1500))
        return CompositeVideoClip([video_clip, sub_clip])

    def package_full_video(self, body_clip):
        sequence = []

        # Intro
        intro_path = self._load_asset(self.intro_file)
        if intro_path:
            logger.info("📦 Insertando Intro...")
            intro = VideoFileClip(intro_path).resize(newsize=(self.width, self.height))
            sequence.append(intro)

        sequence.append(body_clip)

        # Outro
        outro_path = self._load_asset(self.outro_file)
        if outro_path:
            logger.info("📦 Insertando Outro...")
            outro = VideoFileClip(outro_path).resize(newsize=(self.width, self.height))
            sequence.append(outro)

        if len(sequence) == 1: return body_clip
        return concatenate_videoclips(sequence, method="compose")