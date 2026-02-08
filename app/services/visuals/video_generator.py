import os
import time
from vertexai.preview.vision_models import Image, ImageGenerationModel
from app.utils.logger import get_logger

logger = get_logger(__name__)

class VideoGenerator:
    def __init__(self):
        # Usamos el modelo Veo 2.0 optimizado para generación
        # Si tienes acceso a la preview, puedes usar 'veo-2.0-generate-preview'
        self.model_name = "veo-2.0-generate-001" 
        logger.info(f"🎥 Inicializando VideoGenerator con modelo: {self.model_name}")

    def animate_image(self, image_path: str, prompt: str, output_filename: str = "animated_shot.mp4") -> str:
        """
        Transforma una imagen estática en un video usando Veo (Image-to-Video).
        """
        try:
            if not os.path.exists(image_path):
                logger.error(f"❌ Imagen no encontrada: {image_path}")
                return None

            logger.info(f"🚀 Enviando a Veo: {image_path}...")
            logger.info(f"   Prompt: {prompt}")

            # 1. Cargar imagen y modelo
            input_image = Image.load_from_file(image_path)
            model = ImageGenerationModel.from_pretrained(self.model_name)

            # 2. Generar Video (Operación Larga ~60-90s)
            # Nota: Veo permite especificar 'seed' si quisieras determinismo, 
            # pero para video la variación suele ser buena.
            video = model.generate_video(
                image=input_image,
                prompt=prompt,
                aspect_ratio="9:16", # Formato Short
                add_audio=False,     # No necesitamos audio, lo ponemos en edición
                fps=24
            )

            # 3. Guardar el resultado
            output_dir = "output/temp_video_assets"
            os.makedirs(output_dir, exist_ok=True)
            final_path = os.path.join(output_dir, output_filename)
            
            # Guardamos el archivo
            video.save(final_path)
            
            logger.info(f"✨ Video Veo guardado exitosamente: {final_path}")
            return final_path

        except Exception as e:
            logger.error(f"⚠️ Error generando video con Veo: {e}")
            # Si falla (ej. cuota excedida), devolvemos None para que el sistema use la imagen estática
            return None