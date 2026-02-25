"""
ARCHIVO: app/core/factory_manager.py

DESCRIPCIÓN Y FUNCIONALIDAD:
Este documento es el 'Director de Fábrica' u Orquestador Principal. No ejecuta la lógica 
profunda de generación, sino que coordina a los distintos especialistas en un orden estricto.

NUEVA ARQUITECTURA (Audio-Driven Sub-Chaining):
1. FASE 3 (La Voz Manda): Se genera el Audio primero para conocer su duración exacta.
2. FASE 4 (Cálculo Matemático): Se calcula cuántos fragmentos de video (5s) se necesitan 
   para cubrir (Audio + Pausa ASMR).
3. Sub-Encadenamiento: Vertex y Grok entran en un bucle anidado, editando el último frame 
   del fragmento anterior hasta cumplir el tiempo requerido.
"""

import os
import sys
import shutil
import traceback
import math # 🟢 NUEVO: Para redondear los cálculos de tiempo
from moviepy.editor import AudioFileClip # 🟢 NUEVO: Para medir los audios

from app.services.brain.gemini_service import GeminiService
from app.services.visuals.vertex_generator import VertexGenerator
from app.services.audio.tts_service import TTSService, run_tts_sync
from app.services.video.engine import VideoEngine 
from app.services.image.thumbnail_service import ThumbnailService
from app.services.video.grok_api import GrokVideoGenerator 
from app.core.reporter import ReportGenerator
from app.utils.frame_extractor import FrameExtractor
from app.domain.channel_config import CHANNELS
from app.domain.models import AssetSource, VideoOrientation 
from app.utils.logger import get_logger

logger = get_logger("FACTORY_MANAGER")

