"""
Eval Report Generator
======================
Reads all JSON result files from evals/results/ and produces:

  evals/report/eval_report.md   — human-readable Markdown summary
  evals/report/eval_report.json — machine-readable aggregate (CI-friendly)

Run standalone:
    python evals/report/generate_report.py

Or call generate() from run_evals.py after tests complete.
"""
import json
import os
import sys
from datetime import datetime

_HERE = os.path.dirname(os.path.abspath(__file__))
_EVALS_DIR = os.path.dirname(_HERE)
sys.path.insert(0, _EVALS_DIR)

from config import (  # noqa: E402
    THRESHOLDS, TTFT_MEDIAN_LIMIT_S, E2E_MEDIAN_LIMIT_S,
)

RESULTS_DIR = os.path.join(_EVALS_DIR, "results")
REPORT_DIR  = _HERE


# ── JSON loader (returns None if file missing) ─────────────────────────────────

def _load(filename: str) -> dict | None:
    path = os.path.join(RESULTS_DIR, filename)
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as f:
        return json.load(f)


# ── Threshold badge ────────────────────────────────────────────────────────────

def _badge(value, threshold, direction="above") -> str:
    if value is None:
        return "N/A"
    ok = (value >= threshold) if direction == "above" else (value <= threshold)
    return "PASS" if ok else "FAIL"


# ── Section builders ───────────────────────────────────────────────────────────

def _section_rag(lines: list[str]):
    lines.append("## RAG Retrieval\n")
    d = _load("rag_retrieval_results.json")
    if d is None:
        lines.append("_No results (run `pytest evals/correctness/test_rag.py -m 'not live'`)_\n")
        return

    p3  = d.get("precision@3")
    r3  = d.get("recall@3")
    mrr = d.get("mrr")
    p5  = d.get("precision@5")
    r5  = d.get("recall@5")
    lines.append("| Metric      | Value | Threshold | Status |")
    lines.append("|-------------|-------|-----------|--------|")
    lines.append(f"| Precision@3 | {p3}  | >= {THRESHOLDS['rag_precision_at_3']} | {_badge(p3, THRESHOLDS['rag_precision_at_3'])} |")
    lines.append(f"| Recall@3    | {r3}  | >= {THRESHOLDS['rag_recall_at_3']}    | {_badge(r3, THRESHOLDS['rag_recall_at_3'])} |")
    lines.append(f"| MRR         | {mrr} | >= {THRESHOLDS['rag_mrr']}           | {_badge(mrr, THRESHOLDS['rag_mrr'])} |")
    lines.append(f"| Precision@5 | {p5}  | --        | --     |")
    lines.append(f"| Recall@5    | {r5}  | --        | --     |")
    lines.append(f"\n_Queries evaluated: {d.get('num_queries', '?')}_\n")

    faith = _load("rag_faithfulness_results.json")
    if faith:
        mf = faith.get("mean_faithfulness")
        lines.append(
            f"**Faithfulness** (LLM-as-judge): {mf}  "
            f"{_badge(mf, THRESHOLDS['rag_faithfulness'])}  "
            f"_(n={faith.get('num_queries','?')}, judge={faith.get('judge_model','?')})_\n"
        )


def _section_crm(lines: list[str]):
    lines.append("## CRM Tool\n")
    d = _load("crm_results.json")
    if d is None:
        lines.append("_No results (run `pytest evals/correctness/test_crm.py`)_\n")
        return

    tpr = d.get("tpr"); fpr = d.get("fpr"); acc = d.get("argument_accuracy")
    lines.append("| Metric            | Value | Threshold | Status |")
    lines.append("|-------------------|-------|-----------|--------|")
    lines.append(f"| Invocation TPR    | {tpr} | >= {THRESHOLDS['tool_invocation_tpr']} | {_badge(tpr, THRESHOLDS['tool_invocation_tpr'])} |")
    lines.append(f"| Invocation FPR    | {fpr} | <= {THRESHOLDS['tool_invocation_fpr']} | {_badge(fpr, THRESHOLDS['tool_invocation_fpr'], 'below')} |")
    lines.append(f"| Argument Accuracy | {acc} | >= {THRESHOLDS['tool_argument_accuracy']} | {_badge(acc, THRESHOLDS['tool_argument_accuracy'])} |")
    lines.append("")


