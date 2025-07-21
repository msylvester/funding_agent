# Funding Scraper

A comprehensive funding data scraper and RAG (Retrieval-Augmented Generation) agent for tracking startup funding rounds from TechCrunch.

## Features

- **Web Scraping**: Automated scraping of TechCrunch funding articles
- **Data Processing**: Clean and filter funding data with comprehensive metadata
- **RAG Agent**: Intelligent query system with TF-IDF vectorization for funding data retrieval
- **Streamlit Interface**: Interactive web app for querying funding data
- **AI Enhancement**: Optional OpenRouter API integration for enhanced data processing

## Files

- `techcrunch_fundraising_scraper.py` - Main scraper for TechCrunch funding articles
- `rag_agent.py` - RAG system with Streamlit interface for querying funding data
- `clean_data.py` - Data cleaning utilities
- `clean_funding_data.py` - Funding-specific data cleaning
- `filter_funding_data.py` - Data filtering functionality
- `merge_augmented_data.py` - Merge and augment scraped data
- `scraper.py` - General web scraping utilities

## Data Files

- `funding_data.json` - Main funding dataset
- `funding_data_augmented.json` - Enhanced funding data with AI processing
- `funding_data_complete.json` - Complete processed dataset
- `final_scrape.json` - Final scraped results
- `scraped_one.json` - Single scraping session results

## Setup

1. Install dependencies:
```bash
pip install streamlit pandas scikit-learn beautifulsoup4 requests numpy
```

2. (Optional) Set OpenRouter API key for AI enhancement:
```bash
export OPENROUTER_API_KEY=your_api_key_here
```

## Usage

### Run the RAG Agent Interface
```bash
streamlit run rag_agent.py
```

### Run the Scraper
```python
from techcrunch_fundraising_scraper import TechCrunchFundraisingScaper

scraper = TechCrunchFundraisingScaper()
scraper.scrape_funding_data()
```

## Features

- **Smart Filtering**: Date-based filtering and metadata-driven queries
- **Semantic Search**: TF-IDF vectorization for relevant funding round retrieval
- **Real-time Scraping**: Live data collection from TechCrunch funding articles
- **Data Augmentation**: AI-powered enhancement of scraped funding data