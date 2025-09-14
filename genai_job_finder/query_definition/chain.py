from typing import Union
from langchain_ollama import OllamaLLM
from langchain_openai import ChatOpenAI
from langchain.schema.runnable import Runnable

from .config import QueryDefinitionConfig
from .prompts import create_prompt_template
from .parser import JobQueryOutputParser
from .models import JobSearchQueries


def create_llm(config: QueryDefinitionConfig) -> Union[ChatOpenAI, OllamaLLM]:
    """
    Create LLM instance based on configuration.
    
    Args:
        config: Configuration object with LLM settings
        
    Returns:
        Configured LLM instance
        
    Raises:
        ValueError: If provider is not supported or configuration is invalid
    """
    llm_config = config.get_llm_config()
    
    if llm_config["provider"] == "openai":
        if not llm_config["api_key"]:
            raise ValueError(
                "OpenAI API key is required but not provided. "
                "Please set OPENAI_API_KEY environment variable or create a .env file with your API key."
            )
        
        return ChatOpenAI(
            model=llm_config["model"],
            temperature=llm_config["temperature"],
            max_tokens=llm_config["max_tokens"],
            api_key=llm_config["api_key"]
        )
    
    elif llm_config["provider"] == "ollama":
        return OllamaLLM(
            model=llm_config["model"],
            base_url=llm_config["base_url"],
            temperature=llm_config["temperature"],
            num_predict=llm_config["num_predict"]
        )
    
    else:
        raise ValueError(f"Unsupported LLM provider: {llm_config['provider']}")


def create_job_query_chain(config: QueryDefinitionConfig) -> Runnable:
    """
    Create the complete LangChain pipeline for job query generation.
    
    Args:
        config: Configuration object with settings
        
    Returns:
        Configured LangChain pipeline
    """
    # Create components
    llm = create_llm(config)
    prompt_template = create_prompt_template()
    parser = JobQueryOutputParser()
    
    # Build the chain
    chain = prompt_template | llm | parser
    
    return chain


def process_resume_with_chain(
    chain: Runnable, 
    resume_content: str
) -> JobSearchQueries:
    """
    Process resume content through the LangChain pipeline.
    
    Args:
        chain: Configured LangChain pipeline
        resume_content: Text content from resume
        
    Returns:
        Structured job search queries
    """
    result = chain.invoke({"resume_content": resume_content})
    return result


class ChainManager:
    """Manager class for handling LangChain operations."""
    
    def __init__(self, config: QueryDefinitionConfig):
        """Initialize with configuration."""
        self.config = config
        self._chain = None
    
    @property
    def chain(self) -> Runnable:
        """Get or create the chain instance."""
        if self._chain is None:
            self._chain = create_job_query_chain(self.config)
        return self._chain
    
    def process_resume(self, resume_content: str) -> JobSearchQueries:
        """Process resume through the chain."""
        return process_resume_with_chain(self.chain, resume_content)
    
    def reset_chain(self):
        """Reset the chain (useful for configuration changes)."""
        self._chain = None