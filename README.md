# 📝 Job Description Suggestor Agent

An intelligent, human-in-the-loop AI system to help hiring managers create, customize, and finalize job descriptions with ease — powered by OpenAI GPT‑4o and optional local LLMs via Ollama.

---

## 🔧 Features

- 🧠 **AI Draft Generation** — Generate initial job description drafts from hiring manager inputs using OpenAI or local models.
- 🔁 **Feedback Loop** — Iteratively refine the draft based on manager feedback (text or direct edits).
- 🏢 **Final JD Generation** — Enrich drafts with company-specific language using RAG over past job postings.
- ☁️ **Redis-based Session Persistence** — Store all context, drafts, and finalized JDs for later review.
- 🌐 **FastAPI Backend** — Robust API for frontends or automation tools like n8n.
- 📊 **Streamlit Frontend** — Intuitive web UI for manager-friendly interaction.

---

## 🖼️ Architecture

```
+-----------------+        +----------------+         +-----------------------+
| Hiring Manager  |<-----> | Streamlit UI   |<------->| FastAPI Backend (API) |
+-----------------+        +----------------+         +-----------------------+
                                                           |        ^
                                                           v        |
                                                     +----------+  |
                                                     |  Redis    |<-
                                                     +----------+
```

---

## 🛠️ Tech Stack

- Python 3.11
- OpenAI GPT‑4o / Ollama (local LLM)
- FAISS (for RAG similarity search)
- Redis (session store)
- FastAPI (backend API)
- Streamlit (frontend UI)
- Docker + Docker Compose (deployment)

---

## 🚀 Getting Started

### 🔗 Clone the repo

```bash
git clone https://github.com/yourusername/jd-suggestor-agent.git
cd jd-suggestor-agent
```

---

### 📦 1. Local Setup (with virtualenv)

```bash
python -m venv .jd_venv
.\.jd_venv\Scriptsctivate  # On Windows
pip install -r requirements.txt
```

Create your `.env` file:

```env
OPENAI_API_KEY=sk-...
OLLAMA_DISABLED=1            # Set to 0 if using local model
REDIS_HOST=127.0.0.1
REDIS_PORT=6379
API_URL=http://localhost:8000
```

Start Redis (optional):

```bash
docker run -d --name redis -p 6379:6379 redis:7-alpine
```

Run backend:

```bash
python -m uvicorn app.main:app --reload
```

Run frontend:

```bash
streamlit run ui/ui_streamlit_fastapi.py
```

---

### 🐳 2. Docker Setup (full stack)

Update your `.env`:

```env
OPENAI_API_KEY=sk-...
OLLAMA_DISABLED=1
API_URL=http://backend:8000
REDIS_HOST=redis
REDIS_PORT=6379
```

Then run:

```bash
docker compose up --build
```

- Streamlit UI: http://localhost:8501  
- FastAPI Docs: http://localhost:8000/docs  

---

## ✨ Sample Flow

1. Hiring manager enters job title, skills, and context.
2. Agent generates a draft JD using local LLM (Ollama) or GPT‑4o.
3. Manager gives feedback — either via edits or freeform text.
4. Final JD is created with retrieval-augmented generation using past company postings.
5. JD is saved and ready for publishing (e.g., to ATS or job boards).

---

## 📁 Folder Structure

```
.
├── app/
│   ├── api/              # FastAPI route handlers
│   ├── core/             # Draft/final JD generation logic
│   ├── state.py          # Redis session storage
│   └── main.py           # FastAPI app entrypoint
├── ui/
│   └── ui_streamlit.py   # Streamlit frontend
├── data/                 # Corpus + saves
├── .env                  # Environment config
├── Dockerfile            # Backend Docker build
├── docker-compose.yml    # Full stack deployment
├── requirements.txt
└── README.md
```

---

## 🧠 Advanced Topics

- ✅ Session persistence with Redis
- ✅ RAG using FAISS + past job postings
- ✅ Local fallback with TinyLLaMA (Ollama)
- ✅ Frontend-backend API sync via `.env`

---

## 🔒 Security Notes

- Always keep your `.env` file **local** or add it to `.gitignore`
- Use HTTPS and secrets management when deploying to production

---

## 📬 Future Enhancements

- ATS integration to auto-post JDs
- Admin dashboard for reviewing past JDs
- Role-based access (e.g., HR, hiring manager)
- Model finetuning on internal job data

---

## 🙌 Contributors

Built by [@hrithiksarda](https://github.com/hrithiksarda)  
Open to contributions via PR or issues!

---

## 📄 License

MIT License