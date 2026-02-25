class GrokConfig:
    # URL Base de Grok (Interfaz Web)
    URL_HOME = "https://grok.com/imagine"
    
    # Directorios (Rutas relativas desde la raíz del proyecto)
    SESSIONS_DIR = "data/sessions"
    DOWNLOAD_DIR = "output/temp_videos"

    # --- 🕵️‍♂️ SELECTORES CSS (REQUIEREN VALIDACIÓN CON F12) ---
    # Botón para subir imagen (suele ser un icono de paisaje/media)
    # Buscamos por aria-label que es más estable
    SELECTOR_UPLOAD_BTN = 'div[aria-label="Add media"]' 
    
    # Input de archivo (Fallback por si el botón falla)
    SELECTOR_FILE_INPUT = 'input[type="file"]'
    
    # Cuadro de texto donde escribes el prompt
    SELECTOR_TEXT_AREA = '[data-testid="grokInput"]'
    
    # Botón de enviar mensaje (El avioncito)
    SELECTOR_SEND_BTN = '[data-testid="grokSendMessage"]'
    
    # El contenedor del video resultante
    SELECTOR_VIDEO_RESULT = 'video'
    
    # Tiempo máximo de espera (segundos) para que se genere el video
    TIMEOUT_GENERATION = 120