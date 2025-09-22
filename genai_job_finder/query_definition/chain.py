from typing import Union
from langchain.schema.runnable import Runnable
from ..llm_factory import get_query_definition_llm
from .prompts import create_prompt_template
from .parser import JobQueryOutputParser
from .models import JobSearchQueries


def create_llm():
    """
    Create LLM instance for query definition using universal factory.
    
    Returns:
        Configured LLM instance
    """
    return get_query_definition_llm()


def create_job_query_chain() -> Runnable:
    """
    Create the complete LangChain pipeline for job query generation.
    
    Returns:
        Configured LangChain pipeline
    """
    # Create components
    llm = create_llm()
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
    
    def __init__(self):
        """Initialize ChainManager."""
        self._chain = None
    
    @property
    def chain(self) -> Runnable:
        """Get or create the chain instance."""
        if self._chain is None:
            self._chain = create_job_query_chain()
        return self._chain
    
    def process_resume(self, resume_content: str) -> JobSearchQueries:
        """Process resume through the chain."""
        return process_resume_with_chain(self.chain, resume_content)
    
    def reset_chain(self):
        """Reset the chain (useful for configuration changes)."""
        self._chain = None