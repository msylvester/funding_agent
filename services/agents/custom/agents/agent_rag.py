"""
RAG Agent for handling LLM reasoning and response generation
"""
import requests
import json
import traceback
from typing import List, Dict, Any


class RAGAgent:
    def __init__(self, openrouter_api_key: str, openrouter_base_url: str, 
                 default_model: str, max_tokens: int = 500, temperature: float = 0.1):
        """
        Initialize the RAG Agent with OpenRouter configuration
        
        Args:
            openrouter_api_key: API key for OpenRouter
            openrouter_base_url: Base URL for OpenRouter API
            default_model: Default model to use for LLM calls
            max_tokens: Maximum tokens for response
            temperature: Temperature for response generation
        """
        self.openrouter_api_key = openrouter_api_key
        self.openrouter_base_url = openrouter_base_url
        self.default_model = default_model
        self.max_tokens = max_tokens
        self.temperature = temperature

    def call_llm(self, prompt: str) -> str:
        """
        Call OpenRouter LLM API with the given prompt
        
        Args:
            prompt: The prompt to send to the LLM
            
        Returns:
            str: The LLM response or error message
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

    def generate_reasoning_response(self, query: str, documents: List[str], 
                                  metadatas: List[Dict], distances: List[float]) -> str:
        """
        Generate a reasoned response using retrieved documents and LLM
        
        Args:
            query: The user's query
            documents: List of retrieved documents
            metadatas: List of metadata for each document
            distances: List of similarity distances for each document
            
        Returns:
            str: The LLM-generated response with reasoning
        """
        print(f"🤖 DEBUG: Generating reasoning response for query: '{query}'")
        print(f"🤖 DEBUG: Processing {len(documents)} documents")
        
        if not documents:
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
        llm_response = self.call_llm(reasoning_prompt)
        
        print(f"🤖 DEBUG: Received LLM response with {len(llm_response)} characters")
        
        return llm_response
