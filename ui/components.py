"""
Reusable UI components for the Streamlit application
"""

import streamlit as st
from services.data_service import DataService
from services.scraper_service import TechCrunchScraper

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
                <li class="example-item">Which companies raised funding in AI or ML this month?</li>
                <li class="example-item">What are the largest funding rounds in 2024?</li>
                <li class="example-item">Show me fintech companies that raised money recently</li>
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
        col1, col2, col3, col4 = st.columns([3, 0.3, 2, 1.5])
        
        with col1:
            submit_button = st.form_submit_button(
                "🚀 Search Funding Data", 
                use_container_width=True,
                type="primary"
            )
        
        with col3:
            update_button = st.form_submit_button(
                "🔄 Update Data", 
                use_container_width=True,  
                help="Scrape latest funding data from TechCrunch"
            )
        
        with col4:
            ingest_button = st.form_submit_button(
                "📥 Ingest", 
                use_container_width=True
            )
        
        # Handle form submissions
        _handle_form_submission(submit_button, update_button, ingest_button, user_input)

def _handle_form_submission(submit_button: bool, update_button: bool, ingest_button: bool, user_input: str):
    """Handle form submission logic"""
    if submit_button and user_input:
        # Process the query with LLM reasoning
        with st.spinner("🤖 Analyzing funding data with AI reasoning..."):
            data_service = DataService()
            try:
                response = data_service.generate_response_with_reasoning(user_input)
                
                # Store both query and response in session state
                st.session_state.last_query = user_input
                st.session_state.last_response = response
                
            except Exception as e:
                st.error(f"❌ Error processing query: {str(e)}")
                st.session_state.last_response = f"Error: {str(e)}"
            finally:
                data_service.close()
    
    if update_button:
        with st.spinner("🔄 Fetching latest funding data from TechCrunch..."):
            try:
                scraper = TechCrunchScraper()
                result = scraper.run_scraper(max_pages=1)
                
                if result:
                    st.success(f"✅ Successfully scraped {len(result)} funding articles from TechCrunch!")
                    st.info("💾 Data has been saved to techcrunch_minimal.json. Use the 'Ingest' button to load it into the search system.")
                    
                    # Show a preview of the scraped data
                    if len(result) > 0:
                        st.subheader("📋 Preview of Scraped Data")
                        for i, article in enumerate(result[:3], 1):  # Show first 3 articles
                            with st.expander(f"{i}. {article.get('company_name', 'Unknown Company')} - {article.get('funding_amount', 'N/A')}"):
                                st.write(f"**Company:** {article.get('company_name', 'N/A')}")
                                st.write(f"**Funding Amount:** {article.get('funding_amount', 'N/A')}")
                                st.write(f"**Series:** {article.get('series', 'N/A')}")
                                st.write(f"**Sector:** {article.get('sector', 'N/A')}")
                                if article.get('url'):
                                    st.write(f"**Source:** [Read article]({article.get('url')})")
                        
                        if len(result) > 3:
                            st.caption(f"... and {len(result) - 3} more articles")
                else:
                    st.warning("⚠️ No new funding data found or scraping completed with no results.")
                    
            except Exception as e:
                st.error(f"❌ Error during scraping: {str(e)}")
                st.error("Please check your internet connection and try again.")
    
    if ingest_button:
        with st.spinner("📥 Querying MongoDB database..."):
            data_service = DataService()
            try:
                result = data_service.ingest_data()
                
                if result['success']:
                    st.success(result['message'])
                    
                    # Display recent companies with full details
                    if result['recent_companies']:
                        st.subheader("🏢 Recent Companies")
                        
                        for i, company in enumerate(result['recent_companies'], 1):
                            with st.expander(f"{i}. {company.get('company_name', 'Unknown Company')} - {company.get('funding_amount', 'N/A')}"):
                                col1, col2 = st.columns(2)
                                
                                with col1:
                                    st.write(f"**Company:** {company.get('company_name', 'N/A')}")
                                    st.write(f"**Funding Amount:** {company.get('funding_amount', 'N/A')}")
                                    st.write(f"**Series:** {company.get('series', 'N/A')}")
                                    st.write(f"**Valuation:** {company.get('valuation', 'N/A')}")
                                    st.write(f"**Sector:** {company.get('sector', 'N/A')}")
                                
                                with col2:
                                    st.write(f"**Investors:** {company.get('investors', 'N/A')}")
                                    st.write(f"**Founded Year:** {company.get('founded_year', 'N/A')}")
                                    st.write(f"**Total Funding:** {company.get('total_funding', 'N/A')}")
                                    st.write(f"**Date:** {company.get('date', 'N/A')}")
                                    if company.get('url'):
                                        st.write(f"**Article:** [Read more]({company.get('url')})")
                                
                                if company.get('description'):
                                    st.write(f"**Description:** {company.get('description')}")
                else:
                    st.error(f"Error: {result['message']}")
                    if 'error' in result:
                        st.error(f"Details: {result['error']}")
            finally:
                data_service.close()

def render_response_section(response: str):
    """Render the response section with formatted output"""
    st.markdown("### 🤖 AI Analysis Results")
    
    response_container = st.container()
    with response_container:
        st.markdown(response)
    
    st.markdown("---")

def check_and_display_response():
    """Check session state for responses and display them"""
    if hasattr(st.session_state, 'last_response') and st.session_state.last_response:
        if hasattr(st.session_state, 'last_query'):
            st.markdown(f"**Query:** {st.session_state.last_query}")
        render_response_section(st.session_state.last_response)
        
        # Clear the response after displaying to avoid repeated displays
        del st.session_state.last_response
        if hasattr(st.session_state, 'last_query'):
            del st.session_state.last_query

def render_loading_spinner(message: str = "Processing..."):
    """Render a loading spinner with custom message"""
    return st.spinner(message)
