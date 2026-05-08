from dataclasses import dataclass, field
from typing import Any, List, Optional


@dataclass
class ChatbotStrategy:
    """Minimal chat strategy base used by Crew chat windows."""

    name: str
    role: str
    llm_backend: str = "ollama"
    history: List[str] = field(default_factory=list)
    extra_context: Optional[Any] = None

    def process_message(self, message: str) -> str:
        raise NotImplementedError

    def add_to_history(self, message: str) -> None:
        self.history.append(message)
