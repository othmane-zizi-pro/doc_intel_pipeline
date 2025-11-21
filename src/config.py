"""
Configuration for LLM APIs.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

# Gemini API Configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = "gemini-2.5-flash"

# OpenAI API Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = "gpt-4o"  # Best OpenAI model for structured extraction

# Ollama Configuration (local)
OLLAMA_MODEL = "qwen2.5:7b"
OLLAMA_URL = "http://localhost:11434"

# Multi-model orchestration configuration
MODEL_PRIORITY = [
    "openai",    # Try OpenAI first (best quality, no safety filters on business docs)
    "gemini",    # Fallback to Gemini
    "ollama"     # Last resort: local Ollama (if available)
]

# Default model provider
DEFAULT_PROVIDER = "openai"
