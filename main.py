import os
import sys
import asyncio
import argparse
import subprocess # 🟢 Añadido para lanzar Chrome

# --- 🔴 PARCHE CRÍTICO PARA WINDOWS + PYTHON 3.12+ ---
# Esto evita el 'NotImplementedError' de Playwright al intentar conectar con Chrome
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
# -----------------------------------------------------

def cargar_env_manual():
    env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
    if os.path.exists(env_path):
        with open(env_path, 'r', encoding='utf-8-sig') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'): continue
                if '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip().strip('"').strip("'")
    else:
        print("⚠️ ADVERTENCIA: No se encontró el archivo .env")

cargar_env_manual()

# --- 2. IMPORTAR EL GERENTE ---
from app.core.factory_manager import FactoryManager

def iniciar_chrome_debug():
    """Lanza Chrome en Modo Debug y espera confirmación antes de iniciar la fábrica."""
    print("\n🚀 Iniciando Motor de Animación (Grok CDP)...")
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
        sys.exit(1)
        
    print("\n" + "="*50)
    print("🛑 ACCIÓN REQUERIDA EN EL NAVEGADOR:")
    print("1. Revisa la ventana de Chrome que se acaba de abrir.")
    print("2. Inicia sesión en Grok si es necesario.")
    print("3. Asegúrate de estar en el chat principal.")
    print("="*50 + "\n")
    
    input("👉 Presiona ENTER aquí SOLO cuando la web de Grok esté lista...")

# --- 3. INTERFAZ DE USUARIO (CLI) ---
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Silent Factory - Kitchen Edition")
    parser.add_argument("topic", nargs="?", help="Plato a cocinar")
    parser.add_argument("--channel", default="perfect_recipe", help="ID del canal")
    parser.add_argument("--format", choices=["short", "long"], help="Formato del video")
    parser.add_argument("--draft", action="store_true", help="Activa modo borrador rápido")
    
    args = parser.parse_args()
    topic = args.topic
    fmt = args.format
    draft_mode = args.draft 

    print("\n" + "🍳"*30)
    print("   BISTRO AI - SISTEMA DE PEDIDOS")
    print("🍳"*30 + "\n")

    # Menú Interactivo
    if not fmt:
        print("¿Qué desea ordenar?")
        print("  [1] Short (Vertical 9:16) - TikTok/Reels")
        print("  [2] Long  (Horizontal 16:9) - YouTube Clásico")
        print("  [3] 🧪 TEST RÁPIDO - Short (Modo Borrador)") 
        print("  [4] 🧪 TEST RÁPIDO - Long (Modo Borrador)")  
        
        while True:
            choice = input("👉 Elige opción: ").strip()
            if choice == "1":
                fmt = "short"
                draft_mode = False
                break
            elif choice == "2":
                fmt = "long"
                draft_mode = False
                break
            elif choice == "3":
                fmt = "short"
                draft_mode = True 
                break
            elif choice == "4":
                fmt = "long"
                draft_mode = True 
                break
            else:
                print("❌ Opción inválida.")

    if not topic:
        suffix = " (DRAFT)" if draft_mode else ""
        try:
            topic = input(f"\n👉 ¿Qué receta cocinamos en formato {fmt.upper()}{suffix}?: ").strip()
        except KeyboardInterrupt:
            sys.exit()

    if topic:
        # 🟢 Novedad: Encendemos Chrome antes de llamar al gerente (solo si no es borrador o si el borrador usa Grok)
        # Asumo que quieres probar Grok, así que lo lanzamos.
        iniciar_chrome_debug()

        # Instanciamos al Gerente y le damos la orden
        manager = FactoryManager()
        manager.produce_video(
            topic=topic, 
            channel_id=args.channel, 
            orientation_mode=fmt, 
            draft_mode=draft_mode 
        )