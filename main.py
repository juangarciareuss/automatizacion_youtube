import os
import sys
import asyncio

# --- 1. PARCHE PARA WINDOWS (CRÍTICO PARA AUDIO) ---
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# --- 2. CARGADOR MANUAL DE VARIABLES DE ENTORNO (.ENV) ---
# Esto reemplaza a 'from dotenv import load_dotenv' para no obligarte a instalar librerías extra.
def cargar_env_manual():
    # Busca el archivo .env en la misma carpeta que este script
    env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
    
    if os.path.exists(env_path):
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                # Ignorar líneas vacías o comentarios
                if not line or line.startswith('#'):
                    continue
                # Separar CLAVE=VALOR
                if '=' in line:
                    key, value = line.split('=', 1)
                    # Limpiar comillas y espacios, y guardar en el sistema
                    os.environ[key.strip()] = value.strip().strip('"').strip("'")
    else:
        print("⚠️ ADVERTENCIA: No se encontró el archivo .env en la carpeta raíz.")

# Ejecutamos la carga manual inmediatamente
cargar_env_manual()
# ---------------------------------------------------------

# Servicios Base
from app.services.brain.gemini_service import GeminiService
from app.services.visuals.vertex_generator import VertexGenerator
from app.services.audio.tts_service import TTSService, run_tts_sync
from app.services.editing.video_engine import VideoEngine

# Nuevos Servicios (Hitos 5 y 6)
from app.services.image.thumbnail_service import ThumbnailService
from app.domain.models import AssetSource
from app.domain.channel_config import CHANNELS 
from app.utils.logger import get_logger

logger = get_logger("MAIN_FACTORY")

def run_simulation(topic_input=None, voice_name="en-US-ChristopherNeural"):
    if not os.getenv("GEMINI_API_KEY"):
        logger.error("❌ FALTA LA API KEY. Verifica que el archivo .env esté en la carpeta silent_factory.")
        return None

    # 1. SELECCIÓN DE CANAL
    current_channel = CHANNELS["luxury_main"]
    
    logger.info(f"🏭 INICIANDO PRODUCCIÓN: {current_channel.name}")

    # 2. Inicializar Servicios
    try:
        brain = GeminiService()
        eyes = VertexGenerator(download_path="output/temp_assets")
        mouth = TTSService(download_path="output/temp_audio")
        
        if voice_name:
            mouth.voice = voice_name
            logger.info(f"🗣️ Voz configurada: {voice_name}")

        # EL EDITOR AHORA RECIBE LA CONFIGURACIÓN DEL CANAL
        editor = VideoEngine(config=current_channel, output_path="output/final_videos")
        
        # INICIALIZAMOS EL CREADOR DE MINIATURAS
        thumb_maker = ThumbnailService(output_path="output/thumbnails")
        
    except Exception as e:
        logger.error(f"❌ Error inicializando servicios: {e}")
        return None

    # 3. Generar Guion
    # --- CAMBIO PARA DJANGO: Usar input si existe, si no, usar fallback ---
    topic = topic_input if topic_input else "The Rise of the Rothschild Family: Money and Power"
    
    logger.info(f"🧠 Cerebro activado: {topic}...")
    
    try:
        script = brain.generate_script(topic=topic)
        logger.info(f"✅ Guion: '{script.title}'")

        # Forzar uso de Vertex AI
        for scene in script.scenes:
            scene.visual_source = AssetSource.VERTEX_AI

        # 4. Generar Assets Visuales
        logger.info("🎨 Generando arte con Vertex AI...")
        assets_map = eyes.fetch_assets(script.scenes)
        
        # 5. Generar Audio (Voz limpia de SFX)
        logger.info("🎙️ Grabando voces...")
        audio_map = run_tts_sync(mouth, script.scenes)

        # 6. MONTAJE Y BRANDING
        if len(assets_map) > 0 and len(audio_map) > 0:
            logger.info("🎬 Iniciando VideoEngine (Montaje + SFX + Branding)...")
            video_path = editor.assemble_video(script, assets_map, audio_map)
            
            if video_path:
                # 7. GENERACIÓN DE MINIATURA
                logger.info("🖼️ Creando Miniatura Clickbait...")
                # Usamos la primera parte del título como gancho
                hook_text = script.title.split(":")[0] 
                thumb_path = thumb_maker.generate_thumbnail(topic, hook_text)

                logger.info("="*50)
                logger.info(f"🎉 ¡PRODUCCIÓN FINALIZADA CON ÉXITO!")
                logger.info(f"📺 Video Master: {video_path}")
                logger.info(f"🖼️ Thumbnail:   {thumb_path}")
                logger.info("="*50)
                
                # --- CAMBIO PARA DJANGO: Retornar la ruta del archivo ---
                return video_path
        else:
            logger.warning("⚠️ Faltan materiales (Audio o Video).")
            return None

    except Exception as e:
        logger.error(f"❌ FALLA CRÍTICA EN PRODUCCIÓN: {e}")
        # Tip de debug
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    # Permite ejecutarlo desde consola sin argumentos como antes
    run_simulation()