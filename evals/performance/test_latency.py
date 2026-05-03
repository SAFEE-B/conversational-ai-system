"""
Latency Evaluation
===================
Measures TTFT, inter-token latency, and end-to-end response time
across four scenarios (30 trials each).

Scenarios:
  simple   — plain dialogue, no RAG keyword, no medication name
  rag_only — query that triggers RAG retrieval but no tool
  tool_only — query that triggers exactly one tool, minimal RAG benefit
  mixed    — query that triggers both RAG and a tool

Requires live chatbot server.

Run:
    pytest evals/performance/test_latency.py -v -s
"""
import json
import os
import statistics
import sys
import time

import pytest
import websockets

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from conftest import RESULTS_DIR  # noqa: E402
from config import (  # noqa: E402
    CHATBOT_WS_URL, LATENCY_TRIALS, THRESHOLDS,
    TTFT_MEDIAN_LIMIT_S, E2E_MEDIAN_LIMIT_S,
)

# ── Scenario definitions ───────────────────────────────────────────────────
# Each prompt is chosen to reliably hit (or avoid) RAG/tool dispatch.

SCENARIOS = {
    "simple": (
        "Hello, what are your pharmacy hours today?"
        # → no medication keyword, no interaction pattern → plain LLM
    ),
    "rag_only": (
        "What is the best way to store my medications at home safely?"
        # → hits storage_guidelines.txt via RAG; no tool keywords
    ),
    "tool_only": (
        "What is ibuprofen used for?"
        # → triggers get_medication_info; RAG adds little for a known drug
    ),
    "mixed": (
        "My daughter is 6 years old and weighs 22 kg. What is the correct ibuprofen dose for her fever?"
        # → triggers calculate_dosage + RAG retrieves pediatric_dosing.txt
    ),
}


# ── Core measurement function ──────────────────────────────────────────────

async def _measure_one_turn(message: str) -> dict:
    """
    Open a WebSocket, send one message, and time:
      - ttft:          time from send → first token received
      - inter_token:   mean time between consecutive tokens
      - e2e:           time from send → last token received (end message)

    Returns a dict with all three metrics, or raises on connection error.
    """
    async with websockets.connect(CHATBOT_WS_URL, open_timeout=10) as ws:
        # Session init
        await ws.send(json.dumps({"session_id": None}))
        await ws.recv()  # consume session_init

        await ws.send(json.dumps({"type": "message", "content": message}))

        t_send = time.perf_counter()
        t_first_token = None
        token_times = []

        async for raw in ws:
            msg = json.loads(raw)
            t = time.perf_counter()
            mtype = msg.get("type")

            if mtype == "start":
                continue
            elif mtype == "token":
                if t_first_token is None:
                    t_first_token = t
                token_times.append(t)
            elif mtype in ("end", "tool_used"):
                if mtype == "end":
                    break

        if t_first_token is None or not token_times:
            raise RuntimeError("No tokens received — server may have returned an error")

        ttft = t_first_token - t_send
        e2e = token_times[-1] - t_send

        if len(token_times) > 1:
            gaps = [token_times[i] - token_times[i - 1] for i in range(1, len(token_times))]
            inter_token = statistics.mean(gaps)
        else:
            inter_token = 0.0

        return {
            "ttft":        round(ttft, 4),
            "inter_token": round(inter_token, 4),
            "e2e":         round(e2e, 4),
            "n_tokens":    len(token_times),
        }


def _aggregate(samples: list[dict], key: str) -> dict:
    vals = sorted(s[key] for s in samples)
    n = len(vals)
    return {
        "mean":   round(statistics.mean(vals), 4),
        "median": round(statistics.median(vals), 4),
        "p90":    round(vals[int(n * 0.90)], 4),
        "p99":    round(vals[min(int(n * 0.99), n - 1)], 4),
        "min":    round(vals[0], 4),
        "max":    round(vals[-1], 4),
    }


