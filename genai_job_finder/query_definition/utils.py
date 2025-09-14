from pathlib import Path
from typing import List
from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader
from langchain.schema import Document


def load_resume_content(file_path: str) -> str:
    """
    Load and extract text content from a resume file.
    
    Args:
        file_path: Path to the resume file (PDF, DOC, or DOCX)
        
    Returns:
        Extracted text content from the resume
        
    Raises:
        FileNotFoundError: If the file doesn't exist
        ValueError: If the file format is not supported
    """
    file_path = Path(file_path)
    
    if not file_path.exists():
        raise FileNotFoundError(f"Resume file not found: {file_path}")
    
    # Load document based on file extension
    if file_path.suffix.lower() == ".pdf":
        loader = PyPDFLoader(str(file_path))
    elif file_path.suffix.lower() in [".doc", ".docx"]:
        loader = Docx2txtLoader(str(file_path))
    else:
        raise ValueError(f"Unsupported file format: {file_path.suffix}")
    
    # Load and extract text
    documents: List[Document] = loader.load()
    resume_content = "\n".join([doc.page_content for doc in documents])
    
    return resume_content


def validate_resume_content(content: str, min_length: int = 100) -> bool:
    """
    Validate that resume content is sufficient for analysis.
    
    Args:
        content: The extracted resume text
        min_length: Minimum character length required
        
    Returns:
        True if content is valid, False otherwise
    """
    if not content or not content.strip():
        return False
    
    if len(content.strip()) < min_length:
        return False
    
    return True


def clean_resume_content(content: str) -> str:
    """
    Clean and normalize resume content for better LLM processing.
    
    Args:
        content: Raw resume text content
        
    Returns:
        Cleaned and normalized text
    """
    # Remove excessive whitespace
    lines = [line.strip() for line in content.split('\n')]
    lines = [line for line in lines if line]  # Remove empty lines
    
    # Join with single newlines
    cleaned_content = '\n'.join(lines)
    
    # Remove multiple consecutive spaces
    import re
    cleaned_content = re.sub(r'\s+', ' ', cleaned_content)
    
    return cleaned_content


def get_supported_extensions() -> List[str]:
    """Get list of supported file extensions."""
    return [".pdf", ".doc", ".docx"]


def is_supported_file(file_path: str) -> bool:
    """Check if file extension is supported."""
    return Path(file_path).suffix.lower() in get_supported_extensions()