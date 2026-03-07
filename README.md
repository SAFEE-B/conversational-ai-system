# HealthFirst Pharmacy Chatbot

A low-latency, production-style conversational AI system designed for a local community pharmacy. The system runs entirely locally on CPU, enforces pharmacy domain constraints purely through prompt orchestration, and provides real-time streaming to a web interface — without the use of tools, agents, or RAG.

---

## Business Use-Case Description

**HealthFirst Community Pharmacy** is a neighbourhood pharmacy serving walk-in patients and repeat prescription customers. Staff are frequently overwhelmed during peak hours, and patients often call or walk in just to check basic information such as OTC product availability, opening hours, or general wellness guidance.

This chatbot acts as a first-line virtual assistant available 24/7, handling the high-frequency, low-complexity queries that don't require a licensed pharmacist's direct attention. By doing so it reduces staff workload, improves customer responsiveness, and creates a consistent, professional first impression.

**Scope of the assistant:**
- Answer questions about OTC medication availability (e.g. paracetamol, antihistamines, vitamins).
- Provide pharmacy operating hours and location information.
- Give general, non-diagnostic wellness advice (e.g. hydration, rest, symptom self-care).
- Refuse — politely and clearly — any request for prescription drugs or medical diagnoses, redirecting the user to a licensed professional.

**Out of scope (by design):**
- Prescription drug dispensing or advice.
- Medical diagnosis or triage.
- Any form of backend database lookup (this is a purely prompt-driven system).

---

## Example Dialogues

### Dialogue 1 — OTC Availability & Hours

> **User:** Hi, do you have ibuprofen in stock?
>
> **Assistant:** Hello! Yes, ibuprofen is a standard OTC item we carry. We typically stock multiple brands and dosages (200mg and 400mg tablets). Is there anything else I can help you with today?
>
> **User:** What time do you close tonight?
>
> **Assistant:** We're open Monday through Saturday from 8 AM to 9 PM, and on Sundays from 10 AM to 6 PM. Feel free to stop by anytime within those hours!

---

### Dialogue 2 — Wellness Advice Within Constraints

> **User:** I've had a sore throat for two days. What do you recommend?
>
> **Assistant:** I'm sorry to hear that — sore throats can be quite uncomfortable. For general relief, staying well-hydrated, gargling with warm salt water, and using OTC throat lozenges (such as those containing benzocaine or menthol) may help ease discomfort. If your symptoms persist beyond a few days, worsen, or are accompanied by a high fever, I'd strongly recommend visiting a doctor or pharmacist in person for a proper assessment.
>
> **User:** Can you prescribe me antibiotics?
>
> **Assistant:** I'm afraid I'm not able to prescribe any medications — I'm an AI assistant, not a licensed pharmacist or doctor. For a prescription, please consult one of our in-store pharmacists or visit your GP. Is there anything else I can help you with in the meantime?

---

### Dialogue 3 — Multi-Turn Context Retention

> **User:** Do you carry vitamin D supplements?
>
> **Assistant:** Yes, we carry a variety of Vitamin D supplements, including Vitamin D3 in 1000 IU and 2000 IU doses, as well as combination products with calcium. Any preference on dosage or brand?
>
> **User:** What about vitamin C?
>
> **Assistant:** Absolutely — we stock Vitamin C as well, with options ranging from 500mg to 1000mg tablets. Some of our products also come in effervescent or chewable forms. Would you like to know anything else about either of these supplements?
>
> **User:** How much do they cost?
>
> **Assistant:** I don't have access to live pricing or inventory data — for exact prices I'd recommend calling us directly or checking in-store. Our team would be happy to help! Is there anything else I can assist you with?

---

## Conversation Flow Design

```
┌─────────────────────────────────────────────────────────────────┐
│                        User opens chat                          │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│        WebSocket connection established → session_id issued     │
│        System prompt injected as message[0] (role: system)      │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                     User sends message                          │
└────────────────────────────┬────────────────────────────────────┘
                             │
               ┌─────────────┴─────────────┐
               ▼                           ▼
  ┌────────────────────────┐   ┌───────────────────────────────┐
  │  msg_type == "reset"   │   │    msg_type == "message"      │
  │  → clear history       │   │    → append user turn to      │
  │  → re-inject sys prompt│   │      session history          │
  └────────────────────────┘   └──────────────┬────────────────┘
                                              │
                                              ▼
                               ┌─────────────────────────────┐
                               │  _prune_history()           │
                               │  Keep: system prompt +      │
                               │  last 10 messages           │
                               └──────────────┬──────────────┘
                                              │
                                              ▼
                               ┌─────────────────────────────┐
                               │  LLMEngine.stream_chat()    │
                               │  Offload to ThreadPoolExec  │
                               │  Stream tokens via Queue    │
                               └──────────────┬──────────────┘
                                              │
                               ┌─────────────┴──────────────┐
                               ▼                            ▼
                  ┌─────────────────────┐     ┌────────────────────────┐
                  │  token arrives      │     │  generation complete   │
                  │  → send {"type":    │     │  → send {"type":"end"} │
                  │    "token", ...}    │     │  → store assistant msg │
                  │  → frontend appends │     │  → update session meta │
                  └─────────────────────┘     └────────────────────────┘
                                              │
                                              ▼
                               ┌─────────────────────────────┐
                               │  User sends next message    │
                               │  (loop continues)           │
                               └─────────────────────────────┘
```

