import os
import sys
from django.shortcuts import render
from django.conf import settings
from .forms import VideoGeneratorForm  # <--- IMPORTAMOS TU NUEVO FORMULARIO

# --- IMPORTACIÓN DIRECTA ---
try:
    from main import run_simulation
except ImportError as e:
    print(f"❌ ERROR IMPORTANDO MAIN: {e}")
    # Definimos una función dummy que acepta argumentos extra (*args, **kwargs) para que no falle
    def run_simulation(topic_input, voice_name=None): return None

def dashboard_view(request):
    video_url = None
    
    # 1. Si es POST (Click en Generar), llenamos el formulario con los datos
    if request.method == "POST":
        form = VideoGeneratorForm(request.POST)
        
        if form.is_valid():
            # 2. Extraemos los datos limpios
            topic = form.cleaned_data['topic']
            voice_id = form.cleaned_data['voice_id']
            director_notes = form.cleaned_data['director_notes']
            
            print(f"🔴 DJANGO: Configurando fábrica...")
            print(f"   - Tema: {topic}")
            print(f"   - Voz: {voice_id}")
            print(f"   - Notas: {director_notes}")

            # 3. Lógica de "Director": Inyectamos las notas en el prompt si existen
            full_topic_input = topic
            if director_notes:
                full_topic_input = f"{topic}. (IMPORTANT SCRIPT INSTRUCTIONS: {director_notes})"

            # 4. Ejecutamos el motor pasando la VOZ también
            # NOTA: Debes actualizar tu main.py para que acepte 'voice_name'
            generated_path = run_simulation(
                topic_input=full_topic_input, 
                voice_name=voice_id
            )
            
            if generated_path:
                filename = os.path.basename(generated_path)
                video_url = f"{settings.MEDIA_URL}final_videos/{filename}"
                print(f"🟢 DJANGO: Video exitoso: {video_url}")
            else:
                print("⚠️ DJANGO: El script corrió pero retornó None.")
    
    else:
        # 5. Si es GET (Primera visita), mostramos el formulario vacío
        form = VideoGeneratorForm()

    # 6. Pasamos 'form' al HTML para que se dibuje solo
    return render(request, "core/dashboard.html", {
        "form": form, 
        "video_url": video_url
    })