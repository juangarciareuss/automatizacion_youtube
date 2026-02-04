from dataclasses import dataclass

@dataclass
class ChannelConfig:
    name: str             # Nombre interno para logs (Ej: "Empire of Wealth")
    theme_name: str       # Debe coincidir con un tema en themes.py (Ej: "luxury")
    music_mood: str       # Nombre de la carpeta en assets/music/ (Ej: "luxury")
    voice_name: str       # Voz de Edge TTS (Ej: "en-US-ChristopherNeural")
    
    # Nombres EXACTOS de los archivos en assets/branding/
    intro_file: str       
    outro_file: str       
    watermark_file: str   
    subscribe_file: str   

# --- BASE DE DATOS DE TUS CANALES ---
CHANNELS = {


"luxury_main": ChannelConfig(
        name="Silent Billionaires",  # <--- ACTUALIZA ESTO
        theme_name="luxury",
        music_mood="luxury",
        voice_name="en-US-ChristopherNeural", # Voz profunda tipo documental
        intro_file="intro.mp4",
        outro_file="outro.mp4",
        watermark_file="logo.png", # Asegúrate de que exista o comenta esta línea si no tienes logo aún
        subscribe_file=""
    ),
    
    # 2. EJEMPLO FUTURO: CANAL DE TECNOLOGÍA
    # "tech_channel": ChannelConfig(
    #     name="Future Tech",
    #     theme_name="modern_tech",   # Tendrías que crear este tema
    #     music_mood="cyberpunk",     # Tendrías que crear carpeta assets/music/cyberpunk
    #     voice_name="en-US-RogerNeural",
    #     intro_file="intro_tech.mp4",
    #     outro_file="outro_tech.mp4",
    #     watermark_file="logo_tech.png",
    #     subscribe_file="subscribe.png"
    # )
}   