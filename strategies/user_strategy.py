from dataclasses import dataclass

from .base_strategy import ChatbotStrategy


@dataclass
class UserStrategy(ChatbotStrategy):
    """Fallback strategy for Crew multi-user chat responses."""

    name: str = "Computer"
    role: str = "assistant"

    def process_message(self, message: str) -> str:
        response = f"[{self.name}] Acknowledged via {self.llm_backend}: {message}"
        self.add_to_history(f"User: {message}")
        self.add_to_history(response)
        return response
