import os
from dataclasses import dataclass
from typing import Set
from dotenv import load_dotenv

load_dotenv()

def get_api_key() -> str:
    """Retrieve API key from environment or raise error"""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("API key not found. Please set the OPENAI_API_KEY environment variable.")
    return api_key


@dataclass
class ChatConfig:
    """Configuration for the chat application"""

    api_key: str = get_api_key()  # This becomes a class variable
    model: str = os.getenv("CLIENT_TYPE") == "azure" and os.getenv("AZURE_DEPLOYMENT") or os.getenv("OPENAI_MODEL")
    exit_commands: Set[str] = frozenset({"/exit", "/quit"})
    base_url: str = os.getenv("OPENAI_BASE_URL", "") #"http://localhost:8000/v1"
    use_azure: bool = os.getenv("CLIENT_TYPE") == "azure"

    def __init__(self):
        # Prevent instantiation
        raise TypeError("ChatConfig is not meant to be instantiated")
