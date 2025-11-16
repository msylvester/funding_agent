# pip install "llama-index>=0.10" "llama-index-llms-openai" \
#             "llama-index-vector-stores-chroma" chromadb sentence-transformers

from llama_index.core import VectorStoreIndex, Document
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.core.tools import QueryEngineTool
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.llms.openai import OpenAI as LlamaOpenAI
from llama_index.core.agent.workflow import FunctionAgent
import chromadb
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database import FundingDatabase


def create_rag_agent():
    """
    Create a RAG agent with safer Chroma initialization.
    Uses EphemeralClient to avoid stale connections and creates fresh embeddings.
    """
    # 1) Use EphemeralClient for safer initialization (no stale connections)
    client = chromadb.EphemeralClient()
    collection = client.create_collection("rag_knowledge_base")

    # 2) Load data from MongoDB
    print("Loading data from MongoDB...")
    db = FundingDatabase()
    companies = db.read_all_companies()
    print(f"Loaded {len(companies)} companies")

    # 3) Create documents from company data
    documents = []
    for company in companies:
        company_name = company.get('company_name', '')
        description = company.get('description', '')

        if company_name or description:
            doc_text = f"Company: {company_name}\nDescription: {description}"
            doc = Document(
                text=doc_text,
                metadata={
                    "company_name": company_name,
                    "source": "mongodb"
                }
            )
            documents.append(doc)

    print(f"Created {len(documents)} documents for embedding")

    # 4) Use SentenceTransformer model for embeddings
    embed = HuggingFaceEmbedding(model_name="sentence-transformers/all-MiniLM-L6-v2")

    # 5) Create ChromaVectorStore and build index with fresh embeddings
    vector_store = ChromaVectorStore(chroma_collection=collection)
    index = VectorStoreIndex.from_documents(
        documents,
        vector_store=vector_store,
        embed_model=embed,
        show_progress=True
    )

    print("Embeddings created successfully")

    # 6) Create a query engine + wrap it as a TOOL
    qe = index.as_query_engine(similarity_top_k=4)
    rag_tool = QueryEngineTool.from_defaults(
        query_engine=qe,
        name="rag_search",
        description="Retrieve relevant passages from the Chroma knowledge base.",
    )

    # 7) Use GPT-4o-mini as your reasoning LLM
    llm = LlamaOpenAI(model="gpt-4o-mini")
    agent = FunctionAgent(llm=llm, tools=[rag_tool])

    return agent


# --- Run a test query ---
if __name__ == "__main__":
    import asyncio

    agent = create_rag_agent()

    async def main():
        reply = await agent.run("Tell me about Superdial")
        print(reply)

    asyncio.run(main())
