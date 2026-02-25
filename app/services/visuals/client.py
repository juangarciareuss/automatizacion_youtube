import os
from google import genai
from google.genai import types
from PIL import Image
from io import BytesIO
from app.utils.logger import get_logger

logger = get_logger(__name__)

class VertexClient:
    """
    Cliente Vertex AI configurado quirúrgicamente para tu cuenta.
    """
    def __init__(self):
        self.api_key = os.getenv("VERTEX_API_KEY")
        if not self.api_key:
            raise ValueError("❌ VERTEX_API_KEY no encontrada")
            
        self.client = genai.Client(api_key=self.api_key)
        
        # 🟢 EL ÚNICO MODELO QUE TE RESPONDIÓ (Aunque fuera con error 400)
        self.model_name = "imagen-3.0-generate-002" 

    def generate_raw_image(self, prompt: str, output_path: str) -> str:
        try:
            logger.info(f"📡 Enviando prompt a {self.model_name}...")
            
            # CONFIGURACIÓN BLINDADA PARA IMAGEN 4 FAST
            # El error 400 decía: "Only block_low_and_above is supported"
            response = self.client.models.generate_images(
                model=self.model_name,
                prompt=prompt,
                config=types.GenerateImagesConfig(
                    number_of_images=1,
                    aspect_ratio="9:16",
                    # 👇 ESTA ES LA LLAVE MAESTRA
                    safety_filter_level="block_low_and_above",
                    person_generation="allow_adult",
                )
            )

            if response.generated_images:
                image_bytes = response.generated_images[0].image.image_bytes
                image = Image.open(BytesIO(image_bytes))
                image.save(output_path, format="PNG")
                logger.info(f"✅ ¡IMAGEN GENERADA! Guardada en: {output_path}")
                return output_path
            
            return None

        except Exception as e:
            logger.error(f"❌ Error Vertex: {e}")
            
            # DIAGNÓSTICO FINAL: Si esto falla, es que Google cambió permisos en tiempo real.
            if "404" in str(e):
                logger.error("💀 Tu API Key no tiene acceso a NINGÚN modelo de imagen (3.0 ni 4.0).")
            elif "400" in str(e):
                logger.error("💀 Error de configuración persistente. Verifica la documentación de 'safety_filter_level'.")
                
            return None