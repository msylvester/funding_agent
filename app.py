"""
Main Streamlit application for Funding Intelligence RAG
"""

import streamlit as st
from config.settings import APP_CONFIG
from views.home import home_page
from views.funding import funding_page
from views.opensource import opensource_page
from views.huggingface import huggingface_page
from views.hackernews import hackernews_page

def main():
    """Main application entry point"""
    
    # Configure Streamlit page settings
    st.set_page_config(
        page_title=APP_CONFIG['page_title'],
        page_icon=APP_CONFIG['page_icon'],
        layout=APP_CONFIG['layout'],
        initial_sidebar_state='expanded'  # Changed to show sidebar
    )
    
    # Sidebar navigation
    with st.sidebar:
        st.markdown("# 🔮 Navigation")
        st.markdown("---")
        
        # Navigation options with radio buttons for better UX
        page = st.radio(
            "Choose a page:",
            ["🏠 Home", "💰 Funding", "🔓 Open Source", "🤗 Hugging Face", "📰 Hacker News"],
            index=0,
            label_visibility="collapsed"
        )
        
        st.markdown("---")
        st.markdown("### About")
        st.markdown("**Krystal Ball Z** - Your AI-powered funding intelligence platform")
    
    # Route to appropriate page
    if page == "🏠 Home":
        home_page()
    elif page == "💰 Funding":
        funding_page()
    elif page == "🔓 Open Source":
        opensource_page()
    elif page == "🤗 Hugging Face":
        huggingface_page()
    elif page == "📰 Hacker News":
        hackernews_page()

if __name__ == "__main__":
    main()
