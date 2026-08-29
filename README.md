# CareerPilot AI

**AI-Powered Career & Job Application Intelligence Platform**

CareerPilot AI is a full-stack AI application that helps job seekers analyze job descriptions against their resumes, identify skill gaps, improve application materials, and prepare for interviews.

It combines **LLMs, RAG, vector search, structured outputs, voice AI, authentication, plan-based feature gating, and persistent user data** into one career intelligence platform.

> **Project Status:** MVP / In Progress

---

## 🚀 What CareerPilot AI Does

A user can upload a resume, paste a job description, and use AI to understand how well they match the role and what they should improve.

The platform can then help the user prepare for the interview using the same resume and job description.

### Core workflow

```text
Resume + Job Description
          │
          ▼
   AI Analysis Engine
          │
    ┌─────┴─────┐
    ▼           ▼
Match Analysis  Job Intelligence
    │
    ▼
Resume Improvements
    │
    ▼
Interview Preparation
    │
    ▼
Answer Evaluation
    │
    ▼
Weakness Analysis
```

---

# ✨ Key Features

### Resume & Job Intelligence

* Resume/JD match scoring
* Missing skills identification
* Strong areas analysis
* Recommended resume changes
* Required vs preferred skills
* Experience level analysis
* Work mode and location analysis
* Hidden signals from job descriptions
* Follow-up chat grounded in resume + JD

### 🤖 AI Resume Tools

* Resume optimizer with before/after bullet rewrites
* Headline generator
* Professional summary generator
* Career objective generator
* Skills list generator
* Role description generator
* STAR story generator
* Cover letter generator
* Resignation letters
* Professional bios
* Job-search emails

A no-fabrication rule is used for generated resume content so the system does not intentionally invent experience, metrics, or technologies that are not supported by the user's resume.

### 🎤 AI Interview Preparation

* Technical interview mode
* Behavioral interview mode
* HR interview mode
* Job-specific interview mode
* Questions generated from the user's resume and target job
* RAG-grounded interview questions
* Adaptive follow-up questions
* Interview answer evaluation
* Communication and completeness evaluation
* Weakness analysis
* Personalized study recommendations

### 🔊 Voice Interview

* Text-to-speech for interview questions
* Speech-to-text for spoken answers
* OpenAI audio APIs
* Interactive voice interview workflow

### 🧠 RAG & Knowledge Grounding

* Chroma vector database
* Voyage AI embeddings
* Curated interview knowledge base
* Retrieval-grounded interview generation
* LangChain/FastAPI/vector database/Python/SQL/LLM/system-design/deployment knowledge

### 📊 Career Intelligence

* Career DNA — persistent professional profile
* Career Twin — current-vs-target career snapshot
* Career Simulator — "what if" career scenarios
* Career readiness score
* Career intelligence using real web search
* Salary information
* Career-path analysis
* Truth Guard — independent verification of generated content

### 📁 Application Management

* Job application tracker
* Kanban and list views
* Application status tracking
* Optional interview dates
* Resume library
* Public resume sharing
* Dashboard analytics

### 🔐 Authentication & Accounts

* User registration
* Login/logout
* JWT authentication
* bcrypt password hashing
* Email verification
* Password reset
* JWT revocation
* Per-user data isolation
* Free/Pro plan system
* Server-side usage quotas
* Feature gating
* Rate limiting

---

# 🧠 AI Architecture

```text
                         CareerPilot AI
                              │
                 ┌────────────┴────────────┐
                 │                         │
          Next.js Frontend          FastAPI Backend
                 │                         │
                 │             ┌───────────┼───────────┐
                 │             │           │           │
                 │            LLM         RAG        SQL DB
                 │             │           │           │
                 │          Claude      Chroma    SQLite/Postgres
                 │                         │
                 │                    Voyage AI
                 │
                 └──────────── API ────────────────┐
                                                    │
                                              OpenAI Audio
                                               STT + TTS
```

### AI request flow

```text
User Input
    │
    ▼
FastAPI API
    │
    ├── Document Parsing
    │
    ├── Resume + JD Processing
    │
    ├── RAG Retrieval ──► Chroma ──► Voyage AI
    │
    └── Claude API
            │
            ▼
     Structured AI Output
            │
            ▼
       Database Storage
            │
            ▼
       Next.js Frontend
```

