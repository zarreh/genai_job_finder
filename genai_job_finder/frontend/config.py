import os
from dataclasses import dataclass
from typing import Dict, Any, Optional
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

@dataclass
class FrontendConfig:
    """Configuration for the Streamlit frontend"""
    
    # App settings
    app_title: str = "GenAI Job Finder"
    app_icon: str = "🔍"
    layout: str = "wide"
    
    # Pagination settings
    jobs_per_page: int = 15
    max_pages_per_search: int = 10
    default_pages_to_search: int = 3
    
    # Search settings
    default_location: str = ""
    search_delay_min: float = 2.0
    search_delay_max: float = 4.0
    
    # Time filter options
    time_filter_options: Dict[str, str] = None
    
    def __post_init__(self):
        if self.time_filter_options is None:
            self.time_filter_options = {
                "Any time": None,
                "Past hour": "r3600",      # 1 hour in seconds
                "Past 24 hours": "r86400", # 24 hours in seconds
                "Past week": "r604800",    # 7 days in seconds
                "Past month": "r2592000"   # 30 days in seconds
            }
    
    @classmethod
    def get_streamlit_config(cls) -> Dict[str, Any]:
        """Get configuration for Streamlit page setup"""
        config = cls()
        return {
            "page_title": config.app_title,
            "page_icon": config.app_icon,
            "layout": config.layout,
            "initial_sidebar_state": "expanded"
        }


@dataclass
class LLMConfig:
    """Configuration for individual LLM instances."""
    provider: str  # "openai" or "ollama"
    model: str
    temperature: float = 0.7
    max_tokens: Optional[int] = None
    
    # OpenAI specific
    api_key: Optional[str] = None
    
    # Ollama specific
    base_url: str = "http://localhost:11434"
    num_predict: Optional[int] = None
    
    def __post_init__(self):
        """Load API key from environment if not provided."""
        if self.provider == "openai" and self.api_key is None:
            self.api_key = os.getenv("OPENAI_API_KEY")


@dataclass 
class ChatConfig:
    """Configuration for the entire chat system."""
    
    # Chat LLM configuration
    chat_llm: LLMConfig
    
    # Resume analysis LLM configuration  
    resume_llm: LLMConfig
    
    # Chat behavior settings
    max_chat_history: int = 2000
    memory_token_limit: int = 2000
    enable_topic_filtering: bool = True
    
    # File upload settings
    max_file_size_mb: int = 10
    allowed_extensions: tuple = ('.pdf', '.doc', '.docx')


def get_default_chat_config() -> ChatConfig:
    """Get default chat configuration with Ollama for both chat and resume analysis."""
    return ChatConfig(
        chat_llm=LLMConfig(
            provider="ollama",
            model="llama3.2", 
            temperature=0.7
        ),
        resume_llm=LLMConfig(
            provider="ollama",
            model="llama3.2",
            temperature=0.1  # Lower temperature for resume analysis
        )
    )


def get_mixed_chat_config() -> ChatConfig:
    """Get mixed configuration: Ollama for chat, OpenAI for resume analysis."""
    return ChatConfig(
        chat_llm=LLMConfig(
            provider="ollama",
            model="llama3.2",
            temperature=0.7
        ),
        resume_llm=LLMConfig(
            provider="openai", 
            model="gpt-3.5-turbo",
            temperature=0.1,
            max_tokens=1000
        )
    )


def get_openai_chat_config() -> ChatConfig:
    """Get OpenAI configuration for both chat and resume analysis."""
    return ChatConfig(
        chat_llm=LLMConfig(
            provider="openai",
            model="gpt-3.5-turbo",
            temperature=0.7,
            max_tokens=1500
        ),
        resume_llm=LLMConfig(
            provider="openai",
            model="gpt-3.5-turbo", 
            temperature=0.1,
            max_tokens=1000
        )
    )


def get_chat_config_from_env() -> ChatConfig:
    """Load configuration from environment variables."""
    
    # Chat LLM configuration
    chat_provider = os.getenv("CHAT_LLM_PROVIDER", "ollama")
    chat_model = os.getenv("CHAT_LLM_MODEL", "llama3.2")
    chat_temperature = float(os.getenv("CHAT_LLM_TEMPERATURE", "0.7"))
    
    # Resume LLM configuration  
    resume_provider = os.getenv("RESUME_LLM_PROVIDER", "ollama")
    resume_model = os.getenv("RESUME_LLM_MODEL", "llama3.2")
    resume_temperature = float(os.getenv("RESUME_LLM_TEMPERATURE", "0.1"))
    
    return ChatConfig(
        chat_llm=LLMConfig(
            provider=chat_provider,
            model=chat_model,
            temperature=chat_temperature,
            max_tokens=int(os.getenv("CHAT_LLM_MAX_TOKENS", "1500")) if os.getenv("CHAT_LLM_MAX_TOKENS") else None
        ),
        resume_llm=LLMConfig(
            provider=resume_provider,
            model=resume_model, 
            temperature=resume_temperature,
            max_tokens=int(os.getenv("RESUME_LLM_MAX_TOKENS", "1000")) if os.getenv("RESUME_LLM_MAX_TOKENS") else None
        ),
        max_chat_history=int(os.getenv("CHAT_MAX_HISTORY", "2000")),
        enable_topic_filtering=os.getenv("CHAT_TOPIC_FILTERING", "true").lower() == "true"
    )


def get_chat_config() -> ChatConfig:
    """Get chat configuration based on environment settings."""
    config_mode = os.getenv("CHAT_CONFIG_MODE", "default")
    
    if config_mode == "mixed":
        return get_mixed_chat_config()
    elif config_mode == "openai": 
        return get_openai_chat_config()
    elif config_mode == "env":
        return get_chat_config_from_env()
    else:
        return get_default_chat_config()
