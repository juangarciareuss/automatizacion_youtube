from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum

# 1. Enums (Mantenemos tus Enums y agregamos VERTEX)
class VisualStyle(str, Enum):
    LUXURY_MINIMAL = "luxury_minimal"
    DARK_DOCUMENTARY = "dark_documentary"
    VIBRANT_POP = "vibrant_pop"
    CINEMATIC = "cinematic"

class VideoOrientation(str, Enum):
    PORTRAIT = "portrait"   # Shorts/Reels (9:16)
    LANDSCAPE = "landscape" # YouTube Standard (16:9)
    SQUARE = "square"       # LinkedIn/Insta Feed (1:1)

class AssetSource(str, Enum):
    PEXELS = "pexels"
    PIXABAY = "pixabay"
    GOOGLE_IMAGES = "google_images" 
    AI_GENERATED = "ai_generated" 
    VERTEX_AI = "vertex_ai" # <--- NUEVO: Para distinguir explícitamente Google Cloud

# 2. La Escena (El corazón del cambio)
class Scene(BaseModel):
    id: int = Field(..., description="Número secuencial de la escena")
    
    # CAMBIO 1: Renombramos/Aliamos para compatibilidad
    # Tu lo llamabas narrative_text, Gemini suele devolver narration. 
    # Al ponerlo así, mantenemos tu nombre pero somos flexibles.
    narration: str = Field(..., alias="narrative_text", description="Lo que dirá la voz en off")

    # CAMBIO 2: El campo híbrido
    # 'visual_search_term' es bueno para Pexels (palabras clave)
    # 'visual_description' es necesario para Vertex (prompt detallado)
    visual_search_term: Optional[str] = Field(None, description="Keywords cortas para buscadores clásicos")
    
    # --- EL CAMBIO CRÍTICO QUE ARREGLA EL BUG ---
    visual_description: str = Field(..., description="Prompt detallado y cinemático para la IA Generativa")
    
    # Instrucciones visuales
    visual_source: AssetSource = Field(default=AssetSource.VERTEX_AI, description="Fuente del asset")

    # Instrucciones para el VideoEngine (Hacemos opcionales para que no rompa si Gemini olvida uno)
    duration_estimate: Optional[float] = Field(default=5.0, description="Duración estimada")
    transition_effect: Optional[str] = Field(default="crossfade", description="Efecto de transición")
    overlay_text: Optional[str] = None

    class Config:
        populate_by_name = True # Permite usar 'narration' o 'narrative_text' indistintamente

# 3. El Guion Maestro
class VideoScript(BaseModel):
    title: str
    
    # Hacemos opcionales estos campos para que el script de prueba rápida no falle 
    # si Gemini no inventa los tags en la primera pasada.
    description_youtube: Optional[str] = Field(default="", description="Descripción SEO")
    tags: List[str] = Field(default_factory=list)
    
    orientation: VideoOrientation = VideoOrientation.PORTRAIT
    scenes: List[Scene]
    
    bg_music_keywords: Optional[str] = Field(default="luxury ambient", description="Música de fondo")
    voice_speed_factor: float = Field(default=1.0)