"""
RAG Component Evaluation
=========================
Part 1 — Retrieval Relevance  (direct retriever call, no server required)
  Metrics: Precision@3, Precision@5, Recall@3, Recall@5, MRR

Part 2 — Faithfulness  (requires live server + ANTHROPIC_API_KEY)
  Metric: mean faithfulness score (0-1) over 25 queries using LLM-as-judge

Run only Part 1:
    pytest evals/correctness/test_rag.py -m "not live" -v

Run everything:
    pytest evals/correctness/test_rag.py -v
"""
import json
import os
import statistics
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from conftest import ws_chat_turn, RESULTS_DIR  # noqa: E402

from config import (  # noqa: E402
    CHROMA_PERSIST_DIR, EMBEDDING_MODEL, RAG_TOP_K_VALUES,
    RAG_GT_DIR, THRESHOLDS, JUDGE_MODEL,
)

# ── Safe import: retriever needs chromadb + sentence-transformers ──────────
try:
    from retrieval.retriever import DocumentRetriever
    _RETRIEVER_AVAILABLE = True
except ImportError:
    _RETRIEVER_AVAILABLE = False

# ── Safe import: judge needs google-generativeai ──────────────────────────
try:
    import google.generativeai as _genai
    _JUDGE_AVAILABLE = bool(os.environ.get("GOOGLE_API_KEY"))
except ImportError:
    _JUDGE_AVAILABLE = False


# ── Fixtures ───────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def retriever():
    if not _RETRIEVER_AVAILABLE:
        pytest.skip("chromadb / sentence-transformers not installed")
    r = DocumentRetriever(
        chroma_persist_dir=CHROMA_PERSIST_DIR,
        embedding_model=EMBEDDING_MODEL,
        top_k=max(RAG_TOP_K_VALUES),
    )
    try:
        r.load()
    except Exception as e:
        pytest.skip(f"Retriever failed to load (index documents first): {e}")
    return r


@pytest.fixture(scope="module")
def ground_truth():
    path = os.path.join(RAG_GT_DIR, "rag_ground_truth.json")
    return json.load(open(path, encoding="utf-8"))


# ── Metric helpers ─────────────────────────────────────────────────────────

def _chunk_id(chunk: dict) -> str:
    return f"{chunk['source']}::chunk{chunk['chunk_index']}"


def _precision_at_k(retrieved: list[str], relevant: set[str], k: int) -> float:
    hits = sum(1 for cid in retrieved[:k] if cid in relevant)
    return hits / k if k else 0.0


def _recall_at_k(retrieved: list[str], relevant: set[str], k: int) -> float:
    hits = sum(1 for cid in retrieved[:k] if cid in relevant)
    return hits / len(relevant) if relevant else 0.0


def _reciprocal_rank(retrieved: list[str], relevant: set[str]) -> float:
    for rank, cid in enumerate(retrieved, start=1):
        if cid in relevant:
            return 1.0 / rank
    return 0.0


# ── Judge helper ───────────────────────────────────────────────────────────

_FAITHFULNESS_PROMPT = """\
You are evaluating whether a chatbot answer is faithful to the provided context.

CONTEXT (retrieved document chunks):
{context}

QUESTION:
{query}

ANSWER:
{answer}

Evaluate: is every factual claim in the ANSWER supported by the CONTEXT?
- Score 1.0  if every claim is supported.
- Score 0.5  if most claims are supported but one or two are not.
- Score 0.0  if the answer makes claims not found in the context (hallucination).

Respond with ONLY a JSON object: {{"score": <float 0.0-1.0>, "reason": "<one sentence>"}}"""


def _judge_faithfulness(query: str, context_chunks: list[dict], answer: str) -> dict:
    """Call the Gemini judge and return {score, reason}. Returns None on API failure."""
    if not _JUDGE_AVAILABLE:
        return None

    context_text = "\n\n---\n\n".join(c["text"] for c in context_chunks)
    prompt = _FAITHFULNESS_PROMPT.format(
        context=context_text, query=query, answer=answer
    )

    try:
        _genai.configure(api_key=os.environ["GOOGLE_API_KEY"])
        model = _genai.GenerativeModel(JUDGE_MODEL)
        response = model.generate_content(prompt)
        raw = response.text.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1].lstrip("json").strip()
        parsed = json.loads(raw)
        return {"score": float(parsed["score"]), "reason": parsed.get("reason", "")}
    except Exception as e:
        return {"score": None, "error": str(e)}


# ══════════════════════════════════════════════════════════════════════════════
# PART 1 — Retrieval Relevance  (no server required)
# ══════════════════════════════════════════════════════════════════════════════