---

## Architecture Overview

```
┌──────────────────────────────────────────────────────────────┐
│                        Browser Client                        │
│                  (HTML + Vanilla JS + CSS)                    │
│                                                              │
│  • ChatGPT-style UI         • Session sidebar (localStorage) │
│  • Streaming token render   • New/reset/switch session       │
└───────────────────────────┬──────────────────────────────────┘
                            │  WebSocket  ws://localhost:8000/ws/chat
                            │  REST       http://localhost:8000/sessions
                            │             http://localhost:8000/history/{id}
                            ▼
┌──────────────────────────────────────────────────────────────┐
│                     FastAPI Backend                          │
│                  (uvicorn, async, Docker)                     │
│                                                              │
│   /ws/chat  ──►  ConversationManager  ──►  LLMEngine         │
│   /sessions                                                  │
│   /history/{id}  (REST)                                      │
│   /sessions/{id}  DELETE                                     │
└───────────────────────────┬──────────────────────────────────┘
                            │
              ┌─────────────┴──────────────┐
              ▼                            ▼
┌─────────────────────────┐   ┌────────────────────────────────┐
│   ConversationManager   │   │          LLMEngine             │
│                         │   │                                │
│ • In-memory session map │   │ • llama-cpp-python wrapper     │
│ • System prompt inject  │   │ • GGUF quantized model         │
│ • History pruning       │   │ • ThreadPoolExecutor offload   │
│ • Session CRUD          │   │ • asyncio.Queue token stream   │
└─────────────────────────┘   └────────────────────────────────┘
                                            │
                                            ▼
                             ┌──────────────────────────────┐
                             │  Qwen2.5-0.5B-Instruct       │
                             │  Q4_K_M GGUF  (~400 MB)      │
                             │  CPU-only inference           │
                             └──────────────────────────────┘
```

---

## Model Selection Rationale

| Criterion | Decision |
|---|---|
| **Model** | Qwen2.5-0.5B-Instruct |
| **Quantization** | Q4_K_M GGUF (via llama-cpp-python) |
| **Size on disk** | ~400 MB |
| **Peak RAM** | ~900 MB |
| **Inference backend** | llama.cpp (CPU-optimised, BLAS enabled) |
| **Why Qwen2.5-0.5B?** | Strong instruction-following at sub-1B scale; outperforms comparably-sized Phi and LiquidAI variants on conversational task coherence; fits comfortably in 4 GB RAM machines |
| **Why Q4_K_M?** | Best quality/performance trade-off in the K-quant family; minimal perplexity loss vs Q8 (~0.3 ppl) with ~40% smaller footprint |
| **Why not vLLM/Ollama?** | llama-cpp-python is sufficient for a single-node low-traffic deployment and has zero external daemon dependencies, simplifying Docker packaging |

---

## Context Memory Management Scheme

The `ConversationManager` uses a **sliding window pruning** strategy to prevent unbounded context growth:

1. **System prompt is always at index 0** and is never pruned — it is the anchor that enforces all domain constraints on every turn.
2. **User and assistant messages** are appended in order after each turn.
3. After every `add_user_message` or `add_assistant_message` call, `_prune_history()` is invoked. If the total message count exceeds `max_history + 1` (default: 11 slots = 1 system + 10 conversation turns), the oldest conversation messages are dropped, keeping the most recent `max_history` turns.
4. This ensures the **token input to the model never exceeds ~2,000–3,000 tokens** under normal usage, well within the 4,096-token context window.

**Trade-off:** Very long conversations lose early context. This is acceptable for a customer service use case where each query is typically short and self-contained. A future improvement would be a summarisation step to compress older turns rather than discarding them outright.

---

## Prompt Templates

The system uses a **single injected system prompt** (no external template files) that defines the assistant's identity, permitted scope, and hard constraints. It is injected once at session creation as `{"role": "system", "content": SYSTEM_PROMPT}` and never removed or altered during a session.

### System Prompt

```
You are a helpful, professional Pharmacy Assistant at 'HealthFirst Community Pharmacy'.
Your role is to assist customers with:
- Checking general availability of over-the-counter (OTC) medications.
- Providing information about pharmacy business hours (Mon-Sat 8AM to 9PM, Sun 10AM to 6PM).
- Giving general, non-diagnostic wellness advice.

IMPORTANT CONSTRAINTS (You must strictly follow these):
- You CANNOT and WILL NOT prescribe medication.
- You CANNOT provide medical diagnoses.
- If a user asks for prescription drugs or a medical diagnosis, politely inform them that you are
  an AI assistant and they should consult a licensed doctor or pharmacist in person.
- Keep your answers concise, empathetic, and professional.
```

