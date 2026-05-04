"""
Master Eval Runner
===================
Single entry-point that runs the full evaluation suite and generates a report.

Usage:
    python evals/run_evals.py                   # full suite (server must be running)
    python evals/run_evals.py --no-live         # correctness-only, no server needed
    python evals/run_evals.py --no-performance  # skip throughput/latency tests
    python evals/run_evals.py --report-only     # regenerate report from existing results

Env vars:
    CHATBOT_WS_URL    — override WebSocket URL  (default: ws://localhost:8000/ws/chat)
    CHATBOT_BASE_URL  — override HTTP base URL  (default: http://localhost:8000)
    GOOGLE_API_KEY    — required for LLM-as-judge tests (RAG faithfulness, conversational)
    JUDGE_MODEL       — override judge model    (default: gemini-2.5-flash-preview-05-20)
"""
import argparse
import os
import subprocess
import sys
import time

_EVALS_DIR = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT  = os.path.dirname(_EVALS_DIR)

# Load .env from repo root (so GOOGLE_API_KEY etc. propagate to subprocess calls)
try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(_REPO_ROOT, ".env"))
except ImportError:
    pass


def _run_pytest(args: list[str], label: str) -> int:
    """Run pytest with given args; print header; return exit code."""
    print(f"\n{'=' * 60}")
    print(f"  {label}")
    print(f"{'=' * 60}")
    cmd = [sys.executable, "-m", "pytest"] + args + ["-v", "--tb=short"]
    result = subprocess.run(cmd, cwd=_EVALS_DIR)
    return result.returncode


def main():
    parser = argparse.ArgumentParser(description="HealthFirst chatbot eval runner")
    parser.add_argument("--no-live",         action="store_true", help="Skip tests that require the live server")
    parser.add_argument("--no-performance",  action="store_true", help="Skip latency and throughput tests")
    parser.add_argument("--report-only",     action="store_true", help="Regenerate report from existing JSON results")
    args = parser.parse_args()

    failures = []

    if not args.report_only:
        # ── 1. Correctness — no server required ───────────────────────────────
        rc = _run_pytest(
            ["correctness/test_crm.py",   "-m", "not live"],
            "CRM Tool — direct unit tests",
        )
        if rc: failures.append("crm-unit")

        rc = _run_pytest(
            ["correctness/test_tools.py", "-m", "not live"],
            "Pharmacy Tools — direct unit tests",
        )
        if rc: failures.append("tools-unit")

        rc = _run_pytest(
            ["correctness/test_rag.py",   "-m", "not live"],
            "RAG Retrieval metrics (no server)",
        )
        if rc: failures.append("rag-retrieval")

        # ── 2. Live correctness & performance ─────────────────────────────────
        if not args.no_live:
            rc = _run_pytest(
                ["correctness/test_crm.py",            "-m", "live"],
                "CRM Tool — live invocation accuracy",
            )
            if rc: failures.append("crm-live")

            rc = _run_pytest(
                ["correctness/test_tools.py",           "-m", "live"],
                "Pharmacy Tools — live invocation accuracy",
            )
            if rc: failures.append("tools-live")

            rc = _run_pytest(
                ["correctness/test_rag.py",             "-m", "live"],
                "RAG Faithfulness (LLM-as-judge)",
            )
            if rc: failures.append("rag-faithfulness")

            rc = _run_pytest(
                ["correctness/test_conversational.py"],
                "Conversational Quality (LLM-as-judge)",
            )
            if rc: failures.append("conversational")

            if not args.no_performance:
                rc = _run_pytest(
                    ["performance/test_latency.py", "-s"],
                    "Latency — TTFT / inter-token / E2E",
                )
                if rc: failures.append("latency")

                rc = _run_pytest(
                    ["performance/test_throughput.py", "-s"],
                    "Throughput / Concurrency ramp",
                )
                if rc: failures.append("throughput")

    # ── 3. Generate report ─────────────────────────────────────────────────────
    print(f"\n{'=' * 60}")
    print("  Generating eval report")
    print(f"{'=' * 60}")
    sys.path.insert(0, _EVALS_DIR)
    from report.generate_report import generate  # noqa: E402
    md_path, json_path = generate()
    print(f"  Report  -> {md_path}")
    print(f"  Summary -> {json_path}")

    # ── 4. Final summary ───────────────────────────────────────────────────────
    print(f"\n{'=' * 60}")
    if failures:
        print(f"  FAILED suites: {', '.join(failures)}")
        print(f"{'=' * 60}\n")
        sys.exit(1)
    else:
        print("  All suites passed.")
        print(f"{'=' * 60}\n")


if __name__ == "__main__":
    main()