---

# 🛠️ Tech Stack

| Area                | Technology                       |
| ------------------- | -------------------------------- |
| Frontend            | Next.js, React, TypeScript, CSS  |
| Backend             | Python, FastAPI                  |
| LLM                 | Anthropic Claude API             |
| Structured Outputs  | Claude native structured outputs |
| RAG                 | Chroma + Voyage AI               |
| Embeddings          | Voyage AI                        |
| Speech-to-Text      | OpenAI                           |
| Text-to-Speech      | OpenAI                           |
| Database            | SQLite / PostgreSQL              |
| ORM                 | SQLAlchemy                       |
| Authentication      | JWT + bcrypt                     |
| Document Processing | pypdf, python-docx               |
| API Documentation   | FastAPI / OpenAPI                |
| Version Control     | Git / GitHub                     |

---

# 📁 Project Structure

```text
careerpilot-ai/
│
├── backend/
│   ├── app/
│   │   ├── models/
│   │   │   ├── schemas.py
│   │   │   └── db_models.py
│   │   │
│   │   ├── routers/
│   │   │   ├── auth.py
│   │   │   ├── analyze.py
│   │   │   ├── chat.py
│   │   │   ├── interview.py
│   │   │   ├── resume.py
│   │   │   ├── resume_library.py
│   │   │   ├── applications.py
│   │   │   ├── account.py
│   │   │   ├── dashboard.py
│   │   │   ├── career.py
│   │   │   └── career_dna.py
│   │   │
│   │   ├── services/
│   │   │   ├── document_parser.py
│   │   │   ├── llm_client.py
│   │   │   ├── vector_store.py
│   │   │   ├── interview_engine.py
│   │   │   ├── analysis_store.py
│   │   │   ├── email_client.py
│   │   │   ├── stt_client.py
│   │   │   └── tts_client.py
│   │   │
│   │   ├── auth.py
│   │   ├── config.py
│   │   ├── db.py
│   │   ├── plans.py
│   │   ├── rate_limit.py
│   │   └── main.py
│   │
│   ├── data/
│   ├── seed_vector_db.py
│   └── requirements.txt
│
├── frontend/
│   ├── app/
│   │   ├── applications/
│   │   ├── career/
│   │   ├── career-dna/
│   │   ├── dashboard/
│   │   ├── interview/
│   │   ├── resumes/
│   │   ├── pricing/
│   │   ├── login/
│   │   ├── register/
│   │   └── ...
│   │
│   ├── components/
│   ├── contexts/
│   └── lib/
│
├── .gitignore
├── README.md
└── ...
```

---

# 👨‍💻 My Role

I designed and developed CareerPilot AI as a **full-stack AI application**.

My work includes:

* AI/LLM integration
* Prompt engineering
* Structured AI outputs
* RAG architecture
* Vector database integration
* Resume/document processing
* Interview generation and evaluation
* Voice AI integration
* FastAPI backend development
* Next.js frontend development
* Authentication and authorization
* Database integration
* Feature gating and usage quotas
* Application/business logic
* Testing and debugging
* Git/GitHub version control

---

# 🔐 Accounts, Plans & Infrastructure

CareerPilot AI includes a real account system rather than being only a single-session demo.

### Authentication

* bcrypt password hashing
* JWT sessions
* JWT revocation
* Email verification flow
* Password reset flow
* "Log out everywhere" functionality
* Per-account data isolation

### Free & Pro Plans

| Feature               | Free |       Pro |
| --------------------- | ---: | --------: |
| Resume analyses       |    3 | Unlimited |
| Interview questions   |   15 | Unlimited |
| Voice actions         |   10 | Unlimited |
| Cover letters         |    ✓ |         ✓ |
| ATS checks            |    ✓ |         ✓ |
| Readiness score       |    ✓ |         ✓ |
| Career documents      |    ✓ |         ✓ |
| Resume optimizer      |    — |         ✓ |
| Content generators    |    — |         ✓ |
| Weakness analysis     |    — |         ✓ |
| Application tracker   |    — |         ✓ |
| Resume library        |    — |         ✓ |
| Public resume sharing |    — |         ✓ |
| Career intelligence   |    — |         ✓ |

