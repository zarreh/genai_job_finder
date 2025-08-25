from langchain_ollama import OllamaLLM
from .config import CleanerConfig


def get_llm(config: CleanerConfig = None) -> OllamaLLM:
    """Get configured LLM instance."""
    if config is None:
        config = CleanerConfig()
    
    return OllamaLLM(
        model=config.ollama_model,
        base_url=config.ollama_base_url,
        temperature=config.ollama_temperature,
        num_predict=config.ollama_max_tokens
    )
