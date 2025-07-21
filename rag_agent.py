import streamlit as st
import pandas as pd
import json
from datetime import datetime, timedelta
import re
from typing import List, Dict, Optional
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from techcrunch_fundraising_scraper import TechCrunchFundraisingScaper
from filter_funding_data import filter_funding_data

class FundingRAGAgent:
    def __init__(self):
        self.data = self.load_data()
        self.vectorizer = TfidfVectorizer(stop_words='english', max_features=1000)
        self.document_vectors = None
        self.documents = []
        self.filtered_indices = None
        self.setup_rag()
    
    def load_data(self):
        """Load funding data from funding_data.json"""
        try:
            with open('funding_data.json', 'r') as f:
                data = json.load(f)
            return pd.DataFrame(data)
        except Exception as e:
            st.error(f"Error loading funding_data.json: {e}")
            return pd.DataFrame()
    
    def setup_rag(self, date_filter: Optional[Dict] = None):
        """Setup RAG system by creating document vectors with optional date filtering"""
        if self.data.empty:
            return
        
        # Apply date filtering if specified
        filtered_data = self._apply_date_filter(self.data, date_filter) if date_filter else self.data
        
        # Store filtered indices for later use
        self.filtered_indices = filtered_data.index.tolist()
        
        # Create documents by combining relevant fields
        self.documents = []
        for _, row in filtered_data.iterrows():
            doc = f"""
            Company: {row.get('company_name', '')}
            Funding Amount: {row.get('funding_amount', '')}
            Valuation: {row.get('valuation', '')}
            Series: {row.get('series', '')}
            Total Funding: {row.get('total_funding', '')}
            Investors: {row.get('investors', '')}
            """
            self.documents.append(doc.strip())
        
        # Create TF-IDF vectors
        if self.documents:
            self.document_vectors = self.vectorizer.fit_transform(self.documents)
    
    def search_similar_documents(self, query: str, top_k: int = 5) -> List[Dict]:
        """Find most similar documents to the query"""
        if not self.documents or self.document_vectors is None:
            return []
        
        # Vectorize the query
        query_vector = self.vectorizer.transform([query])
        
        # Calculate cosine similarity
        similarities = cosine_similarity(query_vector, self.document_vectors).flatten()
        
        # Get top-k most similar documents
        top_indices = np.argsort(similarities)[::-1][:top_k]
        
        results = []
        for idx in top_indices:
            if similarities[idx] > 0.1:  # Minimum similarity threshold
                # Map back to original data using filtered indices
                original_idx = self.filtered_indices[idx] if self.filtered_indices else idx
                results.append({
                    'document': self.documents[idx],
                    'similarity': similarities[idx],
                    'data': self.data.iloc[original_idx].to_dict()
                })
        
        return results
    
    def generate_response(self, query: str) -> str:
        """Generate response based on retrieved documents"""
        # Search for relevant documents
        relevant_docs = self.search_similar_documents(query, top_k=3)
        
        if not relevant_docs:
            return "I couldn't find any relevant funding information for your query. Please try rephrasing your question."
        
        # Analyze query intent
        query_lower = query.lower()
        
        if any(word in query_lower for word in ['recent', 'latest', 'new']):
            return self._handle_recent_funding_query(relevant_docs)
        elif any(word in query_lower for word in ['amount', 'funding', 'raised', 'investment']):
            return self._handle_funding_amount_query(relevant_docs)
        elif any(word in query_lower for word in ['company', 'startup', 'who']):
            return self._handle_company_query(relevant_docs)
        else:
            return self._handle_general_query(relevant_docs)
    
    def _handle_recent_funding_query(self, docs: List[Dict]) -> str:
        """Handle queries about recent funding"""
        response = "Here are the most recent funding announcements I found:\n\n"
        
        for i, doc in enumerate(docs[:3], 1):
            data = doc['data']
            title = data.get('title', 'N/A')
            company = data.get('company_name', 'N/A')
            amount = data.get('funding_amount', 'N/A')
            date = data.get('date', 'N/A')
            
            response += f"{i}. **{company}**\n"
            response += f"   - Funding: {amount}\n"
            response += f"   - Date: {date}\n"
            response += f"   - Details: {title}\n\n"
        
        return response
    
    def _handle_funding_amount_query(self, docs: List[Dict]) -> str:
        """Handle queries about funding amounts"""
        response = "Here are the funding details I found:\n\n"
        
        for i, doc in enumerate(docs[:3], 1):
            data = doc['data']
            company = data.get('company_name', 'N/A')
            amount = data.get('funding_amount', 'Not specified')
            title = data.get('title', 'N/A')
            
            response += f"{i}. **{company}**\n"
            response += f"   - Amount: {amount}\n"
            response += f"   - Details: {title}\n\n"
        
        return response
    
    def _handle_company_query(self, docs: List[Dict]) -> str:
        """Handle queries about specific companies"""
        response = "Here's what I found about the companies:\n\n"
        
        for i, doc in enumerate(docs[:3], 1):
            data = doc['data']
            company = data.get('company_name', 'N/A')
            amount = data.get('funding_amount', 'Not specified')
            source = data.get('source', 'N/A')
            url = data.get('url', '')
            
            response += f"{i}. **{company}**\n"
            response += f"   - Funding: {amount}\n"
            response += f"   - Source: {source}\n"
            if url:
                response += f"   - [Read more]({url})\n"
            response += "\n"
        
        return response
    
    def _handle_general_query(self, docs: List[Dict]) -> str:
        """Handle general queries"""
        response = "Based on the funding data, here's what I found:\n\n"
        
        for i, doc in enumerate(docs[:3], 1):
            data = doc['data']
            title = data.get('title', 'N/A')
            company = data.get('company_name', 'N/A')
            amount = data.get('funding_amount', 'Not specified')
            
            response += f"{i}. **{title}**\n"
            response += f"   - Company: {company}\n"
            response += f"   - Funding: {amount}\n\n"
        
        return response
    
    def _apply_date_filter(self, data: pd.DataFrame, date_filter: Dict) -> pd.DataFrame:
        """Apply date filtering to the dataset"""
        if data.empty or 'date' not in data.columns:
            return data
        
        filtered_data = data.copy()
        
        # Convert date column to datetime if it's not already
        if not pd.api.types.is_datetime64_any_dtype(filtered_data['date']):
            filtered_data['date'] = pd.to_datetime(filtered_data['date'], errors='coerce')
        
        # Apply date range filters
        if 'start_date' in date_filter and date_filter['start_date']:
            start_date = pd.to_datetime(date_filter['start_date'])
            filtered_data = filtered_data[filtered_data['date'] >= start_date]
        
        if 'end_date' in date_filter and date_filter['end_date']:
            end_date = pd.to_datetime(date_filter['end_date'])
            filtered_data = filtered_data[filtered_data['date'] <= end_date]
        
        # Apply relative date filters (e.g., last N days)
        if 'days_back' in date_filter and date_filter['days_back']:
            cutoff_date = datetime.now() - timedelta(days=date_filter['days_back'])
            filtered_data = filtered_data[filtered_data['date'] >= cutoff_date]
        
        return filtered_data
    
    def apply_date_filter(self, date_filter: Optional[Dict] = None):
        """Apply date filter and rebuild the RAG system"""
        self.setup_rag(date_filter)
    
    def get_stats(self) -> Dict:
        """Get statistics about the funding data"""
        if self.data.empty:
            return {}
        
        stats = {
            'total_articles': len(self.data),
            'sources': self.data['source'].value_counts().to_dict(),
            'companies_with_funding': len(self.data[self.data['funding_amount'].notna()]),
            'recent_articles': len(self.data[self.data['is_recent'] == True]) if 'is_recent' in self.data.columns else 0
        }
        
        return stats

