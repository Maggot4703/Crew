AI setup for Crew chatbot (Ollama / DeepSeek)

This document and the scripts in scripts/ help install, test, and configure a local model backend for Crew's chatbot.

Recommended backend: Ollama (local inference server)

Quick steps (Ollama)

1) On the host that will run the model ("me@home"):
   - Install Ollama using official docs: https://ollama.ai/docs/installation
   - Pull a small model (example):
       ollama pull deepseek-r1:1.5b
   - Start server:
       ollama serve &
   - Verify locally:
       curl http://localhost:11434/api/tags

2) From the Crew machine (this repo):
   - Ensure Python dependency 'requests' is installed in the runtime env:
       pip install requests
   - Update Crew config (via GUI or config.json):
       {
         "chatbot": {
           "model": "deepseek-r1:1.5b",
           "llm_backend": "ollama",
           "ollama_base_url": "http://<ME_HOME_IP>:11434"
         }
       }
   - Use scripts in CREW/Crew/scripts:
       - setup_ollama.sh --pull deepseek-r1:1.5b  # runs ollama pull when ollama is present
       - test_ollama_connection.sh <host> [model]
       - test_deepseek.sh <host> [port]

Alternative: DeepSeek HTTP server

- If you have a DeepSeek Code HTTP server, run it on me@home and ensure it serves /v1/completions.
- Configure Crew to use DeepSeek by setting the fallback or by adjusting deepseek_integration.py endpoint.

Networking

- Ensure firewall allows traffic from the Crew host to me@home on the model port (11434 for Ollama, 8000 for DeepSeek by default).
- Use the host IP or a DNS/hosts entry accessible to the Crew machine.

Testing

- From the Crew host, run:
    bash scripts/test_ollama_connection.sh <ME_HOME_IP>
    bash scripts/test_deepseek.sh <ME_HOME_IP>

Notes

- These scripts are helpers and should be reviewed for your environment before running. They do not attempt to install system packages automatically.
- If you want, I can add automation to edit Crew's config.json to point to a chosen ME_HOME_IP and commit that change.
