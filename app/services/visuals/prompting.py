"""
ARCHIVO: app/services/visuals/prompting.py
"""

from app.domain.models import VideoOrientation

class PromptArchitect:
    @staticmethod
    def construct_super_prompt(scene, script):
        """
        🧬 FUSIÓN NUCLEAR (VERSIÓN AISLADA): Une la Acción de la escena con la Biblia Visual.
        Garantiza la coherencia del entorno SIN contaminar el estado de la comida (cruda vs cocida).
        """
        bible = script.visual_bible
        raw_action = scene.action_prompt
        
        # 1. INYECCIÓN DE DEPENDENCIAS (Superficie)
        # Reemplazamos el token de superficie si Gemini lo usó explícitamente.
        if "[SURFACE]" in raw_action:
            raw_action = raw_action.replace("[SURFACE]", bible.surface)

        # 🟢 ELIMINADO: La inyección forzada de 'hero_object'.
        # Ahora Vertex solo dibujará lo que Gemini dictamine en 'raw_action', 
        # respetando la línea de tiempo de la receta.

        # 2. ENSAMBLAJE DEL SUPER PROMPT
        # Estructura: [ESTILO] + [ACCIÓN ESTRICTA] + [ENTORNO] + [LUZ] + [PALETA] + [NEGATIVO]
        # Nota: No inyectamos el prop_inventory completo aquí para evitar que Vertex dibuje
        # todas las herramientas flotando en el fondo. Gemini ya menciona la herramienta
        # necesaria dentro del raw_action.
        super_prompt = (
            f"Commercial food photography, 8k, hyper-realistic, highly detailed texture. "
            f"SCENE ACTION: {raw_action}. "
            f"ENVIRONMENT CONTEXT: Surface is {bible.surface}. Background is {bible.background}. "
            f"LIGHTING: {bible.lighting}. "
            f"COLORS: {bible.color_palette}. "
            f"Exclude: text, watermark, human face, distorted hands, floating tools, extra knives, dirty cloth, blur, cartoon, illustration, finished food in background if not in action."
        )
        
        # 3. AJUSTE TÉCNICO DE CÁMARA
        if script.orientation == VideoOrientation.PORTRAIT:
            super_prompt += " Vertical composition 9:16, centered subject."
        else:
            super_prompt += " Wide composition 16:9."
        
        return super_prompt