def _section_tools(lines: list[str]):
    lines.append("## Pharmacy Tools\n")
    tools = [
        ("Drug Interaction",  "drug_interaction_results.json"),
        ("Dosage Calculator", "dosage_results.json"),
        ("Medication Info",   "medication_info_results.json"),
    ]
    lines.append("| Tool             | TPR  | FPR  | Arg Acc | TPR    | FPR    |")
    lines.append("|------------------|------|------|---------|--------|--------|")
    for label, fname in tools:
        d = _load(fname)
        if d is None:
            lines.append(f"| {label:<16} | --   | --   | --      | no data | no data |")
            continue
        tpr = d.get("tpr"); fpr = d.get("fpr"); acc = d.get("argument_accuracy")
        lines.append(
            f"| {label:<16} | {tpr} | {fpr} | {acc}   | "
            f"{_badge(tpr, THRESHOLDS['tool_invocation_tpr'])} | "
            f"{_badge(fpr, THRESHOLDS['tool_invocation_fpr'], 'below')} |"
        )
    lines.append("")


def _section_conversational(lines: list[str]):
    lines.append("## Conversational Quality\n")
    d = _load("conversational_results.json")
    if d is None:
        lines.append("_No results (run `pytest evals/correctness/test_conversational.py`)_\n")
        return

    tcr = d.get("task_completion_rate")
    par = d.get("policy_adherence_rate")
    coh = d.get("mean_coherence_score")
    lines.append("| Metric                | Value | Threshold | Status |")
    lines.append("|-----------------------|-------|-----------|--------|")
    lines.append(f"| Task Completion Rate  | {tcr} | >= {THRESHOLDS['task_completion_rate']}  | {_badge(tcr, THRESHOLDS['task_completion_rate'])} |")
    lines.append(f"| Policy Adherence Rate | {par} | >= {THRESHOLDS['policy_adherence_rate']}  | {_badge(par, THRESHOLDS['policy_adherence_rate'])} |")
    lines.append(f"| Mean Coherence (0-1)  | {coh} | >= {THRESHOLDS['coherence_score']}  | {_badge(coh, THRESHOLDS['coherence_score'])} |")
    lines.append(f"\n_Dialogues: {d.get('n_dialogues','?')}, judge: {d.get('judge_model','?')}_\n")


def _section_latency(lines: list[str]):
    lines.append("## Latency\n")
    summary = _load("latency_summary.json")
    if summary is None:
        lines.append("_No results (run `pytest evals/performance/test_latency.py`)_\n")
        return

    lines.append(f"Thresholds: TTFT median <= {TTFT_MEDIAN_LIMIT_S}s | E2E median <= {E2E_MEDIAN_LIMIT_S}s\n")
    lines.append("| Scenario   | TTFT med | TTFT p90 | TTFT p99 | E2E med | E2E p90 | E2E p99 | ITL mean | TTFT   | E2E    |")
    lines.append("|------------|----------|----------|----------|---------|---------|---------|----------|--------|--------|")
    for row in summary:
        ttft_m = row.get("ttft_median")
        e2e_m  = row.get("e2e_median")
        lines.append(
            f"| {row['scenario']:<10} "
            f"| {row.get('ttft_median')} "
            f"| {row.get('ttft_p90')} "
            f"| {row.get('ttft_p99')} "
            f"| {row.get('e2e_median')} "
            f"| {row.get('e2e_p90')} "
            f"| {row.get('e2e_p99')} "
            f"| {row.get('inter_token_mean')} "
            f"| {_badge(ttft_m, TTFT_MEDIAN_LIMIT_S, 'below')} "
            f"| {_badge(e2e_m, E2E_MEDIAN_LIMIT_S, 'below')} |"
        )
    lines.append("")

    for fname, label in [("latency_ttft.png", "TTFT by Scenario"), ("latency_e2e.png", "E2E by Scenario")]:
        if os.path.exists(os.path.join(REPORT_DIR, fname)):
            lines.append(f"![{label}]({fname})\n")


