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
        self.chroma_client = chromadb.PersistentClient(path="./chromadb_data")
        self.chroma_collection = self.chroma_client.get_or_create_collection("funding_data_embeddings")
        
        # Load existing documents if they exist in ChromaDB
        self._load_existing_data()
    
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

                # Clear existing collection data and add new data
                try:
                    # Get existing collection or create new one
                    self.chroma_collection = self.chroma_client.get_or_create_collection("funding_data_embeddings")
                    
                    # Clear existing data in the collection
                    existing_data = self.chroma_collection.get()
                    if existing_data and existing_data.get('ids'):
                        self.chroma_collection.delete(ids=existing_data['ids'])
                        print(f"Cleared {len(existing_data['ids'])} existing documents from ChromaDB")
                        
                except Exception as e:
                    print(f"Error clearing collection: {e}")
                    # If there's an issue, try to create a fresh collection
                    try:
                        self.chroma_client.delete_collection("funding_data_embeddings")
                        self.chroma_collection = self.chroma_client.create_collection("funding_data_embeddings")
                    except:
                        self.chroma_collection = self.chroma_client.get_or_create_collection("funding_data_embeddings")
            
                # Store each document's embedding into ChromaDB
                document_ids = []
                for i, doc in enumerate(self.documents):
                    doc_id = str(uuid.uuid4())
                    document_ids.append(doc_id)
                    self.chroma_collection.add(
                        documents=[doc],
                        embeddings=[dense_vectors[i].tolist()],
                        metadatas=[{"company_data": str(self.companies_data[i])}],  # Convert to string for ChromaDB
                        ids=[doc_id]
                    )
                
                print(f"Added {len(document_ids)} documents to ChromaDB")
                
                # Verify the data was added
                verification_count = self.chroma_collection.count()
                print(f"ChromaDB collection now contains {verification_count} documents")

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
    
    def _load_existing_data(self):
        """Load existing documents from ChromaDB if available"""
        try:
            collection_count = self.chroma_collection.count()
            print(f'ChromaDB collection count on init: {collection_count}')
            if collection_count > 0:
                # Get all documents from ChromaDB
                all_data = self.chroma_collection.get()
                print(f"Retrieved data keys: {list(all_data.keys()) if all_data else 'None'}")
                
                if all_data and all_data.get('documents'):
                    self.documents = all_data['documents']
                    # Fit the vectorizer with existing documents
                    if self.documents:
                        self.vectorizer.fit(self.documents)
                        print(f"Loaded {len(self.documents)} existing documents from ChromaDB and fitted vectorizer")
                    else:
                        print("No documents found in ChromaDB data")
                else:
                    print("No documents key found in ChromaDB data")
            else:
                print("ChromaDB collection is empty")
        except Exception as e:
            print(f"Error loading existing data: {e}")
            import traceback
            traceback.print_exc()
    
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
            print(f'the collection_count is {collection_count}')
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
        
        # Extract only company names and investors from the retrieved documents
        companies_info = []
        for doc, meta in zip(documents, metadatas):
            # Parse the document to extract company name and investors
            lines = doc.split('\n')
            company_name = "Unknown"
            investors = "Unknown"
            funding_amount = "Unknown"
            
            for line in lines:
                if line.strip().startswith("Company:"):
                    company_name = line.replace("Company:", "").strip()
                elif line.strip().startswith("Investors:"):
                    investors = line.replace("Investors:", "").strip()
                elif line.strip().startswith("Funding Amount:"):
                    funding_amount = line.replace("Funding Amount:", "").strip()
            
            companies_info.append({
                'company': company_name,
                'investors': investors,
                'funding_amount': funding_amount
            })
        
        # Format the response to show only relevant information
        response_lines = [f"Query: {query}\n", "Retrieved Companies:"]
        
        for i, info in enumerate(companies_info, 1):
            response_lines.append(f"{i}. {info['company']} - {info['funding_amount']}")
            if info['investors'] and info['investors'] != "Unknown":
                response_lines.append(f"   Investors: {info['investors']}")
            response_lines.append("")  # Empty line for spacing
        
        return "\n".join(response_lines)