def run_ingest_process():
    """Run the complete ingest process: scrape -> filter -> augment existing data"""
    try:
        # Step 1: Run the scraper
        st.info("Step 1: Scraping TechCrunch funding data...")
        scraper = TechCrunchFundraisingScaper()
        scraped_data = scraper.run_scraper(max_pages=3)
        
        if not scraped_data:
            st.warning("No data scraped from TechCrunch")
            return False
        
        st.info(f"Scraped {len(scraped_data)} articles")
        
        # Step 2: Filter the scraped data
        st.info("Step 2: Filtering scraped data...")
        filter_success = filter_funding_data('scraped_one.json', 'final_scrape.json')
        
        if not filter_success:
            st.error("Failed to filter scraped data")
            return False
        
        # Step 3: Augment existing funding_data_complete.json with filtered results
        st.info("Step 3: Augmenting existing funding data...")
        augment_success = augment_funding_data()
        
        if not augment_success:
            st.error("Failed to augment funding data")
            return False
        
        st.info("Ingest process completed successfully!")
        return True
        
    except Exception as e:
        st.error(f"Error during ingest process: {e}")
        return False

def augment_funding_data():
    """Augment existing funding_data_complete.json with new filtered data"""
    try:
        # Load existing funding data
        existing_data = []
        try:
            with open('funding_data_complete.json', 'r', encoding='utf-8') as f:
                existing_data = json.load(f)
        except FileNotFoundError:
            st.info("No existing funding_data_complete.json found, creating new file")
        
        # Load filtered new data
        try:
            with open('final_scrape.json', 'r', encoding='utf-8') as f:
                new_data = json.load(f)
        except FileNotFoundError:
            st.error("final_scrape.json not found")
            return False
        
        # Combine data, removing duplicates based on URL
        seen_urls = set()
        
        # Add existing data URLs to seen set
        for item in existing_data:
            url = item.get('url', '')
            if url:
                seen_urls.add(url)
        
        # Add new data that doesn't already exist
        new_items_added = 0
        for item in new_data:
            url = item.get('url', '')
            if url and url not in seen_urls:
                existing_data.append(item)
                seen_urls.add(url)
                new_items_added += 1
            elif not url:  # Add items without URLs
                existing_data.append(item)
                new_items_added += 1
        
        # Save augmented data back to funding_data_complete.json
        with open('funding_data_complete.json', 'w', encoding='utf-8') as f:
            json.dump(existing_data, f, indent=2, ensure_ascii=False)
        
        st.info(f"Added {new_items_added} new items to funding_data_complete.json")
        st.info(f"Total items in dataset: {len(existing_data)}")
        
        return True
        
    except Exception as e:
        st.error(f"Error augmenting funding data: {e}")
        return False

