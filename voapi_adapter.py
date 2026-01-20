"""
voapi_adapter.py
Lightweight helper to call VoAPI (OpenAI-compatible endpoint).
This module requires environment variables:
 - VOAPI_API_KEY (required)
 - VOAPI_BASE_URL (optional, defaults to https://demo.voapi.top/v1)

It exposes a simple function `chat_completion(messages, model=None, **kwargs)`
that returns text. It uses requests to call the provider in a compatible way.
"""
import os, requests, json, time

VOAPI_API_KEY = os.environ.get("VOAPI_API_KEY")
if not VOAPI_API_KEY:
    raise RuntimeError("VOAPI_API_KEY environment variable is required for VoAPI provider.")

VOAPI_BASE_URL = os.environ.get("VOAPI_BASE_URL", "https://demo.voapi.top/v1").rstrip('/')

DEFAULT_MODEL = "deepseek-ai-DeepSeek-R1"

def chat_completion(messages, model=None, timeout=60, temperature=0.7, **kwargs):
    model = model or DEFAULT_MODEL
    url = f"{VOAPI_BASE_URL}/chat/completions"
    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
    }
    payload.update(kwargs)
    headers = {
        "Authorization": f"Bearer {VOAPI_API_KEY}",
        "Content-Type": "application/json"
    }
    resp = requests.post(url, headers=headers, json=payload, timeout=timeout)
    try:
        data = resp.json()
    except Exception:
        resp.raise_for_status()
    # Try common response shapes
    # OpenAI-like: data['choices'][0]['message']['content']
    if isinstance(data, dict):
        if 'choices' in data and len(data['choices'])>0:
            ch = data['choices'][0]
            if isinstance(ch, dict) and 'message' in ch and isinstance(ch['message'], dict):
                return ch['message'].get('content') or ch.get('text') or json.dumps(ch)
            # older style
            if 'text' in ch:
                return ch['text']
        # direct text field
        if 'text' in data and isinstance(data['text'], str):
            return data['text']
    # fallback: return raw json string
    return json.dumps(data)