Usage quotas and feature restrictions are enforced **server-side**, not only through the frontend.

---

# ⚙️ Running Locally

## 1. Backend

```bash
cd backend

python -m venv venv

# Windows
venv\Scripts\activate

pip install -r requirements.txt
```

Create your environment file:

```bash
# Windows / Git Bash
cp .env.example .env
```

Configure the required API keys and generate a secure JWT secret.

For example:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

Seed the vector database:

```bash
python seed_vector_db.py
```

Start the backend:

```bash
uvicorn app.main:app --reload
```

Backend:

```text
http://localhost:8000
```

API documentation:

```text
http://localhost:8000/docs
```

## 2. Frontend

Open another terminal:

```bash
cd frontend
npm install
```

Create the frontend environment file:

```bash
cp .env.local.example .env.local
```

Then:

```bash
npm run dev
```

Frontend:

```text
http://localhost:3000
```

---

# 🔑 Environment Variables

API keys and secrets are **not committed to this repository**.

Use:

```text
backend/.env.example
frontend/.env.local.example
```

as templates.

Typical backend configuration includes:

```text
ANTHROPIC_API_KEY=
VOYAGE_API_KEY=
OPENAI_API_KEY=
JWT_SECRET=
DATABASE_URL=
```

Never commit real API keys, passwords, tokens, or other secrets.

---

# 🗄️ Database

CareerPilot AI currently supports:

* SQLite for local development
* PostgreSQL for production-oriented database testing

The SQL database stores application data such as:

* Users
* Sessions
* Applications
* Resume versions
* Career profile data

Chroma is used separately for the RAG knowledge base.

---

# 🧪 Testing & Development

The project has been developed with a focus on verifying AI-generated output rather than assuming that generated code or content is automatically correct.

Important development principles include:

* Verify AI-generated code before using it
* Validate API behavior
* Test authentication flows
* Test feature gating
* Test database behavior
* Test resume parsing
* Test RAG retrieval
* Test interview generation/evaluation
* Test frontend/backend integration
* Check error handling
* Avoid exposing secrets
* Test changes before considering a feature complete

---

# 📌 Current Project Status

CareerPilot AI is currently an **MVP / work in progress**.

The core application functionality has been implemented and tested locally.

### Implemented

* Resume/JD analysis
* Job intelligence
* AI chat
* Resume optimization
* Interview preparation
* Adaptive interviews
* Voice interview functionality
* RAG
* Chroma vector database
* Voyage AI embeddings
* Career DNA
* Career Twin
* Career Simulator
* Truth Guard
* Cover letters
* ATS checks
* Career documents
* Application tracker
* Resume library
* Dashboard
* Authentication
* Email verification/reset flows
* Free/Pro feature gating

### Still planned for production

* Real Stripe/Razorpay payment processing
* Monthly usage resets
* Production PostgreSQL infrastructure
* Redis/distributed rate limiting
* Cloud file storage
* Production email infrastructure
* Production secrets management
* Monitoring and error tracking
* Automated backups
* Production deployment
* Custom domain
* Mobile applications

---

# 🔮 Future Improvements

Potential future development includes:

* Production payment system
* Mobile applications
* Browser extension
* Public API/SDK
* More advanced RAG retrieval and reranking
* Expanded interview knowledge base
* Structured resume editor
* Enterprise SSO
* LinkedIn integrations where officially supported
* Job-board integrations where officially supported
* CareerPilot autonomous agent architecture

---

# ⚠️ Important Notes

This repository represents an **MVP rather than a production-ready commercial service**.

The Pro plan currently demonstrates server-side feature gating, but **real payment processing is not connected yet**.

Some infrastructure components are intentionally simplified for the MVP, including:

* Lifetime rather than monthly usage quotas
* Single-process in-memory rate limiting
* Local Chroma persistence
* Local development email fallback
* SQLite as the default local database

These are known engineering decisions rather than hidden limitations.

---

# 📄 License

This project is currently intended as a personal portfolio/project demonstration.

No production license has been selected yet.
