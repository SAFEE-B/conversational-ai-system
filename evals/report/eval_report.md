# HealthFirst Pharmacy Chatbot — Eval Report

_Generated: 2026-05-03 13:19:35_

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

_No results (run `pytest evals/correctness/test_crm.py`)_

---

## Pharmacy Tools

| Tool             | TPR  | FPR  | Arg Acc | TPR    | FPR    |
|------------------|------|------|---------|--------|--------|
| Drug Interaction | --   | --   | --      | no data | no data |
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
