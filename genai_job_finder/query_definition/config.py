import os
from typing import Optional, Dict, Any
from dataclasses import dataclass
from pathlib import Path
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())


@dataclass
class QueryDefinitionConfig:
    """Configuration for query definition service."""
    
    # LLM Settings
    llm_provider: str = "openai"  # "openai" or "ollama"
    llm_model: str = "gpt-3.5-turbo"  # or "llama3.2" for ollama
    temperature: float = 0.1
    max_tokens: int = 1000
    
    # Ollama Settings
    ollama_base_url: str = "http://localhost:11434"
    ollama_num_predict: int = 1000
    
    # OpenAI Settings
    openai_api_key: Optional[str] = None
    
    # File Processing
    supported_extensions: tuple = (".pdf", ".doc", ".docx")
    
    # Output Settings
    max_primary_titles: int = 5
    max_secondary_titles: int = 8
    max_skill_queries: int = 3
    
    def __post_init__(self):
        """Post-initialization to set API key from environment if not provided."""
        if self.llm_provider == "openai" and self.openai_api_key is None:
            self.openai_api_key = os.getenv("OPENAI_API_KEY")
    
    def get_llm_config(self) -> Dict[str, Any]:
        """Get LLM configuration dictionary."""
        if self.llm_provider == "openai":
            return {
                "provider": "openai",
                "model": self.llm_model,
                "temperature": self.temperature,
                "max_tokens": self.max_tokens,
                "api_key": self.openai_api_key
            }
        elif self.llm_provider == "ollama":
            return {
                "provider": "ollama",
                "model": self.llm_model,
                "base_url": self.ollama_base_url,
                "temperature": self.temperature,
                "num_predict": self.ollama_num_predict
            }
        else:
            raise ValueError(f"Unsupported LLM provider: {self.llm_provider}")
    
    def validate_file_path(self, file_path: str) -> Path:
        """Validate and return Path object for resume file."""
        path = Path(file_path)
        
        if not path.exists():
            raise FileNotFoundError(f"Resume file not found: {file_path}")
        
        if path.suffix.lower() not in self.supported_extensions:
            raise ValueError(
                f"Unsupported file format: {path.suffix}. "
                f"Supported formats: {', '.join(self.supported_extensions)}"
            )
        
        return path


def get_default_config() -> QueryDefinitionConfig:
    """Get default configuration instance."""
    return QueryDefinitionConfig()


def get_openai_config() -> QueryDefinitionConfig:
    """Get OpenAI-specific configuration."""
    return QueryDefinitionConfig(
        llm_provider="openai",
        llm_model="gpt-3.5-turbo"
    )


def get_ollama_config() -> QueryDefinitionConfig:
    """Get Ollama-specific configuration."""
    return QueryDefinitionConfig(
        llm_provider="ollama",
        llm_model="llama3.2"
    )