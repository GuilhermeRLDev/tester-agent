import requests

def generate_test(prompt, model="/home/workspace/mistral-quant/llama.cpp/deepseek.Q4_K_M.gguf"):
    """Call llama.cpp to generate code based on the prompt."""
    print(f"Generating test for prompt: {prompt}")
    # Ensure the model is available in the specified path
    payload = {
        "prompt": prompt,
        "max_tokens": 1024,
        "temperature": 0.2,
        "top_p": 0.9
    }

    response = requests.post("http://127.0.0.1:8080/completion", json=payload, timeout=3600)
    response.raise_for_status()
    print(response.json()["content"])
    return response.json()["content"]  # adjust depending on API response structure

