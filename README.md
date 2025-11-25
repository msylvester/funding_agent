# 💰 Funding Intelligence RAG

A comprehensive RAG (Retrieval-Augmented Generation) system for analyzing startup funding data with AI-powered insights using a sophisticated multi-agent architecture.


<figure>
  <img src="images/home_.png" alt="Funding Intelligence RAG Home Screen" width="600">
  <figcaption><strong>Figure 1:</strong> Home screen of the Funding Intelligence RAG Streamlit app.</figcaption>
</figure>

## ✨ Features

- 🤖 **Multi-Agent Workflows**: Hierarchical AI agent orchestration using OpenAI Agents SDK
- 🧠 **Custom RAG System**: Production-grade RAG with ChromaDB vectorization and intelligent reasoning
- 🔍 **Intelligent Query Routing**: Automatic intent classification and workflow selection
- 💡 **Investor Recommendations**: AI-powered investor matching based on sector and funding data
- 🔬 **Company Research**: Automated research combining internal knowledge base with live web search
- 🕷️ **Web Scraping**: Automated scraping of TechCrunch and other funding sources
- 🌐 **Streamlit Interface**: Interactive multi-page web app
- 📊 **MongoDB Integration**: Scalable database storage for funding data

## 🤖 Multi-Agent Workflow Architecture

The system implements a sophisticated multi-agent architecture using the **OpenAI Agents SDK (v0.3.0+)** with a hierarchical orchestrator-worker pattern. Multiple specialized AI agents collaborate in chains to deliver intelligent responses.

### Architecture Overview

```
User Query (Streamlit)
    ↓
Orchestrator Workflow (Intent Classification)
    ↓
    ├─ "advice" → Advice Workflow
    │       ↓
    │   1. Sector Classifier Agent (GPT-4o-mini)
    │   2. Advice Agent (GPT-4o + MongoDB tools)
    │   3. Summarize Agent (GPT-4o)
    │
    └─ "research" → Research Workflow
            ↓
        1. RAG Research Agent (GPT-4o + RAG tools)
        2. Web Research Agent (GPT-4o-mini + WebSearch)
```

### Workflow Components

#### 🎯 Orchestrator Workflow (`services/workflows/orchestrator_workflow.py`)
**Entry point for all user queries** - intelligently routes requests to specialized workflows.

- **Intent Classifier Agent** (GPT-4o-mini): Analyzes user intent and classifies into:
  - **"advice"**: Fundraising recommendations, investor matching, strategy questions
  - **"research"**: Company information lookup, funding history queries
- **Smart Routing**: Directs queries to appropriate specialized workflow based on classification
- **Trace Metadata**: Built-in observability for debugging and monitoring

#### 🔬 Research Workflow (`services/workflows/research_workflow.py`)
**Multi-stage pipeline** for comprehensive company research combining internal knowledge with live web data.

**Agent Chain**:
1. **RAG Research Agent** (GPT-4o):
   - Queries ChromaDB vector database using custom RAG tools
   - Retrieves relevant companies from internal funding knowledge base
   - Returns structured list with company names, descriptions, and relevance scores

2. **Web Research Agent** (GPT-4o-mini):
   - Enriches RAG results with live web search
   - Gathers: website, company size, headquarters, founding year, industry details
   - Returns comprehensive company profiles

**Data Flow**: Conversation history is maintained across agent calls, enabling context-aware responses.

#### 💡 Advice Workflow (`services/workflows/advice_workflow.py`)
**Intelligent investor matching** and strategic fundraising guidance.

**Agent Chain**:
1. **Sector Classification**:
   - Dynamically fetches valid sectors from MongoDB
   - Uses OpenAI structured outputs with confidence scoring
   - Confidence threshold: 0.8 (falls back to generic advice below threshold)

