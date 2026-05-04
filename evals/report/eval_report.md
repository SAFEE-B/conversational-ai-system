# HealthFirst Pharmacy Chatbot — Eval Report

_Generated: 2026-05-04 13:17:42_

---

## RAG Retrieval

| Metric      | Value | Threshold | Status |
|-------------|-------|-----------|--------|
| Precision@3 | 0.4133  | >= 0.35 | PASS |
| Recall@3    | 0.98  | >= 0.85    | PASS |
| MRR         | 0.96 | >= 0.8           | PASS |
| Precision@5 | 0.256  | --        | --     |
| Recall@5    | 1.0  | --        | --     |

_Queries evaluated: 25_

---

## CRM Tool

| Metric            | Value | Threshold | Status |
|-------------------|-------|-----------|--------|
| Invocation TPR    | 0.875 | >= 0.8 | PASS |
| Invocation FPR    | 0.0 | <= 0.1 | PASS |
| Argument Accuracy | 1.0 | >= 0.75 | PASS |

---

## Pharmacy Tools

| Tool             | TPR  | FPR  | Arg Acc | TPR    | FPR    |
|------------------|------|------|---------|--------|--------|
| Drug Interaction | 0.5 | 0.0 | 0.25   | FAIL | PASS |
| Dosage Calculator | --   | --   | --      | no data | no data |
| Medication Info  | --   | --   | --      | no data | no data |

---

## Conversational Quality

_No results (run `pytest evals/correctness/test_conversational.py`)_

---

## Latency

_No results (run `pytest evals/performance/test_latency.py`)_

---

## Throughput / Concurrency

_No results (run `pytest evals/performance/test_throughput.py`)_
