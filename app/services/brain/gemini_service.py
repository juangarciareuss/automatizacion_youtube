import os
from google import genai
from google.genai import types
from app.domain.models import VideoScript
from app.utils.logger import get_logger

logger = get_logger(__name__)

class GeminiService:
    def __init__(self):
        # Usamos la API Key estándar de Google AI Studio
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("❌ GEMINI_API_KEY no encontrada en .env")
            
        # Inicializamos el cliente con el SDK moderno (google-genai)
        self.client = genai.Client(api_key=api_key)
        
        # --- MODELO SOLICITADO POR EL USUARIO ---
        self.model_name = "gemini-3-flash-preview" 

    def generate_script(self, topic: str) -> VideoScript:
        # 1. Definimos la Instrucción del Sistema
        system_instruction = """
        You are an expert documentary scriptwriter for a Luxury/History YouTube channel.
        Your goal is to create engaging, storytelling-driven scripts.
        """

        # 2. Definimos el Prompt del Usuario (CON INSTRUCCIONES DE SFX)
        prompt = f"""
        Create a script about: "{topic}"
        Language: English (Professional, engaging, storytelling style).
        
        Structure requirements (Strict JSON):
        1. Title: Catchy, under 60 chars.
        2. Scenes: Array of 6 scenes.
        3. Each scene must have:
           - "id": 1, 2, ...
           - "text": The narration (approx 130-170 characters per scene).
             IMPORTANT: Include sound effects tags [SFX: sound_name] inside the text exactly where they happen. 
             Example: "The engine roared [SFX: whoosh] as it sped away." 
             Available SFX: [whoosh].
            "image_prompt": A detailed visual description for an AI image generator. 
             CRITICAL: Do not just use the brand name (e.g., don't say "Tous logo"). 
             Instead, DESCRIBE the visual identity physically (e.g., "A silver jewelry pendant shaped like a teddy bear", "A minimalist store with green emerald details").
             MANDATORY STYLE: "Award-winning documentary photography, shot on Arri Alexa, 35mm lens, hyper-realistic, 8k".
             NEGATIVE CONSTRAINTS: "No text, no watermarks, no cgi, no 3d render, no cartoon".

        Output ONLY raw JSON. No markdown formatting.
        """

        try:
            # Llamada compatible con Gemini API (SDK google-genai)
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction, 
                    response_mime_type="application/json",
                    response_schema=VideoScript, 
                    temperature=0.7,
                )
            )

            # Validación y Parsing
            if response.parsed:
                script_obj = response.parsed
                logger.info(f"✅ Guion generado con Gemini 3: '{script_obj.title}'")
                return script_obj
            else:
                # Fallback por si la respuesta llega como texto plano
                logger.warning("⚠️ Respuesta sin parsear automáticamente, intentando manual...")
                return VideoScript.model_validate_json(response.text)

        except Exception as e:
            logger.error(f"❌ Error en GeminiService: {e}")
            raise e