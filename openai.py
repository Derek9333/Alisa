"""Local shim to provide a minimal OpenAI-like interface expected by the project.

This shim delegates chat completions to voapi_adapter.chat_completion(...).
If you want to use the official OpenAI SDK, remove/rename this file and install 'openai' package.
"""
import os
import importlib

class _CompletionsProxy:
    def __init__(self, client):
        self._client = client

    def create(self, **kwargs):
        # Delegate to voapi_adapter.chat_completion
        try:
            voapi = importlib.import_module('voapi_adapter')
        except Exception as e:
            raise RuntimeError("voapi_adapter module not available. Ensure VOAPI adapter exists or install the official openai package.") from e
        api_key = kwargs.pop('api_key', self._client.api_key)
        base_url = kwargs.pop('base_url', self._client.base_url)
        return voapi.chat_completion(api_key=api_key, base_url=base_url, **kwargs)

class OpenAI:
    def __init__(self, api_key=None, base_url=None, **kwargs):
        self.api_key = api_key or os.environ.get('VOAPI_API_KEY')
        self.base_url = base_url or os.environ.get('VOAPI_BASE_URL') or 'https://api.voapi.ai/v3/openai'
        self.chat = type('C', (), {'completions': _CompletionsProxy(self)})()
