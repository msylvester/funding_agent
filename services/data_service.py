"""
Data service layer for handling database operations
"""
from services.database import FundingDatabase
from typing import List, Dict, Any, Optional
from sklearn.feature_extraction.text import TfidfVectorizer
import chromadb
from chromadb.config import Settings
import uuid
import streamlit as st

class DataService:
    def __init__(self):
        self.db = FundingDatabase()
        self.vectorizer = TfidfVectorizer(max_features=1000, stop_words='english')
        self.documents = []
        self.document_vectors = None
        self.companies_data = []
       
        # Initialize ChromaDB client and collection using new configuration
        self.chroma_client = chromadb.Client(settings=Settings(persist_directory=".chromadb"))
        self.chroma_collection = self.chroma_client.get_or_create_collection("funding_data_embeddings")
    
    def ingest_data(self) -> Dict[str, Any]:
        """
        Handle data ingestion - query MongoDB and return results
        """
        try:
            # Get recent companies (last 10) with all their details
            recent_companies = self.db.read_all_companies()
            
            # Embed the data after successful retrieval
            embed_result = self.embed_data(recent_companies)
            
            return {
                'success': True,
                'recent_companies': recent_companies,
                'message': f"Successfully retrieved {len(recent_companies)} recent companies and created {len(self.documents)} document embeddings",
                'embed_success': embed_result['success']
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': 'Failed to retrieve data from MongoDB'
            }
    
    def embed_data(self, companies_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Create document embeddings from company data
        """
        try:
            if not companies_data:
                return {
                    'success': False,
                    'message': 'No company data provided for embedding'
                }
            
            # Store the companies data for later use
            self.companies_data = companies_data
            
            # Create documents by combining relevant fields
            self.documents = []
            for company in companies_data:
                doc = f"""
                Company: {company.get('company_name', '')}
                Funding Amount: {company.get('funding_amount', '')}
                Investors: {company.get('investors', '')}
                Sector: {company.get('sector', '')}
                Description: {company.get('description', '')}
                """
                self.documents.append(doc.strip())
            
            # Create TF-IDF vectors
            if self.documents:
                self.document_vectors = self.vectorizer.fit_transform(self.documents)
                dense_vectors = self.document_vectors.toarray()

                # Store each document's embedding into ChromaDB
                for i, doc in enumerate(self.documents):
                    self.chroma_collection.add(
                        documents=[doc],
                        embeddings=[dense_vectors[i].tolist()],
                        metadatas=[{"company_data": self.companies_data[i]}],
                        ids=[str(uuid.uuid4())]
                    )

                return {
                    'success': True,
                    'message': f'Successfully created embeddings for {len(self.documents)} documents and stored in ChromaDB'
                }
            else:
                return {
                    'success': False,
                    'message': 'No documents created for embedding'
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': 'Failed to create document embeddings'
            }
    
    def close(self):
        """Close database connection"""
        self.db.close_connection()
        
    def retrieve_documents(self, query: str, n_results: int = 3) -> dict:
        """
        Retrieve relevant documents from ChromaDB based on the query.
        """
        # Check if vectorizer is fitted, if not, try to fit it with existing data
        try:
            # Try to transform the query - this will fail if vectorizer isn't fitted
            query_vector = self.vectorizer.transform([query]).toarray()[0].tolist()
        except:
            # If vectorizer isn't fitted, check if we have documents to fit it
            if not self.documents:
                # No documents available, return empty results
                return {"documents": [[]], "metadatas": [[]], "distances": [[]]}
            
            # Fit the vectorizer with existing documents
            self.vectorizer.fit(self.documents)
            query_vector = self.vectorizer.transform([query]).toarray()[0].tolist()
        
        result = self.chroma_collection.query(query_embeddings=[query_vector], n_results=n_results)
        return result

    def generate_response(self, query: str) -> str:
        """
        Implements Retrieval Augmented Generation (RAG) by retrieving relevant documents
        and generating a response.
        """
        # Check if we have any data in ChromaDB
        try:
            collection_count = self.chroma_collection.count()
            if collection_count == 0:
                return "No data available. Please click 'Ingest' to load data from the database first."
        except:
            return "No data available. Please click 'Ingest' to load data from the database first."
        
        results = self.retrieve_documents(query)
        # ChromaDB returns a list wrapping the results; extract the first list.
        documents = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]
        
        if not documents:
            return "No relevant documents found for your query. Try rephrasing or check if data has been ingested."
        
        context = ""
        for doc, meta in zip(documents, metadatas):
            context += f"\nDocument: {doc}\nMetadata: {meta}\n"
        
        # Placeholder for LLM integration.
        response = (
            f"Query: {query}\n"
            f"Retrieved Context: {context}\n"
            f"RAG Response: [This is a placeholder response using RAG]"
        )
        return response
