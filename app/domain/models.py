from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum

# 1. Enums (Mantenemos tus estilos avanzados)
class VisualStyle(str, Enum):
    LUXURY_MINIMAL = "luxury_minimal"
    DARK_DOCUMENTARY = "dark_documentary"
    VIBRANT_POP = "vibrant_pop"
    CINEMATIC = "cinematic"
    FOOD_PORN_MACRO = "food_porn_macro" 

class VideoOrientation(str, Enum):
    PORTRAIT = "portrait"   # Shorts/Reels (9:16)
    LANDSCAPE = "landscape" # YouTube Standard (16:9)
    SQUARE = "square"       # LinkedIn/Insta Feed (1:1)

class AssetSource(str, Enum):
    PEXELS = "pexels"
    PIXABAY = "pixabay"
    GOOGLE_IMAGES = "google_images" 
    AI_GENERATED = "ai_generated" 
    VERTEX_AI = "vertex_ai" 
    YOUTUBE_CC = "youtube_cc" # Agregado por compatibilidad

# 2. La Escena (CORREGIDA: Eliminamos alias para evitar confusiones)
class Scene(BaseModel):
    id: int = Field(..., description="Número secuencial de la escena")
    
    # --- CORRECCIÓN 1: Nombre directo ---
    # Antes: narration (alias="narrative_text")
    # Ahora: narrative_text (nombre real, compatible con main.py)
    narrative_text: str = Field(..., description="Lo que dirá la voz en off")

    # --- CORRECCIÓN 2: Nombre directo ---
    # Antes: visual_description (alias="image_prompt")
    # Ahora: image_prompt (nombre real, compatible con main.py)
    image_prompt: str = Field(..., description="Prompt detallado para Vertex AI")
    
    # --- CAMPOS OPCIONALES ---
    visual_search_term: Optional[str] = Field(None, description="Keywords para stock")
    
    # El cerebro de la consistencia
    output_state: Optional[str] = Field(None, description="Estado visual de los objetos al terminar la acción")
    
    # Configuración Técnica
    visual_source: AssetSource = Field(default=AssetSource.VERTEX_AI, description="Fuente del asset")
    duration_estimate: Optional[float] = Field(default=3.0, description="Duración estimada")
    transition_effect: Optional[str] = Field(default="crossfade", description="Efecto de transición")
    overlay_text: Optional[str] = None

    class Config:
        populate_by_name = True

# 3. El Guion Maestro
class VideoScript(BaseModel):
    title: str
    
    description_youtube: Optional[str] = Field(default="", description="Descripción SEO")
    tags: List[str] = Field(default_factory=list)
    
    orientation: VideoOrientation = VideoOrientation.PORTRAIT
    scenes: List[Scene]
    
    bg_music_keywords: Optional[str] = Field(default="lofi hip hop beat, relaxing cooking", description="Música de fondo")
    voice_speed_factor: float = Field(default=1.1, description="Velocidad de voz (1.1 es bueno para Shorts)")