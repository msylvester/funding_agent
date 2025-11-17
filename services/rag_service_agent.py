"""
RAG Service Agent - Function Tool Implementation

This module provides a RAG (Retrieval Augmented Generation) agent that can be used
as tools within other OpenAI Agents SDK workflows.
"""

from __future__ import annotations
from typing import Any
import asyncio
import sys
import os

# Path setup for imports
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from agents import Agent, ModelSettings, Runner, RunConfig, TResponseInputItem, trace, function_tool
from pydantic import BaseModel
from typing import Any
import json

# Import DataService for RAG functionality
from services.data_service import DataService


# ===============================
# GLOBAL DATA SERVICE INSTANCE
# ===============================

# Lazy initialization to avoid loading ChromaDB on import
_data_service_instance = None

def _get_data_service() -> DataService:
    """Get or create the singleton DataService instance."""
    global _data_service_instance
    if _data_service_instance is None:
        _data_service_instance = DataService()

        # Check if ChromaDB collection is empty and auto-ingest if needed
        if _data_service_instance.chroma_collection.count() == 0:
            print("⚠️ ChromaDB collection is empty. Auto-ingesting data from MongoDB...")
            result = _data_service_instance.ingest_data()
            if isinstance(result, dict) and result.get('success'):
                print(f"✅ {result.get('message', 'Data ingested successfully')}")
            else:
                error_msg = result.get('message', str(result)) if isinstance(result, dict) else str(result)
                print(f"❌ Ingestion issue: {error_msg}")
    return _data_service_instance


def reset_data_service():
    """Reset the singleton DataService instance.

    Call this after embed_data() to ensure fresh collection reference.
    """
    global _data_service_instance
    _data_service_instance = None
    print("🔄 DataService singleton reset - will reinitialize on next access")


# ===============================
# SCHEMAS
# ===============================

class RAGSource(BaseModel):
    """Represents a single source document from RAG retrieval."""
    company_name: str
    relevance_score: float
    document_snippet: str


class RAGQueryResponse(BaseModel):
    """Structured output for RAG queries."""
    answer: str
    sources: list[RAGSource]
    confidence_score: float
    reasoning: str


# ===============================
# FUNCTION TOOLS
# ===============================

@function_tool
def rag_semantic_search(query: str, top_k: int = 5, distance_threshold: float = 0.3) -> dict:
    """
    Search the ChromaDB vector store for documents relevant to the query.

    This tool performs semantic similarity search using OpenAI embeddings
    to find the most relevant company documents based on the query.

    Args:
        query: The search query (e.g., "fintech startups in Saudi Arabia")
        top_k: Maximum number of results to return (default: 5)
        distance_threshold: Minimum similarity score for relevance filtering (default: 0.3, range 0.0-1.0)

    Returns:
        Dictionary containing:
            - documents: List of relevant document texts
            - metadatas: List of metadata for each document (company_name, company_index)
            - distances: List of similarity distances (lower = more similar)
            - count: Number of results returned
    """
    ds = _get_data_service()

    # Retrieve documents using DataService's method
    results = ds.retrieve_documents(query, n_results=top_k, similarity_threshold=distance_threshold)

    # Extract from nested lists (ChromaDB format)
    documents = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]
    distances = results.get("distances", [[]])[0]

    return {
        "documents": documents,
        "metadatas": metadatas,
        "distances": distances,
        "count": len(documents)
    }


@function_tool
def rag_generate_reasoning(query: str, documents: list[str], metadatas_json: str, distances: list[float]) -> str:
    """
    Generate a reasoned response using the RAG agent based on retrieved documents.

    This tool takes the retrieved documents and uses an LLM to generate
    a comprehensive, reasoned answer that synthesizes the information.

    Args:
        query: The original user query
        documents: List of document texts from rag_semantic_search
        metadatas_json: JSON string of metadata list from rag_semantic_search (e.g., '[{"company_name": "...", "company_index": 0}]')
        distances: List of distance scores from rag_semantic_search

    Returns:
        A reasoned response string that answers the query based on the documents.
    """
    ds = _get_data_service()

    if not documents:
        return "No relevant documents were found for this query. Please try a different search term."

    # Parse metadatas from JSON string
    metadatas = json.loads(metadatas_json)

    # Use the RAG agent to generate reasoning
    response = ds.rag_agent.generate_reasoning_response(query, documents, metadatas, distances)

    return response


@function_tool
def rag_full_query(query: str, top_k: int = 5) -> dict:
    """
    Perform a complete RAG query: search + generate reasoned response.

    This is a convenience tool that combines semantic search and reasoning
    generation into a single call.

    Args:
        query: The search query to answer
        top_k: Maximum number of documents to retrieve (default: 5)

    Returns:
        Dictionary containing:
            - answer: The generated reasoned response
            - sources: List of source company names used
            - document_count: Number of documents retrieved
    """
    ds = _get_data_service()

    # Step 1: Retrieve documents
    results = ds.retrieve_documents(query, n_results=top_k)
    documents = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]
    distances = results.get("distances", [[]])[0]

    if not documents:
        return {
            "answer": "No relevant documents found for your query.",
            "sources": [],
            "document_count": 0
        }

    # Step 2: Generate reasoning
    answer = ds.rag_agent.generate_reasoning_response(query, documents, metadatas, distances)

    # Extract source company names
    sources = [meta.get("company_name", "Unknown") for meta in metadatas]

    return {
        "answer": answer,
        "sources": sources,
        "document_count": len(documents)
    }


