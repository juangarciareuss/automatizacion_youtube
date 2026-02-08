import os
import sys
import asyncio
import argparse
import traceback
import time

# --- 1. PARCHE PARA WINDOWS (Evita errores de Loop) ---
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# --- 2. CARGADOR MANUAL DE VARIABLES (.env) ---
def cargar_env_manual():
    env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
    if os.path.exists(env_path):
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'): continue
                if '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip().strip('"').strip("'")
    else:
        print("⚠️ ADVERTENCIA: No se encontró el archivo .env")

cargar_env_manual()

# --- IMPORTACIÓN DE SERVICIOS ---
from app.services.brain.gemini_service import GeminiService
from app.services.visuals.vertex_generator import VertexGenerator
from app.services.audio.tts_service import TTSService, run_tts_sync
from app.services.editing.video_engine import VideoEngine
from app.services.image.thumbnail_service import ThumbnailService
from app.domain.models import AssetSource
from app.domain.channel_config import CHANNELS
from app.utils.logger import get_logger

logger = get_logger("MAIN_FACTORY")

# --- FUNCIÓN PRINCIPAL ---
def run_simulation(topic_input=None, channel_id="perfect_recipe"): # <--- POR DEFECTO: COCINA
    
    # Validación básica de credenciales
    if not os.getenv("GEMINI_API_KEY"):
        logger.error("❌ FALTA LA API KEY. Verifica tu archivo .env")
        return None

    # 1. SELECCIÓN DINÁMICA DE CANAL
    if channel_id not in CHANNELS:
        logger.error(f"❌ Canal '{channel_id}' no existe en CHANNELS. Opciones: {list(CHANNELS.keys())}")
        return None
    
    current_channel = CHANNELS[channel_id]
    
    logger.info("="*60)
    logger.info(f"🏭 INICIANDO PRODUCCIÓN: {current_channel.name}")
    logger.info(f"🎭 Persona: {current_channel.prompt_persona}") 
    logger.info(f"📱 Formato: {current_channel.orientation.value}")
    logger.info("="*60)

    # 2. INICIALIZAR SERVICIOS (Inyección de Dependencias)
    try:
        # A. CEREBRO: Configura la personalidad (Chef vs Historiador)
        brain = GeminiService(persona=current_channel.prompt_persona) 
        
        # B. OJOS: Configura el estilo visual (Food Porn vs Luxury)
        eyes = VertexGenerator(
            download_path="output/temp_assets", 
            style_modifier=current_channel.visual_style
        )
        
        # C. BOCA: Configura la voz específica del canal
        mouth = TTSService(download_path="output/temp_audio")
        mouth.voice = current_channel.voice_name 
        logger.info(f"🗣️ Voz configurada: {current_channel.voice_name}")

        # D. EDITOR: Recibe la configuración completa (fuentes, música, logos)
        editor = VideoEngine(config=current_channel, output_path="output/final_videos")
        
        # E. MINIATURAS
        thumb_maker = ThumbnailService(output_path="output/thumbnails")
        
    except Exception as e:
        logger.error(f"❌ Error inicializando servicios: {e}")
        return None

    # 3. GENERAR GUION
    # Si no hay input, usamos el tema de prueba predeterminado
    topic = topic_input if topic_input else "The Ultimate Truffle Smash Burger"
    
    logger.info(f"🧠 Cerebro cocinando guion sobre: {topic}...")
    
    try:
        # Generamos el guion estructurado
        script = brain.generate_script(topic=topic)
        logger.info(f"✅ Guion generado: '{script.title}'")
        
        # Log de depuración para verificar la MEMORIA VISUAL
        logger.info("🔍 Revisión de Consistencia Visual (Output State):")
        for s in script.scenes:
            state = s.output_state if s.output_state else "[(Sin memoria)]"
            logger.info(f"   Scene {s.id}: {s.narrative_text[:30]}... -> MEMORIA: {state}")

        # Forzamos que la fuente visual sea Vertex AI
        for scene in script.scenes:
            scene.visual_source = AssetSource.VERTEX_AI

        # 4. GENERAR ASSETS VISUALES (Con Memoria de Continuidad)
        logger.info("🎨 Vertex AI encendiendo hornos (Generando Assets)...")
        assets_map = eyes.fetch_assets(script.scenes)
        
        # 5. GENERAR AUDIO
        logger.info("🎙️ Grabando voz en off...")
        audio_map = run_tts_sync(mouth, script.scenes)

        # 6. MONTAJE Y RENDERIZADO (CON BLINDAJE ANTI-CRASH Y VEO)
        
        # --- AIRBAG DE SEGURIDAD ---
        if assets_map is None: 
            assets_map = {}
            logger.warning("⚠️ Vertex devolvió None (Revisa fetch_assets)")
        if audio_map is None: 
            audio_map = {}
            logger.warning("⚠️ TTS devolvió None (Revisa run_tts_sync)")
        
        # ==============================================================================
        # 🚀 FASE PREMIUM: LA LÓGICA "SPOILER" (Escena 15 -> Escena 1)
        # ==============================================================================
        # LÓGICA: La Escena 15 es el resultado real acumulado.
        # Por tanto, tomamos la imagen final (15), la animamos, y esa animación
        # se convierte en nuestra Intro (1).
        
        # 1. Encontramos la última escena (El plato terminado real)
        if script.scenes:
            last_scene_id = max([s.id for s in script.scenes]) # Típicamente 15
            
            if last_scene_id in assets_map and os.path.exists(assets_map[last_scene_id]):
                logger.info(f"🌟 Detectado Final Real (Escena {last_scene_id}). Preparando animación Veo...")
                
                final_video_path = None
                try:
                    # Import dinámico para evitar crash si falta el archivo
                    from app.services.visuals.video_generator import VideoGenerator
                    veo = VideoGenerator()
                    
                    veo_prompt = (
                        "Slow cinematic pan, orbiting shot, volumetric steam rising from hot food, "
                        "glistening texture, professional food commercial, 4k, high detail"
                    )
                    
                    # A. ANIMAMOS la imagen de la ESCENA 15
                    # Nota: Esto tomará 60-90 segundos. No cierres la consola.
                    final_video_path = veo.animate_image(
                        image_path=assets_map[last_scene_id],
                        prompt=veo_prompt,
                        output_filename=f"veo_final_dish_{int(time.time())}.mp4"
                    )
                except ImportError:
                    logger.warning("⚠️ No VideoGenerator found. Usando imagen estática.")
                except Exception as e:
                    logger.error(f"❌ ERROR CRÍTICO VEO: {e}")
                    traceback.print_exc()

                # B. CLONACIÓN HACIA ATRÁS (El resultado se convierte en la Intro)
                if final_video_path and os.path.exists(final_video_path):
                    # ÉXITO: El video va al final y al principio
                    assets_map[last_scene_id] = final_video_path
                    assets_map[1] = final_video_path
                    logger.info(f"✅ ¡CÍRCULO CERRADO! Video de Escena {last_scene_id} copiado a Escena 1 (Intro).")
                else:
                    # FALLO (o no animado): Copiamos la IMAGEN estática de la 15 a la 1
                    # Esto asegura que al menos la foto sea la correcta y no carne cruda
                    assets_map[1] = assets_map[last_scene_id]
                    logger.info(f"⚠️ Veo falló o no se activó. Imagen estática de Escena {last_scene_id} copiada a Escena 1.")

        # ==============================================================================

        if len(assets_map) > 0 and len(audio_map) > 0:
            logger.info("🎬 Iniciando VideoEngine (Montaje + SFX + Branding)...")
            video_path = editor.assemble_video(script, assets_map, audio_map)
            
            if video_path:
                # 7. EXTRAS (Miniatura)
                logger.info("🖼️ Creando Miniatura...")
                try:
                    # Usamos la primera parte del título como gancho
                    hook_text = script.title.split(":")[0][:20] 
                    thumb_path = thumb_maker.generate_thumbnail(topic, hook_text)
                except Exception as e:
                    logger.warning(f"⚠️ Miniatura falló (no crítico): {e}")

                logger.info("="*60)
                logger.info(f"🎉 ¡ORDER UP! VIDEO LISTO: {current_channel.name}")
                logger.info(f"📂 Archivo: {video_path}")
                logger.info("="*60)
                return video_path
        else:
            logger.warning("🛑 PRODUCCIÓN DETENIDA POR FALTA DE MATERIALES:")
            logger.warning(f"   - Imágenes válidas: {len(assets_map)}")
            logger.warning(f"   - Audios válidos: {len(audio_map)}")
            return None

    except Exception as e:
        logger.error(f"❌ FALLA CRÍTICA EN PROCESO: {e}")
        traceback.print_exc()
        return None

