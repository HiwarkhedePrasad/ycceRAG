# 🧠 YCCE-AI — The Automated Knowledge Engine

> *"A self-updating RAG pipeline that turns a static college website into a living AI brain."*

---

## ⚡ Overview

YCCE-AI is an end-to-end Retrieval-Augmented Generation (RAG) system designed specifically for the Yeshwantrao Chavan College of Engineering (YCCE). It features a **zero-touch automated data pipeline** that scrapes, processes, and vectorizes college data, paired with a sleek, client-side AI chat interface for students and faculty.

### How the Pipeline Works:
1. **🕷️ Crawl:** A BFS spider runs daily to discover HTML pages and PDFs across the `ycce.edu` domain.
2. **📖 Extract:** Cleans boilerplate HTML and deep-dives into complex PDF tables (syllabi, rulebooks) page-by-page.
3. **🧠 Vectorize:** Chunks text and generates 384-dimensional embeddings using Supabase Edge Functions (`gte-small`).
4. **💾 Sync:** Upserts data into a Supabase `pgvector` database.
5. **🔄 Self-Heal:** Uses SHA-256 hashing to detect content changes. New information automatically overwrites outdated data, ensuring the AI is always up-to-date.
6. **💬 Chat:** A sleek, animated frontend queries the vector database and uses Google's Gemini Flash model to synthesize conversational answers.

---

## 🛠️ Tech Stack

| Component | Technology |
|---|---|
| **Language** | Python 3.12 |
| **Embeddings** | Supabase Edge Runtime (`gte-small`, 384-dim) |
| **Vector DB** | Supabase (PostgreSQL + `pgvector`) |
| **Generative AI** | Google Gemini 3 Flash Preview (Client-side) |
| **Text Processing** | LangChain (`RecursiveCharacterTextSplitter`) |
| **PDF Extraction** | PyMuPDF (`fitz`) |
| **HTML Parsing** | BeautifulSoup4 + `lxml` |
| **Frontend** | Vanilla HTML, CSS (Glassmorphism), JavaScript |
| **Automation** | GitHub Actions (Daily Cron) |

---

## 📁 Project Structure

```text
Prompt-a-thon/
├── main.py                    # Pipeline orchestrator
├── config.py                  # Environment & settings configurations
├── requirements.txt           # Python dependencies
├── .env.example               # Template for backend secrets
│
├── crawler/                   # Data Ingestion
│   ├── spider.py              # Sitemap parser & BFS web crawler
│   ├── extractor.py           # HTML text cleaner and noise removal
│   └── pdf_parser.py          # PDF text extractor via PyMuPDF
│
├── processor/                 # Data Transformation
│   ├── chunker.py             # LangChain text splitter
│   ├── embedder.py            # Supabase Edge Function embedding client
│   └── deduplicator.py        # SHA-256 change detection logic
│
├── database/                  # Storage Layer
│   ├── supabase_client.py     # DB operations (upsert/delete)
│   └── setup.sql              # One-time vector DB schema setup
│
├── frontend/                  # User Interface
│   ├── index.html             # Supabase Auth login/signup page
│   ├── chat.html              # Interactive RAG chat interface
│   ├── css/style.css          # UI styling
│   └── js/                    # Auth, Chat, and Supabase config scripts
│
└── .github/workflows/
    └── daily_scraper.yml      # GitHub Actions cron job for automation
```

---

## 🚀 Quick Start Guide

### 1. Local Repository Setup
Clone the repository and install the backend dependencies:
```bash
git clone https://github.com/your-org/ycce-ai.git
cd ycce-ai
pip install -r requirements.txt
```

### 2. Supabase Configuration
- Create a new project at [supabase.com](https://supabase.com).
- Navigate to the **SQL Editor** and execute the contents of `database/setup.sql` to initialize the `pgvector` extension, tables, and RPC search functions.
- Deploy the Supabase Edge Functions for embed and search (required for embedding generation and frontend querying).

### 3. Environment Variables
Create your `.env` file in the root directory:
```bash
cp .env.example .env
```

Edit the `.env` file with your specific credentials:
```env
SUPABASE_URL=your_project_url
SUPABASE_SERVICE_KEY=your_service_role_key
SUPABASE_ANON_KEY=your_anon_key
TARGET_DOMAIN=https://www.ycce.edu
MAX_PAGES=500
MAX_PDFS=200
```

*Note: Update `frontend/js/supabase-config.js` and `frontend/js/chat.js` with your public Supabase Anon Key and Gemini API Key.*

### 4. Run the Pipeline
Execute the orchestrator to begin crawling, extracting, and syncing data:
```bash
python main.py
```

### 5. Launch the Frontend
The frontend uses standard web technologies. You can serve it locally using Python's built-in HTTP server:
```bash
cd frontend
python -m http.server 8000
```
Navigate to `http://localhost:8000` to log in and chat.

---

## 🔑 Key Design Decisions

- **Prioritizing Freshness:** When a URL's content changes, all OLD chunks are deleted first, then new chunks are inserted. Newer always wins. The system never holds conflicting versions of the same page.
- **Smart Chunking:** The pipeline utilizes an overlapping window (`CHUNK_SIZE=500`, `CHUNK_OVERLAP=100`) to ensure context isn't lost between paragraph breaks.
- **PDF Deep-Dive:** PyMuPDF extracts text page-by-page, handling tables and complex layouts.
- **Deduplication:** SHA-256 hashes per chunk detect exact content changes — unchanged URLs are skipped entirely.
- **Serverless Scale:** By offloading embeddings to Supabase Edge Functions and answer generation to client-side Gemini API calls, the backend requires minimal compute overhead.

---

## 🤖 Automation (GitHub Actions)

The repository includes a workflow (`daily_scraper.yml`) that runs the pipeline automatically every day at midnight UTC (5:30 AM IST).
To enable this, add the following secrets to your GitHub repository:
- `SUPABASE_URL`
- `SUPABASE_SERVICE_KEY`
- `SUPABASE_ANON_KEY`

---

## 📊 How the Chatbot Queries

Once data is in Supabase, any frontend can call the `match_knowledge` function:

```sql
SELECT * FROM match_knowledge(
    query_embedding := '[0.1, 0.2, ...]'::vector,
    match_threshold := 0.7,
    match_count := 5
);
```

This returns the top 5 most relevant chunks with similarity scores, ready for an LLM to use as context.

---

## 📜 License

MIT License