def test_rag_retrieval_metrics(retriever, ground_truth):
    """
    Runs all 25 ground-truth queries through the retriever and computes
    Precision@3, Precision@5, Recall@3, Recall@5, and MRR.

    Saves results to evals/results/rag_results.json.
    Asserts against thresholds from config.py.
    """
    p3_list, p5_list, r3_list, r5_list, rr_list = [], [], [], [], []
    per_query = []

    for item in ground_truth:
        query = item["query"]
        relevant = set(item["relevant_chunk_ids"])

        chunks = retriever.retrieve(query, top_k=max(RAG_TOP_K_VALUES))
        retrieved_ids = [_chunk_id(c) for c in chunks]

        p3 = _precision_at_k(retrieved_ids, relevant, k=3)
        p5 = _precision_at_k(retrieved_ids, relevant, k=5)
        r3 = _recall_at_k(retrieved_ids, relevant, k=3)
        r5 = _recall_at_k(retrieved_ids, relevant, k=5)
        rr = _reciprocal_rank(retrieved_ids, relevant)

        p3_list.append(p3); p5_list.append(p5)
        r3_list.append(r3); r5_list.append(r5)
        rr_list.append(rr)

        per_query.append({
            "query_id":            item["query_id"],
            "query":               query,
            "relevant_chunk_ids":  list(relevant),
            "retrieved_chunk_ids": retrieved_ids,
            "precision@3":         round(p3, 4),
            "precision@5":         round(p5, 4),
            "recall@3":            round(r3, 4),
            "recall@5":            round(r5, 4),
            "mrr":                 round(rr, 4),
        })

    def avg(lst): return round(sum(lst) / len(lst), 4)

    metrics = {
        "num_queries": len(ground_truth),
        "precision@3": avg(p3_list),
        "precision@5": avg(p5_list),
        "recall@3":    avg(r3_list),
        "recall@5":    avg(r5_list),
        "mrr":         avg(rr_list),
        "per_query":   per_query,
    }

    path = os.path.join(RESULTS_DIR, "rag_retrieval_results.json")
    with open(path, "w") as f:
        json.dump(metrics, f, indent=2)

    print(f"\n[RAG Retrieval]  n={metrics['num_queries']}")
    print(f"  Precision  @3={metrics['precision@3']}  @5={metrics['precision@5']}")
    print(f"  Recall     @3={metrics['recall@3']}  @5={metrics['recall@5']}")
    print(f"  MRR        ={metrics['mrr']}")
    print(f"  → {path}")

    assert metrics["precision@3"] >= THRESHOLDS["rag_precision_at_3"], (
        f"Precision@3 {metrics['precision@3']} below threshold {THRESHOLDS['rag_precision_at_3']}"
    )
    assert metrics["recall@3"] >= THRESHOLDS["rag_recall_at_3"], (
        f"Recall@3 {metrics['recall@3']} below threshold {THRESHOLDS['rag_recall_at_3']}"
    )
    assert metrics["mrr"] >= THRESHOLDS["rag_mrr"], (
        f"MRR {metrics['mrr']} below threshold {THRESHOLDS['rag_mrr']}"
    )


# ══════════════════════════════════════════════════════════════════════════════
# PART 2 — Faithfulness  (requires live server + ANTHROPIC_API_KEY)
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.live
async def test_rag_faithfulness(live_server, retriever, ground_truth):
    """
    For each ground-truth query:
      1. Retrieve top-3 chunks directly via the retriever.
      2. Send the query to the live chatbot and collect the response.
      3. Ask the judge LLM: are all claims in the response supported by the chunks?

    Saves per-query scores + aggregate stats to evals/results/rag_faithfulness_results.json.
    """
    if not _JUDGE_AVAILABLE:
        pytest.skip("GOOGLE_API_KEY not set or google-generativeai package not installed")

    per_query = []
    scores = []

    for item in ground_truth:
        query = item["query"]

        # Step 1: get retrieval context directly (mirrors what the server does)
        chunks = retriever.retrieve(query, top_k=3)

        # Step 2: get the chatbot's actual response over WebSocket
        ws_result = await ws_chat_turn(query)
        answer = ws_result["response"]

        if not answer.strip():
            continue  # skip if server returned nothing

        # Step 3: judge faithfulness
        judgment = _judge_faithfulness(query, chunks, answer)
        score = judgment.get("score") if judgment else None

        entry = {
            "query_id":    item["query_id"],
            "query":       query,
            "answer":      answer[:300],
            "num_chunks":  len(chunks),
            "faithfulness_score": score,
            "reason":      (judgment or {}).get("reason", ""),
        }
        per_query.append(entry)

        if score is not None:
            scores.append(score)

    mean_faith = round(statistics.mean(scores), 4) if scores else None
    std_faith  = round(statistics.stdev(scores), 4) if len(scores) > 1 else None

    results = {
        "num_queries":         len(per_query),
        "mean_faithfulness":   mean_faith,
        "std_faithfulness":    std_faith,
        "judge_model":         JUDGE_MODEL,
        "per_query":           per_query,
    }

    path = os.path.join(RESULTS_DIR, "rag_faithfulness_results.json")
    with open(path, "w") as f:
        json.dump(results, f, indent=2)

    print(f"\n[RAG Faithfulness]  n={len(scores)}")
    print(f"  Mean={mean_faith}  Std={std_faith}")
    print(f"  → {path}")

    assert mean_faith is not None, "No faithfulness scores collected — judge calls all failed"
    assert mean_faith >= THRESHOLDS["rag_faithfulness"], (
        f"Mean faithfulness {mean_faith} below threshold {THRESHOLDS['rag_faithfulness']}"
    )
