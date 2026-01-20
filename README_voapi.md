# Project adapted for VoAPI (deepseek-ai-DeepSeek-R1)

Files added:
- voapi_adapter.py - adapter to call VoAPI chat/completions
- openai.py - compatibility shim to let existing code that imports openai continue to work
- health_check.py - simple health and voapi_test endpoint
- README_voapi.md - this file

Environment variables required:
- VOAPI_API_KEY (required)
- VOAPI_BASE_URL (optional, default: https://demo.voapi.top/v1)
- TG_TOKEN (required)
- PORT (optional, default: 8080)

Deployment notes:
- On Render, set VOAPI_API_KEY in Environment Secrets and set PORT to 8080 (or use default)
- For polling bots, use Background Worker with start command `python bot.py` (or your project's start file)
- For webhook bots, use Web Service and configure webhooks accordingly

Security:
- Never commit VOAPI_API_KEY to source control.
