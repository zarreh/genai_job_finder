from ..llm_factory import get_data_cleaner_llm


def get_llm():
    """Get configured LLM instance for data cleaner."""
    return get_data_cleaner_llm()
