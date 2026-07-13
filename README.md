# ⚡ CodePilot AI

> **Autonomous Software Engineering Agent Platform**  
> A multi-agent AI system that acts as a junior software engineer — analyzing repos, fixing bugs, generating code, writing tests, reviewing PRs, and creating documentation.

[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-green)](https://fastapi.tiangolo.com)
[![LangGraph](https://img.shields.io/badge/LangGraph-0.2-purple)](https://langchain-ai.github.io/langgraph/)
[![React](https://img.shields.io/badge/React-18-blue)](https://react.dev)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## 🏗️ Architecture

```
Developer Request
       ↓
   React UI (Vite)
       ↓
  FastAPI Gateway
       ↓
  LangGraph StateGraph
  ┌─────────────────────────────────────────────────┐
  │  Analyzer → Knowledge → Planner                 │
  │       ↓         ↓          ↓                    │
  │  CodeGen → Refactor → Testing → Reviewer → Docs │
  │                    ↓                            │
  │             Human Approval                      │
  │                    ↓                            │
  │             GitHub Agent → PR                   │
  └─────────────────────────────────────────────────┘
       ↓
  Celery (async) → Redis
       ↓
  PostgreSQL + Qdrant
```

## 🤖 The 9 Agents

| Agent | Icon | Responsibility |
|-------|------|----------------|
| **Repository Analyzer** | 🔍 | Architecture detection, dependency mapping, complexity scoring |
| **Knowledge Agent** | 🧠 | Code embeddings in Qdrant, semantic search |
| **Planner Agent** | 📋 | Task decomposition, multi-agent orchestration |
| **Code Generation** | ⚡ | Functions, APIs, SQL, components |
| **Refactoring** | 🔧 | SOLID violations, dead code, code smells |
| **Testing** | 🧪 | Unit tests, integration tests, mocks, edge cases |
| **Code Reviewer** | 👁️ | Security, performance, maintainability scoring |
| **Documentation** | 📚 | README, API docs, UML/sequence diagrams |
| **GitHub** | 🐙 | Branch, commit, pull request |

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose
- OpenAI API key (or Gemini/Ollama)
- GitHub Personal Access Token (optional, for real PRs)

### 1. Clone & Configure
```bash
git clone https://github.com/yourname/codepilot-ai
cd "CodePilot AI"
cp .env.example .env
# Edit .env with your API keys
```

### 2. Start All Services
```bash
docker-compose up -d
```

This starts:
- 🐘 **PostgreSQL** — `localhost:5432`
- 🔴 **Redis** — `localhost:6379`
- 🟡 **Qdrant** — `localhost:6333`
- 🚀 **FastAPI** — `http://localhost:8000`
- ⚙️ **Celery Worker** — Background task processing
- 🌸 **Flower** — `http://localhost:5555` (Celery monitor)
- ⚛️ **React UI** — `http://localhost:5173`

### 3. Access
| Service | URL |
|---------|-----|
| **Frontend** | http://localhost:5173 |
| **API Docs** | http://localhost:8000/docs |
| **Celery Monitor** | http://localhost:5555 |
| **Qdrant Dashboard** | http://localhost:6333/dashboard |

### 4. First Login
Register an account at http://localhost:5173/login, then:
1. **Add a repository** → Connect your GitHub repo URL
2. **Create a workflow** → Describe your task in natural language
3. **Watch the agents work** → Live streaming log
4. **Approve** → Review the plan and approve the PR

---

## 🛠️ Local Development (Without Docker)

### Backend
```bash
cd backend
python -m venv venv
venv\Scripts\activate       # Windows
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Celery Worker
```bash
cd backend
celery -A app.workers.celery_app worker --loglevel=info
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

---

## ⚙️ Configuration

Key `.env` variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `LLM_PROVIDER` | `openai` / `gemini` / `ollama` | `openai` |
| `OPENAI_API_KEY` | OpenAI API key | — |
| `GITHUB_TOKEN` | GitHub PAT for PR creation | — |
| `QDRANT_URL` | Qdrant vector DB URL | `http://localhost:6333` |
| `SECRET_KEY` | JWT signing key | — |

---

## 🏛️ Tech Stack

| Layer | Technology |
|-------|-----------|
| **Frontend** | React 18, Vite, Zustand, Recharts |
| **Backend** | FastAPI, Python 3.11, SQLAlchemy 2.0 |
| **AI Orchestration** | LangGraph, LangChain |
| **LLMs** | OpenAI GPT-4o / Google Gemini / Ollama |
| **Vector DB** | Qdrant |
| **Database** | PostgreSQL 16 |
| **Cache/Queue** | Redis 7 |
| **Background Jobs** | Celery 5 |
| **Deployment** | Docker Compose |

---

## 📁 Project Structure

```
CodePilot AI/
├── frontend/                  # React + Vite frontend
│   └── src/
│       ├── components/        # Sidebar, AgentCard, StreamingLog, etc.
│       ├── pages/             # Dashboard, Repositories, Workflows, etc.
│       ├── services/api.js    # Axios API client
│       └── stores/appStore.js # Zustand state
│
├── backend/
│   └── app/
│       ├── agents/            # 9 LangGraph agents + graph.py
│       ├── models/            # SQLAlchemy ORM models
│       ├── routers/           # FastAPI route handlers
│       ├── services/          # LLM, Qdrant, GitHub services
│       ├── workers/           # Celery tasks
│       └── core/              # Auth, RBAC, Audit
│
├── docker-compose.yml
├── .env.example
└── README.md
```

---

## 🔒 Features

- ✅ **JWT Authentication** + RBAC (Admin / Developer / Viewer)
- ✅ **Human-in-the-Loop** — Approve/reject before PR creation
- ✅ **Streaming Responses** — Server-Sent Events for live agent logs
- ✅ **Persistent Workflows** — LangGraph checkpointing
- ✅ **Audit Logs** — Full trail of all actions
- ✅ **Semantic Search** — Ask questions about your codebase
- ✅ **Multi-provider LLM** — OpenAI, Gemini, Ollama
- ✅ **GitHub Integration** — Real PR creation via API

---

## 📄 License

MIT © 2025 CodePilot AI
