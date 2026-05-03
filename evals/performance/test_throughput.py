"""
Throughput / Concurrency Evaluation
=====================================
Ramps concurrent virtual users from 1 → max(THROUGHPUT_LEVELS).
Each virtual user sends a fixed 3-turn conversation in a single WebSocket session.

Identifies:
  max_sustainable_concurrency — highest concurrency where median TTFT < TTFT_MEDIAN_LIMIT_S
                                 AND median E2E < E2E_MEDIAN_LIMIT_S
  breakpoint                  — first concurrency level where either threshold is violated
  throughput                  — turns/sec at each concurrency level

Saves:
  evals/results/throughput_results.json
  evals/report/throughput_ttft.png
  evals/report/throughput_e2e.png
  evals/report/throughput_tps.png

Run:
    pytest evals/performance/test_throughput.py -v -s
"""
import asyncio
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
    CHATBOT_WS_URL, THROUGHPUT_LEVELS,
    TTFT_MEDIAN_LIMIT_S, E2E_MEDIAN_LIMIT_S,
)

# ── Fixed conversation (3 turns, covers simple → tool path) ───────────────────
# Kept short and deterministic so that timing reflects server load, not prompt length.

_CONVERSATION = [
    "Hello, can you tell me your pharmacy hours?",
    "What is ibuprofen used for?",
    "Thank you, that's all I needed.",
]


# ── Per-user coroutine ─────────────────────────────────────────────────────────

async def _run_user_session(user_id: int) -> list[dict]:
    """
    Opens one WebSocket, sends all turns, returns a list of per-turn timing dicts.
    On connection failure returns an empty list (counted as full user error).
    """
    turns = []
    try:
        async with websockets.connect(CHATBOT_WS_URL, open_timeout=15) as ws:
            # Session initialisation
            await ws.send(json.dumps({"session_id": None}))
            await ws.recv()  # discard session_init ack

            for turn_idx, message in enumerate(_CONVERSATION):
                await ws.send(json.dumps({"type": "message", "content": message}))

                t_send = time.perf_counter()
                t_first_token = None
                token_times: list[float] = []

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
                        # tool_used is informational; keep consuming until "end"

                if t_first_token is None or not token_times:
                    # Server returned no tokens for this turn — skip it
                    continue

                ttft  = t_first_token - t_send
                e2e   = token_times[-1] - t_send
                turns.append({
                    "user_id":  user_id,
                    "turn":     turn_idx,
                    "ttft":     round(ttft, 4),
                    "e2e":      round(e2e, 4),
                    "n_tokens": len(token_times),
                })

    except Exception as exc:
        print(f"  [user {user_id}] connection error: {exc}")

    return turns


# ── Concurrency runner ─────────────────────────────────────────────────────────

async def _run_concurrency_level(n_users: int) -> dict:
    """
    Launch n_users sessions concurrently, collect all per-turn metrics,
    return aggregate stats + wall-clock throughput.
    """
    t_wall_start = time.perf_counter()
    results = await asyncio.gather(*[_run_user_session(i) for i in range(n_users)])
    t_wall_end = time.perf_counter()
    wall_seconds = t_wall_end - t_wall_start

    all_turns = [t for user_turns in results for t in user_turns]
    n_users_ok = sum(1 for user_turns in results if user_turns)
    n_errors   = n_users - n_users_ok

    if not all_turns:
        return {
            "n_users":         n_users,
            "n_users_ok":      0,
            "n_errors":        n_users,
            "n_turns":         0,
            "wall_seconds":    round(wall_seconds, 3),
            "throughput_tps":  0.0,
            "ttft":            None,
            "e2e":             None,
        }

    ttft_vals = sorted(t["ttft"] for t in all_turns)
    e2e_vals  = sorted(t["e2e"]  for t in all_turns)
    n         = len(ttft_vals)

    def _stats(vals):
        n = len(vals)
        return {
            "mean":   round(statistics.mean(vals), 4),
            "median": round(statistics.median(vals), 4),
            "p90":    round(vals[int(n * 0.90)], 4),
            "p99":    round(vals[min(int(n * 0.99), n - 1)], 4),
            "min":    round(vals[0], 4),
            "max":    round(vals[-1], 4),
        }

    throughput_tps = round(len(all_turns) / wall_seconds, 3) if wall_seconds > 0 else 0.0

    return {
        "n_users":         n_users,
        "n_users_ok":      n_users_ok,
        "n_errors":        n_errors,
        "n_turns":         len(all_turns),
        "wall_seconds":    round(wall_seconds, 3),
        "throughput_tps":  throughput_tps,
        "ttft":            _stats(ttft_vals),
        "e2e":             _stats(e2e_vals),
        "raw_turns":       all_turns,
    }


