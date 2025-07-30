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
import traceback
import os
from datetime import datetime
import requests
import json

class DataService:
    def __init__(self):
        print("🔧 DEBUG: Initializing DataService...")
        
        self.db = FundingDatabase()
        self.vectorizer = TfidfVectorizer(max_features=1000, stop_words='english')
        self.documents = []
        self.document_vectors = None
        self.companies_data = []
        
        # Load OpenRouter API configuration
        from config.settings import API_CONFIG
        self.openrouter_api_key = API_CONFIG['openrouter_api_key']
        self.openrouter_base_url = API_CONFIG['openrouter_base_url']
        self.default_model = API_CONFIG['default_model']
        self.max_tokens = API_CONFIG['max_tokens']
        self.temperature = API_CONFIG['temperature']
       
        # Initialize ChromaDB client and collection using new configuration
        try:
            chroma_path = "./chromadb_data"
            print(f"🔧 DEBUG: Creating ChromaDB client with path: {chroma_path}")
            print(f"🔧 DEBUG: ChromaDB path exists: {os.path.exists(chroma_path)}")
            
            self.chroma_client = chromadb.PersistentClient(path=chroma_path)
            print("🔧 DEBUG: ChromaDB client created successfully")
            
            self.chroma_collection = self.chroma_client.get_or_create_collection("funding_data_embeddings")
            print(f"🔧 DEBUG: ChromaDB collection created/retrieved: {self.chroma_collection.name}")
            print(f"🔧 DEBUG: Initial collection count: {self.chroma_collection.count()}")
            
        except Exception as e:
            print(f"❌ ERROR: Failed to initialize ChromaDB: {e}")
            traceback.print_exc()
            raise
        
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
            
            # Verify the data was actually stored
            final_count = self.chroma_collection.count()
            print(f"Final ChromaDB count after ingestion: {final_count}")
            
            # Run debug inspection
            self.debug_chromadb_state()
            
            return {
                'success': True,
                'recent_companies': recent_companies,
                'message': f"Successfully retrieved {len(recent_companies)} companies and created {final_count} document embeddings",
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
        print('abotu to embed')
        try:
            if not companies_data:
                print('not companies')
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

                # Handle dimension mismatch by recreating collection
                try:
                    # Always delete and recreate collection to avoid dimension mismatch
                    print("🔧 DEBUG: Recreating ChromaDB collection to avoid dimension mismatch...")
                    try:
                        self.chroma_client.delete_collection("funding_data_embeddings")
                        print("🔧 DEBUG: Deleted existing collection")
                    except Exception as e:
                        print(f"🔧 DEBUG: Collection didn't exist or couldn't delete: {e}")
                    
                    # Create fresh collection
                    self.chroma_collection = self.chroma_client.create_collection("funding_data_embeddings")
                    print(f"🔧 DEBUG: Created new collection with dimension {len(dense_vectors[0])}")
                        
                except Exception as e:
                    print(f"❌ ERROR: Failed to recreate collection: {e}")
                    raise
            
                # Store each document's embedding into ChromaDB
                print(f'🔧 DEBUG: About to add {len(self.documents)} documents to ChromaDB')
                document_ids = []
                documents_to_add = []
                embeddings_to_add = []
                metadatas_to_add = []
                
                for i, doc in enumerate(self.documents):
                    doc_id = str(uuid.uuid4())
                    document_ids.append(doc_id)
                    documents_to_add.append(doc)
                    embeddings_to_add.append(dense_vectors[i].tolist())
                    
                    # Convert date to Unix timestamp
                    company_date = self.companies_data[i].get('date')
                    unix_timestamp = None
                    if company_date:
                        try:
                            # Handle different date formats that might come from MongoDB
                            if isinstance(company_date, str):
                                # Try parsing common date formats
                                for date_format in ['%Y-%m-%d', '%Y-%m-%d %H:%M:%S', '%m/%d/%Y', '%d/%m/%Y']:
                                    try:
                                        parsed_date = datetime.strptime(company_date, date_format)
                                        unix_timestamp = int(parsed_date.timestamp())
                                        break
                                    except ValueError:
                                        continue
                            elif hasattr(company_date, 'timestamp'):
                                # If it's already a datetime object
                                unix_timestamp = int(company_date.timestamp())
                        except Exception as e:
                            print(f"⚠️ WARNING: Could not parse date '{company_date}' for company {self.companies_data[i].get('company_name', 'Unknown')}: {e}")
                    
                    metadata = {
                        "company_index": i, 
                        "company_name": self.companies_data[i].get('company_name', 'Unknown')
                    }
                    
                    # Only add date_unix if we have a valid timestamp
                    if unix_timestamp is not None:
                        metadata["date_unix"] = unix_timestamp
                    metadatas_to_add.append(metadata)
                    print(f'🔧 DEBUG: Prepared document {i+1}: {self.companies_data[i].get("company_name", "Unknown")} (date: {unix_timestamp})')
                
                # Add all documents in one batch
                print("🔧 DEBUG: Adding documents to ChromaDB in batch...")
                self.chroma_collection.add(
                    documents=documents_to_add,
                    embeddings=embeddings_to_add,
                    metadatas=metadatas_to_add,
                    ids=document_ids
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
            print(f"❌ ERROR in embed_data: {e}")
            traceback.print_exc()
            return {
                'success': False,
                'error': str(e),
                'message': 'Failed to create document embeddings'
            }
    
    def _load_existing_data(self):
        """Load existing documents from ChromaDB if available"""
        try:
            print("🔧 DEBUG: Loading existing data from ChromaDB...")
            collection_count = self.chroma_collection.count()
            print(f'🔧 DEBUG: ChromaDB collection count on init: {collection_count}')
            
            if collection_count > 0:
                print("🔧 DEBUG: Found existing data, retrieving...")
                # Get all documents from ChromaDB
                all_data = self.chroma_collection.get()
                print(f"🔧 DEBUG: Retrieved data keys: {list(all_data.keys()) if all_data else 'None'}")
                print(f"🔧 DEBUG: Documents count in retrieved data: {len(all_data.get('documents', []))}")
                
                if all_data and all_data.get('documents'):
                    self.documents = all_data['documents']
                    # Fit the vectorizer with existing documents
                    if self.documents:
                        self.vectorizer.fit(self.documents)
                        print(f"✅ DEBUG: Loaded {len(self.documents)} existing documents from ChromaDB and fitted vectorizer")
                    else:
                        print("⚠️ DEBUG: No documents found in ChromaDB data")
                else:
                    print("⚠️ DEBUG: No documents key found in ChromaDB data")
            else:
                print("ℹ️ DEBUG: ChromaDB collection is empty on initialization")
        except Exception as e:
            print(f"❌ ERROR: Error loading existing data: {e}")
            traceback.print_exc()
    
    def debug_chromadb_state(self):
        """Debug method to inspect ChromaDB state"""
        print("\n" + "="*50)
        print("🔍 CHROMADB DEBUG STATE INSPECTION")
        print("="*50)
        
        try:
            # Collection info
            print(f"Collection name: {self.chroma_collection.name}")
            count = self.chroma_collection.count()
            print(f"Document count: {count}")
            
            if count > 0:
                # Get all data
                all_data = self.chroma_collection.get()
                print(f"Available keys: {list(all_data.keys())}")
                
                if all_data.get('documents'):
                    print(f"Documents retrieved: {len(all_data['documents'])}")
                    for i, doc in enumerate(all_data['documents'][:3]):  # Show first 3
                        print(f"Document {i+1} preview: {doc[:100]}...")
                
                if all_data.get('metadatas'):
                    print(f"Metadatas retrieved: {len(all_data['metadatas'])}")
                    for i, meta in enumerate(all_data['metadatas'][:3]):  # Show first 3
                        print(f"Metadata {i+1}: {meta}")
                
                if all_data.get('ids'):
                    print(f"IDs retrieved: {len(all_data['ids'])}")
                    print(f"Sample IDs: {all_data['ids'][:3]}")
            else:
                print("Collection is empty")
                
        except Exception as e:
            print(f"Error during debug inspection: {e}")
            traceback.print_exc()
        
        print("="*50)
        print("END DEBUG STATE INSPECTION")
        print("="*50 + "\n")

    def close(self):
        """Close database connection"""
        self.db.close_connection()
        
    def retrieve_documents(self, query: str, n_results: int = 3, distance_threshold: float = 1.6) -> dict:
        print(f"🔍 DEBUG: Starting document retrieval...")
        print(f"🔍 DEBUG: Query = '{query}'")
        print(f"🔍 DEBUG: Documents count = {len(self.documents)}")
        print(f"🔍 DEBUG: Distance threshold = {distance_threshold}")
        
        try:
            collection_count = self.chroma_collection.count()
            print(f"🔍 DEBUG: ChromaDB collection count = {collection_count}")
        except Exception as e:
            print(f"❌ ERROR: Failed to get collection count: {e}")
            return {"documents": [[]], "metadatas": [[]], "distances": [[]]}

        # Check if vectorizer is fitted
        try:
            print("🔍 DEBUG: Creating query vector...")
            query_vector = self.vectorizer.transform([query]).toarray()[0].tolist()
            print(f"🔍 DEBUG: Query vector created successfully, length = {len(query_vector)}")
            print(f"🔍 DEBUG: Query vector sample (first 5): {query_vector[:5]}")
        except Exception as e:
            print(f"❌ ERROR: Vectorizer error: {e}")
            traceback.print_exc()
            return {"documents": [[]], "metadatas": [[]], "distances": [[]]}

        try:
            print(f"🔍 DEBUG: Querying ChromaDB with n_results={n_results}...")
            result = self.chroma_collection.query(
                query_embeddings=[query_vector],
                n_results=n_results
            )
            print(f"🔍 DEBUG: ChromaDB result keys: {list(result.keys())}")
            print(f"🔍 DEBUG: Raw documents returned: {len(result.get('documents', [[]])[0])}")
            print(f"🔍 DEBUG: Raw distances: {result.get('distances', [[]])[0]}")
            
            # Filter results based on distance threshold
            documents = result.get('documents', [[]])[0]
            metadatas = result.get('metadatas', [[]])[0]
            distances = result.get('distances', [[]])[0]
            
            # Filter by distance threshold
            filtered_documents = []
            filtered_metadatas = []
            filtered_distances = []
            
            for i, distance in enumerate(distances):
                if distance <= distance_threshold:
                    filtered_documents.append(documents[i])
                    filtered_metadatas.append(metadatas[i])
                    filtered_distances.append(distance)
                    print(f"🔍 DEBUG: Keeping document {i+1} with distance {distance}")
                else:
                    print(f"🔍 DEBUG: Filtering out document {i+1} with distance {distance} (> {distance_threshold})")
            
            # Return filtered results in the same format as ChromaDB
            filtered_result = {
                "documents": [filtered_documents],
                "metadatas": [filtered_metadatas], 
                "distances": [filtered_distances]
            }
            
            print(f"🔍 DEBUG: Filtered documents returned: {len(filtered_documents)}")
            print(f"🔍 DEBUG: Filtered distances: {filtered_distances}")
            print(f"🔍 DEBUG: Filtered metadatas count: {len(filtered_metadatas)}")
            
            return filtered_result
        except Exception as e:
            print(f"❌ ERROR: ChromaDB query failed: {e}")
            traceback.print_exc()
            return {"documents": [[]], "metadatas": [[]], "distances": [[]]}

    def generate_response(self, query: str) -> str:
        """
        Implements Retrieval Augmented Generation (RAG) by retrieving relevant documents
        and generating a response.
        """
        print(f"🤖 DEBUG: Starting response generation for query: '{query}'")
        
        # Check if we have any data in ChromaDB
        try:
            collection_count = self.chroma_collection.count()
            print(f'🤖 DEBUG: Collection count check: {collection_count}')
            if collection_count == 0:
                print("⚠️ DEBUG: No data in ChromaDB collection")
                return "No data available. Please click 'Ingest' to load data from the database first."
        except Exception as e:
            print(f"❌ ERROR: Failed to check collection count: {e}")
            return "Error checking data availability. Please try again or contact support."
        
        print("🤖 DEBUG: Retrieving relevant documents...")
        results = self.retrieve_documents(query)
        
        # ChromaDB returns a list wrapping the results; extract the first list.
        documents = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]
        
        print(f"🤖 DEBUG: Retrieved {len(documents)} documents")
        print(f"🤖 DEBUG: Retrieved {len(metadatas)} metadatas")
        
        if not documents:
            print("⚠️ DEBUG: No documents found for query")
            return "No relevant documents found for your query. Try rephrasing or check if data has been ingested."
        
        # Extract only company names and investors from the retrieved documents
        companies_info = []
        for i, (doc, meta) in enumerate(zip(documents, metadatas)):
            print(f"🤖 DEBUG: Processing document {i+1}:")
            print(f"🤖 DEBUG: Document preview: {doc[:100]}...")
            print(f"🤖 DEBUG: Metadata: {meta}")
            
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
            print(f"🤖 DEBUG: Extracted - Company: {company_name}, Amount: {funding_amount}")
        
        # Format the response to show only relevant information
        response_lines = [f"Query: {query}\n", "Retrieved Companies:"]
        print(f'🤖 DEBUG: Building response with {len(companies_info)} companies')
        
        for i, info in enumerate(companies_info, 1):
            response_lines.append(f"{i}. {info['company']} - {info['funding_amount']}")
            if info['investors'] and info['investors'] != "Unknown":
                response_lines.append(f"   Investors: {info['investors']}")
            response_lines.append("")  # Empty line for spacing
        
        final_response = "\n".join(response_lines)
        print(f"🤖 DEBUG: Final response length: {len(final_response)} characters")
        return final_response

    def _call_openrouter_llm(self, prompt: str) -> str:
        """
        Call OpenRouter LLM API with the given prompt
        """
        print(f"🤖 DEBUG: Calling OpenRouter LLM with prompt length: {len(prompt)}")
        
        if not self.openrouter_api_key:
            print("❌ ERROR: OpenRouter API key not found")
            return "Error: OpenRouter API key not configured. Please set OPENROUTER_API_KEY environment variable."
        
        headers = {
            "Authorization": f"Bearer {self.openrouter_api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.default_model,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "max_tokens": self.max_tokens,
            "temperature": self.temperature
        }
        
        try:
            print(f"🤖 DEBUG: Making request to {self.openrouter_base_url}")
            response = requests.post(
                self.openrouter_base_url,
                headers=headers,
                json=payload,
                timeout=30
            )
            
            print(f"🤖 DEBUG: Response status code: {response.status_code}")
            
            if response.status_code == 200:
                response_data = response.json()
                llm_response = response_data['choices'][0]['message']['content']
                print(f"🤖 DEBUG: LLM response length: {len(llm_response)}")
                return llm_response
            else:
                print(f"❌ ERROR: OpenRouter API error: {response.status_code}")
                print(f"❌ ERROR: Response: {response.text}")
                return f"Error calling LLM API: {response.status_code} - {response.text}"
                
        except requests.exceptions.Timeout:
            print("❌ ERROR: Request timeout")
            return "Error: Request to LLM API timed out. Please try again."
        except requests.exceptions.RequestException as e:
            print(f"❌ ERROR: Request exception: {e}")
            return f"Error: Network error when calling LLM API: {str(e)}"
        except Exception as e:
            print(f"❌ ERROR: Unexpected error: {e}")
            traceback.print_exc()
            return f"Error: Unexpected error when calling LLM API: {str(e)}"

    def generate_response_with_reasoning(self, query: str) -> str:
        """
        Implements Retrieval Augmented Generation (RAG) with LLM reasoning by retrieving 
        relevant documents and generating a reasoned response using OpenRouter LLM.
        """
        print(f"🤖 DEBUG: Starting RAG with reasoning for query: '{query}'")
        
        # Check if we have any data in ChromaDB
        try:
            collection_count = self.chroma_collection.count()
            print(f'🤖 DEBUG: Collection count check: {collection_count}')
            if collection_count == 0:
                print("⚠️ DEBUG: No data in ChromaDB collection")
                return "No data available. Please click 'Ingest' to load data from the database first."
        except Exception as e:
            print(f"❌ ERROR: Failed to check collection count: {e}")
            return "Error checking data availability. Please try again or contact support."
        
        print("🤖 DEBUG: Retrieving relevant documents...")
        results = self.retrieve_documents(query)
        
        # ChromaDB returns a list wrapping the results; extract the first list.
        documents = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0]
        
        print(f"🤖 DEBUG: Retrieved {len(documents)} documents")
        
        if not documents:
            print("⚠️ DEBUG: No documents found for query")
            return "No relevant documents found for your query. Try rephrasing or check if data has been ingested."
        
        # Create context from retrieved documents
        context_parts = []
        for i, (doc, meta, distance) in enumerate(zip(documents, metadatas, distances)):
            print(f"🤖 DEBUG: Processing document {i+1} with distance {distance}")
            context_parts.append(f"Document {i+1} (relevance: {1-distance:.3f}):\n{doc}")
        
        context = "\n\n".join(context_parts)
        
        # Create reasoning prompt
        reasoning_prompt = f"""You are an expert analyst specializing in startup funding and venture capital. 

Based on the following funding data retrieved from our database, please provide a comprehensive and insightful answer to this question: "{query}"

RETRIEVED FUNDING DATA:
{context}

INSTRUCTIONS:
1. Analyze the retrieved data carefully
2. Provide specific details about companies, funding amounts, investors, and dates when available
3. If the query asks about time periods (like "last 7 days"), note any limitations in the data
4. Organize your response clearly with bullet points or numbered lists when appropriate
5. Include relevant insights about funding trends, sectors, or investor patterns if applicable
6. If the data is limited or doesn't fully answer the question, acknowledge this

Please provide a detailed, professional response:"""

        print(f"🤖 DEBUG: Created reasoning prompt with {len(reasoning_prompt)} characters")
        
        # Call LLM for reasoning
        llm_response = self._call_openrouter_llm(reasoning_prompt)
        
        print(f"🤖 DEBUG: Received LLM response with {len(llm_response)} characters")
    
        return llm_response
    
    
