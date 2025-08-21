"""
Configuration settings for the frontend application
"""
from dataclasses import dataclass
from typing import Dict, Any

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
    time_filter_options: Dict[str, int] = None
    
    def __post_init__(self):
        if self.time_filter_options is None:
            self.time_filter_options = {
                "Any time": None,
                "Past 24 hours": 1,
                "Past week": 7,
                "Past month": 30
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
