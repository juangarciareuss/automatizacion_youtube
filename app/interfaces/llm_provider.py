from abc import ABC, abstractmethod
from app.domain.models import VideoScript

class LLMProvider(ABC):
    """
    Contrato abstracto para cualquier cerebro de IA (Gemini, GPT-4, Claude).
    Garantiza que todos los cerebros devuelvan un VideoScript válido.
    """
    
    @abstractmethod
    def generate_script(self, topic: str, style: str) -> VideoScript:
        pass