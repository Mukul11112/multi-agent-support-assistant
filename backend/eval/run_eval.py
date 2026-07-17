"""
Evaluation harness: routing accuracy, retrieval hit rate, and latency.

Run:  python -m backend.eval.run_eval
      python -m backend.eval.run_eval --csv docs/eval_results.csv

Put the printed table in your project report. It is worth reporting numbers from
BOTH configurations (mock vs. real LLM, fallback vs. real embeddings) - showing
that you measured the difference is worth more than one flattering number.

Metrics:
  Routing accuracy  - predicted agents overlap the labelled agents.
  Retrieval hit@k   - the expected source document appears in the retrieved chunks.
  Escalation rate   - share of queries the system handed to a human. Not a
                      failure metric: correct escalation is a feature. Read it
                      alongside retrieval hit rate - high escalation with high
                      hit rate means the score threshold is set too aggressively.
"""
from __future__ import annotations

import argparse
import csv
import logging
import statistics
import time

from backend.agents.router import route
from backend.eval.dataset import EVAL_SET
from backend.rag.retriever import retrieve

logging.getLogger().setLevel(logging.ERROR)  # keep the table readable


def percentile(values: list[float], pct: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    k = max(0, min(len(ordered) - 1, round(pct / 100 * len(ordered) + 0.5) - 1))
    return ordered[k]


def evaluate() -> tuple[list[dict], dict]:
    rows: list[dict] = []

    for case in EVAL_SET:
        t0 = time.perf_counter()
        decision = route(case["query"])
        route_ms = (time.perf_counter() - t0) * 1000

        predicted = decision["agents"]
        expected = case["expected_agents"]
        route_ok = bool(set(predicted) & set(expected))

        t1 = time.perf_counter()
        chunks = retrieve(case["query"], domain=predicted[0])
        retr_ms = (time.perf_counter() - t1) * 1000

        retrieved_sources = [c["source"] for c in chunks]
        if case["expected_source"] is None:
            retr_ok = None
        else:
            retr_ok = case["expected_source"] in retrieved_sources

        rows.append({
            "query": case["query"],
            "expected_agents": "|".join(expected),
            "predicted_agents": "|".join(predicted),
            "routing_ok": route_ok,
            "routing_confidence": round(decision["confidence"], 2),
            "expected_source": case["expected_source"] or "",
            "top_source": retrieved_sources[0] if retrieved_sources else "",
            "top_score": chunks[0]["score"] if chunks else 0.0,
            "retrieval_ok": retr_ok,
            "n_chunks": len(chunks),
            "route_ms": round(route_ms, 1),
            "retrieval_ms": round(retr_ms, 1),
        })

    scored_retr = [r for r in rows if r["retrieval_ok"] is not None]
    latencies = [r["route_ms"] + r["retrieval_ms"] for r in rows]

    summary = {
        "n_queries": len(rows),
        "routing_accuracy": sum(r["routing_ok"] for r in rows) / len(rows),
        "retrieval_hit_rate": (sum(r["retrieval_ok"] for r in scored_retr)
                               / len(scored_retr)) if scored_retr else 0.0,
        "no_retrieval_rate": sum(1 for r in rows if r["n_chunks"] == 0) / len(rows),
        "mean_top_score": statistics.mean([r["top_score"] for r in rows]),
        "mean_latency_ms": statistics.mean(latencies),
        "p95_latency_ms": percentile(latencies, 95),
    }
    return rows, summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", help="write per-query results to this path")
    parser.add_argument("--verbose", action="store_true", help="print every query")
    args = parser.parse_args()

    from backend import config
    from backend.embeddings.embedder import get_embedder
    from backend.llm.client import get_llm

    print("=" * 78)
    print("CONFIGURATION")
    print(f"  LLM       : {get_llm().name} ({config.active_model()})")
    print(f"  Embeddings: {get_embedder().name}")
    print(f"  top_k={config.RETRIEVAL_TOP_K}  min_score={config.RETRIEVAL_MIN_SCORE}"
          f"  chunk={config.CHUNK_SIZE}/{config.CHUNK_OVERLAP}")
    print("=" * 78)

    rows, summary = evaluate()

    failures = [r for r in rows if not r["routing_ok"]
                or r["retrieval_ok"] is False]

    if args.verbose:
        print(f"\n{'':2} {'ROUTE':6} {'RETR':5}  QUERY")
        for r in rows:
            rt = "PASS" if r["routing_ok"] else "FAIL"
            rr = "-" if r["retrieval_ok"] is None else ("PASS" if r["retrieval_ok"] else "FAIL")
            print(f"   {rt:6} {rr:5}  {r['query'][:60]}")

    if failures:
        print(f"\nFAILURES ({len(failures)}):")
        for r in failures:
            reasons = []
            if not r["routing_ok"]:
                reasons.append(f"routed to {r['predicted_agents']}, "
                               f"expected {r['expected_agents']}")
            if r["retrieval_ok"] is False:
                reasons.append(f"top source {r['top_source'] or 'none'}, "
                               f"expected {r['expected_source']}")
            print(f"  - {r['query'][:58]}")
            for reason in reasons:
                print(f"      {reason}")

    print("\n" + "=" * 78)
    print("SUMMARY")
    print(f"  Queries evaluated   : {summary['n_queries']}")
    print(f"  Routing accuracy    : {summary['routing_accuracy']:.1%}")
    print(f"  Retrieval hit@{4:<2}    : {summary['retrieval_hit_rate']:.1%}")
    print(f"  Queries w/ 0 chunks : {summary['no_retrieval_rate']:.1%}")
    print(f"  Mean top-1 score    : {summary['mean_top_score']:.3f}")
    print(f"  Mean latency        : {summary['mean_latency_ms']:.0f} ms")
    print(f"  p95 latency         : {summary['p95_latency_ms']:.0f} ms")
    print("=" * 78)
    print("  (latency excludes answer generation; it is routing + retrieval only)")

    if args.csv:
        import pathlib
        path = pathlib.Path(args.csv)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            writer.writerows(rows)
        print(f"\nPer-query results written to {path}")


if __name__ == "__main__":
    main()
