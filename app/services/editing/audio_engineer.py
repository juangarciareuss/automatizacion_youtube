import os
import random
import re
from moviepy.editor import AudioFileClip, CompositeAudioClip, afx
from app.utils.logger import get_logger

logger = get_logger(__name__)

class AudioEngineer:
    def __init__(self, config):
        self.config = config
        # Rutas base asumidas
        self.music_base_path = "assets/music"
        self.sfx_base_path = "assets/sfx"

    def process_full_mix(self, video_clip, script, scene_clips):
        """
        Toma el video mudo (o solo con voz) y le agrega:
        1. Música de fondo (según el mood del canal).
        2. Auto-ducking (bajar música cuando habla la IA).
        3. SFX (efectos de sonido sincronizados con el texto).
        """
        logger.info("🎚️ [AUDIO ENGINEER] Iniciando mezcla de sonido...")
        
        # 1. Obtener el audio base (la voz en off de las escenas)
        voice_audio = video_clip.audio
        
        if not voice_audio:
            logger.warning("⚠️ El video no tiene audio base (voz).")
            return video_clip

        final_audio_layers = [voice_audio]

        # 2. Música de Fondo (Background Music)
        bg_music = self._select_music_by_mood()
        if bg_music:
            # Hacemos que la música dure lo mismo que el video (loop si es necesario)
            bg_music = afx.audio_loop(bg_music, duration=video_clip.duration)
            
            # Aplicamos Ducking: Volumen bajo (0.10) para no tapar la voz
            # Podrías hacerlo más complejo, pero volumen constante bajo suele funcionar mejor en YouTube
            bg_music = bg_music.volumex(0.12) 
            
            final_audio_layers.insert(0, bg_music) # Poner al fondo

        # 3. Insertar Efectos de Sonido (SFX)
        sfx_clips = self._generate_sfx_clips(script, scene_clips)
        if sfx_clips:
            final_audio_layers.extend(sfx_clips)

        # 4. Mezcla Final
        try:
            full_mix = CompositeAudioClip(final_audio_layers)
            return video_clip.set_audio(full_mix)
        except Exception as e:
            logger.error(f"❌ Error en la mezcla de audio: {e}")
            return video_clip

    def _select_music_by_mood(self):
        """Busca una canción aleatoria en la carpeta del mood configurado."""
        mood_path = os.path.join(self.music_base_path, self.config.music_mood)
        
        if not os.path.exists(mood_path):
            logger.warning(f"⚠️ Carpeta de música no encontrada: {mood_path}")
            return None
            
        supported_ext = ('.mp3', '.wav')
        songs = [f for f in os.listdir(mood_path) if f.lower().endswith(supported_ext)]
        
        if not songs:
            logger.warning(f"⚠️ No hay canciones en: {mood_path}")
            return None
            
        selected_song = random.choice(songs)
        full_path = os.path.join(mood_path, selected_song)
        logger.info(f"🎵 Música seleccionada: {selected_song}")
        
        return AudioFileClip(full_path)

    def _generate_sfx_clips(self, script, scene_clips):
        """
        Analiza el texto del guion buscando etiquetas [SFX: nombre] 
        y coloca el sonido en el momento aproximado.
        """
        sfx_objects = []
        current_time_cursor = 0.0
        
        try:
            # Iteramos escena por escena para mantener la sincronía
            for i, scene in enumerate(script.scenes):
                if i >= len(scene_clips): break
                
                scene_duration = scene_clips[i].duration
                text = scene.narration or ""
                
                # Buscamos todas las etiquetas [SFX: loquesea]
                matches = re.finditer(r'\[SFX:\s*(.*?)\]', text, re.IGNORECASE)
                
                total_chars = len(text)
                
                for match in matches:
                    sfx_name = match.group(1).strip().lower()
                    
                    # Calcular posición temporal
                    # Si el tag está al 50% del texto, el sonido va al 50% del clip
                    char_index = match.start()
                    percentage = char_index / max(total_chars, 1)
                    sfx_start_time = current_time_cursor + (percentage * scene_duration)
                    
                    # Cargar el archivo de sonido
                    sfx_path = os.path.join(self.sfx_base_path, f"{sfx_name}.wav")
                    
                    # Intentar .mp3 si no existe .wav
                    if not os.path.exists(sfx_path):
                        sfx_path = os.path.join(self.sfx_base_path, f"{sfx_name}.mp3")
                    
                    if os.path.exists(sfx_path):
                        clip = AudioFileClip(sfx_path).set_start(sfx_start_time)
                        # Ajuste de volumen para SFX
                        clip = clip.volumex(0.8) 
                        sfx_objects.append(clip)
                        logger.info(f"🔊 SFX insertado: {sfx_name} en {sfx_start_time:.2f}s")
                    else:
                        logger.warning(f"⚠️ SFX faltante: {sfx_name} (buscado en {self.sfx_base_path})")

                # Avanzamos el cursor de tiempo (restando el padding usado en timeline_builder si lo hubiera)
                # Asumimos que scene_clips[i] es la duración real en el montaje
                current_time_cursor += (scene_duration - 0.8) # El padding negativo del concatenate

        except Exception as e:
            logger.error(f"❌ Error procesando SFX: {e}")
            
        return sfx_objects