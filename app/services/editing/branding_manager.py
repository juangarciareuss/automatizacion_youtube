import os
from moviepy.editor import VideoFileClip, ImageClip, CompositeVideoClip, concatenate_videoclips, TextClip
from app.utils.logger import get_logger

logger = get_logger(__name__)

class BrandingManager:
    def __init__(self, config, assets_path="assets/branding", width=1080, height=1920):
        """
        Recibe el objeto 'config' completo (ChannelConfig) en lugar de parámetros sueltos.
        """
        self.config = config
        self.assets_path = assets_path
        self.width = width
        self.height = height
        
        # Intentamos cargar la fuente personalizada si existe
        self.font = "Arial"
        if hasattr(self.config, 'font_path') and self.config.font_path:
            if os.path.exists(self.config.font_path):
                self.font = self.config.font_path
            else:
                logger.warning(f"⚠️ Fuente no encontrada en: {self.config.font_path}. Usando Arial.")

    def _load_asset(self, filename):
        if not filename: return None
        # Si es ruta absoluta o ya existe
        if os.path.exists(filename): return filename
        
        # Si es relativa a assets/branding
        path = os.path.join(self.assets_path, filename)
        if os.path.exists(path): return path
        
        return None

    def create_dynamic_intro(self, image_path: str, title_text: str, duration: float = 3.5):
        """Genera una intro elegante con la imagen del plato y el título."""
        logger.info(f"✨ Generando Intro Dinámica: {title_text}")
        
        try:
            # 1. Imagen de fondo con efecto Ken Burns (Zoom in)
            img_clip = (ImageClip(image_path)
                        .set_duration(duration)
                        .resize(height=self.height)
                        .resize(lambda t: 1 + 0.04 * t) # Zoom suave (1.0 -> 1.14)
                        .set_position("center"))

            # 2. Título elegante
            # Dividimos texto si es largo
            wrapped_title = title_text.split(":")[0].replace(" ", "\n", 2) 
            
            txt_clip = (TextClip(wrapped_title, 
                                 fontsize=80, 
                                 color='white', 
                                 font=self.font,
                                 align='center',
                                 stroke_color='black', 
                                 stroke_width=2,
                                 kerning=2)
                        .set_position(('center', 0.35), relative=True)
                        .set_duration(duration)
                        .crossfadein(0.5))

            return CompositeVideoClip([img_clip, txt_clip], size=(self.width, self.height))
            
        except Exception as e:
            logger.error(f"❌ Error creando intro dinámica: {e}")
            return None

    def create_dynamic_outro(self, image_path: str, duration: float = 4.0):
        """Genera una outro simple pidiendo suscripción."""
        logger.info("👋 Generando Outro Dinámica...")
        text = getattr(self.config, 'outro_text', "Subscribe for more.") or "Subscribe"
        
        try:
            img_clip = (ImageClip(image_path)
                        .set_duration(duration)
                        .resize(height=self.height)
                        .fadein(0.5))
            
            txt_clip = (TextClip(text, fontsize=70, color='white', font=self.font, stroke_color='black', stroke_width=2)
                        .set_position('center')
                        .set_duration(duration)
                        .set_start(0.5)
                        .crossfadein(0.5))
            
            return CompositeVideoClip([img_clip, txt_clip], size=(self.width, self.height)).fadeout(0.5)
        except Exception as e:
            logger.error(f"❌ Error outro dinámica: {e}")
            return None

    def apply_watermark(self, video_clip):
        logo_path = self._load_asset(self.config.watermark_file)
        if not logo_path: return video_clip

        logger.info(f"🎨 Aplicando Logo: {self.config.watermark_file}")
        
        logo = (ImageClip(logo_path)
                .resize(width=150)
                .margin(top=50, right=50, opacity=0)
                .set_position(("right", "top"))
                .set_duration(video_clip.duration)
                .set_opacity(0.8))
        
        return CompositeVideoClip([video_clip, logo])

    def add_lower_third(self, video_clip):
        sub_path = self._load_asset(self.config.subscribe_file)
        if not sub_path: return video_clip

        logger.info("🎨 Añadiendo Animación Suscribirse")
        start_t = min(5, video_clip.duration - 2)
        
        if sub_path.endswith(".mov") or sub_path.endswith(".mp4"):
            sub_clip = VideoFileClip(sub_path, has_mask=True).resize(width=600)
        else:
            sub_clip = ImageClip(sub_path).resize(width=600).set_duration(4)
        
        sub_clip = sub_clip.set_start(start_t).set_position(("center", 1400))
        return CompositeVideoClip([video_clip, sub_clip])

    def package_full_video(self, body_clip, hero_image=None, title_text=""):
        sequence = []

        # --- INTRO ---
        intro_path = self._load_asset(self.config.intro_file)
        if intro_path:
            # Caso A: Intro en video (Billionaires)
            logger.info("📦 Insertando Intro de Archivo...")
            intro = VideoFileClip(intro_path).resize(newsize=(self.width, self.height))
            sequence.append(intro)
        elif hero_image and title_text:
            # Caso B: Intro dinámica (Recetas)
            dyn_intro = self.create_dynamic_intro(hero_image, title_text)
            if dyn_intro: sequence.append(dyn_intro)

        # --- CUERPO ---
        sequence.append(body_clip)

        # --- OUTRO ---
        outro_path = self._load_asset(self.config.outro_file)
        if outro_path:
            # Caso A: Outro en video
            logger.info("📦 Insertando Outro de Archivo...")
            outro = VideoFileClip(outro_path).resize(newsize=(self.width, self.height))
            sequence.append(outro)
        elif hero_image:
            # Caso B: Outro dinámica
            dyn_outro = self.create_dynamic_outro(hero_image)
            if dyn_outro: sequence.append(dyn_outro)

        if len(sequence) == 1: return body_clip
        return concatenate_videoclips(sequence, method="compose")