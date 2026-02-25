"""
ARCHIVO: app/services/visuals/vertex_generator.py

DESCRIPCIÓN Y FUNCIONALIDAD:
Este documento funciona como los "Ojos" de la fábrica. Su única responsabilidad es 
tomar las descripciones textuales (prompts) de las escenas y convertirlas en imágenes 
estáticas (.png) utilizando la Inteligencia Artificial de Google Vertex AI.

Se ha refactorizado para operar bajo demanda (una imagen a la vez) y soportar Visual Chaining.

Flujo exacto:
1. Recibe una escena específica desde el orquestador (puede incluir una imagen base anterior).
2. Verifica si la imagen de la escena ya existe en la carpeta temporal (Sistema de Caché).
   - Si existe, se la salta para ahorrar tiempo y dinero.
   - Si no existe, delega la creación del prompt detallado al PromptArchitect.
3. Prepara los parámetros de la API (excluyendo 'aspect_ratio' si es edición para evitar colapsos).
4. Llama a la API de Vertex AI para generar o editar la imagen.
5. Si la API de Google lanza un error de cuota (429), entra en un bucle de espera progresivo 
   (30s, 60s, etc.) y reintenta automáticamente.
6. Guarda la imagen descargada en 'output/temp_assets' y devuelve la ruta.
"""

import os
import time
from vertexai.preview.vision_models import Image # Importación necesaria para Image-to-Image
from app.domain.models import VideoOrientation, AssetSource
from app.utils.logger import get_logger

# 🟢 IMPORTAMOS LOS MÓDULOS ESPECIALIZADOS
from app.services.visuals.auth import VertexAuth
from app.services.visuals.prompting import PromptArchitect

logger = get_logger(__name__)

class VertexGenerator:
    def __init__(self, download_path="output/temp_assets"):
        self.download_path = download_path
        os.makedirs(download_path, exist_ok=True)
        
        # 1. Delegamos la conexión al módulo de Auth
        self.model = VertexAuth.get_model()

    def generate_scene(self, scene, script, orientation: VideoOrientation = VideoOrientation.PORTRAIT, init_image_path: str = None) -> str:
        """
        Genera una única imagen para una escena. 
        Si recibe un init_image_path, hace Image-to-Image (Visual Chaining).
        """
        # Solo procesamos si la fuente es Vertex
        if scene.visual_source != AssetSource.VERTEX_AI:
            return None

        # Configurar Aspect Ratio para Vertex
        aspect_ratio = "16:9" if orientation == VideoOrientation.LANDSCAPE else "9:16"
        
        # 🟢 SISTEMA DE CACHÉ / CHECKPOINT
        # Definimos cómo se debería llamar el archivo
        expected_filename = f"scene_{scene.id}.png"
        expected_filepath = os.path.join(self.download_path, expected_filename)
        
        # Verificamos si ya existe en el disco
        if os.path.exists(expected_filepath):
            logger.info(f"♻️ Caché encontrado: {expected_filename} ya existe. Saltando generación de Vertex.")
            return expected_filepath

        # Si no existe, continuamos con la generación normal
        # 2. Delegamos la creación del texto al Arquitecto
        smart_prompt = PromptArchitect.construct_super_prompt(scene, script)
        
        # 3. Ejecutamos la generación con reintentos
        return self._generate_single_image_with_retries(scene, smart_prompt, aspect_ratio, expected_filepath, init_image_path)

    def _generate_single_image_with_retries(self, scene, prompt, aspect_ratio, filepath, init_image_path=None):
        """Maneja el bucle de intentos y errores específicos de la API."""
        max_retries = 3
        
        for attempt in range(max_retries):
            try:
                # Preparamos los parámetros base de la petición (SIN aspect_ratio para no romper el Image-to-Image)
                kwargs = {
                    "prompt": prompt,
                    "number_of_images": 1,
                    "safety_filter_level": "block_some", 
                    "person_generation": "allow_adult"
                }

                # Si el orquestador nos pasa una imagen base (el frame del video anterior)
                if init_image_path and os.path.exists(init_image_path):
                    logger.info(f"🎨 Editando Escena {scene.id} sobre frame anterior (Intento {attempt+1})...")
                    base_image = Image.load_from_file(init_image_path)
                    
                    # Cambiamos al modo de edición de Vertex. La imagen hereda el tamaño de base_image.
                    images = self.model.edit_image(base_image=base_image, **kwargs)
                else:
                    logger.info(f"🎨 Generando Escena {scene.id} desde cero (Intento {attempt+1})...")
                    
                    # Al generar de cero, SÍ inyectamos el aspect_ratio al diccionario justo antes de llamar
                    kwargs["aspect_ratio"] = aspect_ratio
                    # Generación pura (Text-to-Image)
                    images = self.model.generate_images(**kwargs)

                # Guardado de archivo
                filename = os.path.basename(filepath)
                images[0].save(location=filepath, include_generation_parameters=False)
                
                logger.info(f"   ✨ Guardada: {filename}")
                return filepath # Éxito, salimos del bucle de reintentos

            except Exception as e:
                error_str = str(e)
                if "429" in error_str or "Quota" in error_str:
                    wait_time = 30 * (attempt + 1)
                    logger.warning(f"⚠️ CUOTA EXCEDIDA. Pausando {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    logger.error(f"❌ Error Vertex Escena {scene.id}: {e}")
                    # Si el error no es de cuota, retornamos None en el último intento
                    if attempt == max_retries - 1:
                        return None