import os
from openai import OpenAI

def get_grok_client():
    """
    Initializes and returns an OpenAI client configured for the xAI Grok API.
    Expects XAI_API_KEY to be set in the environment.
    """
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        # Provide a default or raise an exception - for local dev, might want to raise
        # but let's let the user know if it's missing.
        raise ValueError("GROQ_API_KEY environment variable is not set. Please provide your Groq API key.")
        
    return OpenAI(
        api_key=api_key,
        base_url="https://api.groq.com/openai/v1",
    )
