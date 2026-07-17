# Multi-Agent AI Customer Support Assistant (RAG + LLMs)

A customer support assistant for a fictional Indian electronics retailer,
**TechMart Electronics**. Five specialist LLM agents sit behind an orchestrator
that reads each question, decides who should answer it, and grounds every answer
in the company's own documentation using RAG.

The distinguishing feature is that **routing is real**. A question about a refund
goes to Billing. A question about a device that won't pair goes to Technical.
*"I paid for Premium yesterday but it's still locked"* goes to **both**, and
their two answers are merged into one reply — because it is genuinely a payment
question and a provisioning fault at the same time, and answering only half of it
is a wrong answer.

---

## Contents

- [How it works](#how-it-works)
- [Quick start](#quick-start)
- [Configuration](#configuration)
- [Project structure](#project-structure)
- [API reference](#api-reference)
- [Testing](#testing)
- [Evaluation](#evaluation)
- [Deployment](#deployment)
- [Design decisions](#design-decisions)
- [Troubleshooting](#troubleshooting)

---

## How it works

```
                    ┌──────────────────────────────────────────┐
   user question    │              ORCHESTRATOR                │
   ───────────────► │                                          │
                    │  1. Router: LLM classifies intent and    │
                    │     picks 1–2 specialists                │
                    └────────────────┬─────────────────────────┘
                                     │
              ┌──────────────────────┼──────────────────────┐
              ▼                      ▼                      ▼
       ┌────────────┐         ┌────────────┐         ┌────────────┐
       │  BILLING   │         │ TECHNICAL  │   ...   │    FAQ     │
       └──────┬─────┘         └──────┬─────┘         └──────┬─────┘
              │  2. Each agent retrieves ONLY from its own domain
              ▼                      ▼                      ▼
       ┌──────────────────────────────────────────────────────────┐
       │      FAISS vector store (domain-tagged chunks)           │
       │      all-MiniLM-L6-v2 embeddings, cosine similarity      │
       └──────────────────────────────────────────────────────────┘
              │  3. Retrieved chunks + persona + guardrails → LLM
              ▼
       ┌──────────────────────────────────────────────────────────┐
       │  4. Aggregator merges multi-agent answers into one voice  │
       │  5. Escalate to human if grounding is weak                │
       └──────────────────────────────────────────────────────────┘
                                     │
                                     ▼
                        answer + agent badges + sources
                        (persisted to MongoDB)
```

**Five specialists**

| Agent | Handles | Retrieves from |
|---|---|---|
| Billing | Refunds, payments, invoices, subscriptions, GST, EMI | refund_policy, pricing, user_manual |
| Technical | Login, setup, pairing, Wi-Fi, faults, warranty diagnostics | user_manual, installation_guide, warranty |
| Product | Specs, prices, comparisons, stock, delivery | products, pricing, shipping_policy, warranty |
| Complaint | Anger, repeat failures, escalation, consumer rights | refund_policy, shipping_policy |
| FAQ | Company info, hours, contacts, privacy — and the fallback | faq, shipping_policy |

---

## Quick start

**Requirements:** Python 3.10+, Node 18+. MongoDB and an LLM API key are both
optional for a first run.

```bash
# 1. Backend
python -m venv .venv && source .venv/bin/activate    # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env

# 2. Build the knowledge base PDFs and embed them
python scripts/build_kb.py
python -m backend.rag.ingest

# 3. Run the API
uvicorn backend.main:app --reload
#    → http://localhost:8000/docs
#    → http://localhost:8000/health   (check what actually loaded)
```

```bash
# 4. Frontend, in a second terminal
cd frontend
npm install
cp .env.local.example .env.local
npm run dev
#    → http://localhost:3000
```

Register an account and ask something. **It works with no API key** — see below.

### Running with no API key

Out of the box `LLM_PROVIDER=mock`, so the whole system runs end to end with no
credentials and no network: routing, retrieval, memory, aggregation, auth, and
the API all execute real code paths. The mock LLM does keyword routing and echoes
the retrieved context back, which is enough to prove the plumbing works and to
run the tests in CI.

It is **not** enough for your demo video. Get a free Groq key
([console.groq.com](https://console.groq.com)) and set:

```bash
LLM_PROVIDER=groq
GROQ_API_KEY=gsk_your_key_here
```

Then check `/health` shows `"provider": "groq"` before you record.

---

## Configuration

Everything lives in `.env` (see `.env.example` for the annotated list).

| Variable | Default | Notes |
|---|---|---|
| `LLM_PROVIDER` | `mock` | `groq` \| `openai` \| `gemini` \| `ollama` \| `mock` |
| `GROQ_API_KEY` | — | Free tier, recommended |
| `EMBEDDING_MODEL` | `all-MiniLM-L6-v2` | 384-dim, ~90 MB, downloads on first run |
| `CHUNK_SIZE` / `CHUNK_OVERLAP` | `900` / `150` | Characters |
| `RETRIEVAL_TOP_K` | `4` | Chunks per agent |
| `RETRIEVAL_MIN_SCORE` | `0.25` | Below this → escalate instead of guessing |
| `MONGO_URI` | `mongodb://localhost:27017` | Falls back to in-memory if unreachable |
| `JWT_SECRET` | dev value | **Change for deployment** |
| `MEMORY_TURNS` | `6` | Prior turns sent to the LLM |

---

## Project structure

```
customer-support-ai/
├── backend/
│   ├── main.py                 FastAPI app, CORS, /health
│   ├── config.py               all tunables, read from .env
│   ├── agents/
│   │   ├── base.py             retrieve → generate → confidence → escalate
│   │   ├── specialists.py      the five agents (persona + domain)
│   │   ├── router.py           LLM intent detection + keyword fallback
│   │   └── orchestrator.py     routing, parallel execution, aggregation
│   ├── rag/
│   │   ├── chunker.py          PDF → domain-tagged chunks
│   │   ├── ingest.py           chunks → embeddings → FAISS   (CLI)
│   │   └── retriever.py        domain-filtered semantic search
│   ├── embeddings/embedder.py  MiniLM + offline fallback
│   ├── vectorstore/faiss_store.py  FAISS IndexFlatIP + metadata
│   ├── llm/client.py           groq/openai/gemini/ollama/mock
│   ├── database/db.py          MongoDB + in-memory fallback
│   ├── api/                    auth.py, chat.py, analytics.py
│   ├── models/schemas.py       Pydantic contracts
│   ├── eval/                   labelled set + metrics harness
│   └── tests/                  33 tests, no keys needed
├── frontend/                   Next.js + Tailwind
│   ├── pages/                  index.js (chat), login.js
│   ├── components/             Message, Sidebar, RoutingTrace
│   └── services/api.js         API client
├── knowledge_base/             8 generated PDFs
├── scripts/
│   ├── kb_content.py           source content
│   └── build_kb.py             → knowledge_base/*.pdf
├── docs/                       report notes, eval results
├── requirements.txt
└── .env.example
```

---

## API reference

Interactive docs at `/docs` once running.

| Method | Endpoint | Auth | Purpose |
|---|---|---|---|
| `POST` | `/auth/register` | — | Create account → JWT |
| `POST` | `/auth/login` | — | Sign in → JWT |
| `GET` | `/auth/me` | ✓ | Current user |
| `POST` | `/chat` | ✓ | **Ask a question** (routes, retrieves, answers) |
| `GET` | `/chat/sessions` | ✓ | List conversations |
| `GET` | `/chat/history/{id}` | ✓ | Full transcript |
| `DELETE` | `/chat/history/{id}` | ✓ | Delete a conversation |
| `GET` | `/analytics` | ✓ | Agent usage, escalation rate, latency |
| `GET` | `/health` | — | Which backends actually loaded |

**Example**

```bash
TOKEN=$(curl -s -X POST localhost:8000/auth/register \
  -H 'Content-Type: application/json' \
  -d '{"email":"me@example.com","password":"password123","name":"Me"}' \
  | python -c "import sys,json;print(json.load(sys.stdin)['access_token'])")

curl -s -X POST localhost:8000/chat \
  -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' \
  -d '{"message":"I paid for Premium yesterday but it is still locked"}'
```

```jsonc
{
  "session_id": "a3f...",
  "answer": "Your payment went through...",
  "agents": ["billing", "technical"],     // ← two specialists
  "routing": { "confidence": 0.92, "reasoning": "payment + entitlement fault" },
  "sources": [ { "source": "user_manual.pdf", "page": 1, "score": 0.71 } ],
  "escalated": false,
  "latency_ms": 2140
}
```

---

## Testing

```bash
pytest backend/tests -v      # 33 tests
```

No API key, no Mongo, no network needed — they run against the mock LLM and the
in-memory DB. They do need the vector index, so run `build_kb.py` and
`ingest` first.

Coverage includes auth (duplicate email, wrong password, bad token), session
isolation between users, chunking, domain-filtered retrieval, router output
sanitisation against malformed LLM responses, and the cross-domain two-agent
requirement.

---

## Evaluation

```bash
python -m backend.eval.run_eval --verbose
python -m backend.eval.run_eval --csv docs/eval_results.csv
```

Measures routing accuracy, retrieval hit@k, escalation rate, and latency over 32
labelled queries (`backend/eval/dataset.py`) written in customer phrasing rather
than document vocabulary.

**Report numbers from both configurations.** Showing that you measured the gap
between the offline fallbacks and the real stack is worth more marks than one
flattering number with no baseline:

| Configuration | Routing accuracy | Retrieval hit@4 |
|---|---|---|
| Mock router + hashing embedder (no keys) | 75.0% | 64.5% |
| Groq Llama 3.3 + MiniLM embeddings | *run it and fill this in* | *fill this in* |

---

## Deployment

**Backend → Render** (`render.yaml` included)

The knowledge base and vector index are built at deploy time, so the index is
never committed to git:

```yaml
buildCommand: pip install -r requirements.txt && python scripts/build_kb.py && python -m backend.rag.ingest
startCommand: uvicorn backend.main:app --host 0.0.0.0 --port $PORT
```

Set in the Render dashboard: `LLM_PROVIDER`, `GROQ_API_KEY`, `MONGO_URI`,
`JWT_SECRET`, and `CORS_ORIGINS=https://your-app.vercel.app`.

**Frontend → Vercel**

Import the repo, set root directory to `frontend`, and add
`NEXT_PUBLIC_API_URL=https://your-service.onrender.com`.

**Database → MongoDB Atlas**

Create a free M0 cluster, add a database user, allow network access from
`0.0.0.0/0` (Render has no static IPs on the free tier), and paste the
connection string into `MONGO_URI`.

> Render free instances sleep after inactivity and the first request then takes
> ~50s while the dyno wakes *and* reloads the embedding model. Hit the URL once
> before you start recording your demo.

---

## Design decisions

**Domain-tagged chunks, not one shared index.** Each chunk carries the agents
allowed to retrieve it. This is what makes the system multi-agent rather than one
chatbot with five prompts: the Billing agent literally cannot surface the
soundbar pairing guide, so it cannot drift outside its remit.

**Router returns at most two agents.** Three-way routing produced bloated,
repetitive answers in testing with no accuracy gain.

**Two-agent answers are merged by an LLM, not concatenated.** Stapling two
replies together reads like a bureaucracy — both specialists greet you and both
restate your problem. The merge call is skipped for single-agent queries, so the
cost lands only where it buys something.

**Confidence-based escalation.** If the top retrieval score is below
`RETRIEVAL_MIN_SCORE`, the agent says it doesn't know and escalates rather than
letting the LLM improvise a refund window. The Complaint agent escalates earliest
(0.45) — a frustrated customer given a confidently wrong answer is a worse
outcome than one handed to a human.

**Everything has an offline fallback.** Mock LLM, in-memory DB, hashing
embedder. The app always boots and `/health` reports what actually loaded. This
is what makes the project testable in CI and demonstrable on a laptop with no
network — but the fallbacks are convenience, not deployment modes.

**Router output is sanitised.** LLMs return `"billing"` instead of
`["billing"]`, invent agent names, and duplicate entries. `_sanitise()` repairs
all of it, with a regex keyword router as the final backstop.

**Known limitation:** retrieval is pure dense vector search. Exact-token queries
like a specific SKU ("TM-NB-A14") are a known weakness of embeddings; a BM25
hybrid would fix it and is the first thing worth adding next.

---

## Troubleshooting

| Symptom | Cause and fix |
|---|---|
| `No vector index in ...` | Run `python scripts/build_kb.py && python -m backend.rag.ingest` |
| Answers start with `[mock LLM]` | `LLM_PROVIDER` is still `mock`. Set `groq` + a key. |
| `/health` shows `hashing-fallback` | `pip install sentence-transformers` (needs internet on first run) |
| `database: in-memory` | Mongo unreachable. Start it, or set `MONGO_URI` to Atlas. History won't survive restarts until you do. |
| `password cannot be longer than 72 bytes` | A `passlib` + `bcrypt≥4.1` clash. This project calls `bcrypt` directly and is not affected — if you see it, you added passlib back. |
| CORS error in the browser | Add your frontend origin to `CORS_ORIGINS` in `.env` |
| Frontend: "Cannot reach the server" | Backend isn't running, or `NEXT_PUBLIC_API_URL` is wrong. Next.js only reads `.env.local` at build/dev start — restart after editing. |
| Retrieval quality is poor | Confirm `/health` shows sentence-transformers, then tune `CHUNK_SIZE` and `RETRIEVAL_MIN_SCORE` and re-run the eval |

---

## Deliverables checklist

- [x] Source code (backend + frontend)
- [x] Knowledge base PDFs (8 documents)
- [x] README with setup and deployment
- [x] Test suite (33 tests)
- [x] Evaluation harness with labelled dataset
- [ ] **Demo video** — compulsory, you must record this
- [ ] Deployment links (Vercel + Render) — fill in once deployed
- [ ] Project report PDF — see `docs/REPORT_NOTES.md` for the raw material
