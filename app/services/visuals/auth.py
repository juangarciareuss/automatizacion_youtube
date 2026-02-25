import os
import json
import vertexai
from google.oauth2 import service_account
from vertexai.preview.vision_models import ImageGenerationModel
from app.utils.logger import get_logger
from dotenv import load_dotenv

# Cargar variables de entorno por si acaso no están cargadas
load_dotenv()

logger = get_logger(__name__)

class VertexAuth:
    @staticmethod
    def get_model():
        """
        Autentica con Google Cloud y retorna el modelo especificado en el .env.
        """
        try:
            # 1. Obtener nombre del modelo desde .env (o usar default seguro)
            model_name = os.getenv("VERTEX_MODEL_NAME", "imagen-3.0-generate-001")
            
            # 2. Localizar credenciales
            cred_filename = "google_credentials.json"
            root_dir = os.getcwd() 
            cred_path = os.path.join(root_dir, cred_filename)
            
            if not os.path.exists(cred_path):
                 logger.error(f"❌ ERROR CRÍTICO: No encuentro {cred_filename}")
                 raise FileNotFoundError(f"Falta el archivo {cred_filename}.")

            # 3. Leer Project ID del JSON
            with open(cred_path, "r") as f:
                project_id = json.load(f).get("project_id")

            # 4. Autenticación Oficial
            credentials = service_account.Credentials.from_service_account_file(cred_path)
            
            vertexai.init(
                project=project_id, 
                location="us-central1", 
                credentials=credentials 
            )
            
            # 5. Instanciar Modelo
            model = ImageGenerationModel.from_pretrained(model_name)
            logger.info(f"✅ Vertex AI Conectado | Modelo: {model_name}")
            return model

        except Exception as e:
            logger.error(f"❌ Error de Autenticación Vertex: {e}")
            raise e