from abc import ABC, abstractmethod

import ollama

from src.utils.config import LLMConfig
from src.utils.logger import logger


class OllamaManager:
    """Manages Ollama model availability."""

    @staticmethod
    def ensure_ready(model_name: str = "llama3.2") -> bool:
        """Ensure Ollama model is downloaded and ready."""
        try:
            models = ollama.list()
            if not any(model_name in m["name"] for m in models["models"]):
                logger.info(f"Downloading {model_name}...")
                ollama.pull(model_name)
            logger.info(f"{model_name} ready")
            return True
        except Exception as e:
            logger.info(f"Ollama not running! {e}")
            logger.info("   Run: ollama serve")
            logger.info(f"   Then: ollama pull {model_name}")
            return False


class BaseGenerator(ABC):
    @abstractmethod
    def generate(self, prompt: str) -> str:
        """Generate text from a prompt."""
        pass


class OllamaGenerator(BaseGenerator):
    def __init__(self, config: LLMConfig, auto_setup: bool = True) -> None:
        self.model = config.model_name
        self.temperature = config.temperature
        if auto_setup:
            OllamaManager.ensure_ready(self.model)

    def generate(self, prompt: str) -> str:
        """Generate text using Ollama."""
        try:
            response = ollama.chat(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                options={"temperature": self.temperature},
            )
            return response["message"]["content"]
        except Exception as e:
            return f"Error: {e}"
