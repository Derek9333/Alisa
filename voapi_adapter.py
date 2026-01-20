import os
import time
import json
import socket
import logging
import requests
from requests.exceptions import RequestException, ConnectionError, Timeout

logger = logging.getLogger(__name__)

DEFAULT_TIMEOUT = 15
DEFAULT_MAX_RETRIES = 3
DEFAULT_BACKOFF = 0.5

def _request_with_retries(method, url, json_payload=None, headers=None, timeout=DEFAULT_TIMEOUT):
    attempt = 0
    while True:
        try:
            resp = requests.request(method, url, json=json_payload, headers=headers, timeout=timeout)
            resp.raise_for_status()
            return resp
        except (RequestException, ConnectionError, Timeout) as e:
            attempt += 1
            logger.warning("Request attempt %d failed: %s", attempt, e)
            if attempt > DEFAULT_MAX_RETRIES:
                logger.exception("Max retries exceeded for %s %s", method, url)
                raise
            backoff = DEFAULT_BACKOFF * (2 ** (attempt - 1))
            time.sleep(backoff)

def _resolve_ok(host: str) -> bool:
    try:
        socket.getaddrinfo(host, None)
        return True
    except Exception as e:
        logger.debug("DNS resolution failed for %s: %s", host, e)
        return False

def _normalize_endpoint(base_url: str) -> str:
    base_url = base_url.rstrip('/')
    # If already contains chat/completions, assume user provided full endpoint
    if 'chat/completions' in base_url:
        return base_url
    # Otherwise append the standard path
    return base_url + '/v1/chat/completions'

def _extract_host(endpoint: str) -> str:
    try:
        return endpoint.split('://',1)[1].split('/')[0].split(':')[0]
    except Exception:
        return endpoint

def chat_completion(*, messages=None, api_key=None, base_url=None, timeout=DEFAULT_TIMEOUT, **kwargs):
    """Call VoAPI-compatible endpoint for DeepSeek model.
    Use VOAPI_BASE_URL env or pass base_url. Do not hardcode incorrect paths.
    """
    api_key = api_key or os.environ.get('VOAPI_API_KEY')
    base_url = base_url or os.environ.get('VOAPI_BASE_URL') or ''

    if not api_key:
        raise RuntimeError('VOAPI_API_KEY is not set (passed nor in environment)')
    if not base_url:
        raise RuntimeError('VOAPI_BASE_URL is not set. Set VOAPI_BASE_URL to your VoAPI endpoint (e.g. https://api.deepseek.com)')

    endpoint = _normalize_endpoint(base_url)
    host = _extract_host(endpoint)

    if not _resolve_ok(host):
        raise RuntimeError(f"Failed to resolve host '{host}'. Check VOAPI_BASE_URL and network/DNS settings.")

    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json',
    }

    payload = {}
    if messages is not None:
        payload['messages'] = messages
    # merge kwargs (model, temperature, max_tokens, etc)
    payload.update(kwargs)
    # default model not set here; caller provides model (e.g. 'deepseek/deepseek-r1')

    resp = _request_with_retries('POST', endpoint, json_payload=payload, headers=headers, timeout=timeout)

    try:
        data = resp.json()
    except Exception:
        return {'choices': [{'text': resp.text}]}

    # Normalize: if choices contain message.content return normalized structure
    if isinstance(data, dict) and 'choices' in data:
        normalized = []
        for c in data['choices']:
            if isinstance(c, dict):
                if 'message' in c and isinstance(c['message'], dict):
                    txt = c['message'].get('content') or c['message'].get('text') or ''
                else:
                    txt = c.get('text') or c.get('content') or ''
                normalized.append({'text': txt})
            else:
                normalized.append({'text': str(c)})
        return {'choices': normalized}
    if isinstance(data, dict) and 'text' in data:
        return {'choices': [{'text': data.get('text')}]}
    return {'choices': [{'text': json.dumps(data)}]}
