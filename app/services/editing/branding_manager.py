import os
from moviepy.editor import VideoFileClip, ImageClip, CompositeVideoClip, concatenate_videoclips, TextClip, ColorClip
from app.utils.logger import get_logger

logger = get_logger(__name__)

class BrandingManager:
    def __init__(self, config, assets_path="assets/branding", width=1080, height=1920):
        """
        Recibe el objeto 'config' completo (ChannelConfig).
        """
        self.config = config
        self.assets_path = assets_path
        self.width = width
        self.height = height
        
        # --- DIAGNÓSTICO DE IMAGEMAGICK (CRÍTICO PARA TEXTOS) ---
        # Verificamos si MoviePy va a poder renderizar texto
        try:
            from moviepy.config import get_setting
            binary = get_setting("IMAGEMAGICK_BINARY")
            if not binary or not os.path.exists(binary):
                logger.warning(f"⚠️ PELIGRO: ImageMagick no detectado en: {binary}")
                logger.warning("   Los textos NO saldrán. Configura os.environ['IMAGEMAGICK_BINARY'] en video_engine.py")
            else:
                logger.info(f"✅ ImageMagick detectado correctamente.")
        except Exception:
            pass

        # Configuración de Fuente
        self.font = "Arial"
        if hasattr(self.config, 'font_path') and self.config.font_path:
            if os.path.exists(self.config.font_path):
                self.font = self.config.font_path
            else:
                logger.warning(f"⚠️ Fuente no encontrada en: {self.config.font_path}. Usando Arial.")

    def _load_asset(self, filename):
        if not filename: return None
        if os.path.exists(filename): return filename
        
        path = os.path.join(self.assets_path, filename)
        if os.path.exists(path): return path
        
        return None

    def create_dynamic_intro(self, image_path: str, title_text: str, duration: float = 3.5):
        """Genera una intro elegante con la imagen del plato y el título."""
        logger.info(f"✨ Generando Intro Dinámica: {title_text}")
        
        try:
            # 1. Imagen de fondo con CROP-TO-FILL (Para que sirva en 16:9 y 9:16)
            img_clip = ImageClip(image_path).set_duration(duration)
            
            # Calculamos el ratio para llenar la pantalla sin bordes negros
            img_w, img_h = img_clip.size
            ratio = max(self.width / img_w, self.height / img_h)
            
            img_clip = (img_clip
                        .resize(ratio)  # Escalar para cubrir
                        .set_position("center")
                        .crop(width=self.width, height=self.height) # Recortar sobrante
                        .resize(lambda t: 1 + 0.04 * t)) # Zoom suave (Ken Burns)

            # 2. Título elegante (Blindado)
            try:
                # Dividimos texto si es largo para que entre en pantalla
                wrapped_title = title_text.split(":")[0].replace(" ", "\n", 2) 
                
                # Tamaño de fuente dinámico según el ancho del video
                font_size = 100 if self.width > self.height else 80 
                
                txt_clip = (TextClip(wrapped_title, 
                                     fontsize=font_size, 
                                     color='white', 
                                     font=self.font,
                                     method='caption', # Mejor para ajustar saltos de línea
                                     size=(int(self.width * 0.8), None), # Ancho máx 80%
                                     align='center',
                                     stroke_color='black', 
                                     stroke_width=2,
                                     kerning=2)
                            .set_position(('center', 'center')) # Centrado absoluto
                            .set_duration(duration)
                            .crossfadein(0.5))
                
                # Sombra simple para legibilidad
                txt_shadow = (TextClip(wrapped_title, 
                                     fontsize=font_size, 
                                     color='black', 
                                     font=self.font,
                                     method='caption',
                                     size=(int(self.width * 0.8), None),
                                     align='center')
                            .set_position(('center', 'center'))
                            .set_duration(duration)
                            .set_opacity(0.6))

                # Retornamos capas: Fondo + Sombra + Texto
                return CompositeVideoClip([img_clip, txt_shadow, txt_clip], size=(self.width, self.height))
            
            except Exception as e:
                logger.error(f"❌ Error generando TEXTO de Intro (ImageMagick?): {e}")
                # Si falla el texto, devolvemos al menos la imagen de fondo
                return img_clip
            
        except Exception as e:
            logger.error(f"❌ Error creando intro dinámica general: {e}")
            return None

    def create_dynamic_outro(self, image_path: str, duration: float = 4.0):
        """Genera una outro simple pidiendo suscripción."""
        logger.info("👋 Generando Outro Dinámica...")
        text = getattr(self.config, 'outro_text', "Subscribe for more.") or "Subscribe"
        
        try:
            # Fondo con Crop-to-Fill
            img_clip = ImageClip(image_path).set_duration(duration)
            img_w, img_h = img_clip.size
            ratio = max(self.width / img_w, self.height / img_h)
            
            img_clip = (img_clip
                        .resize(ratio)
                        .set_position("center")
                        .crop(width=self.width, height=self.height)
                        .fadein(0.5))
            
            # Texto
            try:
                txt_clip = (TextClip(text, 
                                     fontsize=70, 
                                     color='white', 
                                     font=self.font, 
                                     stroke_color='black', 
                                     stroke_width=2)
                            .set_position('center')
                            .set_duration(duration)
                            .set_start(0.5)
                            .crossfadein(0.5))
                
                return CompositeVideoClip([img_clip, txt_clip], size=(self.width, self.height)).fadeout(0.5)
            except Exception:
                return img_clip.fadeout(0.5)

        except Exception as e:
            logger.error(f"❌ Error outro dinámica: {e}")
            return None

    def apply_watermark(self, video_clip):
        logo_path = self._load_asset(self.config.watermark_file)
        if not logo_path: return video_clip

        logger.info(f"🎨 Aplicando Logo: {self.config.watermark_file}")
        
        # Logo escalado relativo al ancho del video (15% del ancho)
        logo_width = int(self.width * 0.15)
        
        logo = (ImageClip(logo_path)
                .resize(width=logo_width)
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
        
        # Tamaño relativo
        sub_width = int(self.width * 0.4) # 40% del ancho de pantalla
        
        if sub_path.endswith(".mov") or sub_path.endswith(".mp4"):
            sub_clip = VideoFileClip(sub_path, has_mask=True).resize(width=sub_width)
        else:
            sub_clip = ImageClip(sub_path).resize(width=sub_width).set_duration(4)
        
        # Posición dinámica (abajo centro)
        y_pos = int(self.height * 0.8)
        sub_clip = sub_clip.set_start(start_t).set_position(("center", y_pos))
        
        return CompositeVideoClip([video_clip, sub_clip])

    def package_full_video(self, body_clip, hero_image=None, title_text=""):
        sequence = []

        # --- INTRO ---
        intro_path = self._load_asset(self.config.intro_file)
        if intro_path:
            logger.info("📦 Insertando Intro de Archivo...")
            # Resize robusto para llenar pantalla
            intro = VideoFileClip(intro_path)
            # Aquí podrías agregar lógica de crop-to-fill para videos de intro también si lo deseas
            intro = intro.resize(newsize=(self.width, self.height)) 
            sequence.append(intro)
        elif hero_image and title_text:
            dyn_intro = self.create_dynamic_intro(hero_image, title_text)
            if dyn_intro: sequence.append(dyn_intro)

        # --- CUERPO ---
        sequence.append(body_clip)

        # --- OUTRO ---
        outro_path = self._load_asset(self.config.outro_file)
        if outro_path:
            logger.info("📦 Insertando Outro de Archivo...")
            outro = VideoFileClip(outro_path).resize(newsize=(self.width, self.height))
            sequence.append(outro)
        elif hero_image:
            dyn_outro = self.create_dynamic_outro(hero_image)
            if dyn_outro: sequence.append(dyn_outro)

        if len(sequence) == 1: return body_clip
        return concatenate_videoclips(sequence, method="compose")