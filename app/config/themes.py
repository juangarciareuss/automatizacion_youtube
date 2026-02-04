class ThemeConfig:
    """
    Repositorio central de estilos.
    Aquí definimos cómo se ve el video sin tocar el código del motor.
    """
    
    # Tema 1: Lujo Clásico (Por defecto)
    # Usamos fuentes seguras de sistema por ahora (Arial/Georgia) para evitar errores.
    # En el futuro, pondremos aquí la ruta a 'assets/fonts/Bodoni.ttf'
    LUXURY_DEFAULT = {
        "font": "Georgia-Bold",  # Una fuente con serifa, más elegante que Arial
        "fontsize": 70,
        "color": "#F4E5B0",      # Dorado Pálido (Pale Gold) - Muy elegante
        "stroke_color": "black", # Borde negro para legibilidad
        "stroke_width": 3,
        "position": ("center", "bottom"), # Ubicación estándar
        "fade_duration": 0.2     # Suavidad de aparición del texto
    }

    # Tema 2: Futuro (Ejemplo de Escalabilidad)
    TECH_MODERN = {
        "font": "Arial",
        "fontsize": 65,
        "color": "#00FFCC",      # Cyan Neón
        "stroke_color": "#003333",
        "stroke_width": 2,
        "position": "center",
        "fade_duration": 0.1
    }

    @classmethod
    def get_theme(cls, theme_name="luxury"):
        """Selector simple que no detiene el programa."""
        if theme_name == "tech":
            return cls.TECH_MODERN
        return cls.LUXURY_DEFAULT