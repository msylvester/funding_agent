"""
Main Streamlit application for Funding Intelligence RAG
"""

import streamlit as st
from config.settings import APP_CONFIG
from views.home import home_page

def main():
    """Main application entry point"""
    
    # Configure Streamlit page settings
    st.set_page_config(
        page_title=APP_CONFIG['page_title'],
        page_icon=APP_CONFIG['page_icon'],
        layout=APP_CONFIG['layout'],
        initial_sidebar_state=APP_CONFIG['sidebar_state']
    )
    
    # Run the home page
    home_page()

if __name__ == "__main__":
    main()
