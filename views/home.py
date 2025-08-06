import streamlit as st
from ui.components import render_header, render_example_queries, render_search_form
from ui.styles import apply_custom_styles
from services.data_service import DataService

def home_page():
    """Main home page for the Funding Intelligence RAG"""
    st.write("Welcome to Krysta Ballz!")
