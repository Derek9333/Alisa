"""Local shim to provide a minimal OpenAI-like interface expected by the project.

This shim avoids import-time failures when a local file named `openai.py` shadows the real package.
It provides a small `OpenAI` class with `chat` -> `completions.create(...)` API that delegates
to the project's voapi adapter if available.

If you plan to use the official `openai` package, rename or remove this file.
"""
import os
import importlib

class _ChatCompletions:
    def __init__(self, parent):
        self._parent = parent

    def create(self, **kwargs):
        """Delegate to voapi_adapter.chat_completion if available, else raise informative error."""
        try:
            voapi = importlib.import_module('voapi_adapter')
        except Exception as e:
            raise RuntimeError(
                "voapi_adapter module not available. Ensure VOAPI adapter exists or install the official openai package."
            ) from e
        # Use api_key/base_url from parent unless explicitly provided
        api_key = kwargs.pop('api_key', self._parent.api_key)
        base_url = kwargs.pop('base_url', self._parent.base_url)
        return voapi.chat_completion(api_key=api_key, base_url=base_url, **kwargs)

class OpenAI:
    def __init__(self, api_key=None, base_url=None, **kwargs):
        # store provided credentials; project code may pass these or rely on env vars
        self.api_key = api_key or os.environ.get('VOAPI_API_KEY')
        self.base_url = base_url or os.environ.get('VOAPI_BASE_URL')
        self.chat = type('X', (), {'completions': _ChatCompletions(self)})()
        # backward compatibility: some code may expect .ChatCompletion or .chat_completions
        self.chat_completions = _ChatCompletions(self)