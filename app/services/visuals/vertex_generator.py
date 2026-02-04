import os
import json
import time
import vertexai
from google.oauth2 import service_account
from vertexai.preview.vision_models import ImageGenerationModel
from app.domain.models import Scene
from app.utils.logger import get_logger

logger = get_logger(__name__)

class VertexGenerator:
    def __init__(self, download_path="output/temp_assets"):
        self.download_path = download_path
        os.makedirs(download_path, exist_ok=True)
        
        # --- ESTRATEGIA: FUERZA BRUTA ---
        cred_filename = "google_credentials.json"
        
        # Buscamos en la carpeta actual (donde está main.py)
        root_dir = os.getcwd()
        cred_path = os.path.join(root_dir, cred_filename)
        
        if not os.path.exists(cred_path):
             logger.error(f"❌ NO ENCUENTRO EL JSON EN: {root_dir}")
             raise FileNotFoundError(f"Falta {cred_filename}")

        logger.info(f"🔑 Usando llave: {cred_path}")
        
        try:
            # 1. Cargar Credenciales como Objeto
            self.credentials = service_account.Credentials.from_service_account_file(cred_path)
            
            # 2. Leer Project ID
            with open(cred_path, "r") as f:
                project_id = json.load(f).get("project_id")

            # 3. Inicializar Vertex pasando credenciales EXPLÍCITAMENTE
            vertexai.init(
                project=project_id, 
                location="us-central1",
                credentials=self.credentials 
            )
            
            # --- CAMBIO CRÍTICO: MODELO ESTABLE ---
            # Probamos con Imagen 2 (imagegeneration@006) que es a prueba de balas.
            # Si esto funciona, es que Imagen 3 requiere un permiso extra en tu consola.
            self.model_name = "imagen-4.0-fast-generate-001" 
            self.model = ImageGenerationModel.from_pretrained(self.model_name)
            
            logger.info(f"✅ Conectado a Vertex AI (Modelo: {self.model_name})")
                
        except Exception as e:
            logger.error(f"❌ Error fatal iniciando Vertex: {e}")
            raise e

    def generate_asset(self, scene: Scene) -> str:
        try:
            if not scene.visual_description: return None

            # Prompt ajustado para Imagen 2
            prompt = f"{scene.visual_description}, cinematic lighting, 8k, photorealistic, 9:16 aspect ratio"
            logger.info(f"🎨 Generando con {self.model_name} (Escena {scene.id})...")
            
            images = self.model.generate_images(
                prompt=prompt,
                number_of_images=1,
                aspect_ratio="9:16",
                # Estos parámetros son más seguros para Imagen 2
                safety_filter_level="block_some", 
                person_generation="allow_adult"
            )

            filename = f"scene_{scene.id}.png"
            filepath = os.path.join(self.download_path, filename)
            images[0].save(location=filepath, include_generation_parameters=False)
            logger.info(f"   ✨ Guardado: {filename}")
            return filepath

        except Exception as e:
            if "429" in str(e):
                logger.warning("⏳ Vertex saturado. Esperando 60s...")
                time.sleep(60)
                return self.generate_asset(scene)
            
            logger.error(f"❌ Error generando imagen: {e}")
            # Fallback vital: Si falla la IA, no rompemos el video, devolvemos None
            return None

    def fetch_assets(self, scenes: list) -> dict:
        assets_map = {}
        for scene in scenes:
            path = self.generate_asset(scene)
            if path: assets_map[scene.id] = path
            time.sleep(3) # Imagen 2 es más rápida, bajamos espera
        return assets_map