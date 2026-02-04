from django.db import models

class VideoProject(models.Model):
    ESTADOS = [
        ('IDEA', '💡 Idea / Borrador'),
        ('SCRIPTING', '📝 Guion Listo'),
        ('RENDERING', '⚙️ Renderizando'),
        ('DONE', '✅ Terminado'),
        ('UPLOADED', '🚀 Subido a YouTube'),
    ]

    title = models.CharField("Título del Video", max_length=200)
    slug = models.SlugField(unique=True, help_text="ID único (ej: blackrock-empire)")
    status = models.CharField(max_length=20, choices=ESTADOS, default='IDEA')
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Métricas (Para tu futuro dashboard)
    views = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.title} ({self.get_status_display()})"

class Scene(models.Model):
    EFECTOS = [
        ('ZOOM_SLOW', '🔍 Zoom Lento (Ken Burns)'),
        ('ZOOM_FAST', '⚡ Zoom Agresivo (Gancho)'),
        ('PARTICLES_GOLD', '✨ Partículas Doradas'),
        ('MONEY_RAIN', '💸 Lluvia de Dinero'),
        ('STATIC', '🛑 Estático'),
    ]

    video = models.ForeignKey(VideoProject, related_name='scenes', on_delete=models.CASCADE)
    order = models.PositiveIntegerField("Orden", default=1)
    
    narration_text = models.TextField("Texto Narración (TTS)")
    visual_prompt = models.TextField("Prompt para Vertex AI")
    
    overlay_text = models.CharField("Texto en Pantalla (Opcional)", max_length=100, blank=True)
    effect_type = models.CharField(max_length=50, choices=EFECTOS, default='ZOOM_SLOW')
    
    duration = models.IntegerField("Duración (seg)", default=5)

    class Meta:
        ordering = ['order']
        verbose_name = "Escena"
        verbose_name_plural = "Escenas"

    def __str__(self):
        return f"Escena {self.order}: {self.narration_text[:30]}..."