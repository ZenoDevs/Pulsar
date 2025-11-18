# Pulsar 🌌

**Pulsar** is an advanced **Narrative Intelligence** platform designed for the Italian news landscape.
It aggregates articles from diverse sources (e.g., ANSA, Il Giornale, La Repubblica) to reveal how the same event is framed differently across the political spectrum. Think of it as a "Ground.news" tailored for Italy, powered by state-of-the-art AI and clustering algorithms.

![Pulsar UI](https://via.placeholder.com/1200x600.png?text=Pulsar+Dashboard+Preview)

## ✨ Key Features

- **🔍 Multi-Source Search**: Real-time scraping and aggregation from major Italian news outlets.
- **🧠 AI-Powered Clustering**:
  - Uses **Hierarchical Agglomerative Clustering (HAC)** on semantic embeddings to group related articles with high precision.
  - **AI "Chief Editor"**: A GPT-4o based post-processing step that intelligently merges duplicate clusters (e.g., "Tregua a Gaza" vs "Cessate il fuoco").
- **⚖️ Bias Analysis**:
  - Automatically detects the political leaning (Left, Center, Right) of every single article using LLMs.
  - Visualizes the "Bias Distribution" for each story with intuitive color-coded bars and indicators.
- **🤖 Deep Coverage Analysis**:
  - Generates an on-demand **AI Report** for every story.
  - Provides a **Neutral Overview** of the facts.
  - Analyzes **Editorial Framing**, explaining _why_ and _how_ sources differ in their coverage, citing specific headlines.
- **💎 Liquid Glass UI**: A modern, responsive interface featuring glassmorphism, smooth animations, and a "Pulsar" loader.

## 🛠️ Tech Stack

### Backend (`/backend`)

- **Framework**: [FastAPI](https://fastapi.tiangolo.com/) (Python 3.12+)
- **AI & NLP**:
  - **OpenAI API** (GPT-4o-mini, text-embedding-3-small) for embeddings, bias detection, and summarization.
  - **Scikit-learn** & **NumPy** for vector math and clustering algorithms.
- **Data Processing**:
  - Custom scrapers using `BeautifulSoup4` and `Requests`.
  - `Pandas` for data manipulation.
  - Background tasks for non-blocking search operations.
- **Caching**: SQLite / In-memory caching to minimize API costs and latency.

### Frontend (`/frontend`)

- **Framework**: [React](https://react.dev/) (Vite)
- **Styling**: Custom CSS with **Glassmorphism** design system.
- **Routing**: `react-router-dom` for navigation.
- **Markdown**: `react-markdown` for rendering rich AI analysis.

## 🚀 How It Works

1.  **Search & Scrape**: The user queries a topic. Pulsar activates parallel scrapers to fetch the latest articles from supported Italian newspapers.
2.  **Enrichment**:
    - Each article is analyzed by GPT-4o-mini to determine its political bias.
    - An embedding vector is generated for the article's content.
3.  **Clustering (The "Magic Touch")**:
    - Articles are grouped into "Stories" using HAC based on cosine similarity of their embeddings.
    - An AI agent reviews the clusters and merges those referring to the exact same event, ensuring no duplicates.
4.  **Presentation**:
    - Stories are ranked by "hotness" (number of articles).
    - The UI displays the bias distribution and allows users to drill down into the coverage.
5.  **Analysis**:
    - On the detail page, an AI agent reads all headlines and snippets to produce a comparative analysis of the media coverage.

## 📦 Installation & Setup

### Prerequisites

- Python 3.10+
- Node.js 18+
- An OpenAI API Key

### 1. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv .venv

# Activate virtual environment
# Windows (PowerShell):
.\.venv\Scripts\Activate.ps1
# Linux/Mac:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure Environment
# Create a .env file in /backend and add:
# OPENAI_API_KEY=sk-your-key-here

# Run Server
uvicorn app.main:app --reload
```

Backend runs on `http://localhost:8000`. API Docs at `/docs`.

### 2. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Run Development Server
npm run dev
```

Frontend runs on `http://localhost:5173`.

## 🔮 Future Roadmap

- [ ] **Historical Timeline**: Visualize how a narrative evolves over time.
- [ ] **More Sources**: Add support for Il Corriere, La Stampa, and independent blogs.
- [ ] **User Accounts**: Save favorite topics and track specific narratives.
- [ ] **RAG Chat**: Chat with the news using Retrieval-Augmented Generation.

---

**Pulsar** - _Illuminating the narrative._
