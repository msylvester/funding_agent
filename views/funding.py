import streamlit as st
from ui.components import render_header, render_example_queries, render_search_form
from ui.styles import apply_custom_styles

def funding_page():
    """Funding Intelligence RAG page"""
    
    # Apply custom CSS styling
    apply_custom_styles()
    
    # Render header section
    render_header()
    
    # Initialize session state for form submission if not exists
    if 'last_submitted' not in st.session_state:
        st.session_state.last_submitted = ""
    
    # Render example queries section
    render_example_queries()
    
    # Render search form and handle submissions
    render_search_form()
