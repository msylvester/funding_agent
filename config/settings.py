"""
Application configuration settings
"""

# Streamlit App Configuration
APP_CONFIG = {
    'page_title': 'Funding Intelligence RAG',
    'page_icon': '💰',
    'layout': 'wide',
    'sidebar_state': 'collapsed'
}

# Database Configuration
DATABASE_CONFIG = {
    'mongodb_uri': 'mongodb://localhost:27017/',
    'database_name': 'funded',
    'collection_name': 'companies'
}

# API Configuration
API_CONFIG = {
    'openrouter_base_url': 'https://openrouter.ai/api/v1/chat/completions',
    'default_model': 'anthropic/claude-3-haiku',
    'max_tokens': 500,
    'temperature': 0.1
}

# Data Processing Configuration
DATA_CONFIG = {
    'similarity_threshold': 0.1,
    'max_features': 1000,
    'top_k_results': 3
}

# File Paths
FILE_PATHS = {
    'funding_data': 'funding_data.json',
    'funding_data_complete': 'funding_data_complete.json',
    'final_scrape': 'final_scrape.json',
    'scraped_one': 'scraped_one.json'
}