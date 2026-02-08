from dataclasses import dataclass
from typing import Optional
from app.domain.models import VideoOrientation

@dataclass
class ChannelConfig:
    # --- Identidad Básica ---
    name: str             # Nombre interno
    theme_name: str       # Referencia a themes.py (colores, fuentes)
    
    # --- Assets (Archivos) ---
    music_mood: str       # Carpeta en assets/music/
    voice_name: str       # Voz de Edge TTS
    intro_file: str | None       
    outro_file: str | None      
    watermark_file: str   
    subscribe_file: str   

    # --- Cerebro & Estrategia (Control de la IA) ---
    prompt_persona: str   # 'business_historian' o 'master_chef'
    visual_style: str     # El prompt descriptivo REAL para Vertex
    
    # --- Formato Técnico (CRÍTICO PARA QUE FUNCIONE) ---
    orientation: VideoOrientation 
    
    # --- Switches de Formato ---
    generate_shorts: bool = False 
    generate_ebook: bool = False
    
    # --- Branding Dinámico ---
    font_path: str | None = None 
    outro_text: str | None = None

# --- BASE DE DATOS DE TUS CANALES ---
CHANNELS = {

    # CANAL 1: EL ACTUAL (Silent Billionaires)
    "luxury_main": ChannelConfig(
        name="Silent Billionaires",
        theme_name="luxury",
        music_mood="tension", 
        voice_name="en-US-ChristopherNeural",
        
        # Assets estáticos
        intro_file="assets/branding/intro.mp4", 
        outro_file="assets/branding/outro.mp4",
        watermark_file="logo.png",
        subscribe_file="subscribe.png",
        
        # IA Config
        prompt_persona="business_historian", 
        # Prompt largo para Vertex:
        visual_style="Award-winning documentary photography, cinematic lighting, 8k, hyper-realistic, dark moody tones",
        
        # Formato
        orientation=VideoOrientation.LANDSCAPE, # 16:9
        generate_shorts=False,               
        generate_ebook=False
    ),
    
    # CANAL 2: EL NUEVO (The Perfect Recipe)
    "perfect_recipe": ChannelConfig(
        name="The Perfect Recipe",
        theme_name="fresh_kitchen",          
        music_mood="lofi_cooking",           
        voice_name="en-US-AriaNeural",       
        
        # Intro/Outro son None para que el BrandingManager las genere dinámicamente
        intro_file=None, 
        outro_file=None,
        watermark_file="chef_logo.png",
        subscribe_file="subscribe_food.png",
        
        # IA Config
        prompt_persona="master_chef",        
        # Prompt largo para Vertex (Vital para el Food Porn):
        visual_style="Food Porn aesthetic, Macro 100mm lens, f/1.8, bokeh, volumetric steam, glistening textures, professional studio lighting",
        
        # Formato
        orientation=VideoOrientation.PORTRAIT, # 9:16 (Shorts)
        generate_shorts=True,                
        generate_ebook=True,
        
        # Configuración de Branding Dinámico
        font_path="assets/fonts/PlayfairDisplay.ttf", 
        outro_text="Subscribe for more perfect recipes."
    )
}