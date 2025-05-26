# backend/config.py

# -------------------------
# LLM API Configuration
# -------------------------
# Choose and configure one LLM API provider.
# The agent.py currently uses a placeholder LLMClient.
# To use a real LLM, you will need to:
# 1. Install the required Python library (e.g., 'groq', 'openai').
# 2. Update LLMClient in agent.py to use the chosen library and API key.
# 3. Store your API key here and load it in LLMClient.

# Example for Groq API
GROQ_API_KEY = "your_groq_api_key_here" 
# Get yours from https://console.groq.com/keys

# Example for OpenAI API
OPENAI_API_KEY = "your_openai_api_key_here"
# Get yours from https://platform.openai.com/api-keys

# Generic LLM API Key (if you implement a client that uses a generic key)
# LLM_API_KEY = "your_llm_api_key_here"
# LLM_API_BASE_URL = "your_llm_api_base_url_if_needed" # For self-hosted or other models

# -------------------------
# Sandbox Configuration
# -------------------------
# Timeout for code execution in the sandbox (in seconds)
# This can be overridden when calling the sandbox execution function.
DEFAULT_SANDBOX_TIMEOUT = 30  # seconds

# Default Docker image for Python execution in sandbox.py
# Ensure this image is available or can be pulled.
DEFAULT_PYTHON_IMAGE = "python:3.10-slim"

# -------------------------
# Other Configurations
# -------------------------
# Add any other global configurations your application might need.
# Example: LOG_LEVEL = "INFO"

print("config.py loaded") # Optional: for debugging to confirm it's imported
