# Universal LLM Configuration
# Easy model switching for all modules - just change the model names below

# =============================================================================
# MODULE LLM ASSIGNMENTS - EDIT THESE TO SWITCH MODELS
# =============================================================================

# Data Cleaner Module
data_cleaner_llm = "gpt-3.5-turbo"

# Query Definition Module  
query_definition_llm = "gpt-3.5-turbo"

# Frontend Chat Module
frontend_chat_llm = "llama3.2"

# Frontend Resume Analysis Module
frontend_resume_llm = "gpt-3.5-turbo"

# =============================================================================
# MODEL CONFIGURATIONS - DO NOT EDIT BELOW (automatically handled)
# =============================================================================

import os
from typing import Dict, Any, Optional

# Load environment variables with explicit error handling
from dotenv import load_dotenv

# Load from .env file - fail if there are issues
env_loaded = load_dotenv()
if not env_loaded:
    raise RuntimeError("Failed to load .env file. Make sure .env exists and is readable.")

# Get the OpenAI API key - fail if not found for OpenAI models
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    print("WARNING: OPENAI_API_KEY not found in environment. OpenAI models will not work.")

# Model registry with their default configurations
MODEL_CONFIGS = {
    # OpenAI Models
    "gpt-3.5-turbo": {
        "provider": "openai",
        "model": "gpt-3.5-turbo",
        "temperature": 0.1,
        "max_tokens": 1000,
        "api_key": OPENAI_API_KEY
    },
    "gpt-4": {
        "provider": "openai", 
        "model": "gpt-4",
        "temperature": 0.1,
        "max_tokens": 1000,
        "api_key": OPENAI_API_KEY
    },
    "gpt-4-turbo": {
        "provider": "openai",
        "model": "gpt-4-turbo",
        "temperature": 0.1,
        "max_tokens": 1000,
        "api_key": OPENAI_API_KEY
    },
    "gpt-4o-mini": {
        "provider": "openai",
        "model": "gpt-4o-mini",
        "temperature": 0.1,
        "max_tokens": 1000,
        "api_key": OPENAI_API_KEY
    },
    "gpt-5-nano": {
        "provider": "openai",
        "model": "gpt-5-nano",
        "temperature": 0.1,
        "max_tokens": 1000,
        "api_key": OPENAI_API_KEY
    },
    
    # Ollama Models
    "llama3.2": {
        "provider": "ollama",
        "model": "llama3.2",
        "temperature": 0.1,
        "max_tokens": 1000,
        "base_url": "http://localhost:11434"
    },
    "llama3.1": {
        "provider": "ollama",
        "model": "llama3.1", 
        "temperature": 0.1,
        "max_tokens": 1000,
        "base_url": "http://localhost:11434"
    },
    "mistral": {
        "provider": "ollama",
        "model": "mistral",
        "temperature": 0.1,
        "max_tokens": 1000,
        "base_url": "http://localhost:11434"
    },
    "codellama": {
        "provider": "ollama",
        "model": "codellama",
        "temperature": 0.1,
        "max_tokens": 1000,
        "base_url": "http://localhost:11434"
    },
    "gemma2:27b": {
        "provider": "ollama",
        "model": "gemma2:27b",
        "temperature": 0.1,
        "max_tokens": 1000,
        "base_url": "http://localhost:11434"
    }
}

def get_model_config(model_name: str) -> Dict[str, Any]:
    """Get configuration for a specific model.
    
    Args:
        model_name: Name of the model (e.g., 'gpt-3.5-turbo', 'llama3.2')
        
    Returns:
        Dictionary with model configuration
        
    Raises:
        ValueError: If model is not found in registry
    """
    if model_name not in MODEL_CONFIGS:
        available_models = list(MODEL_CONFIGS.keys())
        raise ValueError(f"Model '{model_name}' not found. Available models: {available_models}")
    
    config = MODEL_CONFIGS[model_name].copy()
    
    # Validate OpenAI API key if needed
    if config["provider"] == "openai" and not config.get("api_key"):
        raise ValueError(f"OpenAI API key is required for model '{model_name}'. Please set OPENAI_API_KEY environment variable.")
    
    return config

def get_data_cleaner_config() -> Dict[str, Any]:
    """Get LLM config for data cleaner module."""
    return get_model_config(data_cleaner_llm)

def get_query_definition_config() -> Dict[str, Any]:
    """Get LLM config for query definition module."""
    return get_model_config(query_definition_llm)

def get_frontend_chat_config() -> Dict[str, Any]:
    """Get LLM config for frontend chat module."""
    return get_model_config(frontend_chat_llm)

def get_frontend_resume_config() -> Dict[str, Any]:
    """Get LLM config for frontend resume analysis module.""" 
    return get_model_config(frontend_resume_llm)

# Module configuration mapping
MODULE_CONFIGS = {
    "data_cleaner": get_data_cleaner_config,
    "query_definition": get_query_definition_config,
    "frontend_chat": get_frontend_chat_config,
    "frontend_resume": get_frontend_resume_config
}

def get_module_config(module_name: str) -> Dict[str, Any]:
    """Get LLM config for any module.
    
    Args:
        module_name: Name of the module
        
    Returns:
        Dictionary with model configuration for the module
    """
    if module_name not in MODULE_CONFIGS:
        available_modules = list(MODULE_CONFIGS.keys())
        raise ValueError(f"Module '{module_name}' not found. Available modules: {available_modules}")
    
    return MODULE_CONFIGS[module_name]()