# ===============================
# RAG QUERY AGENT
# ===============================

rag_query_agent = Agent(
    name="RAG Query Agent",
    instructions="""
You are a RAG (Retrieval Augmented Generation) research assistant with access to a knowledge base
of funded startup companies.

Your workflow:
1. When given a query, use rag_semantic_search to find relevant documents
2. Analyze the retrieved documents and their relevance scores (distances)
3. Use rag_generate_reasoning to synthesize a comprehensive answer
4. Provide your final response with sources and confidence assessment

Guidelines:
- Always cite which companies/documents informed your answer
- Be honest about the relevance and coverage of the retrieved information
- If no relevant documents are found, say so clearly
- Lower distance scores indicate higher relevance (< 1.0 is very relevant, > 1.5 is loosely relevant)
- Provide a confidence score (0.0-1.0) based on:
  - Number of relevant documents found
  - Distance scores (relevance)
  - How well the documents address the query

Output format:
- answer: Your synthesized response to the query
- sources: List of {company_name, relevance_score, document_snippet}
- confidence_score: 0.0-1.0 based on evidence quality
- reasoning: Brief explanation of how you arrived at the answer
""",
    model="gpt-4o",
    output_type=RAGQueryResponse,
    tools=[rag_semantic_search, rag_generate_reasoning],
    model_settings=ModelSettings(store=True),
)


# ===============================
# WORKFLOW FUNCTIONS
# ===============================

async def run_rag_query(question: str) -> dict[str, Any]:
    """
    Run a RAG query using the agent to retrieve and reason over documents.

    Args:
        question: The user's question to answer using RAG

    Returns:
        Dictionary containing:
            - answer: The generated answer
            - sources: List of source information
            - confidence_score: Confidence in the answer
            - reasoning: Explanation of the answer
    """
    with trace("RAG Query Workflow"):
        conversation_history: list[TResponseInputItem] = [
            {
                "role": "user",
                "content": [{"type": "input_text", "text": question}],
            }
        ]

        result = await Runner.run(
            rag_query_agent,
            input=conversation_history,
            run_config=RunConfig(
                trace_metadata={
                    "__trace_source__": "rag-service-agent",
                    "workflow_id": "rag_query_v1",
                }
            ),
        )

        output = result.final_output

        return {
            "answer": output.answer,
            "sources": [
                {
                    "company_name": source.company_name,
                    "relevance_score": source.relevance_score,
                    "document_snippet": source.document_snippet,
                }
                for source in output.sources
            ],
            "confidence_score": output.confidence_score,
            "reasoning": output.reasoning,
        }


def run_rag_query_sync(question: str) -> dict[str, Any]:
    """
    Synchronous wrapper for run_rag_query().

    Use this for testing harnesses or synchronous code.

    Args:
        question: The user's question to answer using RAG

    Returns:
        Dictionary with answer, sources, confidence_score, and reasoning.
    """
    return asyncio.run(run_rag_query(question))


# ===============================
# EXPORT TOOLS FOR OTHER AGENTS
# ===============================

def get_rag_tools():
    """
    Get the RAG function tools for use in other agents.

    Returns:
        List of function tools that can be passed to an Agent's tools parameter.

    Example:
        from rag_service_agent import get_rag_tools

        my_agent = Agent(
            name="My Agent",
            tools=get_rag_tools() + [other_tool],
            ...
        )
    """
    return [rag_semantic_search, rag_generate_reasoning, rag_full_query]


# ===============================
# STANDALONE TESTING
# ===============================

if __name__ == "__main__":
    print("Testing RAG Service Agent...")
    print("=" * 50)

    # Test queries
    test_queries = [
        #should at least select Vast Data
        "storage technology",
        # should at least select tahoe therapeutics
        "medical research",
        # should at least select uno platform
        "enterprise grade developer tools",

        # should at least describe Palabar
        "ai powered speech translation",
        #should at least describe 8 sleep
        "ai powered sleep tech",
        
    ]

    for query in test_queries:
        print(f"\nQuery: {query}")
        print("-" * 50)

        try:
            result = run_rag_query_sync(query)
            print(f"Answer: {result['answer'][:200]}...")
            print(f"Confidence: {result['confidence_score']}")
            print(f"Sources: {len(result['sources'])} documents")
            for source in result['sources'][:3]:
                print(f"  - {source['company_name']} (relevance: {source['relevance_score']:.2f})")
        except Exception as e:
            print(f"Error: {e}")

        print("=" * 50)
