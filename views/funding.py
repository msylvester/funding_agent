import streamlit as st
from ui.components import render_header, render_example_queries, render_search_form
from ui.styles import apply_custom_styles
from services.database.data_service import DataService
from services.processing.article_processor import ArticleProcessor
from urllib.parse import urlparse
import requests

def funding_page():
    """Funding Intelligence RAG page"""
    
    # Apply custom CSS styling
    
    # Render header section
    render_header()
    
    # Initialize session state for form submission if not exists
    if 'last_submitted' not in st.session_state:
        st.session_state.last_submitted = ""
    
    # Initialize session state for modal management
    if 'show_confirmation_modal' not in st.session_state:
        st.session_state.show_confirmation_modal = False
    if 'pending_article_data' not in st.session_state:
        st.session_state.pending_article_data = None
    if 'pending_article_url' not in st.session_state:
        st.session_state.pending_article_url = None
    
    # Render example queries section
    render_example_queries()
    
    # Render article URL form
    render_article_url_form()
    
    # Render search form and handle submissions
    render_search_form()
    
    # Show confirmation modal if needed
    if st.session_state.show_confirmation_modal:
        _show_confirmation_modal()
    
    # Process the submission outside the form
    if st.session_state.last_submitted:
        current_input = st.session_state.last_submitted

        # Show loading animation while processing
        with st.spinner("Analyzing funding data..."):
            data_service = DataService()
            response = data_service.generate_response(current_input)
            data_service.close()
        
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
        st.caption("💡 Tip: You can filter by specific date ranges by mentioning timeframes like 'last 30 days' or 'this month'")
    elif any(term in query_lower for term in ["ai", "ml", "fintech", "saas"]):
        st.caption("💡 Tip: Try combining industry filters with funding stages for more specific results")

def render_article_url_form():
    """Render the article URL submission form"""
    with st.expander("📰 Add Company from Article URL", expanded=False):
        st.markdown("""
        <div style="margin-bottom: 1rem;">
            <p>Submit a URL to a funding article and we'll extract the company information using AI agents and add it to our database.</p>
            <p><strong>Supported sources:</strong> TechCrunch, Crunchbase, VentureBeat, and other funding news sites.</p>
        </div>
        """, unsafe_allow_html=True)
        
        with st.form(key="article_url_form", clear_on_submit=True):
            # Create columns for input and button side by side
            col1, col2 = st.columns([3, 1])
            
            with col1:
                article_url = st.text_input(
                    "🔗 Article URL",
                    placeholder="e.g., https://techcrunch.com/2024/01/15/startup-raises-50m-series-b/",
                    help="Enter the full URL to a funding article"
                )
            
            with col2:
                # Add some vertical spacing to align with input field
                st.write("")  # This adds vertical spacing
                submit_button = st.form_submit_button(
                    "🔍 Process Article",
                    use_container_width=True,
                    type="primary"
                )
            
            # Handle form submission
            if submit_button and article_url:
                _process_article_for_confirmation(article_url)

def _process_article_for_confirmation(article_url: str):
    """Process article and show confirmation modal before saving to database"""
    
    # Validate URL format
    try:
        parsed_url = urlparse(article_url)
        if not all([parsed_url.scheme, parsed_url.netloc]):
            st.error("❌ Please enter a valid URL (must include http:// or https://)")
            return
    except Exception:
        st.error("❌ Invalid URL format")
        return
    
    # Show processing message
    with st.spinner("🤖 Processing article and extracting company information..."):
        try:
            # Initialize article processor with a session
            session = requests.Session()
            session.headers.update({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            })
            
            processor = ArticleProcessor(session, "")
            
            # Process the article URL WITHOUT saving to database
            article_data = processor.scrape_article_content(article_url, auto_save=False)
            
            if not article_data:
                st.error("❌ Failed to extract content from the article. Please check the URL and try again.")
                return
            
            # Check if we extracted valid funding data
            if not processor.is_valid_funding_data(article_data):
                st.warning("⚠️ Could not extract valid funding information from this article.")
                st.info("The article was processed but doesn't appear to contain standard funding details (company name and funding amount).")
                
                # Show what was extracted anyway
                with st.expander("📋 Raw Extracted Data", expanded=True):
                    st.json({
                        "title": article_data.get("title", "Not found"),
                        "company_name": article_data.get("company_name", "Not found"),
                        "funding_amount": article_data.get("funding_amount", "Not found"),
                        "series": article_data.get("series", "Not found"),
                        "investors": article_data.get("investors", "Not found")
                    })
                return
            
            # Store data in session state and trigger modal
            st.session_state.pending_article_data = article_data
            st.session_state.pending_article_url = article_url
            st.session_state.show_confirmation_modal = True
            st.rerun()
            
        except Exception as e:
            st.error(f"❌ Error processing article: {str(e)}")
            st.error("Please check the URL and try again. Make sure the article is publicly accessible.")

@st.dialog("Confirm Company Data")
def _show_confirmation_modal():
    """Show confirmation modal with extracted company data"""
    
    article_data = st.session_state.pending_article_data
    article_url = st.session_state.pending_article_url
    
    if not article_data:
        st.error("No article data found")
        return
    
    st.markdown("### 📊 Extracted Company Information")
    st.markdown("Please review the extracted information before adding to the database:")
    
    # Display extracted company information in a nice format
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("🏢 Company", article_data.get('company_name', 'Not found'))
        st.metric("💰 Funding Amount", article_data.get('funding_amount', 'Not found'))
        st.metric("📈 Series", article_data.get('series', 'Not found'))
    
    with col2:
        st.metric("🤝 Investors", article_data.get('investors', 'Not specified'))
        st.metric("📅 Date", article_data.get('date', 'Not found'))
        st.metric("📰 Source", article_data.get('source', 'Article'))
    
    # Show article details
    with st.expander("📰 Article Details", expanded=False):
        st.write(f"**Title:** {article_data.get('title', 'Not found')}")
        st.write(f"**URL:** {article_url}")
        if article_data.get('content'):
            st.write(f"**Content Preview:** {article_data.get('content')[:200]}...")
    
    # Action buttons
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col1:
        if st.button("✅ Confirm & Save", type="primary", use_container_width=True):
            _confirm_and_save_article()
    
    with col2:
        if st.button("❌ Cancel", use_container_width=True):
            _cancel_modal()
    
    with col3:
        # Optional: Add edit functionality later
        st.write("")

def _confirm_and_save_article():
    """Confirm and save the article data to database"""
    try:
        from services.article_processor import ArticleProcessor
        
        # Get data from session state
        article_data = st.session_state.pending_article_data
        
        if not article_data:
            st.error("No article data to save")
            return
        
        # Initialize processor to access the database write method
        processor = ArticleProcessor(None, "")
        
        # Write to database
        company_id = processor.write_company_to_db(article_data)
        
        if company_id:
            st.success("✅ Company successfully added to database!")
        else:
            st.info("ℹ️ Company already exists in database or could not be saved.")
        
        # Clear modal state
        _clear_modal_state()
        st.rerun()
        
    except Exception as e:
        st.error(f"❌ Error saving to database: {str(e)}")

def _cancel_modal():
    """Cancel modal and clear state"""
    _clear_modal_state()
    st.rerun()

def _clear_modal_state():
    """Clear modal-related session state"""
    st.session_state.show_confirmation_modal = False
    st.session_state.pending_article_data = None
    st.session_state.pending_article_url = None

