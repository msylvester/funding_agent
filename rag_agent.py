import streamlit as st
import pandas as pd
import json
from datetime import datetime
import re
from typing import List, Dict
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

class FundingRAGAgent:
    def __init__(self):
        self.data = self.load_data()
        self.vectorizer = TfidfVectorizer(stop_words='english', max_features=1000)
        self.document_vectors = None
        self.documents = []
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
    
    def setup_rag(self):
        """Setup RAG system by creating document vectors"""
        if self.data.empty:
            return
        
        # Create documents by combining relevant fields
        self.documents = []
        for _, row in self.data.iterrows():
            doc = f"""
            Title: {row.get('title', '')}
            Company: {row.get('company_name', '')}
            Funding Amount: {row.get('funding_amount', '')}
            Source: {row.get('source', '')}
            Date: {row.get('date', '')}
            URL: {row.get('url', '')}
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
                results.append({
                    'document': self.documents[idx],
                    'similarity': similarities[idx],
                    'data': self.data.iloc[idx].to_dict()
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

def main():
    st.title("Funding Data RAG Agent")
    
    # Initialize the RAG agent
    if 'rag_agent' not in st.session_state:
        with st.spinner("Loading funding data from funding_data.json..."):
            st.session_state.rag_agent = FundingRAGAgent()
    
    agent = st.session_state.rag_agent
    
    # Initialize session state for form submission if not exists
    if 'last_submitted' not in st.session_state:
        st.session_state.last_submitted = ""
    
    # Create a form for more reliable input handling
    with st.form(key="input_form", clear_on_submit=True):
        user_input = st.text_input("Ask about funding data", key="user_input_field")
        
        # Create columns for buttons
        col1, col2 = st.columns([1, 1])
        with col1:
            submit_button = st.form_submit_button("Submit")
        with col2:
            ingest_button = st.form_submit_button("Ingest")
        
        if submit_button and user_input:
            # Store the input in session state to process after form submission
            st.session_state.last_submitted = user_input
        
        if ingest_button:
            st.success("Ingest button clicked!")
    
    # Process the submission outside the form
    if st.session_state.last_submitted:
        current_input = st.session_state.last_submitted
        
        # Get response from agent
        response = agent.generate_response(current_input)
        
        # Display the response
        st.success(response)
        
        # Clear the last submitted value to prevent re-processing
        st.session_state.last_submitted = ""

if __name__ == "__main__":
    main()