def main():
    # Apply custom CSS for better styling
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
    </style>
    """, unsafe_allow_html=True)
    
    # Enhanced title with gradient effect
    st.markdown('<h1 class="main-title">💰 Funding Intelligence RAG</h1>', unsafe_allow_html=True)
    st.markdown('<p class="subtitle">Explore the latest startup funding rounds with AI-powered insights</p>', unsafe_allow_html=True)
    
    # Initialize the RAG agent
    if 'rag_agent' not in st.session_state:
        with st.spinner("Loading funding data from funding_data.json..."):
            st.session_state.rag_agent = FundingRAGAgent()
    
    agent = st.session_state.rag_agent
    
    # Initialize session state for form submission if not exists
    if 'last_submitted' not in st.session_state:
        st.session_state.last_submitted = ""
    
    # Add example queries section
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
    
    # Create a form for more reliable input handling
    with st.form(key="input_form", clear_on_submit=True):
        user_input = st.text_input("🔍 Ask about funding data", 
                                   placeholder="e.g., Show me all Series A rounds from the last 30 days",
                                   key="user_input_field")
        
        # Create columns for buttons with better spacing
        col1, col2, col3 = st.columns([3, 0.5, 2])
        with col1:
            submit_button = st.form_submit_button("🚀 Search Funding Data", 
                                                  use_container_width=True,
                                                  type="primary")
        with col3:
            ingest_button = st.form_submit_button("🔄 Update Data", 
                                                  use_container_width=True,
                                                  help="Scrape latest funding data from TechCrunch")
        
        if submit_button and user_input:
            # Store the input in session state to process after form submission
            st.session_state.last_submitted = user_input
        
        if ingest_button:
            with st.spinner("🔄 Fetching latest funding data from TechCrunch..."):
                success = run_ingest_process()
                if success:
                    st.success("✅ Data updated successfully! The latest funding rounds have been added to the database.")
                    # Force re-initialization of the agent with new data
                    st.session_state.rag_agent = FundingRAGAgent()
                    st.rerun()
                else:
                    st.error("❌ Update failed. Please check your internet connection and try again.")
    
    # Process the submission outside the form
    if st.session_state.last_submitted:
        current_input = st.session_state.last_submitted
        
        # Show loading animation while processing
        with st.spinner("🤔 Analyzing funding data..."):
            # Get response from agent
            response = agent.generate_response(current_input)
        
        # Display the response with enhanced formatting
        st.markdown("### 📊 Results")
        
        # Create a container for the response with custom styling
        response_container = st.container()
        with response_container:
            # Check if response contains structured data (tables, lists)
            if "Company:" in response or "- " in response:
                # Display as info box for structured responses
                st.info(response)
            else:
                # Display as success box for general responses
                st.success(response)
        
        # Add a divider for visual separation
        st.markdown("---")
        
        # Add helpful tips based on the query
        if any(term in current_input.lower() for term in ["series a", "series b", "series c", "funding round"]):
            st.caption("💡 Tip: You can filter by specific date ranges by mentioning timeframes like 'last 30 days' or 'this month'")
        elif any(term in current_input.lower() for term in ["ai", "ml", "fintech", "saas"]):
            st.caption("💡 Tip: Try combining industry filters with funding stages for more specific results")
        
        # Clear the last submitted value to prevent re-processing
        st.session_state.last_submitted = ""

if __name__ == "__main__":
    main()
