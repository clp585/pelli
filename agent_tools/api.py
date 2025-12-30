"""
API client module for Gemini API calls.
"""
import os
from typing import Any, Optional
from google import genai
from google.genai import types

from .retry import retry_with_backoff
from .config import logger

# Use the shared client from genai_client.py
from .genai_client import client as _shared_client

def get_client():
    """Get the shared Gemini API client."""
    return _shared_client

def get_vertex_client():
    """Get or create a Vertex AI client (singleton) for operations requiring Vertex AI.
    
    Vertex AI requires Application Default Credentials (ADC), NOT API keys.
    API keys are NOT supported by Vertex AI APIs.
    """
    global _vertex_client
    if _vertex_client is None:
        # Check environment variables for Vertex AI configuration
        vertexai_env = os.getenv("GOOGLE_GENAI_USE_VERTEXAI", "false").lower() in ("true", "1", "yes")
        project = os.getenv("GOOGLE_CLOUD_PROJECT")
        location = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
        
        # Warn if API key is present (Vertex AI doesn't use API keys)
        api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        if api_key:
            logger.warning(
                "API key detected in environment. Vertex AI does NOT use API keys. "
                "Application Default Credentials (ADC) are required instead."
            )
        
        # Try to create Vertex AI client
        # IMPORTANT: Do NOT pass api_key - Vertex AI requires ADC credentials
        try:
            if vertexai_env and project:
                # Explicit configuration from env vars
                _vertex_client = genai.Client(
                    vertexai=True,
                    project=project,
                    location=location
                    # NOTE: Do not pass api_key - Vertex AI requires ADC
                )
                logger.info(f"Created Vertex AI client with project={project}, location={location}")
            elif project:
                # Project is set, try with project and default location
                _vertex_client = genai.Client(
                    vertexai=True,
                    project=project,
                    location=location
                    # NOTE: Do not pass api_key - Vertex AI requires ADC
                )
                logger.info(f"Created Vertex AI client with project={project}, location={location} (from env)")
            else:
                # Try with just vertexai=True (will use ADC if configured)
                if vertexai_env:
                    # Env var is set but no project - try with defaults
                    _vertex_client = genai.Client(vertexai=True)
                else:
                    # No env vars set - try with explicit vertexai=True (uses ADC)
                    _vertex_client = genai.Client(vertexai=True)
                logger.info("Created Vertex AI client using Application Default Credentials")
                
        except Exception as e:
            _vertex_client = None
            logger.error(f"Failed to create Vertex AI client: {e}")
            raise ValueError(
                "In-painting requires Vertex AI with Application Default Credentials (ADC).\n"
                "API keys are NOT supported by Vertex AI.\n\n"
                "Setup instructions:\n"
                "1. Install Google Cloud SDK: https://cloud.google.com/sdk/docs/install\n"
                "2. Run: gcloud auth application-default login\n"
                "3. Set environment variables:\n"
                "   GOOGLE_GENAI_USE_VERTEXAI=true\n"
                "   GOOGLE_CLOUD_PROJECT=your-project-id\n"
                "   GOOGLE_CLOUD_LOCATION=us-central1 (optional)\n\n"
                "OR set GOOGLE_APPLICATION_CREDENTIALS to a service account JSON file path.\n"
                "See: https://cloud.google.com/docs/authentication/application-default-credentials"
            ) from e
    return _vertex_client

# For backward compatibility
client = _shared_client


@retry_with_backoff()
def _call_generate_content(model: str, contents: list, config: Optional[Any] = None):
    """
    Wrapper for client.models.generate_content with automatic retry logic.
    This function is decorated with exponential backoff retry.
    """
    client = get_client()
    if config:
        return client.models.generate_content(model=model, contents=contents, config=config)
    else:
        return client.models.generate_content(model=model, contents=contents)

