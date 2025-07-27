"""
Reusable UI components for the Streamlit application
"""

import streamlit as st

def render_header():
    """Render the main header section"""
    st.markdown('<h1 class="main-title">💰 Funding Intelligence RAG</h1>', unsafe_allow_html=True)
    st.markdown('<p class="subtitle">Explore the latest startup funding rounds with AI-powered insights</p>', unsafe_allow_html=True)

def render_example_queries():
    """Render the example queries expandable section"""
    with st.expander("💡 Example Queries", expanded=False):
        st.markdown("""
        <div class="example-queries">
            <div class="example-title">Try asking about:</div>
            <ul style="margin: 0; padding-left: 1.5rem;">
                <li class="example-item">Show me all Series A rounds from the last 30 days</li>
                <li class="example-item">Which companies raised funding in AI or ML this month?</li>
                <li class="example-item">What are the largest funding rounds in 2024?</li>
                <li class="example-item">Show me fintech companies that raised money recently</li>
                <li class="example-item">Which investors participated in recent Series B rounds?</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

def render_search_form():
    """Render the main search form with input and buttons"""
    with st.form(key="input_form", clear_on_submit=True):
        user_input = st.text_input(
            "🔍 Ask about funding data", 
            placeholder="e.g., Show me all Series A rounds from the last 30 days",
            key="user_input_field"
        )
        
        # Create columns for buttons with better spacing
        col1, col2, col3 = st.columns([3, 0.5, 2])
        
        with col1:
            submit_button = st.form_submit_button(
                "🚀 Search Funding Data", 
                use_container_width=True,
                type="primary"
            )
        
        with col3:
            ingest_button = st.form_submit_button(
                "🔄 Update Data", 
                use_container_width=True,  
                help="Scrape latest funding data from TechCrunch"
            )
        
        # Handle form submissions
        _handle_form_submission(submit_button, ingest_button, user_input)

def _handle_form_submission(submit_button: bool, ingest_button: bool, user_input: str):
    """Handle form submission logic"""
    if submit_button and user_input:
        # Store the input in session state to process after form submission
        st.session_state.last_submitted = user_input
    
    if ingest_button:
        with st.spinner("🔄 Fetching latest funding data from TechCrunch..."):
            # TODO: Implement data ingestion logic
            st.info("Data ingestion functionality not implemented yet")

def render_response_section(response: str):
    """Render the response section with formatted output"""
    st.markdown("### 📊 Results")
    
    response_container = st.container()
    with response_container:
        st.info(response)
    
    st.markdown("---")

def render_loading_spinner(message: str = "Processing..."):
    """Render a loading spinner with custom message"""
    return st.spinner(message)