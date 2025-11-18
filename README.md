# Pulsar 🌌

**Pulsar** is an advanced **Narrative Intelligence** platform designed for the Italian news landscape.
It aggregates articles from diverse sources (e.g., ANSA, Il Giornale, La Repubblica) to reveal how the same event is framed differently across the political spectrum. Think of it as a "Ground.news" tailored for Italy, powered by state-of-the-art AI and clustering algorithms.

![Pulsar UI](https://via.placeholder.com/1200x600.png?text=Pulsar+Dashboard+Preview)

## ✨ Key Features

- **🔍 Hybrid Search Engine**:
  - Combines **Live Web Scraping** with a **Local Vector Database**.
  - Instantly retrieves historical results while fetching fresh news in the background.
  - **Full-Text Extraction**: Automatically visits article pages to scrape the full body text for deeper analysis.
- **🧠 AI-Powered Clustering**:
  - Uses **Hierarchical Agglomerative Clustering (HAC)** on semantic embeddings (Title + Snippet + Body) to group related articles with high precision.
  - **AI "Chief Editor"**: A GPT-4o based post-processing step that intelligently merges duplicate clusters.
- **⚖️ Advanced Bias Analysis (3-Layer System)**:
  - **Layer 1 (Source Bias)**: Uses historical reputation as a baseline.
  - **Layer 2 (AI Analysis)**: GPT-4o-mini analyzes the specific tone and framing of the article text.
  - **Layer 3 (Fusion Logic)**: A confidence-based system decides whether to trust the AI (if confidence > 65%) or fallback to the source's reputation, preventing hallucinations on neutral news.
  - **Localized Explanations**: Provides short, context-aware explanations in Italian for _why_ an article is classified a certain way.
- **⚡ High-Performance Scraping**:
  - **Parallel Execution**: Scrapers for different sources run concurrently using `ThreadPoolExecutor`, drastically reducing wait times.
  - **Smart Caching**: Results are cached in SQLite to ensure instant load times for repeated queries.
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

1.  **Search & Scrape**: The user queries a topic. Pulsar activates **parallel scrapers** to fetch the latest articles from supported Italian newspapers (ANSA, Il Giornale, La Repubblica) simultaneously.
2.  **Enrichment & Analysis**:
    - **Full-Text Scraping**: The system visits the URLs to extract the full content.
    - **AI Bias Check**: Each article is analyzed for political tone. The system calculates a **confidence score** to filter out noise.
    - **Vectorization**: An embedding is generated based on the full context.
    - **Persistence**: Data is saved to a local SQLite database.
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
