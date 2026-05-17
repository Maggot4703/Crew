try:
    import requests
except Exception:
    requests = None

DEESEEK_CODE_SERVER_URL = "http://localhost:8000"
DEESEEK_REQUEST_TIMEOUT = 15


def deepseek_code_query(prompt: str) -> str:
    """
    Send a prompt to the DeepSeek Code server and return the response.
    If the 'requests' library is not installed, return a clear error message instead of raising on import.
    """
    if requests is None:
        return "[ERROR] 'requests' library not installed. Install it to use DeepSeek integration."

    try:
        response = requests.post(
            f"{DEESEEK_CODE_SERVER_URL}/v1/completions",  # Adjust endpoint as needed
            json={"prompt": prompt},
            timeout=DEESEEK_REQUEST_TIMEOUT,
        )
        response.raise_for_status()
        data = response.json()
        # Adjust the key based on DeepSeek's API response structure
        return data.get("result") or data.get("choices", [{}])[0].get(
            "text", "[No response]"
        )
    except Exception as e:
        return f"[ERROR] Failed to contact DeepSeek Code server: {e}"
