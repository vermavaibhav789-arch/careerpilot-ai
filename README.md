# CareerPilot AI

AI-powered resume/job-description match scoring and interview practice,
with real accounts, a Free/Pro plan system, an application tracker, a
resume library, and a dashboard — not just a single-session demo.

Upload a resume, paste a job description, and get a match score, missing
skills, strong areas, and concrete resume edits — then practice interview
questions generated from your actual resume and the job, graded on
technical accuracy, completeness, and communication, with adaptive
follow-ups like a real interviewer.

## How it works

```
Frontend (Next.js)
      │
      ▼
Backend API (FastAPI) ── JWT auth + rate limiting + plan quotas on every route
      │
      ├── Auth              — register/login, bcrypt + JWT, verification, password reset
      ├── Document parser   — extracts text from PDF/DOCX/TXT resumes
      ├── LLM engine        — Claude API, native structured outputs
      ├── Vector database   — Chroma + Voyage AI embeddings (RAG)
      ├── Email             — verification/reset emails (or console in dev mode)
      └── SQL database      — users, sessions, applications, resumes (SQLite or Postgres)
                  │
                  ▼
          LLM API (Claude)
```

### Core features

- **Resume/JD matching**: Claude compares the resume and job description
  and returns a structured `MatchAnalysis` (match score, missing skills,
  strong areas, recommended changes) via [Claude's native structured
  outputs](https://docs.claude.com/en/docs/build-with-claude/structured-outputs).
- **Job intelligence**: the JD analyzed on its own terms — required vs.
  preferred skills, experience level, work mode, location, and "hidden
  signals" (what it emphasizes beyond its literal skill list).
- **Chat**: follow-up questions ("Why am I not a good match?") grounded in
  the resume + JD + match analysis.
- **RAG-grounded interview questions**: generated from your resume and the
  JD, grounded by a curated knowledge base (RAG, LangChain, FastAPI, vector
  DBs, Python, SQL, LLM APIs, system design, deployment) in Chroma, across
  four modes — technical, behavioral, HR, job-specific.
- **Adaptive follow-ups**: Claude decides whether a real interviewer would
  probe deeper on a given answer; capped at one level so it can't spiral.
- **Two-way voice**: questions read aloud (OpenAI TTS) and spoken answers
  transcribed (OpenAI STT) — Claude's API has neither audio input nor
  output, so both go through a separate call.
- **Resume optimizer**: concrete before/after bullet rewrites. Hard rule
  enforced in the prompt: never invent experience, metrics, or tools the
  resume doesn't support.
- **Cover letter generator**: six tones, grounded in the actual resume/JD.
- **ATS compatibility checklist**: heuristic checks against documented
  parsing pitfalls — deliberately not a fabricated precision score, since
  no single real ATS score exists across vendors.
- **Readiness score**: resume match + interview performance combined into
  one number, computed from stored data (no extra LLM call).
- **Weakness analysis**: after an interview round, recurring strengths/gaps
  across all answered questions, with specific study recommendations.
- **Standalone content generators**: headline, summary, objective, skills
  list, single bullets, role descriptions, and STAR stories — for when you
  need new content, not a rewrite of something existing. Same
  no-fabrication rule as the resume optimizer.
- **Other career documents**: resignation letters, professional bios, and
  six kinds of job-search emails (thank-you, follow-up, networking, salary
  negotiation, offer acceptance/decline) — grounded in your resume/JD where
  relevant, generic where it doesn't need to be.
- **Public resume sharing**: opt-in, unguessable-link sharing of a saved
  resume — no account required to view it, similar to sharing a Google Doc
  link. Off by default; you choose per-resume.
- **Career intelligence, grounded in real web search**: salary data and a
  career-path map both use Claude's server-side web search tool to pull
  current numbers rather than guessing from training data, which goes
  stale fast and was never reliable for compensation figures anyway.
- **Application tracker views**: list and Kanban (grouped by status),
  plus optional interview dates per application.
- **Career DNA**: a persistent professional profile (skills, achievements,
  certifications, target roles/industries, preferences, goals) that
  carries across every resume and session instead of resetting each time.
  Sync any analyzed resume into it with one click — additive and deduped,
  never overwrites what's already there. Free on every plan, since it's
  your own identity data, not a premium AI feature.
- **Career Twin**: a computed snapshot (not a running simulation) combining
  your Career DNA with your latest analysis into a current-vs-target view —
  skill gaps toward your stated target role, readiness, one honest verdict.
- **Career Simulator**: "what if" scenario analysis — a career change,
  relocation, learning a new skill, accepting a job — grounded in real web
  search and your Career DNA where available, explicitly framed as an
  informed estimate rather than a guarantee.
- **Truth Guard**: an independent second AI pass that fact-checks any
  generated text against your actual resume — a different call from
  whichever one wrote it, specifically instructed to be skeptical. Defense
  in depth on top of the no-fabrication prompt instructions already in the
  resume optimizer, section generator, and document generator. Free on
  every plan — safety checks shouldn't be paywalled.

### Accounts, plans, and product infrastructure

- **Real accounts**: bcrypt-hashed passwords, JWT sessions, data persists
  in a SQL database across restarts and devices.
- **Email verification & password reset**: real token-based flows. If no
  SMTP is configured, emails print to the backend console instead of
  failing — the whole flow works immediately with zero setup, and you can
  switch to real delivery by filling in `.env` (see Setup below).
- **JWT revocation**: resetting your password or hitting "log out
  everywhere" invalidates every previously-issued token instantly, not
  just client-side.
- **Rate limiting**: login/register/forgot-password are capped per IP to
  blunt brute-force and spam (single-process in-memory limiter — see
  "Design notes" for the production caveat).
- **Free/Pro plans**: Free gets limited analyses, interview questions, and
  voice actions, plus cover letters, ATS checks, and readiness scores. Pro
  adds unlimited usage, the resume optimizer, weakness analysis,
  application tracker, and resume library. **No payment processing is
  wired up** — the "Upgrade to Pro" button on `/pricing` sets the plan
  directly, for testing. See "What's simplified" below before treating
  this as a real paid product.
- **Application tracker**: save jobs with a status
  (saved/applied/OA/interview/final round/offer/rejected), scoped per
  account, gated to Pro.
- **Resume library**: save a parsed resume once, reuse it against new job
  descriptions without re-uploading the file. Gated to Pro.
- **Dashboard**: aggregate stats (average match score, average interview
  score, application funnel, recent sessions) across every session on the
  account — available on both plans.

## Tech stack

| Layer | Choice |
|---|---|
| Backend | FastAPI |
| Auth | JWT (PyJWT) + bcrypt password hashing |
| Database | SQLite by default; **verified working against real Postgres 16** — see "Postgres" below |
| Email | Python's built-in `smtplib`, dev-mode console fallback when unconfigured |
| Rate limiting | In-memory sliding window (single-process; see "Design notes") |
| LLM | Claude API (`claude-sonnet-5`), native structured outputs |
| Embeddings | Voyage AI (`voyage-3.5`) — Anthropic's recommended embeddings partner |
| Speech-to-text | OpenAI (`gpt-4o-mini-transcribe`) — Claude's API has no audio input |
| Text-to-speech | OpenAI (`gpt-4o-mini-tts`) — Claude's API has no audio output |
| Vector DB | Chroma (persistent local) — RAG knowledge base only, separate from the SQL database |
| Document parsing | pypdf, python-docx |
| Frontend | Next.js (App Router) + TypeScript, plain CSS |

## Project structure

```
careerpilot-ai/
├── backend/
│   ├── app/
│   │   ├── main.py               FastAPI app + CORS + routers + table creation
│   │   ├── config.py              Settings from .env
│   │   ├── db.py                  SQLAlchemy engine/session
│   │   ├── auth.py                Password hashing, JWT (with revocation), get_current_user
│   │   ├── plans.py                Plan limits + enforce_quota/increment_usage/require_feature
│   │   ├── rate_limit.py           In-memory rate limiter dependency
│   │   ├── models/
│   │   │   ├── schemas.py         Pydantic models (the API contract)
│   │   │   └── db_models.py       User, AnalysisSession, JobApplication, ResumeVersion
│   │   ├── routers/               auth, analyze, chat, interview, resume, resume_library,
│   │   │                          applications, account, dashboard
│   │   ├── services/
│   │   │   ├── document_parser.py    PDF/DOCX/TXT → text
│   │   │   ├── llm_client.py         Claude API calls (structured outputs)
│   │   │   ├── vector_store.py       Chroma + Voyage embeddings (RAG only)
│   │   │   ├── interview_engine.py   RAG retrieval + generation/eval
│   │   │   ├── analysis_store.py     DB-backed session storage, per-user
│   │   │   └── email_client.py       SMTP send, with dev-mode console fallback
│   │   └── data/interview_bank.json   Seed knowledge base
│   ├── seed_vector_db.py          Run once to populate Chroma
│   ├── careerpilot.db             SQLite database (created on first run)
│   └── requirements.txt
└── frontend/
    ├── app/                      analyze (/), interview/, resumes/, applications/,
    │                             dashboard/, pricing/, login/, register/,
    │                             forgot-password/, reset-password/, verify-email/
    ├── contexts/AuthContext.tsx   Current user, login/register/logout
    ├── components/                UploadForm, MatchResults, JobIntelligencePanel, ChatPanel,
    │                             InterviewSession, ScoreGauge, AudioRecorder, QuestionAudio,
    │                             RequireAuth, ResumeToolsPanel, ReadinessPanel, WeaknessReport
    └── lib/                      api.ts (typed backend client), auth.ts, types.ts
```

## Setup

### 1. Get API keys

- **Anthropic** (required): [console.anthropic.com](https://console.anthropic.com)
- **Voyage AI** (required for the interview module's RAG retrieval — free
  tier is plenty): [voyageai.com](https://www.voyageai.com)
- **OpenAI** (optional — only needed for audio-recorded answers and spoken
  questions): [platform.openai.com](https://platform.openai.com)

You'll also generate a `JWT_SECRET` yourself (not an external key) — see
step 2.

### 2. Backend

```bash
cd backend
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env
# edit .env: add ANTHROPIC_API_KEY, VOYAGE_API_KEY, and a real JWT_SECRET:
python3 -c "import secrets; print(secrets.token_hex(32))"

python seed_vector_db.py        # populates the interview question knowledge base
uvicorn app.main:app --reload   # http://localhost:8000
```

The database and its tables are created automatically on first run.

**If you have an existing `careerpilot.db` from before this update**,
delete it before starting the server — new tables/columns were added
(Career DNA, sharing fields on resumes, interview dates on applications),
and `Base.metadata.create_all()` only creates missing *tables*, not
missing *columns* on tables that already exist. A fresh SQLite file avoids
this entirely; it's a single file with no real data to lose in a dev setup.

Visit `http://localhost:8000/docs` for interactive API docs with a working
"Authorize" button for testing protected endpoints directly.

**Enabling real email delivery (optional):** by default, verification and
password-reset emails print to this terminal instead of sending — the app
is fully usable without doing anything here. To send real emails via
Gmail:
1. Turn on 2-Step Verification on the Google account:
   [myaccount.google.com/security](https://myaccount.google.com/security)
2. Generate an App Password (NOT your normal password) at
   [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords)
3. In `.env`, set `SMTP_USERNAME` to the Gmail address and
   `SMTP_PASSWORD` to the 16-character App Password.

Never put a real account password in `.env`, and never paste one into a
chat or commit it anywhere — App Passwords exist specifically so you don't
have to.

**Using Postgres instead of SQLite:** this has been verified to work
against real Postgres 16, not just claimed — the same feature test suite
(auth, quotas, plan gating, application tracker, resume library, RAG
interview flow, dashboard aggregation) was run against both databases with
identical results. To switch, install `postgresql` locally or use a
hosted instance, then set in `.env`:
```
DATABASE_URL=postgresql://user:password@localhost:5432/careerpilot
```
`psycopg2-binary` (already in `requirements.txt`) handles the driver.

### 3. Frontend

```bash
cd frontend
npm install
cp .env.local.example .env.local   # defaults to http://localhost:8000, adjust if needed
npm run dev                        # http://localhost:3000
```

Sign up for an account, upload a resume, paste a job description, and run
an analysis. Everything — sessions, saved resumes, tracked applications —
is scoped to your account and persists across restarts.

## Plans (no payment processing)

| | Free | Pro |
|---|---|---|
| Resume analyses | 3 | Unlimited |
| Interview questions | 15 | Unlimited |
| Voice actions (record/play) | 10 | Unlimited |
| Cover letter, ATS check, readiness score, career documents | ✓ | ✓ |
| Resume optimizer + content generators | — | ✓ |
| Weakness analysis | — | ✓ |
| Application tracker | — | ✓ |
| Resume library + public sharing | — | ✓ |
| Career intelligence (salary + career map) | — | ✓ |

All of this is enforced server-side in `app/plans.py`, not just displayed —
try the 4th analysis on a Free account and you'll get a real 402, not just
a UI hint. The `/pricing` page's "Upgrade to Pro" button calls
`/api/account/upgrade`, which sets the plan directly with no checkout.
Wiring in a real processor (Stripe/Razorpay) means adding a checkout
session + webhook handler in front of that same endpoint, not replacing it
— and deserves its own careful pass with test-mode keys before going near
real money, not being bundled in with everything else.

## Mobile (Android/iOS)

Not included in this repo, and not something to build in a sandboxed
environment with no device simulator to test against. Here's the actual
path:

1. **Framework: React Native with Expo.** It reuses your React knowledge
   from this frontend, and Expo's managed workflow avoids touching native
   Xcode/Android Studio project files directly for most features.
2. **Reuse the backend as-is.** Every `/api/...` endpoint here already
   returns JSON over HTTP — the mobile app is just a different client
   hitting the same FastAPI backend. `lib/api.ts`'s functions are a
   near-direct template for the mobile app's API calls (swap `fetch` +
   `localStorage` for `fetch` + `expo-secure-store` for the JWT).
3. **Local setup:** `npx create-expo-app`, then `npx expo start` gives you
   a QR code — scan it with the Expo Go app on your phone for live reload
   against a real device, no emulator required to get started.
4. **Voice recording** maps to `expo-av`; the rest (screens, forms, state)
   is standard React Native.
5. **Publishing:** a $99/year Apple Developer Program membership for iOS
   App Store, a $25 one-time Google Play Console registration fee for
   Android. Expo's EAS Build handles producing the actual app binaries for
   both stores without needing a Mac for the iOS build.
6. **Do this with Claude Code**, not this chat interface — it has real
   iOS simulators and Android emulators to test against as you go, which
   is the actual missing piece here, not the code itself.

## Design notes / what's simplified

- **No real payment processing** — see "Plans" above. This is the biggest
  one: treat the Pro plan as a demo of what gating *would* look like, not
  a billable product yet.
- **Usage quotas are lifetime, not monthly** — simpler to reason about and
  test. Adding a monthly reset means adding a `period_start` column and
  checking it before reading the counter; the enforcement functions in
  `plans.py` wouldn't change shape.
- **Voice usage counts actions, not seconds** — measuring true audio
  duration would need decoding the file (e.g. via `pydub`/ffmpeg); this
  stage of the product uses "one transcription or one question-audio call
  = one action" as an honest, simple proxy instead.
- **Rate limiting is single-process, in-memory** — fine for the one
  `uvicorn` process this ships with, but won't coordinate across multiple
  workers or machines. Swap for Redis-backed rate limiting
  (e.g. `slowapi` with a Redis backend) before running more than one
  worker process.
- **Email verification is tracked but not enforced** — `email_verified`
  is a real field that gets set correctly, but no endpoint currently
  checks it before allowing access. Hard-gating specific routes behind
  `current_user.email_verified` is a one-line addition wherever you want it.
- **Nested interview data isn't fully normalized** — chat history and
  generated questions live as JSON columns on `AnalysisSession` rather
  than child tables. Fine for "load everything for this session," but
  would need real tables to query into that data directly (e.g. "every
  RAG question ever asked across all accounts").
- **JD is pasted as text, not uploaded as a file** — matches how most
  people actually have a job description, and avoids parsing a second
  document format.
- **Audio recording needs a secure context** — `getUserMedia` only works
  on `localhost` or `https://`.

## Roadmap

Everything in "Core features" and "Accounts, plans, and product
infrastructure" above is built and tested. On the five systems most
recently requested as flagship differentiators, here's the honest state:

- **Career DNA** — done, in full (see above).
- **Truth Guard** — done, as an honest, real version: an independent
  verification pass, not a literal "evidence graph" database (which would
  be over-engineering for what's actually needed here).
- **Career Twin** — done, as an honest version: a computed snapshot from
  existing data, not a continuously-updating simulation (which isn't a
  meaningfully different thing from "recompute it each time you ask,"
  just a more expensive way to say it).
- **Career Simulator** ("what if I change careers/relocate/learn X") — done.
- **CareerPilot Agent** (autonomous multi-agent orchestration with
  permissions and approval workflows) — not built, deliberately. This is
  a real, separate architecture decision — not a feature to bolt on — and
  deserves its own focused discussion about what autonomy and permissions
  should actually mean here before writing code.

What's still genuinely open beyond those five:

1. **Real payment processing** — Stripe or Razorpay, deliberately not
   bundled with everything else (see "Plans" above for why).
2. **LinkedIn import, job board aggregation** — both blocked on needing a
   formal partner/data agreement with LinkedIn or a job board vendor,
   not on engineering time. A *LinkedIn text optimizer* (paste your
   existing headline/About/bullets, get feedback) doesn't have this
   problem since it needs no import — a reasonable near-term add.
3. **"Why am I not getting interviews" / application feedback loop** —
   needs real outcome data over enough volume to find a genuine pattern;
   the tracker + resume library already capture the raw data needed
   (which resume, which outcome), but meaningful learning from a single
   user's few dozen applications is statistically thin — worth building
   as an honest "here's what your own data shows so far" summary, not
   framed as real ML learning.
4. **Monthly (not lifetime) usage resets** — see "Design notes."
5. **Email verification enforcement, production-grade rate limiting,
   mobile app** — see earlier notes above.
6. **A structured resume editor, browser extension, public API/SDKs,
   enterprise SSO** — each a legitimate, separate multi-week project,
   not a feature to bolt on; worth doing deliberately if there's real
   demand.

## Extending it further

- Expand `interview_bank.json` — it's technical-only today, so behavioral/HR
  modes don't get RAG grounding yet (see `interview_engine.py`).
- Add a reranking step after Chroma retrieval for higher-precision grounding.
- Deploy: backend to Railway/Render/Fly.io (mount a persistent volume for
  `careerpilot.db` and `chroma_data/`, or point `DATABASE_URL` at managed
  Postgres), frontend to Vercel.
