import logging
from pathlib import Path
from typing import Optional, Dict, Any

from .config import QueryDefinitionConfig, get_default_config
from .chain import ChainManager
from .utils import load_resume_content, validate_resume_content, clean_resume_content
from .models import JobSearchQueries


logger = logging.getLogger(__name__)


class ResumeQueryService:
    """
    Main service class for generating job search queries from resumes.
    
    This service orchestrates the entire process of:
    1. Loading and processing resume files
    2. Analyzing content with LLM
    3. Generating structured job search queries
    """
    
    def __init__(self, config: Optional[QueryDefinitionConfig] = None):
        """
        Initialize the service with configuration.
        
        Args:
            config: Configuration object. If None, uses default config.
        """
        self.config = config or get_default_config()
        self.chain_manager = ChainManager(self.config)
        logger.info(f"Initialized ResumeQueryService with {self.config.llm_provider} provider")
    
    def process_resume_file(self, file_path: str) -> JobSearchQueries:
        """
        Process a resume file and generate job search queries.
        
        Args:
            file_path: Path to the resume file (PDF, DOC, or DOCX)
            
        Returns:
            Structured job search queries
            
        Raises:
            FileNotFoundError: If the file doesn't exist
            ValueError: If the file format is not supported or content is invalid
        """
        logger.info(f"Processing resume file: {file_path}")
        
        # Validate file path
        validated_path = self.config.validate_file_path(file_path)
        
        # Load resume content
        raw_content = load_resume_content(str(validated_path))
        
        # Validate content
        if not validate_resume_content(raw_content):
            raise ValueError("Resume content is too short or empty for analysis")
        
        # Clean content
        cleaned_content = clean_resume_content(raw_content)
        
        # Process with LLM
        return self.process_resume_content(cleaned_content)
    
    def process_resume_content(self, content: str) -> JobSearchQueries:
        """
        Process resume content directly (without file loading).
        
        Args:
            content: Resume text content
            
        Returns:
            Structured job search queries
            
        Raises:
            ValueError: If content is invalid
        """
        logger.info("Processing resume content with LLM")
        
        # Validate content
        if not validate_resume_content(content):
            raise ValueError("Resume content is too short or empty for analysis")
        
        # Clean content
        cleaned_content = clean_resume_content(content)
        
        # Process through chain
        try:
            result = self.chain_manager.process_resume(cleaned_content)
            logger.info("Successfully generated job search queries")
            return result
        except Exception as e:
            logger.error(f"Error processing resume: {e}")
            raise
    
    def get_config_info(self) -> Dict[str, Any]:
        """Get information about current configuration."""
        return {
            "llm_provider": self.config.llm_provider,
            "llm_model": self.config.llm_model,
            "temperature": self.config.temperature,
            "max_primary_titles": self.config.max_primary_titles,
            "max_secondary_titles": self.config.max_secondary_titles,
            "supported_extensions": self.config.supported_extensions
        }
    
    def update_config(self, new_config: QueryDefinitionConfig):
        """
        Update service configuration.
        
        Args:
            new_config: New configuration object
        """
        self.config = new_config
        self.chain_manager = ChainManager(self.config)
        logger.info(f"Updated configuration to use {self.config.llm_provider} provider")
    
    def health_check(self) -> bool:
        """
        Perform a health check to ensure the service is working.
        
        Returns:
            True if service is healthy, False otherwise
        """
        try:
            # Test with minimal content
            test_content = """
            John Doe
            Software Engineer
            Experience: Python, Machine Learning, 5 years
            Education: Computer Science
            """
            
            result = self.process_resume_content(test_content)
            return len(result.primary_titles) > 0
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False


# Convenience functions for easy usage
def analyze_resume(
    file_path: str, 
    config: Optional[QueryDefinitionConfig] = None
) -> JobSearchQueries:
    """
    Convenience function to analyze a resume file.
    
    Args:
        file_path: Path to resume file
        config: Optional configuration
        
    Returns:
        Job search queries
    """
    service = ResumeQueryService(config)
    return service.process_resume_file(file_path)


def analyze_resume_content(
    content: str,
    config: Optional[QueryDefinitionConfig] = None
) -> JobSearchQueries:
    """
    Convenience function to analyze resume content.
    
    Args:
        content: Resume text content
        config: Optional configuration
        
    Returns:
        Job search queries
    """
    service = ResumeQueryService(config)
    return service.process_resume_content(content)