if __name__ == "__main__":
    # --- INTERFAZ DE COMANDO (CLI) MEJORADA ---
    parser = argparse.ArgumentParser(description="La Fábrica de Contenido AI")
    
    # Argumento 1: El tema (Ahora es opcional, si no está, preguntamos)
    parser.add_argument("topic", nargs="?", help="Nombre de la receta o tema del video")
    
    # Argumento 2: El canal (Por defecto cocina)
    parser.add_argument("--channel", default="perfect_recipe", help="ID del canal (ej: perfect_recipe)")
    
    args = parser.parse_args()
    
    # --- LÓGICA DE ENTRADA ---
    topic_to_cook = args.topic
    
    # Si el usuario NO escribió nada al ejecutar, le preguntamos por consola
    if not topic_to_cook:
        print("\n" + "🍳"*30)
        print("   BISTRO AI - SISTEMA DE PEDIDOS")
        print("🍳"*30 + "\n")
        try:
            topic_to_cook = input("👉 ¿Qué receta quieres cocinar hoy? (ej. Crispy Pork Ramen): ").strip()
        except KeyboardInterrupt:
            print("\n👋 Operación cancelada.")
            sys.exit()

    # Si después de preguntar sigue vacío, cancelamos
    if not topic_to_cook:
        print("❌ Error: Necesito un nombre de receta para empezar.")
    else:
        # ¡A COCINAR!
        run_simulation(topic_input=topic_to_cook, channel_id=args.channel)

