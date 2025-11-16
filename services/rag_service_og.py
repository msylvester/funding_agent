# pip install "llama-index>=0.10" "llama-index-llms-openai" "llama-index-vector-stores-chroma"
# also: pip install chromadb sentence-transformers

from llama_index.core import VectorStoreIndex, StorageContext
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.core.tools import QueryEngineTool
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.llms.openai import OpenAI as LlamaOpenAI
from llama_index.core.agent.workflow import FunctionAgent
import chromadb
'''
Add our config for a chroma_db and o4mini 
'''



# 1) Point to the current chroma_db that is local (in the .env file)
client = chromadb.PersistentClient(path="./chroma")
collection = client.get_or_create_collection("my_collection")
vector_store = ChromaVectorStore(chroma_collection=collection)

# 2) Use your embedding model
embed = HuggingFaceEmbedding(model_name="sentence-transformers/all-MiniLM-L6-v2")

# 3) Build an index over the existing vector store (no re-embed if it's already populated)
index = VectorStoreIndex.from_vector_store(vector_store=vector_store, embed_model=embed)

# 4) Make a query engine and wrap it as a TOOL
qe = index.as_query_engine(similarity_top_k=4)
rag_tool = QueryEngineTool.from_defaults(
    query_engine=qe,
    name="rag_search",
    description="Retrieve relevant passages from the Chroma knowledge base."
)

# 5) change the model to 04 mini
llm = LlamaOpenAI(model="gpt-4o-mini")  # or your preferred model
agent = FunctionAgent(llm=llm, tools=[rag_tool])

# Usage:
reply = agent.run("tell me about superdial ")
print(reply)