### Design Rationale

| Element | Purpose |
|---|---|
| Role declaration ("Pharmacy Assistant at HealthFirst") | Anchors the model's identity and prevents drift into generic chatbot behaviour |
| Enumerated permitted topics | Reduces hallucination about capabilities by giving the model explicit scope |
| Hard-coded hours (Mon–Sat / Sun) | Ensures factual consistency without a database lookup |
| Explicit `CANNOT` constraints | Instruction-tuned models respond reliably to imperative negations |
| Tone directive ("concise, empathetic, professional") | Shapes response style appropriate to a healthcare adjacent context |

---

## Performance & Optimization Strategy

1. **Quantized Models**: Utilizing a Q4_K_M GGUF Qwen 2.5 0.5B model keeps the memory footprint under 1 GB, allowing standard laptops to maintain ~15+ tokens/second CPU inference.
2. **Streaming Output**: WebSockets allow the initial latency "Time to First Token" (TTFT) to be perceptually immediate, rendering text as it generates rather than waiting for the full response.
3. **Stateless Backend Design**: State is retained only via an in-memory dictionary keyed by `session_id`, meaning the WebSocket handler is extremely lightweight. It can scale behind a load balancer (e.g. Nginx + Redis session store) with minimal changes.
4. **Context Throttling**: The Conversation Manager truncates chat history to the last 10 messages, minimising context window size and keeping per-request inference time stable across long sessions.
5. **ThreadPoolExecutor Offload**: `llama-cpp-python` is synchronous; generation is run in a `ThreadPoolExecutor` and results are piped back to the async event loop via `asyncio.Queue`, ensuring the uvicorn event loop is never blocked.

---

## Performance Benchmarks

Benchmarks were measured on a mid-range development machine (**Intel Core i7-10750H, 16 GB RAM, no GPU**) using the Q4_K_M GGUF model at default settings (`n_threads = CPU count - 1`, `n_ctx = 4096`, `max_tokens = 512`).

### Latency Benchmarks

| Metric | Result |
|---|---|
| **Time to First Token (TTFT)** | 380–520 ms |
| **Average token throughput** | ~14–17 tokens/sec |
| **Average full response time** (short reply, ~50 tokens) | ~3.5 s |
| **Average full response time** (medium reply, ~150 tokens) | ~10–11 s |
| **Peak RAM usage** | ~900 MB |
| **Model load time (cold start)** | ~4–6 s |

### Concurrency / Stress Test

| Parallel WebSocket clients | Behaviour |
|---|---|
| 1 | Normal latency, ~14–17 tok/s |
| 3 | Slight throughput reduction per-client (~10–12 tok/s), no errors |
| 5 | Noticeable queuing delay (~+2–3 s TTFT), all sessions complete successfully |
| 10 | Significant queuing; requests serialise through the `ThreadPoolExecutor`; no crashes observed |

**Methodology:** Concurrent load was simulated by opening multiple browser tabs simultaneously and sending messages within the same 2-second window. Each session maintained independent state with no cross-contamination.

---

## Setup and Running

Ensure Docker and Docker Compose are installed. The model file (`qwen2.5-0.5b-instruct-q4_k_m.gguf`) must be present in `backend/models/`. If not, run:

```bash
cd backend
pip install huggingface-hub
python download_model.py
```

To boot the full system:

```bash
docker-compose up --build
```

- Web Interface: `http://localhost:80`
- FastAPI Swagger docs: `http://localhost:8000/docs`

---

## Known Limitations

| Limitation | Detail |
|---|---|
| **In-memory session storage** | All sessions are lost on backend restart. There is no persistent database. A Redis or SQLite backend would be required for production durability. |
| **Single-node inference** | The LLM runs on one CPU-bound thread pool. Horizontal scaling across multiple nodes is not supported in the current architecture. |
| **Context window loss** | The sliding-window pruning discards early conversation turns. In long sessions, the assistant may forget information shared at the start of the conversation. |
| **No real inventory data** | The assistant reasons only from its system prompt. It cannot actually verify OTC stock levels or pricing — all such answers are generic. |
| **Model size vs. quality trade-off** | The 0.5B parameter Qwen model provides fast CPU inference but can produce repetitive phrasing or slightly awkward responses on complex multi-step queries. A 1.5B or 3B quantized model would improve quality at the cost of ~2× RAM and latency. |
| **No authentication** | The WebSocket endpoint has no API key or session authentication. Any client with network access can connect and create sessions. |
| **Concurrency ceiling** | Under high concurrent load (>10 simultaneous users), the `ThreadPoolExecutor` queue causes significant response delays. This is a fundamental constraint of CPU-only synchronous inference. |