def save_production_report(script, assets_map, video_path):
    """
    Guarda un registro detallado para análisis humano y FUTURO ENTRENAMIENTO DE IA.
    """
    report_data = {
        "video_title": script.title,
        "timestamp": time.ctime(),
        "model_used": "vertex-imagen-3", # O el que estés usando
        "scenes": []
    }

    # Recopilamos datos de cada escena
    for scene in script.scenes:
        scene_data = {
            "id": scene.id,
            "narrative": scene.narrative_text,
            "prompt_used": scene.image_prompt,  # <--- ORO PURO PARA ENTRENAR
            "image_path": assets_map.get(scene.id, "MISSING"),
            "context_state": scene.output_state
        }
        report_data["scenes"].append(scene_data)

    # 1. Guardamos como JSON (Para que tu futura IA lo lea)
    json_path = video_path.replace(".mp4", "_training_data.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(report_data, f, indent=4, ensure_ascii=False)

    # 2. Guardamos como Markdown (Para que TÚ lo leas fácil)
    md_path = video_path.replace(".mp4", "_analisis.md")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(f"# Reporte: {script.title}\n\n")
        for s in report_data["scenes"]:
            f.write(f"## Escena {s['id']}\n")
            f.write(f"**Narración:** {s['narrative']}\n")
            f.write(f"**Prompt IA:** `{s['prompt_used']}`\n")
            f.write(f"**Archivo:** {s['image_path']}\n")
            f.write("---\n")

    logger.info(f"💾 Datos de entrenamiento guardados en: {json_path}")