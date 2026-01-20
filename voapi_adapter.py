import os
import time
import json
import requests

DEFAULT_TIMEOUT = 15
DEFAULT_MAX_RETRIES = 3
DEFAULT_BACKOFF = 0.5

def _request_with_retries(method, url, max_retries=DEFAULT_MAX_RETRIES, timeout=DEFAULT_TIMEOUT, **kwargs):
    attempt = 0
    while True:
        try:
            resp = requests.request(method, url, timeout=timeout, **kwargs)
            resp.raise_for_status()
            return resp
        except requests.RequestException as e:
            attempt += 1
            if attempt > max_retries:
                raise
            backoff = DEFAULT_BACKOFF * (2 ** (attempt - 1))
            time.sleep(backoff)

def chat_completion(*, prompt=None, api_key=None, base_url=None, timeout=DEFAULT_TIMEOUT, **kwargs):
    """Call VoAPI-compatible endpoint. Returns parsed JSON-like response similar to OpenAI SDK.
    If VOAPI_API_KEY is not provided, raises RuntimeError.
    """
    api_key = api_key or os.environ.get('VOAPI_API_KEY')
    base_url = base_url or os.environ.get('VOAPI_BASE_URL') or 'https://api.voapi.ai/v3/openai'
    if not api_key:
        raise RuntimeError('VOAPI_API_KEY is not set (passed nor in environment)')

    url = base_url.rstrip('/') + '/v1/chat/completions'
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json',
    }
    payload = dict(kwargs)
    if prompt is not None and 'messages' not in payload:
        payload['messages'] = [{'role': 'user', 'content': prompt}]
    # Provide defaults
    payload.setdefault('model', payload.get('model', 'gpt-4o-mini'))
    payload.setdefault('temperature', payload.get('temperature', 0.7))
    payload.setdefault('max_tokens', payload.get('max_tokens', 512))

    resp = _request_with_retries('POST', url, json=payload, headers=headers, timeout=timeout)
    # Try to parse JSON
    try:
        data = resp.json()
    except Exception:
        # If response is plain text, return as text
        return {'choices': [{'text': resp.text}]}

    # Normalize to expected shape
    # If VoAPI returns choices with message.content, keep it.
    if isinstance(data, dict) and 'choices' in data:
        return data
    # If API returns text field
    if isinstance(data, dict) and 'text' in data:
        return {'choices': [{'text': data.get('text')}]}
    return {'choices': [{'text': json.dumps(data)}]}
