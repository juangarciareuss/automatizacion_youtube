from django import forms

# Opciones de Voces (Las mejores de Edge-TTS)
VOICE_CHOICES = [
    ('en-US-ChristopherNeural', 'Christopher (Documental Profundo) - ACTUAL'),
    ('en-US-RogerNeural', 'Roger (Serio / Noticias)'),
    ('en-US-AriaNeural', 'Aria (Femenina / Profesional)'),
    ('en-US-EricNeural', 'Eric (Enérgico / Joven)'),
]

class VideoGeneratorForm(forms.Form):
    # 1. El Tema (Ya lo tienes)
    topic = forms.CharField(
        label="Tema del Video", 
        max_length=200, 
        widget=forms.TextInput(attrs={
            'class': 'form-control', 
            'placeholder': 'Ej: The Dark Side of Gucci',
            'style': 'padding: 15px; font-size: 1.2rem; width: 100%; border-radius: 8px;'
        })
    )

    # 2. Selector de Voz (NUEVO)
    voice_id = forms.ChoiceField(
        label="Voz del Narrador",
        choices=VOICE_CHOICES,
        initial='en-US-ChristopherNeural',
        widget=forms.Select(attrs={
            'class': 'form-control',
            'style': 'padding: 10px; width: 100%; margin-top: 10px; border-radius: 8px;'
        })
    )

    # 3. Instrucciones de Director (NUEVO - Opcional)
    # Aquí le susurras al oído a Gemini antes de que escriba
    director_notes = forms.CharField(
        label="Notas para el Guionista (Opcional)",
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'placeholder': 'Ej: Enfócate en la traición familiar, sé sarcástico, menciona cifras de dinero exactas...',
            'rows': 3,
            'style': 'width: 100%; margin-top: 10px; border-radius: 8px;'
        })
    )