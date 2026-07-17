# Report notes

Raw material for your project report. This is **not** the report — write that
yourself, in your own words. What's here is the reasoning behind each decision,
which is the part that's hard to reconstruct later and the part that earns marks.

The mark scheme rewards architecture (20), RAG (20), and LLM integration (15)
above everything else — 55 of 100. Spend your report proportionally.

---

## 1. Architecture (20 marks)

### The claim to make

This is a genuine multi-agent system, not one chatbot with five prompts. The
evidence: **each agent has its own retrieval scope.** Every chunk in the vector
store is tagged with the agents allowed to see it (`chunker.py: DOMAIN_MAP`), and
`retrieve(query, domain=...)` filters on that tag. The Billing agent *cannot*
surface the soundbar pairing guide — not because we told it not to, but because
that chunk is not in its retrievable set.

If you strip the domain filter, you have a single RAG chatbot with five system
prompts. That distinction is the core of the 20 marks.

### The flow

```
query → router (LLM intent classification, returns 1–2 agents)
      → each agent retrieves from its own domain
      → each agent generates, grounded, with a persona and guardrails
      → aggregator merges (only if 2 agents)
      → escalation check
      → persist to MongoDB
```

### Decisions worth defending

**Max two agents.** Three-way routing produced bloated, repetitive answers in
testing with no accuracy gain. The cap is in the router prompt *and* enforced in
`_sanitise()` — you cannot trust a prompt to be a constraint.

**Merge, don't concatenate.** Two specialists each open by restating the problem
and offering to help; stapled together it reads like a bureaucracy. A third LLM
call merges them into one voice. It's skipped for single-agent queries (the
common case), so the latency lands only where it buys something.

**Parallel execution.** Two agents run in a `ThreadPoolExecutor`. Each is an
independent network-bound LLM call, so a two-agent query costs roughly the same
wall-clock time as a one-agent query.

**Complaint routing overrides topic.** An angry refund question goes to
Complaints, not Billing. How the customer feels determines who should answer —
this is in both the router prompt and the keyword fallback ordering.

---

## 2. RAG (20 marks)

| Parameter | Value | Why |
|---|---|---|
| Embeddings | all-MiniLM-L6-v2, 384-dim | Brief's recommendation; strong quality/size tradeoff |
| Chunk size | 900 chars | Roughly one policy clause |
| Overlap | 150 chars | Stops a clause being severed at a boundary |
| Index | FAISS `IndexFlatIP` | Exhaustive = no recall loss, no training. At 41 chunks, IVF/HNSW would be premature optimisation. |
| Similarity | Cosine (via normalised inner product) | Length-invariant |
| top_k | 4 per agent | |
| Score floor | 0.25 | Below this → escalate, don't guess |

**Paragraph-aware chunking.** `split_text()` splits on paragraph boundaries
first and only hard-windows oversized paragraphs. Naive fixed-size chunking cuts
"refunds take 5 to 7 business days" in half and the retrieval never recovers.
Cheapest quality win in the pipeline.

**Normalise once, then inner product = cosine.** `IndexFlatIP` over L2-normalised
vectors gives cosine similarity for free.

**Over-fetch before filtering.** When filtering by domain, we fetch `top_k * 6`
and then filter. If you fetch exactly `top_k` first, the nearest chunks may all
belong to other domains and the filter returns nothing.

**Known limitation — state this yourself before the examiner does.** Retrieval is
pure dense vector search. Exact-token queries ("does TM-NB-A14 have Thunderbolt?")
are a known weakness of embeddings, which are built to match meaning, not
strings. A BM25 hybrid (`rank_bm25`, then reciprocal-rank fusion) is the obvious
next step. Naming your own limitation reads as competence; having it found for
you does not.

---

## 3. LLM integration (15 marks)

**Provider abstraction.** `llm/client.py` puts one interface over Groq, OpenAI,
Gemini, Ollama, and a mock. Swapping providers is one line in `.env`. Imports are
lazy, so you only install the SDK you use.

**Guardrails** (`agents/base.py: GUARDRAILS`): answer only from context; cite
sources; escalate rather than invent; stay in your specialisation. Worth quoting
verbatim in the report — it's the anti-hallucination mechanism.

**Never trust LLM output.** `_sanitise()` in `router.py` handles: a bare string
instead of a list, hallucinated agent names, duplicates, missing or non-numeric
confidence, and more than two agents. Below that sits `_fallback_route()`, a
regex router used when the LLM is unreachable or returns junk. **The system
degrades; it does not crash.** Tests in `test_rag.py` cover each malformation.

**Temperature 0.2.** Support answers should be reproducible. Same question, same
answer.

**Memory is bounded to 6 turns.** Full history blows the context window on a long
session and buries the current question under stale text — routing accuracy drops
when the model over-weights old turns.

---

## 4. Evaluation

Run both, report both:

```bash
python -m backend.eval.run_eval --verbose --csv docs/eval_results.csv
```

| Configuration | Routing accuracy | Retrieval hit@4 | Mean top-1 score |
|---|---|---|---|
| Mock router + hashing fallback | 75.0% | 64.5% | 0.463 |
| Groq Llama 3.3 + MiniLM | *fill in* | *fill in* | *fill in* |

The first row is the floor — no LLM, no semantic embeddings, pure keyword
matching. The delta between the rows **is** the value of the LLM router and
dense retrieval, quantified. That comparison is the most defensible thing in your
report, and almost nobody does it.

The 32 queries in `eval/dataset.py` use customer phrasing ("my money hasn't come
back"), not document vocabulary ("refund timeline"). Closing that gap is exactly
what embeddings are for and what keyword search cannot do.

**On escalation rate:** it is not a failure metric. Correct escalation is a
feature. Read it next to retrieval hit rate — high escalation *with* high hit
rate means the score floor is too aggressive.

---

## 5. Things to say honestly in the limitations section

- Dense retrieval only; no BM25 hybrid, so exact SKU lookups are weak.
- Knowledge base is 8 synthetic documents. Real deployments have thousands, where
  chunk count changes the index choice and per-domain filtering gets slower.
- No streaming; the user waits for the full answer.
- JWT in `localStorage` is readable by any XSS. httpOnly cookies are the
  production answer, at the cost of CSRF handling.
- No rate limiting on `/chat`. Each call costs LLM tokens — a trivial abuse vector.
- The aggregator can, in principle, drop a detail while merging. Mitigated by
  prompt instruction, not verified programmatically.
- Evaluation measures routing and retrieval, **not answer quality**. Judging
  faithfulness needs either human ratings or an LLM-as-judge with its own
  validation.

---

## 6. Demo video (compulsory)

Before recording, check `/health` shows `groq` and `sentence-transformers`, not
the fallbacks. Suggested five minutes:

1. `/health` — show the real stack is live (15s)
2. Simple billing question → one agent, sources cited (45s)
3. Technical question → different agent, different documents (45s)
4. **"I paid for Premium yesterday but it's still locked"** → two agent badges,
   merged answer. This is the headline requirement — spend time here (90s)
5. Ask something absurd → watch it escalate instead of hallucinating (30s)
6. Reload the page → history persists from MongoDB (30s)
7. `/analytics` → agent usage and escalation rate (30s)
8. Thirty seconds on architecture, using the README diagram (30s)

Step 5 is the one that separates a good demo from a generic one. Anyone can show
a chatbot answering. Showing it *refuse* to answer, on purpose, by design,
demonstrates you understood the actual problem with RAG systems.
