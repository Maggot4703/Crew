from dataclasses import dataclass

from .base_strategy import ChatbotStrategy


@dataclass
class RefereeStrategy(ChatbotStrategy):
    """Fallback strategy for the Crew chatbot dialog."""

    name: str = "Referee"
    role: str = "referee"

    def process_message(self, message: str) -> str:
        response = f"[{self.name}] Processed via {self.llm_backend}: {message}"
        self.add_to_history(f"User: {message}")
        self.add_to_history(response)
        return response
