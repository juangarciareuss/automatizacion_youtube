import os
import sys
sys.path.append(os.getcwd())

from playwright.sync_api import sync_playwright
from app.services.video_automator.grok.config import GrokConfig

def create_session(account_name):
    print(f"🔧 Configurando cuenta para GROK.COM: {account_name}")
    
    os.makedirs(GrokConfig.SESSIONS_DIR, exist_ok=True)
    file_path = os.path.join(GrokConfig.SESSIONS_DIR, f"{account_name}.json")

    with sync_playwright() as p:
        # Usamos channel="chrome" para parecer un navegador real y evitar bloqueos de Google
        print(f"🌍 Abriendo Chrome Real...")
        try:
            browser = p.chromium.launch(channel="chrome", headless=False)
        except:
            print("⚠️ No encontré Chrome instalado, usando Chromium por defecto.")
            browser = p.chromium.launch(headless=False)

        context = browser.new_context()
        page = context.new_page()

        # 1. Vamos directo a la página que quieres usar
        target_url = "https://grok.com/imagine"
        print(f"🚀 Navegando a: {target_url}")
        page.goto(target_url)

        print("\n" + "="*60)
        print(f"🛑 TAREA MANUAL - LEE CON ATENCIÓN")
        print("1. En la ventana que se abrió, haz clic en 'Sign in' o 'Login'.")
        print("2. Usa tu correo, Google, o X para entrar (lo que prefieras).")
        print("3. SI TE PIDE VERIFICACIÓN, hazla tranquilo.")
        print("4. IMPORTANTE: Espera hasta que veas la pantalla lista para generar imágenes.")
        print("="*60 + "\n")
        
        input("👉 Cuando ya estés dentro y listo para trabajar, presiona ENTER aquí...")

        # Guardamos las cookies de grok.com
        context.storage_state(path=file_path)
        print(f"✅ ¡Sesión de Grok guardada en: {file_path}!")
        browser.close()

if __name__ == "__main__":
    name = input("Nombre para esta sesión (ej: grok_web): ")
    create_session(name)