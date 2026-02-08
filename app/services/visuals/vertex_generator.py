import os
import json
import time
import random
import vertexai
from google.oauth2 import service_account
from vertexai.preview.vision_models import ImageGenerationModel
from app.domain.models import Scene
from app.utils.logger import get_logger

logger = get_logger(__name__)

class VertexGenerator:
    def __init__(self, download_path="output/temp_assets", style_modifier="cinematic food photography, macro details, 8k, hyper-realistic"):
        self.download_path = download_path
        self.style_modifier = style_modifier 
        
        # 1. CONSISTENCIA MATEMÁTICA (GLOBAL SEED)
        self.global_seed = random.randint(1, 100000)
        
        os.makedirs(download_path, exist_ok=True)
        
        # --- AUTENTICACIÓN ---
        cred_filename = "google_credentials.json"
        root_dir = os.getcwd()
        cred_path = os.path.join(root_dir, cred_filename)
        
        if not os.path.exists(cred_path):
             logger.error(f"❌ NO ENCUENTRO EL JSON EN: {root_dir}")
             raise FileNotFoundError(f"Falta {cred_filename}")

        logger.info(f"🔑 Usando llave: {cred_path}")
        
        try:
            self.credentials = service_account.Credentials.from_service_account_file(cred_path)
            with open(cred_path, "r") as f:
                project_id = json.load(f).get("project_id")

            vertexai.init(
                project=project_id, 
                location="us-central1",
                credentials=self.credentials 
            )
            
            self.model_name = "imagen-4.0-fast-generate-001" 
            self.model = ImageGenerationModel.from_pretrained(self.model_name)
            
            logger.info(f"✅ Vertex Ready (Set Virtual Activo) | Modelo: {self.model_name}")
                
        except Exception as e:
            logger.error(f"❌ Error fatal iniciando Vertex: {e}")
            raise e

    def _build_intelligent_prompt(self, scene: Scene, kitchen_set: dict, accumulated_context: list) -> str:
        """Construye un prompt por capas para forzar la continuidad."""
        action_description = getattr(scene, 'image_prompt', None) or getattr(scene, 'visual_description', None)
        if not action_description:
            return None

        # Set (Invariable)
        set_desc = f"Setting: {kitchen_set['environment']}. Tools: {kitchen_set['tools']}."

        # Memoria (Lo que ya pasó)
        context_str = ""
        if accumulated_context:
            past_items = ", ".join(accumulated_context[-2:])
            context_str = f" Visible in background/side: {past_items}."

        # Ensamblaje Final
        full_prompt = (
            f"{self.style_modifier}. "
            f"{set_desc}"
            f"{context_str}"
            f" Main Action Focus: {action_description}. "
            f"Atmosphere: Moody, steam rising, glistening textures."
        )
        return full_prompt

    def generate_asset(self, scene: Scene, prompt_override: str = None) -> str:
        try:
            final_prompt = prompt_override
            if not final_prompt:
                raw_desc = getattr(scene, 'image_prompt', None) or getattr(scene, 'visual_description', None)
                if not raw_desc: return None
                final_prompt = f"{raw_desc}, {self.style_modifier}, 9:16 aspect ratio"

            logger.info(f"🎨 Generando Escena {scene.id}...")
            
            images = self.model.generate_images(
                prompt=final_prompt,
                number_of_images=1,
                aspect_ratio="9:16",
                safety_filter_level="block_some", 
                person_generation="allow_adult",
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
                return self.generate_asset(scene, prompt_override)
            logger.error(f"❌ Error generando imagen: {e}")
            return None

    def fetch_assets(self, scenes: list) -> dict:
        """El ORQUESTADOR CON MEMORIA."""
        assets_map = {} # 1. Creamos la bolsa vacía
        
        # A. DEFINIR EL SET VIRTUAL
        kitchen_set = {
            "environment": "Dark rustic wooden countertop, natural window light from left, blurry dark background",
            "tools": "Cast iron skillet, vintage silver knife, beige linen napkin"
        }
        
        # B. MEMORIA DEL PROCESO
        accumulated_context = [] 
        
        logger.info(f"🎬 Iniciando Secuencia con Set Virtual: {kitchen_set['environment']}")
        
        for scene in scenes:
            smart_prompt = self._build_intelligent_prompt(scene, kitchen_set, accumulated_context)
            
            if smart_prompt:
                path = self.generate_asset(scene, prompt_override=smart_prompt)
                
                # SI LA IMAGEN SE GENERÓ, LA GUARDAMOS EN LA BOLSA
                if path: 
                    assets_map[scene.id] = path
                
                # Actualizar Memoria (Vital para la consistencia)
                output_state = getattr(scene, 'output_state', None)
                if output_state:
                    accumulated_context.append(output_state)
                else:
                    # Fallback si Gemini no dio output_state
                    desc = getattr(scene, 'visual_description', "something")
                    accumulated_context.append(f"prepared {desc[:20]}...")

            time.sleep(1) 

        # --- ESTA ES LA LÍNEA QUE FALTABA ---
        return assets_map