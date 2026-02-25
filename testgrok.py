import os
import subprocess
import time
from playwright.sync_api import sync_playwright

def iniciar_chrome_debug():
    print("🚀 [PASO 1] Abriendo Chrome en Modo Debug...")
    
    ruta_chrome = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
    comando = [
        ruta_chrome,
        "--remote-debugging-port=9222",
        "--user-data-dir=C:\\ChromeBOT",
        "https://grok.com/imagine"
    ]
    
    try:
        subprocess.Popen(comando)
    except FileNotFoundError:
        print(f"❌ Error crítico: Chrome no encontrado en {ruta_chrome}")
        return False
        
    print("\n" + "="*50)
    print("🛑 ACCIÓN REQUERIDA EN EL NAVEGADOR:")
    print("1. Revisa la ventana de Chrome.")
    print("2. Inicia sesión en Grok si es necesario.")
    print("3. Asegúrate de estar en el chat principal.")
    print("="*50 + "\n")
    
    input("👉 Presiona ENTER en la consola SOLO cuando la web esté lista...")
    return True

def conectar_y_animar():
    print("🔌 Estableciendo conexión CDP (Puerto 9222)...")

    with sync_playwright() as p:
        try:
            browser = p.chromium.connect_over_cdp("http://localhost:9222")
            context = browser.contexts[0]
            page = context.pages[0]
            
            print(f"✅ Conexión establecida: {page.title()}")
            
            if "grok.com" not in page.url:
                page.goto("https://grok.com/imagine")
                page.wait_for_load_state("networkidle")

            imagen = r"C:\Users\Darkj\Desktop\Youtube\silent_factory\assets\test_image.jpg"
            prompt = "Animate this image, cinematic slow motion, 4k quality"

            print(f"📤 Inyectando activo base (imagen)...")
            try:
                page.set_input_files('input[type="file"]', imagen, timeout=3000)
                print("   ✅ Imagen cargada en memoria.")
            except Exception:
                print("   ⚠️ Input oculto. Pase a modo manual. Tiene 15s para arrastrar la imagen...")
                time.sleep(15)

            time.sleep(2) 

            print("✍️ Ingresando parámetros de renderizado...")
            page.fill('textarea', prompt)
            
            print("🚀 Transmitiendo petición...")
            page.keyboard.press("Enter")
            
            print("⏳ Esperando a que el servidor de Grok renderice el video (Máx 4 minutos)...")
            
            try:
                # Esperamos a que la etiqueta de video real se inyecte en el DOM
                page.wait_for_selector('video[src*="assets.grok.com"]', timeout=240000)
                print("   ✅ Video final detectado en pantalla.")
            except Exception:
                print("❌ Error: Se agotó el tiempo de espera (4 minutos) o Grok no devolvió el video.")
                return

            # Pausa de 3 segundos para dar tiempo a que la interfaz renderice los botones de control
            time.sleep(3)

            print("📥 Evadiendo Firewall: Clickeando el botón nativo de descarga en la UI...")

            carpeta_salida = os.path.join(os.getcwd(), "output", "final_videos")
            os.makedirs(carpeta_salida, exist_ok=True)
            ruta_guardado = os.path.join(carpeta_salida, f"grok_scene_{int(time.time())}.mp4")

            try:
                # Interceptamos la ventana de descarga que se genera al hacer clic
                with page.expect_download(timeout=60000) as download_info:
                    # Usamos un selector triple para garantizar atrapar el botón sin importar el idioma (Es/En) o la clase
                    boton_descarga = page.locator('button[aria-label="Descargar"], button[aria-label="Download"], button:has(svg.lucide-download)').last
                    boton_descarga.click()
                
                descarga = download_info.value
                
                print("💾 Escribiendo archivo en disco...")
                descarga.save_as(ruta_guardado)

                tamano_mb = os.path.getsize(ruta_guardado) / (1024 * 1024)
                print(f"✅ ¡ÉXITO TOTAL! Video de {tamano_mb:.2f} MB guardado en: {ruta_guardado}")

            except Exception as e:
                print(f"❌ Error durante el clic nativo o la descarga: {e}")

        except Exception as e:
            print(f"💥 Error crítico de motor: {e}")

if __name__ == "__main__":
    if iniciar_chrome_debug():
        conectar_y_animar()