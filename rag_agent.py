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
    def __init__(self, data_source='funding_data.csv'):
        self.data = self.load_data(data_source)
        self.vectorizer = TfidfVectorizer(stop_words='english', max_features=1000)
        self.document_vectors = None
        self.documents = []
        self.setup_rag()
    
    def load_data(self, data_source):
        """Load funding data from CSV or JSON"""
        try:
            if data_source.endswith('.csv'):
                return pd.read_csv(data_source)
            elif data_source.endswith('.json'):
                with open(data_source, 'r') as f:
                    data = json.load(f)
                return pd.DataFrame(data)
        except Exception as e:
            st.error(f"Error loading data: {e}")
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
    st.set_page_config(
        page_title="Funding Data RAG Agent",
        page_icon="💰",
        layout="wide"
    )
    
    st.title("💰 Funding Data RAG Agent")
    st.markdown("Ask questions about startup funding and investment news!")
    
    # Initialize the RAG agent
    if 'rag_agent' not in st.session_state:
        with st.spinner("Loading funding data..."):
            st.session_state.rag_agent = FundingRAGAgent('funding_data.csv')
    
    agent = st.session_state.rag_agent
    
    # Sidebar with statistics
    with st.sidebar:
        st.header("📊 Data Statistics")
        stats = agent.get_stats()
        
        if stats:
            st.metric("Total Articles", stats.get('total_articles', 0))
            st.metric("Companies with Funding", stats.get('companies_with_funding', 0))
            st.metric("Recent Articles", stats.get('recent_articles', 0))
            
            st.subheader("Sources")
            for source, count in stats.get('sources', {}).items():
                st.write(f"• {source}: {count}")
        
        st.markdown("---")
        st.markdown("### Sample Questions")
        st.markdown("""
        - What are the recent funding announcements?
        - Which companies raised the most money?
        - Tell me about Tailor's funding
        - What funding news is from TechCrunch?
        - Show me Series A funding rounds
        """)
    
    # Main chat interface
    st.header("🤖 Chat with the Agent")
    
    # Initialize chat history
    if 'messages' not in st.session_state:
        st.session_state.messages = [
            {"role": "assistant", "content": "Hello! I'm your funding data assistant. Ask me anything about startup funding and investment news!"}
        ]
    
    # Display chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Chat input
    if prompt := st.chat_input("Ask about funding data..."):
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Generate response
        with st.chat_message("assistant"):
            with st.spinner("Searching funding data..."):
                response = agent.generate_response(prompt)
            st.markdown(response)
        
        # Add assistant response to chat history
        st.session_state.messages.append({"role": "assistant", "content": response})
    
    # Data exploration section
    st.header("📈 Data Exploration")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Recent Funding Articles")
        if not agent.data.empty:
            recent_data = agent.data.head(10)
            for _, row in recent_data.iterrows():
                with st.expander(f"{row.get('company_name', 'Unknown')} - {row.get('funding_amount', 'N/A')}"):
                    st.write(f"**Title:** {row.get('title', 'N/A')}")
                    st.write(f"**Source:** {row.get('source', 'N/A')}")
                    st.write(f"**Date:** {row.get('date', 'N/A')}")
                    if row.get('url'):
                        st.write(f"**URL:** {row.get('url')}")
    
    with col2:
        st.subheader("Funding Amounts")
        if not agent.data.empty:
            funding_data = agent.data[agent.data['funding_amount'].notna()]
            if not funding_data.empty:
                st.write(f"Found {len(funding_data)} articles with funding amounts")
                for _, row in funding_data.head(5).iterrows():
                    st.write(f"• **{row.get('company_name', 'Unknown')}**: {row.get('funding_amount', 'N/A')}")
            else:
                st.write("No funding amounts found in the data")

if __name__ == "__main__":
    main()
