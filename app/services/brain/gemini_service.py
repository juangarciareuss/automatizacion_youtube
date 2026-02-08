import os
from google import genai
from google.genai import types
from app.domain.models import VideoScript
from app.utils.logger import get_logger

logger = get_logger(__name__)

class GeminiService:
    def __init__(self, persona: str = "master_chef"):
        """
        Inicializa el servicio con una 'persona' específica.
        """
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("❌ GEMINI_API_KEY no encontrada en .env")
            
        self.client = genai.Client(api_key=api_key)
        self.persona = persona
        
        # Mantenemos tu modelo que funciona perfecto
        self.model_name = "gemini-2.0-flash" 

    def _get_persona_config(self):
        """Selecciona el 'System Prompt' y el estilo según el canal activo."""
        
        # 1. PERFIL: HISTORIADOR (Sin cambios)
        if self.persona == "business_historian":
            return {
                "system": """
                You are an expert documentary scriptwriter for a Luxury/History YouTube channel.
                Goal: Engaging stories about power and money.
                """,
                "visual_style": "Award-winning documentary photography, cinematic lighting, 8k, hyper-realistic.",
                "negative_prompt": "No text, no watermarks, no cgi, no cartoon."
            }
        
        # 2. PERFIL: CHEF INSTRUCTOR (Ajustado: 15 Escenas, Objetivo + Intro/Outro Estimulante)
        elif self.persona == "master_chef":
            # Definimos el estilo base aquí para usarlo dentro del prompt
            base_style = "Food Porn aesthetic, Macro 100mm lens, f/1.8 aperture, bokeh, volumetric steam, 8k professional studio lighting."

            return {
                "system": f"""
                You are a Professional Culinary Instructor.
                YOUR GOAL: Create a logical, step-by-step recipe script (approx 60 seconds).
                
                --- CONSISTENCY PROTOCOL (CRITICAL) ---
                1. DEFINE A 'VISUAL ANCHOR': Choose a specific kitchen setting (e.g., "Dark slate countertop, copper cookware, moody side lighting").
                2. APPLY THE ANCHOR: You MUST start EVERY 'image_prompt' with this exact visual anchor description.
                3. INGREDIENT TRACKING: If you chop green onions in Scene 2, Scene 3 MUST show "chopped green onions".
                
                --- STRUCTURE (15 SCENES) ---
                - SCENE 1 (Intro): The FINAL COOKED dish. Perfect plating. Narrative hook.
                - SCENES 2-14: The Process. Fast cuts. CLOSE-UPS only.
                - SCENE 15 (Outro): The same FINAL COOKED dish.
                
                VISUAL STYLE: {base_style}
                """,
                "visual_style": base_style,
                "negative_prompt": "No text overlay, no typography, no words, no raw meat in final dish, no human faces, no hands, no cartoon, no blurry images, no distortion."
            }
        
        else:
            return self._get_persona_config()

    def generate_script(self, topic: str) -> VideoScript:
        config = self._get_persona_config()
        
        logger.info(f"🤖 Configurando Gemini como: {self.persona} para tema: {topic}")

        # Prompt ajustado para exigir 15 escenas exactas
        prompt = f"""
        Create a objective, step-by-step cooking script for: "{topic}"
        
        Format: Vertical Video (9:16).
        
        REQUIREMENTS (Strict JSON):
        1. Title: Clear and catchy (e.g., "Exquisite Truffle Burger in 60 Seconds").
        2. Scenes: Array of EXACTLY 15 scenes.
        
        CRITICAL OVERRIDE FOR SCENE 1 (INTRO):
        - Scene 1 Visual: CLOSE-UP of the FINAL COOKED DISH. Melting, steaming, golden. NO RAW INGREDIENTS.
        
        PER SCENE FIELDS:
        - "id": 1 to 15.
        - "narrative_text": Direct instructions.
        - "image_prompt": MUST START with the Kitchen Visual Anchor + The specific action.
        - "output_state": Context Memory for next scene.
        
        Negative Constraints: "{config['negative_prompt']}"

        Output ONLY raw JSON matching the 'VideoScript' schema.
        """

        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=config["system"], 
                    response_mime_type="application/json",
                    response_schema=VideoScript,
                    temperature=0.7, # Temperatura controlada para evitar alucinaciones
                )
            )

            if response.parsed:
                script_obj = response.parsed
                logger.info(f"✅ Guion generado: '{script_obj.title}' (Escenas: {len(script_obj.scenes)})")
                
                # Validación simple
                if len(script_obj.scenes) != 15:
                    logger.warning(f"⚠️ Gemini generó {len(script_obj.scenes)} escenas en lugar de 15. El ritmo podría variar.")
                
                return script_obj
            else:
                logger.warning("⚠️ Respuesta sin parsear automáticamente, intentando manual...")
                return VideoScript.model_validate_json(response.text)

        except Exception as e:
            logger.error(f"❌ Error en GeminiService: {e}")
