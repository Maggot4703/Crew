"""
Ollama API client for streaming responses from local LLMs.

Provides a lightweight interface to ollama's /api/generate endpoint
with support for streaming responses, conversation history, and error handling.

Usage:
    client = OllamaClient(model='gemma4:latest')
    for chunk in client.generate("What is machine learning?"):
        print(chunk, end='', flush=True)
"""

import json
import logging
from typing import Dict, Generator, List

import requests

logger = logging.getLogger(__name__)


class OllamaClient:
    """Lightweight client for ollama API with streaming support."""

    DEFAULT_BASE_URL = "http://localhost:11434"
    DEFAULT_MODEL = (
        "deepseek-r1:1.5b"  # Changed from gemma4 (9.8GB) to deepseek-r1 (1.1GB)
    )
    DEFAULT_TIMEOUT = 60.0

    def __init__(
        self,
        model: str = DEFAULT_MODEL,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = DEFAULT_TIMEOUT,
        temperature: float = 0.7,
        top_p: float = 0.9,
    ):
        """
        Initialize Ollama client.

        Args:
            model: Model name (e.g., 'gemma4:latest')
            base_url: Ollama API base URL
            timeout: Request timeout in seconds
            temperature: Response creativity (0.0=deterministic, 1.0=creative)
            top_p: Nucleus sampling parameter
        """
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.temperature = temperature
        self.top_p = top_p
        self.conversation_history: List[Dict[str, str]] = []
        self._stop_flag = False  # Flag for cancelling streaming (Phase 5.3)

        # Verify ollama is accessible
        self._verify_connection()

    def _verify_connection(self) -> None:
        """Verify ollama API is accessible and model is available."""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5.0)
            response.raise_for_status()

            data = response.json()
            available_models = [m["name"] for m in data.get("models", [])]

            if self.model not in available_models:
                logger.warning(
                    f"Model '{self.model}' not found. Available: {available_models}"
                )
        except requests.exceptions.RequestException as e:
            logger.error(f"Cannot connect to ollama at {self.base_url}: {e}")
            raise ConnectionError(
                f"Ollama API unreachable at {self.base_url}. "
                "Make sure ollama is running: `ollama serve`"
            ) from e

    def generate(
        self,
        prompt: str,
        include_history: bool = True,
        context_window: int = 10,
    ) -> str:
        """
        Generate a response (buffered, returns full text).

        Args:
            prompt: User input/question
            include_history: Include conversation history in context
            context_window: Number of previous messages to include

        Returns:
            Full response text
        """
        return "".join(
            self.stream(
                prompt, include_history=include_history, context_window=context_window
            )
        )

    def stream(
        self,
        prompt: str,
        include_history: bool = True,
        context_window: int = 10,
    ) -> Generator[str, None, None]:
        """
        Stream a response token-by-token.

        Args:
            prompt: User input/question
            include_history: Include conversation history in context
            context_window: Number of previous messages to include

        Yields:
            Response chunks (usually 1-20 tokens per chunk)

        Raises:
            ConnectionError: If ollama is unreachable
            ValueError: If model doesn't exist
        """
        # Build context from conversation history
        context = self._build_context(prompt, include_history, context_window)

        # Reset stop flag for new request (Phase 5.3)
        self._stop_flag = False

        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": context,
                    "stream": True,
                    "temperature": self.temperature,
                    "top_p": self.top_p,
                },
                stream=True,
                timeout=self.timeout,
            )
            response.raise_for_status()

            full_response = ""
            for line in response.iter_lines():
                # Check stop flag (Phase 5.3 - allow cancellation)
                if self._stop_flag:
                    logger.info("Stream cancelled by user")
                    break

                if not line:
                    continue

                try:
                    data = json.loads(line)
                    chunk = data.get("response", "")
                    if chunk:  # Only yield non-empty chunks
                        full_response += chunk
                        yield chunk
                except json.JSONDecodeError as e:
                    logger.warning(f"Invalid JSON in stream: {e}")
                    continue

            # Add to history only after successful completion
            self.conversation_history.append({"role": "user", "content": prompt})
            self.conversation_history.append(
                {"role": "assistant", "content": full_response.strip()}
            )

        except requests.exceptions.ConnectionError as e:
            logger.error(f"Connection error: {e}")
            raise ConnectionError(
                f"Cannot connect to ollama at {self.base_url}. "
                "Is ollama running? Try: `ollama serve`"
            ) from e
        except requests.exceptions.Timeout:
            logger.error(f"Request timeout after {self.timeout}s")
            raise TimeoutError(
                f"Ollama response timeout after {self.timeout}s. "
                "Model may be overloaded or response too long."
            )
        except requests.exceptions.HTTPError as e:
            if "model not found" in str(e).lower():
                raise ValueError(
                    f"Model '{self.model}' not found. "
                    "Pull it with: `ollama pull {self.model}`"
                ) from e
            logger.error(f"HTTP error: {e}")
            raise

    def _build_context(
        self, prompt: str, include_history: bool, context_window: int
    ) -> str:
        """Build prompt with optional conversation history."""
        if not include_history or not self.conversation_history:
            return prompt

        # Include only last N messages
        recent = self.conversation_history[-(context_window * 2) :]

        context_parts = []
        for msg in recent:
            role = msg["role"].capitalize()
            content = msg["content"]
            context_parts.append(f"{role}: {content}")

        context_parts.append(f"User: {prompt}")
        return "\n".join(context_parts)

    def clear_history(self) -> None:
        """Clear conversation history."""
        self.conversation_history.clear()

    def get_history(self) -> List[Dict[str, str]]:
        """Get current conversation history."""
        return self.conversation_history.copy()

    def set_model(self, model: str) -> None:
        """Switch to a different model."""
        self.model = model
        logger.info(f"Switched model to {model}")

    def cancel_stream(self) -> None:
        """Signal streaming to stop (Phase 5.3)."""
        self._stop_flag = True
        logger.info("Cancellation signal sent")

    def reset_cancel_flag(self) -> None:
        """Reset the cancellation flag (called before new requests)."""
        self._stop_flag = False

    @staticmethod
    def list_models(base_url: str = DEFAULT_BASE_URL) -> List[str]:
        """Get list of available models."""
        try:
            response = requests.get(f"{base_url.rstrip('/')}/api/tags", timeout=5.0)
            response.raise_for_status()
            data = response.json()
            return [m["name"] for m in data.get("models", [])]
        except requests.exceptions.RequestException as e:
            logger.error(f"Cannot fetch models: {e}")
            return []


if __name__ == "__main__":
    # Quick test
    logging.basicConfig(level=logging.INFO)

    try:
        client = OllamaClient(model="gemma4:latest")
        print("💬 Testing ollama streaming...\n")

        prompt = "Explain machine learning in 2 sentences."
        print(f"Q: {prompt}")
        print("A: ", end="", flush=True)

        for chunk in client.stream(prompt, include_history=False):
            print(chunk, end="", flush=True)

        print("\n")

    except Exception as e:
        print(f"❌ Error: {e}")
