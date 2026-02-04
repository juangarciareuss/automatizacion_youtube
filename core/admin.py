from django.contrib import admin
from .models import VideoProject, Scene

# Esto hace que las escenas aparezcan DENTRO de la página del video
class SceneInline(admin.StackedInline): 
    model = Scene
    extra = 1 # Muestra 1 escena vacía lista para rellenar

@admin.register(VideoProject)
class VideoProjectAdmin(admin.ModelAdmin):
    list_display = ('title', 'status', 'created_at', 'views') # Columnas de la tabla
    list_filter = ('status',) # Filtro lateral
    search_fields = ('title',) # Barra de búsqueda
    inlines = [SceneInline] # <--- Aquí conectamos las escenas