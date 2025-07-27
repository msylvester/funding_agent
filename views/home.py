import streamlit as st
from ui.components import render_header, render_example_queries, render_search_form
from ui.styles import apply_custom_styles

def home_page():
    """Main home page for the Funding Intelligence RAG"""
    
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
    
    # Process the submission outside the form
    if st.session_state.last_submitted:
        current_input = st.session_state.last_submitted
        
        # Show loading animation while processing
        with st.spinner("> Analyzing funding data..."):
            # TODO: Implement query processing logic
            response = f"This is a placeholder response for your query: '{current_input}'"
        
        # Display the response with enhanced formatting
        st.markdown("### 📊 Results")
        
        # Create a container for the response with custom styling
        response_container = st.container()
        with response_container:
            # Display placeholder response
            st.info(response)
        
        # Add a divider for visual separation
        st.markdown("---")
        
        # Add helpful tips based on the query
        _show_query_tips(current_input)
        
        # Clear the last submitted value to prevent re-processing
        st.session_state.last_submitted = ""

def _show_query_tips(query: str):
    """Show contextual tips based on query content"""
    query_lower = query.lower()
    
    if any(term in query_lower for term in ["series a", "series b", "series c", "funding round"]):
        st.caption("=� Tip: You can filter by specific date ranges by mentioning timeframes like 'last 30 days' or 'this month'")
    elif any(term in query_lower for term in ["ai", "ml", "fintech", "saas"]):
        st.caption("=� Tip: Try combining industry filters with funding stages for more specific results")