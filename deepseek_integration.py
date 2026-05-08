import requests

DEESEEK_CODE_SERVER_URL = "http://localhost:8000"
DEESEEK_REQUEST_TIMEOUT = 15


def deepseek_code_query(prompt: str) -> str:
    """
    Send a prompt to the DeepSeek Code server and return the response.
    Args:
        prompt (str): The user prompt or code to send.
    Returns:
        str: The response from DeepSeek Code server.
    """
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