2. **Advice Agent** (GPT-4o):
   - Uses MongoDB function tools to query funding database:
     - `search_funded_companies_by_sector()`: Find funded companies in target sector
     - `get_investors_for_sector()`: Get investor activity statistics
   - Extracts investor-company relationships
   - Generates personalized strategic advice

3. **Summarize & Display Agent** (GPT-4o):
   - Condenses advice into dashboard-friendly format
   - Structures output for UI presentation

### Agent Composition Pattern

All workflows follow this reusable pattern:

```python
# 1. Define Agent with OpenAI Agents SDK
agent = Agent(
    name="Agent Name",
    instructions="Detailed agent instructions...",
    model="gpt-4o",                    # or "gpt-4o-mini"
    output_type=PydanticSchema,        # Structured output validation
    tools=[tool1, tool2],               # Function tools (RAG, MongoDB, WebSearch)
    model_settings=ModelSettings(store=True)
)

# 2. Run Agent Asynchronously
result = await Runner.run(
    agent,
    input=conversation_history,
    run_config=RunConfig(
        trace_metadata={"workflow_id": "..."}
    )
)

# 3. Extract Structured Output
output = result.final_output  # Pydantic model instance
```

**Key Features**:
- **Pydantic Schemas**: Enforce structured, type-safe outputs
- **Conversation History**: Maintained between agents for contextual awareness
- **Function Tools**: Reusable capabilities (RAG, MongoDB, WebSearch) injected into agents
- **Async Execution**: High-performance async/await patterns
- **Observability**: Built-in trace metadata for debugging

## 🧠 Custom RAG Tool Implementation

The system features a production-grade RAG (Retrieval-Augmented Generation) implementation using a **dual-layer architecture**: ChromaDB for vector storage and OpenRouter LLM for intelligent reasoning.

### RAG Architecture

```
MongoDB (Source Data)
    ↓
DataService (Orchestration)
    ↓
    ├─ OpenAI Embeddings (text-embedding-3-small, 1536-dim)
    ↓
ChromaDB (Vector Storage)
    ↓
RAG Agent (OpenRouter LLM Reasoning)
    ↓
Structured Response
```

### Three RAG Function Tools

The RAG system exposes three function tools (via `services/agents/rag_service_agent.py`) that any agent can use:

#### 1. `rag_semantic_search(query, top_k=5, distance_threshold=0.3)`
**Vector similarity search** in ChromaDB knowledge base.

- Creates query embedding using OpenAI
- Performs cosine similarity search
- Filters by distance threshold (0 = identical, 2 = opposite)
- Returns documents, metadata, distances, and count

**Example**:
```python
results = rag_semantic_search("fintech startups", top_k=5)
# Returns: {documents: [...], metadatas: [...], distances: [...], count: 5}
```

#### 2. `rag_generate_reasoning(query, documents, metadatas_json, distances)`
**LLM-powered synthesis** from retrieved documents.

- Takes search results as input
- Uses OpenRouter LLM for intelligent reasoning
- Synthesizes coherent answer with citations
- Acknowledges data limitations when appropriate

**Example**:
```python
answer = rag_generate_reasoning(
    query="Who invested in Stripe?",
    documents=retrieved_docs,
    metadatas_json=json.dumps(metadata),
    distances=distances
)
# Returns: "Stripe was funded by [investors], raising $X million..."
```

#### 3. `rag_full_query(query, top_k=5)`
**Convenience tool** combining search + reasoning in one call.

- All-in-one: retrieval + synthesis
- Returns structured dict with answer, sources, and document count
- Recommended for most use cases

**Example**:
```python
result = rag_full_query("AI companies in healthcare")
# Returns: {answer: "...", sources: [...], document_count: 5}
```

### Usage in Agents

RAG tools are injected into agents via `get_rag_tools()`:

```python
from services.agents.rag_service_agent import get_rag_tools

rag_research_agent = Agent(
    name="RAG research agent",
    instructions="You are a research assistant with RAG access...",
    model="gpt-4o",
    output_type=RagResearchAgentSchema,
    tools=get_rag_tools(),  # ← RAG tools available to agent
    model_settings=ModelSettings(store=True)
)
```

