from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from enum import Enum

# --- 1. ENUMS (El vocabulario) ---
class VisualStyle(str, Enum):
    LUXURY_MINIMAL = "luxury_minimal"
    DARK_DOCUMENTARY = "dark_documentary"
    VIBRANT_POP = "vibrant_pop"
    CINEMATIC = "cinematic"
    FOOD_PORN_MACRO = "food_porn_macro" 

class VideoOrientation(str, Enum):
    PORTRAIT = "portrait"   # 9:16
    LANDSCAPE = "landscape" # 16:9 
    SQUARE = "square"       # 1:1

class AssetSource(str, Enum):
    VERTEX_AI = "vertex_ai"
    STOCK = "stock"
    LOCAL = "local_file"

# --- 2. LA BIBLIA VISUAL (LA CLAVE DE LA CONSISTENCIA) ---
class VisualBible(BaseModel):
    """
    Define el entorno inmutable y las herramientas disponibles.
    Vertex AI usará esto como 'System Prompt' para cada imagen.
    """
    prop_inventory: str = Field(..., description="Inventario estricto de utensilios a usar. Ej: '1. Blue plastic mixing bowl. 2. Black cast-iron skillet.' NO describir comida aquí.")
    surface: str = Field(..., description="La superficie donde ocurre todo. Ej: 'A polished white Carrara marble countertop'")
    lighting: str = Field(..., description="El esquema de luz. Ej: 'Hard sunlight casting sharp shadows from the right side'")
    background: str = Field(..., description="El fondo desenfocado. Ej: 'Blurred tropical patio with palm leaves'")
    color_palette: str = Field(..., description="Colores dominantes. Ej: 'Mint green, ice white, and lime yellow'")
# --- 3. LA ESCENA INTELIGENTE ---
class VideoScene(BaseModel):
    id: int = Field(..., description="Orden secuencial")
    
    # Texto
    narrative_text: str = Field(..., description="Guion que leerá la IA")
    
    # 🟢 NUEVO: Control de tiempo ASMR / Silencio Visual
    asmr_pause: float = Field(default=0.0, description="Segundos de silencio al final de la narración para apreciar el hiperrealismo visual o ASMR.")
    
    # Imagen: Ahora solo describe la ACCIÓN. El objeto viene de la Biblia.
    action_prompt: str = Field(..., description="Solo la acción. Ej: 'Pouring rum into the glass'. NO describir el vaso aquí.")
    
    # Adaptabilidad
    is_essential: bool = Field(default=True)
    
    # Contexto Visual (Memoria de estado)
    output_state: Optional[str] = Field(None, description="Estado del objeto. Ej: 'Glass is half full'")
    
    # Configuración Técnica
    visual_source: AssetSource = Field(default=AssetSource.VERTEX_AI)
    duration_estimate: float = Field(default=3.0)
    
    # Post-producción
    audio_path: Optional[str] = None
    image_path: Optional[str] = None

# --- 4. EL GUION MAESTRO ---
class VideoScript(BaseModel):
    title: str
    orientation: VideoOrientation = Field(default=VideoOrientation.LANDSCAPE)
    
    # 🟢 AQUÍ ESTÁ LA MAGIA: La Biblia Visual Global
    visual_bible: VisualBible = Field(..., description="Definición estricta de objetos persistentes")
    
    scenes: List[VideoScene]
    
    # Audio
    bg_music_keywords: str = Field(default="lofi cooking jazz")
    voice_speed_factor: float = Field(default=1.0)