class FactoryManager:
    
    def __init__(self):
        self.GROK_CLIP_DURATION = 5.0 # Segundos que genera Grok por llamada

    def _validate_assets_structure(self, config):
        music_path = f"assets/music/{config.music_mood}"
        os.makedirs(music_path, exist_ok=True)
        
        if not os.listdir(music_path):
            root_music = "assets/music"
            if os.path.exists(root_music):
                for f in os.listdir(root_music):
                    if f.endswith(".mp3"):
                        shutil.copy(os.path.join(root_music, f), os.path.join(music_path, f))
                        break
        
        os.makedirs("assets/branding", exist_ok=True)
        os.makedirs("output/thumbnails", exist_ok=True)
        os.makedirs("output/final_videos", exist_ok=True)
        os.makedirs("output/temp_assets", exist_ok=True)

    def produce_video(self, topic: str, channel_id: str, orientation_mode: str, draft_mode: bool = False):
        
        # --- PREPARACIÓN DEL ENTORNO ---
        if channel_id not in CHANNELS:
            logger.error(f"❌ Canal '{channel_id}' no encontrado.")
            return None
        
        current_channel = CHANNELS[channel_id]
        
        if orientation_mode == "short":
            current_channel.orientation = VideoOrientation.PORTRAIT
            logger.info("📱 MODO: SHORT (Vertical 9:16)")
        else:
            current_channel.orientation = VideoOrientation.LANDSCAPE
            logger.info("📺 MODO: LONG (Horizontal 16:9)")

        self._validate_assets_structure(current_channel)
        
        logger.info("="*60)
        mode_label = "⚡ DRAFT (Imágenes Estáticas)" if draft_mode else "🐢 PRO (Audio-Driven Visual Chaining)"
        logger.info(f"🏭 BISTRO AI STARTING: {current_channel.name} | {mode_label}")
        logger.info("="*60)

        # --- FASE 1: INSTANCIAR HERRAMIENTAS ---
        try:
            brain = GeminiService() 
            eyes = VertexGenerator(download_path="output/temp_assets")
            mouth = TTSService(download_path="output/temp_audio")
            mouth.voice = current_channel.voice_name
            animator = GrokVideoGenerator()
            editor = VideoEngine(config=current_channel, output_path="output/final_videos", draft_mode=draft_mode)
            thumb_maker = ThumbnailService(output_path="output/thumbnails")
        except Exception as e:
            logger.error(f"❌ Error conectando herramientas: {e}")
            return None

        # --- FASE 2: EL CEREBRO (Guion) ---
        logger.info(f"🧠 Diseñando receta para: {topic}...")
        try:
            script = brain.generate_script(topic=topic, orientation=current_channel.orientation)
            for s in script.scenes: s.visual_source = AssetSource.VERTEX_AI
            logger.info(f"✅ Guion listo: '{script.title}' ({len(script.scenes)} escenas)")
        except Exception as e:
            logger.error(f"❌ Error en escritura de guion: {e}")
            return None

        # --- 🟢 NUEVA FASE 3: LA VOZ (Generación y Medición de Audio) ---
        logger.info("\n🎙️ Grabando narración (Master Clock)...")
        audio_map = run_tts_sync(mouth, script.scenes)

        if not audio_map:
            logger.error("❌ Falló la generación de audio. Abortando.")
            return None

        # --- 🟢 NUEVA FASE 4: PRODUCCIÓN VISUAL SUB-ENCADENADA ---
        logger.info("\n🔗 Iniciando Producción Visual basada en Audio...")
        final_assets_map = {} # Ahora guardará una LISTA de videos por escena
        last_generated_video = None

        for index, scene in enumerate(script.scenes):
            logger.info(f"\n--- PROCESANDO ESCENA {scene.id} ---")
            
            # A. Medir Audio + ASMR
            audio_path = audio_map.get(scene.id)
            audio_duration = 0.0
            if audio_path and os.path.exists(audio_path):
                clip = AudioFileClip(audio_path)
                audio_duration = clip.duration
                clip.close()
            
            total_required_time = audio_duration + scene.asmr_pause
            
            if draft_mode:
                loops_needed = 1
                logger.info(f"⏱️ DRAFT: Se requiere 1 imagen estática.")
            else:
                loops_needed = math.ceil(total_required_time / self.GROK_CLIP_DURATION)
                # Seguridad: Si el audio dura 0.5s, mínimo necesitamos 1 loop
                loops_needed = max(1, loops_needed) 
                logger.info(f"⏱️ Audio ({audio_duration:.1f}s) + ASMR ({scene.asmr_pause}s) = {total_required_time:.1f}s")
                logger.info(f"🔢 Iteraciones Grok requeridas: {loops_needed}")

            scene_videos = [] # Colección de sub-fragmentos

            # B. Bucle de Sub-Encadenamiento
            for step in range(loops_needed):
                if not draft_mode:
                    logger.info(f"   🔄 Sub-fragmento {step+1}/{loops_needed}")
                
                imagen_base_path = None

                # MODO DRAFT
                if draft_mode:
                    logger.info(f"🎨 [Vertex] Generando imagen estática...")
                    imagen_base_path = eyes.generate_scene(scene, script, current_channel.orientation)
                    if imagen_base_path:
                        scene_videos.append(imagen_base_path)
                    continue

                # MODO PRO: FLUJO ENCADENADO
                if index == 0 and step == 0:
                    logger.info(f"🎨 [Vertex] Generando imagen génesis (Text-to-Image)...")
                    imagen_base_path = eyes.generate_scene(scene, script, current_channel.orientation)
                else:
                    logger.info("   🎞️ [Extractor] Capturando estado del video anterior...")
                    output_frame_path = os.path.join("output", "temp_assets", f"base_scene_{scene.id}_step_{step}.png")
                    
                    if last_generated_video and os.path.exists(last_generated_video):
                        extracted_frame = FrameExtractor.extract_last_frame(last_generated_video, output_frame_path)
                        logger.info(f"🎨 [Vertex] Editando imagen (Image-to-Image)...")
                        imagen_base_path = eyes.generate_scene(scene, script, current_channel.orientation, init_image_path=extracted_frame)
                    else:
                        logger.warning("   ⚠️ Sin video previo válido. Volviendo a generar desde cero...")
                        imagen_base_path = eyes.generate_scene(scene, script, current_channel.orientation)

                if not imagen_base_path:
                    logger.error(f"❌ Fallo crítico visual en escena {scene.id}, fragmento {step+1}.")
                    break # Salimos del sub-bucle si Vertex falla

                # Animación con Grok
                logger.info("   🎬 [Grok] Animando fragmento...")
                video_path = animator.animate_image(
                    image_path=imagen_base_path,
                    prompt=scene.action_prompt, 
                    scene_id=f"{scene.id}_{step}" # ID único para el caché
                )
                
                if video_path:
                    scene_videos.append(video_path)
                    last_generated_video = video_path
                else:
                    # 🟢 ELIMINADO EL SALVAVIDAS
                    logger.error(f"   ❌ GROK FALLÓ. Abortando procesamiento de esta escena para no usar fotos.")
                    last_generated_video = None
                    break # Rompe el bucle de fragmentos para no producir basura

            # Guardamos la lista de fragmentos para esta escena
            final_assets_map[scene.id] = scene_videos

        # --- FASE 6: ENSAMBLAJE FINAL ---
        logger.info("\n🎬 Iniciando VideoEngine para empaquetado...")
        try:
            video_path = editor.assemble_video(script, final_assets_map, audio_map)
            
            if video_path:
                ReportGenerator.save_production_report(script, final_assets_map, video_path)
                
                if orientation_mode == "long" and not draft_mode:
                    try:
                        logger.info("🖼️ Creando Miniatura...")
                        thumb_maker.generate_thumbnail(topic, script.title[:20])
                    except Exception as e:
                        logger.warning(f"⚠️ Miniatura falló: {e}")

                logger.info("="*60)
                logger.info(f"🎉 ¡PLATO SERVIDO!: {video_path}")
                logger.info("="*60)
                
                if sys.platform == 'win32': os.startfile(video_path)
                return video_path
            else:
                logger.error("❌ El motor de edición (MoviePy) falló.")
                return None

        except Exception as e:
            logger