The agent can now autonomously decide when and how to use RAG tools based on the user query.

### ChromaDB Integration

**Vector Database**: ChromaDB with persistent storage at `./chromadb_data`

**Storage Schema**:
- **Documents**: Text format: `"Company: [name]\nDescription: [description]"`
- **Embeddings**: OpenAI text-embedding-3-small vectors (1536 dimensions)
- **Metadata**:
  - `company_name`: Company identifier
  - `company_index`: Index in source data
  - `date_unix`: Unix timestamp (optional)
- **Distance Metric**: Cosine similarity (default)

**Data Pipeline** (`services/database/data_service.py`):
1. **Ingestion**: `ingest_data()` pulls companies from MongoDB
2. **Embedding**: `embed_data()` creates vectors with OpenAI API
3. **Storage**: Batch insertion into ChromaDB with metadata
4. **Retrieval**: `retrieve_documents()` performs similarity search
5. **Reasoning**: `generate_response_with_reasoning()` synthesizes answers

**Key Features**:
- **Auto-ingestion**: Automatically loads data from MongoDB if ChromaDB is empty
- **Similarity Filtering**: Configurable threshold for relevance (default: 0.3 distance)
- **Batch Processing**: Efficient embedding creation for large datasets
- **Persistent Storage**: Data persists across application restarts

### RAG Agent (`services/agents/custom/agent_rag.py`)

**LLM reasoning layer** using OpenRouter API.

**Features**:
- Configurable model selection (default via OpenRouter)
- Context construction from retrieved documents
- Prompt engineering for funding domain expertise
- Citation of specific details (companies, amounts, investors, dates)
- Acknowledgment of data limitations

**Example Prompt Pattern**:
```
You are a funding data expert. Based on these documents:
[Document 1] Company: Stripe, Description: Payment processing...
[Document 2] Company: Plaid, Description: Financial APIs...

Answer this query: "Who invested in fintech companies?"
Cite specific details and acknowledge if data doesn't fully answer.
```

<figure>
  <img src="images/results.png" alt="Funding Intelligence RAG Query Results" width="600">
  <figcaption><strong>Figure 2:</strong> Example of AI-powered funding query results.</figcaption>
</figure>

## 📦 Installation

The project is **pip-installable** with a standard Python package structure, making it easy to install and import across different environments.

### Quick Install

**Development Mode** (recommended for development):
```bash
# Clone the repository
git clone <repository-url>
cd funding_scraper

# Install in editable mode
pip install -e .

# Install dependencies
pip install -r requirements.txt
```

**Production Install**:
```bash
pip install .
```

### Package Structure

The project uses `pyproject.toml` for modern Python packaging:

```toml
[project]
name = "funding_scraper"
version = "0.1.0"
description = "Funding data scraper and investor recommendation system"
requires-python = ">=3.8"
```

**Included Packages**:
- `services/` - Core business logic and agents
  - `services.agents` - AI agents (RAG, sector, advice)
  - `services.workflows` - Multi-agent workflows
  - `services.database` - MongoDB and ChromaDB integration
  - `services.scrapers` - Web scraping modules
  - `services.processing` - Data processing utilities
- `config/` - Application configuration
- `views/` - Streamlit UI pages
- `ui/` - UI components and styling
- `utils/` - Utility functions

### Import Usage

After installation, import from anywhere:

```python
# Import workflow orchestrator
from services.workflows.orchestrator_workflow import run_orchestrator_workflow

# Import RAG tools
from services.agents.rag_service_agent import get_rag_tools

# Import configuration
from config.settings import API_CONFIG

# Import database services
from services.database.data_service import DataService
from services.database.mongodb_tools import search_funded_companies_by_sector

# Run async workflow
import asyncio
result = asyncio.run(run_orchestrator_workflow("Research Tesla"))
```