# ══════════════════════════════════════════════════════════════════════════════
# THROUGHPUT TEST
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.live
async def test_throughput_ramp(live_server):
    """
    Ramps concurrent users through THROUGHPUT_LEVELS, recording per-level stats.

    Determines:
      max_sustainable_concurrency — last level within both TTFT and E2E thresholds
      breakpoint                  — first level that violates a threshold (None if none)

    Saves to evals/results/throughput_results.json and generates three plots.
    """
    level_results = []
    max_sustainable = None
    breakpoint_level = None

    for n_users in THROUGHPUT_LEVELS:
        print(f"\n  [Throughput] concurrency={n_users} …", flush=True)
        data = await _run_concurrency_level(n_users)

        ttft_med = data["ttft"]["median"] if data["ttft"] else float("inf")
        e2e_med  = data["e2e"]["median"]  if data["e2e"]  else float("inf")

        within_ttft = ttft_med <= TTFT_MEDIAN_LIMIT_S
        within_e2e  = e2e_med  <= E2E_MEDIAN_LIMIT_S
        sustainable = within_ttft and within_e2e

        data["ttft_within_threshold"] = within_ttft
        data["e2e_within_threshold"]  = within_e2e
        data["sustainable"]           = sustainable

        level_results.append(data)

        print(
            f"    users={n_users}  turns={data['n_turns']}  "
            f"tps={data['throughput_tps']}  "
            f"TTFT_med={ttft_med}s ({'✓' if within_ttft else '✗'})  "
            f"E2E_med={e2e_med}s ({'✓' if within_e2e else '✗'})"
        )

        if sustainable:
            max_sustainable = n_users
        elif breakpoint_level is None:
            breakpoint_level = n_users

    # ── Summary stats ──────────────────────────────────────────────────────────
    summary = {
        "throughput_levels":         THROUGHPUT_LEVELS,
        "ttft_limit_s":              TTFT_MEDIAN_LIMIT_S,
        "e2e_limit_s":               E2E_MEDIAN_LIMIT_S,
        "max_sustainable_concurrency": max_sustainable,
        "breakpoint":                breakpoint_level,
        "per_level":                 [
            {k: v for k, v in d.items() if k != "raw_turns"}
            for d in level_results
        ],
        "raw_per_level":             level_results,
    }

    path = os.path.join(RESULTS_DIR, "throughput_results.json")
    with open(path, "w") as f:
        json.dump(summary, f, indent=2)

    print(f"\n[Throughput Summary]")
    print(f"  max_sustainable_concurrency = {max_sustainable}")
    print(f"  breakpoint                  = {breakpoint_level}")
    print(f"  → {path}")

    # ── Plots ──────────────────────────────────────────────────────────────────
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        report_dir = os.path.join(os.path.dirname(RESULTS_DIR), "report")
        os.makedirs(report_dir, exist_ok=True)

        levels       = [d["n_users"]          for d in level_results]
        ttft_meds    = [d["ttft"]["median"] if d["ttft"] else None for d in level_results]
        e2e_meds     = [d["e2e"]["median"]  if d["e2e"]  else None for d in level_results]
        tps_vals     = [d["throughput_tps"]   for d in level_results]

        def _plot_metric(y_vals, threshold, ylabel, title, fname, threshold_label):
            fig, ax = plt.subplots(figsize=(8, 5))
            ax.plot(levels, y_vals, marker="o", linewidth=2, label=ylabel)
            ax.axhline(threshold, color="red", linestyle="--",
                       linewidth=1.5, label=f"Threshold ({threshold_label}={threshold}s)")
            ax.set_xlabel("Concurrent Users")
            ax.set_ylabel(ylabel)
            ax.set_title(title)
            ax.set_xticks(levels)
            ax.legend()
            ax.grid(axis="y", linestyle="--", alpha=0.5)
            fig.tight_layout()
            p = os.path.join(report_dir, fname)
            fig.savefig(p, dpi=120)
            plt.close(fig)
            print(f"  Plot saved → {p}")

        _plot_metric(
            ttft_meds, TTFT_MEDIAN_LIMIT_S,
            "Median TTFT (s)", "TTFT vs Concurrency", "throughput_ttft.png",
            "TTFT_MEDIAN_LIMIT_S",
        )
        _plot_metric(
            e2e_meds, E2E_MEDIAN_LIMIT_S,
            "Median E2E (s)", "E2E Latency vs Concurrency", "throughput_e2e.png",
            "E2E_MEDIAN_LIMIT_S",
        )

        # Throughput (turns/sec) — no threshold line
        fig, ax = plt.subplots(figsize=(8, 5))
        ax.bar(levels, tps_vals, width=0.6)
        ax.set_xlabel("Concurrent Users")
        ax.set_ylabel("Turns / Second")
        ax.set_title("Throughput vs Concurrency")
        ax.set_xticks(levels)
        ax.grid(axis="y", linestyle="--", alpha=0.5)
        fig.tight_layout()
        tps_path = os.path.join(report_dir, "throughput_tps.png")
        fig.savefig(tps_path, dpi=120)
        plt.close(fig)
        print(f"  Plot saved → {tps_path}")

    except ImportError:
        print("  matplotlib not installed — skipping plots")

    # ── Assertion: at least concurrency=1 must be sustainable ─────────────────
    assert max_sustainable is not None, (
        "Server could not sustain even a single concurrent user within TTFT/E2E thresholds"
    )
