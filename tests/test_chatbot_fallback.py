import importlib
from types import SimpleNamespace


def make_dummy_self():
    # Minimal dummy object with config_manager that returns example llm config
    from config import Config

    conf = Config(config_dir=".", config_filename="config.llm.example.json")
    dummy = SimpleNamespace()
    dummy.config_manager = conf
    # provide optional attribute llm_backend_var with get()
    dummy.llm_backend_var = None
    return dummy


def test_fallback_to_deepseek(monkeypatch):
    # Simulate Ollama client failing to initialize
    class BadOllama:
        def __init__(self, *args, **kwargs):
            raise ConnectionError("Ollama down")

    import sys

    # Patch ollama_client to a failing client
    sys.modules["ollama_client"] = SimpleNamespace(OllamaClient=BadOllama)

    # Patch deepseek to return a known value
    import deepseek_integration

    monkeypatch.setattr(
        deepseek_integration, "deepseek_code_query", lambda prompt: "deepseek reply"
    )

    import gui

    dummy = make_dummy_self()
    resp = gui.CrewGUI.generate_bot_reply(dummy, "Compute 2+2")
    assert resp == "deepseek reply"


def test_ollama_used_when_available(monkeypatch):
    # Simulate Ollama client returning a response
    class GoodOllama:
        def __init__(self, *args, **kwargs):
            pass

        def generate(self, prompt):
            return "ollama reply"

    import sys

    sys.modules["ollama_client"] = SimpleNamespace(OllamaClient=GoodOllama)

    import gui

    dummy = make_dummy_self()
    resp = gui.CrewGUI.generate_bot_reply(dummy, "Compute 2+2")
    assert resp == "ollama reply"
