# Universal LLM Factory
# Simple functions to create LLM instances - no classes, just functions

from typing import Union
from langchain_ollama import OllamaLLM
from langchain_openai import ChatOpenAI
from .llm_config import get_module_config, get_model_config

def create_llm(model_name: str):
    """Create an LLM instance from model name.
    
    Args:
        model_name: Name of the model (e.g., 'gpt-3.5-turbo', 'llama3.2')
        
    Returns:
        LLM instance (ChatOpenAI or OllamaLLM)
    """
    config = get_model_config(model_name)
    
    if config["provider"] == "openai":
        return ChatOpenAI(
            model=config["model"],
            temperature=config["temperature"],
            max_tokens=config["max_tokens"],
            api_key=config["api_key"]
        )
    elif config["provider"] == "ollama":
        return OllamaLLM(
            model=config["model"],
            temperature=config["temperature"],
            num_predict=config["max_tokens"],
            base_url=config["base_url"]
        )
    else:
        raise ValueError(f"Unsupported provider: {config['provider']}")

def create_llm_for_module(module_name: str):
    """Create an LLM instance for a specific module.
    
    Args:
        module_name: Name of the module ('data_cleaner', 'query_definition', etc.)
        
    Returns:
        LLM instance configured for that module
    """
    config = get_module_config(module_name)
    
    if config["provider"] == "openai":
        return ChatOpenAI(
            model=config["model"],
            temperature=config["temperature"],
            max_tokens=config["max_tokens"],
            api_key=config["api_key"]
        )
    elif config["provider"] == "ollama":
        return OllamaLLM(
            model=config["model"],
            temperature=config["temperature"],
            num_predict=config["max_tokens"],
            base_url=config["base_url"]
        )
    else:
        raise ValueError(f"Unsupported provider: {config['provider']}")

# Convenience functions for each module
def get_data_cleaner_llm():
    """Get LLM for data cleaner module."""
    return create_llm_for_module("data_cleaner")

def get_query_definition_llm():
    """Get LLM for query definition module."""
    return create_llm_for_module("query_definition")

def get_frontend_chat_llm():
    """Get LLM for frontend chat module."""
    return create_llm_for_module("frontend_chat")

def get_frontend_resume_llm():
    """Get LLM for frontend resume analysis module."""
    return create_llm_for_module("frontend_resume")