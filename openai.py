"""
openai.py shim that redirects certain calls to VoAPI via voapi_adapter.
"""
import logging
from voapi_adapter import chat_completion, DEFAULT_MODEL

logger = logging.getLogger(__name__)

api_key = None
api_base = None

class ChatCompletion:
    @staticmethod
    def create(model=None, messages=None, **kwargs):
        msgs = messages or []
        model_to_use = model or DEFAULT_MODEL
        try:
            text = chat_completion(msgs, model=model_to_use, **kwargs)
        except Exception as e:
            logger.exception("VoAPI ChatCompletion error")
            raise
        return {"choices":[{"message":{"role":"assistant","content": text}}]}

class Completion:
    @staticmethod
    def create(model=None, prompt=None, **kwargs):
        if isinstance(prompt, str):
            messages = [{"role":"user","content": prompt}]
        else:
            messages = prompt or []
        text = chat_completion(messages, model=model or DEFAULT_MODEL, **kwargs)
        return {"choices":[{"text": text}]}
