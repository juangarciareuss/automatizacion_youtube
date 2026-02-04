import os
from PIL import Image, ImageDraw, ImageFont
from app.services.visuals.vertex_generator import VertexGenerator
from app.utils.logger import get_logger

logger = get_logger(__name__)

class ThumbnailService:
    def __init__(self, output_path="output/thumbnails"):
        self.output_path = output_path
        os.makedirs(output_path, exist_ok=True)
        # Reutilizamos tu generador blindado de Vertex
        self.vertex = VertexGenerator(download_path=output_path)
        
        # Configura tu fuente. Si no existe, usa la default.
        self.font_path = "assets/fonts/impact.ttf" 
        
    def generate_thumbnail(self, topic: str, hook_text: str) -> str:
        logger.info(f"🖼️ Diseñando Miniatura para: {topic}")
        
        try:
            # 1. Prompt Visual para Vertex (Estilo YouTube Clickbait)
            prompt = (
                f"YouTube thumbnail background for a video about {topic}. "
                "Hyper-dramatic, high contrast, shocked emotions, 8k resolution, "
                "vibrant colors, clean background space for text, photorealistic."
            )
            
            # Simulamos un objeto escena para usar el VertexGenerator existente
            class SceneMock:
                id = "thumb"
                visual_description = prompt
            
            # Generamos la imagen base
            base_image_path = self.vertex.generate_asset(SceneMock())
            
            if not base_image_path:
                return None

            # 2. Superponer TEXTO
            return self._add_text_overlay(base_image_path, hook_text)

        except Exception as e:
            logger.error(f"❌ Error creando thumbnail: {e}")
            return None

    def _add_text_overlay(self, image_path: str, text: str) -> str:
        try:
            # Abrir imagen
            img = Image.open(image_path).convert("RGBA")
            draw = ImageDraw.Draw(img)
            
            # Cargar Fuente
            W, H = img.size
            fontsize = int(H * 0.15) # Texto grande (15% del alto)
            
            try:
                font = ImageFont.truetype(self.font_path, fontsize)
            except:
                logger.warning("⚠️ Fuente Impact no encontrada, usando default.")
                font = ImageFont.load_default()

            text = text.upper()
            
            # Posición: Centrado, un poco arriba
            # Usamos textbbox para calcular tamaño (Pillow 10+)
            try:
                left, top, right, bottom = draw.textbbox((0, 0), text, font=font)
                text_w = right - left
                text_h = bottom - top
            except AttributeError:
                # Fallback para Pillow viejo
                text_w, text_h = draw.textsize(text, font=font)
            
            text_x = (W - text_w) / 2
            text_y = H * 0.10 # Arriba

            # Borde Negro (Stroke manual para compatibilidad)
            stroke_width = 6
            for x_offset in range(-stroke_width, stroke_width+1):
                for y_offset in range(-stroke_width, stroke_width+1):
                    draw.text((text_x + x_offset, text_y + y_offset), text, font=font, fill="black")

            # Texto Amarillo Principal
            draw.text((text_x, text_y), text, font=font, fill="#FFD700") # Amarillo Oro

            # Guardar
            final_path = image_path.replace(".png", "_FINAL.png")
            img.save(final_path)
            logger.info(f"✅ Miniatura lista: {final_path}")
            return final_path

        except Exception as e:
            logger.error(f"❌ Error en overlay de texto: {e}")
            return image_path