### Environment Setup

**Required Environment Variables**:
```bash
# OpenAI API (for embeddings and agents)
export OPENAI_API_KEY=your_openai_key_here

# OpenRouter API (for RAG reasoning)
export OPENROUTER_API_KEY=your_openrouter_key_here

# MongoDB (optional, defaults to localhost)
export MONGODB_URI=mongodb://localhost:27017/
```

**Optional Configuration**:
```bash
# ChromaDB path (defaults to ./chromadb_data)
export CHROMA_PATH=./chromadb_data

# Logging level
export LOG_LEVEL=INFO
```

## 🎮 Usage

### 🎨 Run the Streamlit Web Interface
```bash
streamlit run app.py
```

### 💻 Programmatic Usage

```python
import asyncio
from services.workflows.orchestrator_workflow import run_orchestrator_workflow

# Run a research query
async def main():
    result = await run_orchestrator_workflow("What investors fund AI startups?")
    print(result)

asyncio.run(main())
```

### 🧪 Testing Harnesses

Test individual components:
```bash
# Test sector classification
python services/harnesses/sector_harness.py

# Test advice workflow
python services/harnesses/advice_harness.py

# Test research workflow
python services/harnesses/research_workflow_harness.py
```

## 📁 Project Structure

### 🎯 Main Application
- `app.py` - Streamlit multi-page application

### 🤖 AI Agents & Workflows (`/services/`)

**Workflows** (`/services/workflows/`):
- `orchestrator_workflow.py` - Main entry point with intent classification
- `research_workflow.py` - RAG + web research pipeline
- `advice_workflow.py` - Investor matching and strategic advice

**Agents** (`/services/agents/`):
- `rag_service_agent.py` - RAG function tools for agents
- `sector_agent.py` - Sector classification agent
- `custom/agent_rag.py` - RAG reasoning agent (OpenRouter)

**Database** (`/services/database/`):
- `data_service.py` - ChromaDB integration and embeddings
- `mongodb_tools.py` - MongoDB function tools for agents
- `database.py` - MongoDB operations and schema

**Scrapers** (`/services/scrapers/`):
- `scraper_service.py` - TechCrunch scraper
- `article_processor.py` - Article content processing

**Harnesses** (`/services/harnesses/`):
- Testing frameworks for individual workflow components

### 🎨 UI Components (`/ui/` & `/views/`)
- `views/research.py` - Research page with orchestrator integration
- `ui/components.py` - Reusable Streamlit components
- `ui/styles.py` - Custom CSS styling

### ⚙️ Configuration (`/config/`)
- `settings.py` - Application configuration and API settings

## 🔧 Key Components

- **🎯 Multi-Agent Orchestration**: Hierarchical agent workflow with intelligent routing
- **🧠 Production RAG System**: ChromaDB + OpenAI embeddings + OpenRouter reasoning
- **💡 Investor Matching**: AI-powered recommendations based on sector analysis
- **🔍 Vector Search**: Semantic similarity search for funding data retrieval
- **⚡ Live Web Research**: Real-time data enrichment via web search
- **🤖 Function Tools**: Reusable RAG and MongoDB tools for any agent
- **📊 Database Integration**: MongoDB storage with comprehensive schema
- **🎨 Interactive UI**: Streamlit multi-page app with research and advice pages

## 🛠️ Technology Stack

- **Agents**: OpenAI Agents SDK 0.3.0+
- **LLMs**: GPT-4o, GPT-4o-mini, OpenRouter models
- **Embeddings**: OpenAI text-embedding-3-small (1536-dim)
- **Vector DB**: ChromaDB (persistent, cosine similarity)
- **Document DB**: MongoDB
- **UI**: Streamlit multi-page app
- **Schema Validation**: Pydantic v2+
- **Web Scraping**: BeautifulSoup4, requests
