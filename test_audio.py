# test_visuals.py
from app.services.visuals.vertex_generator import VertexGenerator
from app.domain.models import Scene # Asegúrate de importar tu modelo
from dotenv import load_dotenv

load_dotenv()

def test_full_sequence():
    print("🚀 Probando Secuencia Visual con Memoria...")
    
    # Simulamos 3 escenas del guion
    mock_scenes = [
        Scene(id=1, narrative_text="Intro", image_prompt="Close up of a raw wagyu beef patty on a wooden board", output_state="Raw patty ready"),
        Scene(id=2, narrative_text="Cooking", image_prompt="The beef patty sizzling on a hot cast iron skillet", output_state="Cooked patty"),
        Scene(id=3, narrative_text="Plating", image_prompt="Placing the cooked patty on a toasted brioche bun", output_state="Burger assembly")
    ]
    
    generator = VertexGenerator()
    assets = generator.fetch_assets(mock_scenes)
    
    print(f"\n✅ Se generaron {len(assets)} imágenes.")

if __name__ == "__main__":
    test_full_sequence()