# ══════════════════════════════════════════════════════════════════════════════
# PARAMETRISED LATENCY TEST  (one test per scenario)
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.live
@pytest.mark.parametrize("scenario", list(SCENARIOS.keys()))
async def test_latency_scenario(live_server, scenario):
    """
    Runs LATENCY_TRIALS trials for the given scenario, saves raw + aggregate
    results to evals/results/latency_{scenario}.json, and asserts median TTFT
    and E2E are within the thresholds set in config.py.
    """
    message = SCENARIOS[scenario]
    samples = []
    errors = 0

    for trial in range(LATENCY_TRIALS):
        try:
            result = await _measure_one_turn(message)
            samples.append(result)
        except Exception as e:
            errors += 1
            print(f"  [trial {trial+1}] error: {e}")

    assert len(samples) >= LATENCY_TRIALS * 0.8, (
        f"Too many failures: {errors}/{LATENCY_TRIALS} trials failed for scenario '{scenario}'"
    )

    metrics = {
        "scenario":      scenario,
        "message":       message,
        "n_trials":      LATENCY_TRIALS,
        "n_successful":  len(samples),
        "n_errors":      errors,
        "ttft":          _aggregate(samples, "ttft"),
        "inter_token":   _aggregate(samples, "inter_token"),
        "e2e":           _aggregate(samples, "e2e"),
        "raw_samples":   samples,
    }

    path = os.path.join(RESULTS_DIR, f"latency_{scenario}.json")
    with open(path, "w") as f:
        json.dump(metrics, f, indent=2)

    median_ttft = metrics["ttft"]["median"]
    median_e2e  = metrics["e2e"]["median"]

    print(f"\n[Latency:{scenario}]  trials={len(samples)}")
    print(f"  TTFT   median={median_ttft}s  p90={metrics['ttft']['p90']}s  p99={metrics['ttft']['p99']}s")
    print(f"  E2E    median={median_e2e}s   p90={metrics['e2e']['p90']}s   p99={metrics['e2e']['p99']}s")
    print(f"  ITL    mean={metrics['inter_token']['mean']}s")
    print(f"  → {path}")

    assert median_ttft <= TTFT_MEDIAN_LIMIT_S, (
        f"[{scenario}] Median TTFT {median_ttft}s exceeds {TTFT_MEDIAN_LIMIT_S}s"
    )
    assert median_e2e <= E2E_MEDIAN_LIMIT_S, (
        f"[{scenario}] Median E2E {median_e2e}s exceeds {E2E_MEDIAN_LIMIT_S}s"
    )


# ══════════════════════════════════════════════════════════════════════════════
# AGGREGATE SUMMARY  (collects all scenario results, generates plots)
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.live
async def test_latency_summary_and_plots(live_server):
    """
    Reads all per-scenario latency JSON files and produces:
      - evals/results/latency_summary.json  (cross-scenario table)
      - evals/report/latency_ttft.png       (box plot — TTFT by scenario)
      - evals/report/latency_e2e.png        (box plot — E2E by scenario)
    """
    import glob

    result_files = sorted(glob.glob(os.path.join(RESULTS_DIR, "latency_*.json")))
    result_files = [f for f in result_files if "summary" not in f]

    if not result_files:
        pytest.skip("No per-scenario latency results found — run scenario tests first")

    summary = []
    scenario_ttft_raw = {}
    scenario_e2e_raw  = {}

    for rf in result_files:
        d = json.load(open(rf))
        scenario_ttft_raw[d["scenario"]] = [s["ttft"] for s in d["raw_samples"]]
        scenario_e2e_raw[d["scenario"]]  = [s["e2e"]  for s in d["raw_samples"]]
        summary.append({
            "scenario":         d["scenario"],
            "n":                d["n_successful"],
            "ttft_median":      d["ttft"]["median"],
            "ttft_p90":         d["ttft"]["p90"],
            "ttft_p99":         d["ttft"]["p99"],
            "inter_token_mean": d["inter_token"]["mean"],
            "e2e_median":       d["e2e"]["median"],
            "e2e_p90":          d["e2e"]["p90"],
            "e2e_p99":          d["e2e"]["p99"],
        })

    summary_path = os.path.join(RESULTS_DIR, "latency_summary.json")
    with open(summary_path, "w") as f:
        json.dump(summary, f, indent=2)

    # Plots (matplotlib optional — skip gracefully if not installed)
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        report_dir = os.path.join(os.path.dirname(RESULTS_DIR), "report")
        os.makedirs(report_dir, exist_ok=True)

        for metric_key, raw_data, title, fname in [
            ("ttft", scenario_ttft_raw, "Time to First Token (s) by Scenario", "latency_ttft.png"),
            ("e2e",  scenario_e2e_raw,  "End-to-End Response Time (s) by Scenario", "latency_e2e.png"),
        ]:
            labels = list(raw_data.keys())
            data   = [raw_data[k] for k in labels]

            fig, ax = plt.subplots(figsize=(8, 5))
            ax.boxplot(data, labels=labels, patch_artist=True)
            ax.set_title(title)
            ax.set_ylabel("Seconds")
            ax.set_xlabel("Scenario")
            ax.grid(axis="y", linestyle="--", alpha=0.5)
            fig.tight_layout()
            plot_path = os.path.join(report_dir, fname)
            fig.savefig(plot_path, dpi=120)
            plt.close(fig)
            print(f"  Plot saved → {plot_path}")

    except ImportError:
        print("  matplotlib not installed — skipping plots")

    print(f"\n[Latency Summary]")
    for row in summary:
        print(f"  {row['scenario']:10s}  TTFT_med={row['ttft_median']}s  E2E_med={row['e2e_median']}s")
    print(f"  → {summary_path}")
