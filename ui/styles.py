"""
Custom CSS styles for the Streamlit application
"""

import streamlit as st

def apply_custom_styles():
    """Apply custom CSS styling to the Streamlit app"""
    
    st.markdown("""
    <style>
    /* Main container styling */
    .main {
        padding: 2rem;
    }
    
    /* Title styling */
    .main-title {
        font-size: 3rem;
        font-weight: 700;
        background: linear-gradient(120deg, #1e3c72 0%, #2a5298 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 0.5rem;
    }
    
    /* Subtitle styling */
    .subtitle {
        text-align: center;
        color: #666;
        font-size: 1.2rem;
        margin-bottom: 2rem;
    }
    
    /* Form container */
    .stForm {
        background-color: #f7f9fc;
        padding: 2rem;
        border-radius: 12px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
    }
    
    /* Input field styling */
    .stTextInput > div > div > input {
        border-radius: 8px;
        border: 2px solid #e1e4e8;
        padding: 0.75rem 1rem;
        font-size: 1.1rem;
        transition: border-color 0.2s;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: #2a5298;
        box-shadow: 0 0 0 3px rgba(42, 82, 152, 0.1);
    }
    
    /* Button styling */
    .stButton > button {
        background: linear-gradient(120deg, #1e3c72 0%, #2a5298 100%);
        color: white;
        border: none;
        padding: 0.75rem 2rem;
        border-radius: 8px;
        font-weight: 600;
        font-size: 1rem;
        transition: all 0.3s;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.15);
    }
    
    /* Success message styling */
    .stSuccess {
        background-color: #f0f9ff;
        border-left: 4px solid #2a5298;
        padding: 1.5rem;
        border-radius: 8px;
        margin-top: 2rem;
    }
    
    /* Spinner styling */
    .stSpinner > div {
        border-color: #2a5298;
    }
    
    /* Example queries container */
    .example-queries {
        background-color: #f8f9fa;
        padding: 1.5rem;
        border-radius: 8px;
        margin: 1.5rem 0;
        border: 1px solid #e9ecef;
    }
    
    .example-title {
        font-weight: 600;
        color: #333;
        margin-bottom: 0.5rem;
    }
    
    .example-item {
        color: #2a5298;
        cursor: pointer;
        padding: 0.25rem 0;
        transition: color 0.2s;
    }
    
    .example-item:hover {
        color: #1e3c72;
        text-decoration: underline;
    }
    
    /* Sidebar styling */
    .css-1d391kg {
        background-color: #f8f9fa;
    }
    
    .css-1lcbmhc {
        background-color: #f8f9fa;
    }
    
    /* Navigation radio buttons */
    .stRadio > div {
        background-color: #f8f9fa !important;
        padding: 1rem;
        border-radius: 8px;
        box-shadow: none;
        border: none;
    }
    
    /* Radio button labels */
    .stRadio > div > label > div {
        background-color: transparent !important;
    }
    
    /* Radio button container */
    .stRadio {
        background-color: transparent !important;
    }
    
    .stRadio > div > label {
        font-size: 1.1rem;
        font-weight: 500;
        padding: 0.5rem 0;
    }
    
    /* Sidebar title */
    .css-1lcbmhc h1 {
        color: #2a5298;
        text-align: center;
    }
    
    /* Welcome page animations */
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    .welcome-container {
        animation: fadeIn 1s ease-out;
    }
    
    .feature-cards {
        animation: fadeIn 1.5s ease-out;
    }
    </style>
    """, unsafe_allow_html=True)
