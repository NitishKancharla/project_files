from abc import ABC, abstractmethod
from .base_agent import BaseAgent
class BaseAgent(ABC):
    def __init__(self):
        # Lazy load to break circular dependency
        from ..core.gemini_client import GeminiHelper
        from ..core.knowledge_base import DestinationKnowledge
        
        self.gemini = GeminiHelper()
        self.knowledge = DestinationKnowledge()

    @abstractmethod
    def run(self, state: dict) -> dict:
        pass