def _section_throughput(lines: list[str]):
    lines.append("## Throughput / Concurrency\n")
    d = _load("throughput_results.json")
    if d is None:
        lines.append("_No results (run `pytest evals/performance/test_throughput.py`)_\n")
        return

    lines.append(f"- **Max sustainable concurrency**: {d.get('max_sustainable_concurrency', '--')}")
    lines.append(f"- **Breakpoint**: {d.get('breakpoint', 'none — all levels passed')}")
    lines.append(f"- TTFT limit: {d.get('ttft_limit_s')}s | E2E limit: {d.get('e2e_limit_s')}s\n")

    per_level = d.get("per_level", [])
    if per_level:
        lines.append("| Users | Turns | TPS   | TTFT med | E2E med | TTFT   | E2E    | OK |")
        lines.append("|-------|-------|-------|----------|---------|--------|--------|----|")
        for lv in per_level:
            ttft_s = lv.get("ttft") or {}
            e2e_s  = lv.get("e2e")  or {}
            ttft_m = ttft_s.get("median")
            e2e_m  = e2e_s.get("median")
            ok = "YES" if lv.get("sustainable") else "NO"
            lines.append(
                f"| {lv['n_users']:<5} "
                f"| {lv['n_turns']:<5} "
                f"| {lv['throughput_tps']:<5} "
                f"| {ttft_m}     "
                f"| {e2e_m}    "
                f"| {_badge(ttft_m, TTFT_MEDIAN_LIMIT_S, 'below')} "
                f"| {_badge(e2e_m, E2E_MEDIAN_LIMIT_S, 'below')} "
                f"| {ok} |"
            )
    lines.append("")

    for fname, label in [
        ("throughput_ttft.png", "TTFT vs Concurrency"),
        ("throughput_e2e.png",  "E2E vs Concurrency"),
        ("throughput_tps.png",  "Turns/sec vs Concurrency"),
    ]:
        if os.path.exists(os.path.join(REPORT_DIR, fname)):
            lines.append(f"![{label}]({fname})\n")


# ── Master generate function ───────────────────────────────────────────────────

def generate() -> tuple[str, str]:
    """Build the Markdown report and JSON summary. Returns (md_path, json_path)."""
    os.makedirs(REPORT_DIR, exist_ok=True)

    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lines: list[str] = [
        "# HealthFirst Pharmacy Chatbot — Eval Report",
        f"\n_Generated: {ts}_\n",
        "---\n",
    ]

    _section_rag(lines)
    lines.append("---\n")
    _section_crm(lines)
    lines.append("---\n")
    _section_tools(lines)
    lines.append("---\n")
    _section_conversational(lines)
    lines.append("---\n")
    _section_latency(lines)
    lines.append("---\n")
    _section_throughput(lines)

    md_content = "\n".join(lines)
    md_path = os.path.join(REPORT_DIR, "eval_report.md")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(md_content)

    def _scalar(fname, key):
        d = _load(fname)
        return d.get(key) if d else None

    json_summary = {
        "generated_at":                ts,
        "rag_precision_at_3":          _scalar("rag_retrieval_results.json",    "precision@3"),
        "rag_recall_at_3":             _scalar("rag_retrieval_results.json",    "recall@3"),
        "rag_mrr":                     _scalar("rag_retrieval_results.json",    "mrr"),
        "rag_faithfulness":            _scalar("rag_faithfulness_results.json", "mean_faithfulness"),
        "task_completion_rate":        _scalar("conversational_results.json",   "task_completion_rate"),
        "policy_adherence_rate":       _scalar("conversational_results.json",   "policy_adherence_rate"),
        "mean_coherence_score":        _scalar("conversational_results.json",   "mean_coherence_score"),
        "max_sustainable_concurrency": _scalar("throughput_results.json",       "max_sustainable_concurrency"),
        "thresholds":                  THRESHOLDS,
        "ttft_median_limit_s":         TTFT_MEDIAN_LIMIT_S,
        "e2e_median_limit_s":          E2E_MEDIAN_LIMIT_S,
    }
    json_path = os.path.join(REPORT_DIR, "eval_report.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(json_summary, f, indent=2)

    return md_path, json_path


if __name__ == "__main__":
    md, js = generate()
    print(f"Report  -> {md}")
    print(f"Summary -> {js}")
