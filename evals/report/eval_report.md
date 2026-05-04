# HealthFirst Pharmacy Chatbot — Eval Report

_Generated: 2026-05-04 15:02:23_

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
| Drug Interaction | 0.5 | 0.0 | 0.0   | FAIL | PASS |
| Dosage Calculator | 1.0 | 0.0 | 0.4286   | PASS | PASS |
| Medication Info  | 1.0 | 0.0 | 0.0   | PASS | PASS |

---

## Conversational Quality

_No results (run `pytest evals/correctness/test_conversational.py`)_

---

## Latency

Thresholds: TTFT median <= 2.0s | E2E median <= 10.0s

| Scenario   | TTFT med | TTFT p90 | TTFT p99 | E2E med | E2E p90 | E2E p99 | ITL mean | TTFT   | E2E    |
|------------|----------|----------|----------|---------|---------|---------|----------|--------|--------|
| mixed      | 0.0322 | 0.036 | 0.4185 | 0.8657 | 1.1265 | 1.3604 | 0.0112 | PASS | PASS |
| rag_only   | 0.0328 | 0.0364 | 0.4987 | 0.7837 | 1.0292 | 1.336 | 0.0113 | PASS | PASS |
| simple     | 0.0321 | 0.0362 | 0.5968 | 0.5555 | 0.5907 | 0.9623 | 0.0127 | PASS | PASS |
| tool_only  | 0.032 | 0.0359 | 0.4931 | 0.5416 | 0.5688 | 0.855 | 0.013 | PASS | PASS |

---

## Throughput / Concurrency

- **Max sustainable concurrency**: 2
- **Breakpoint**: 5
- TTFT limit: 2.0s | E2E limit: 10.0s

| Users | Turns | TPS   | TTFT med | E2E med | TTFT   | E2E    | OK |
|-------|-------|-------|----------|---------|--------|--------|----|
| 1     | 3     | 0.721 | 0.3983     | 0.7737    | PASS | PASS | YES |
| 2     | 6     | 0.978 | 0.985     | 1.3007    | PASS | PASS | YES |
| 5     | 15    | 1.39  | 2.5245     | 2.8477    | FAIL | PASS | NO |
| 10    | 30    | 1.541 | 4.9912     | 5.3029    | FAIL | PASS | NO |
| 20    | 60    | 1.628 | 10.7243     | 10.9791    | FAIL | FAIL | NO |
