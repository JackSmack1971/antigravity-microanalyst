import os
import logging
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

def get_openrouter_llm(model_name: str = None, temperature: float = 0.7):
    """
    Returns a ChatOpenAI instance configured for OpenRouter.
    """
    api_key = os.getenv("OPENROUTER_API_KEY")
        
    if not api_key:
        logger.warning("OPENROUTER_API_KEY not found. Helper functions may fail or return mocks.")
        return None

    # Default to a cost-effective model if not specified in env or arg
    if not model_name:
        model_name = os.getenv("OPENROUTER_MODEL", "google/gemini-2.0-flash-exp:free")

    return ChatOpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=api_key,
        model=model_name,
        temperature=temperature,
        default_headers={
            "HTTP-Referer": "https://antigravity.microanalyst", # Required by OpenRouter
            "X-Title": "Antigravity Microanalyst"
        }
    )
