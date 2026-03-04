import json
import statistics
import time
import urllib.request


def post_json(url: str, payload: dict) -> dict:
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=600) as resp:
        return json.loads(resp.read().decode("utf-8"))


def main() -> None:
    url = "http://127.0.0.1:8000/api/chat"
    topic = "transformers and attention"
    n = 5

    latencies = []
    history = []
    message = "Hi, I'm ready to start the interview. Please begin."

    for i in range(n):
        payload = {"topic": topic, "history": history, "message": message}
        t0 = time.perf_counter()
        out = post_json(url, payload)
        elapsed = time.perf_counter() - t0

        if "error" in out:
            raise RuntimeError(out["error"])

        # Prefer server-reported latency if available
        lat = float(out.get("latency_seconds", elapsed))
        latencies.append(lat)

        # Continue multi-turn via the returned history
        history = out["history"]
        message = "Thanks. Next question, please."

        print(f"Run {i+1}/{n}: {lat:.3f}s — {out['question']}")

    print("\nSummary")
    print(f"n={n}")
    print(f"min={min(latencies):.3f}s")
    print(f"p50={statistics.median(latencies):.3f}s")
    print(f"mean={statistics.mean(latencies):.3f}s")
    print(f"max={max(latencies):.3f}s")


if __name__ == "__main__":
    main()

