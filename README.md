# 💰 Funding Scraper

A comprehensive funding data scraper and RAG (Retrieval-Augmented Generation) agent for tracking startup funding rounds from TechCrunch.

## ✨ Features

- 🕷️ **Web Scraping**: Automated scraping of TechCrunch funding articles
- 🤖 **AI-Powered Classification**: Smart funding article detection using OpenRouter API
- 🧠 **RAG Agent**: Intelligent query system with TF-IDF vectorization for funding data retrieval
- 🌐 **Streamlit Interface**: Interactive web app for querying funding data
- 📊 **MongoDB Integration**: Scalable database storage for funding data

## 📁 Project Structure

### 🎯 Main Application
- `rag_agent.py` - 🎨 Streamlit RAG interface for querying funding data

### 🛠️ Services (`/services/`)
- `techcrunch_minimal.py` - 🕷️ Main TechCrunch scraper with AI enhancement
- `article_processor.py` - 📝 Article content processing and funding data extraction
- `database.py` - 🗄️ MongoDB database operations and schema management

### 🤖 AI Agents (`/services/agents/`)
- `agent_007.py` - 🎯 AI agent for classifying funding articles using OpenRouter API
- `agent_data_struct.py` - 🧠 AI agent for extracting structured funding data

### 📊 Data Files
- `techcrunch_minimal.json` - 📄 Latest scraped funding data from TechCrunch

## 🚀 Setup

1. **Install dependencies:**
```bash
pip install streamlit pandas scikit-learn beautifulsoup4 requests numpy pymongo
```

2. **Set OpenRouter API key for AI enhancement:**
```bash
export OPENROUTER_API_KEY=your_api_key_here
```

3. **Set MongoDB connection (optional):**
```bash
export MONGODB_URI=mongodb://localhost:27017/
```

## 🎮 Usage

### 🎨 Run the RAG Agent Interface
```bash
streamlit run rag_agent.py
```

### 🕷️ Run the Scraper
```bash
cd services
python techcrunch_minimal.py
```

### 🗄️ Load Data to Database
```bash
cd services
python load_techcrunch_to_db.py --list  # View current database
python load_techcrunch_to_db.py         # Load new data
```

## 🔧 Key Components

- **🎯 Smart Filtering**: AI-powered funding article classification
- **🔍 Semantic Search**: TF-IDF vectorization for relevant funding round retrieval  
- **⚡ Real-time Scraping**: Live data collection from TechCrunch funding articles
- **🤖 AI Enhancement**: OpenRouter API integration for structured data extraction
- **📊 Database Integration**: MongoDB storage with comprehensive schema