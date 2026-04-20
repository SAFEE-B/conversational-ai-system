# HealthFirst Pharmacy Chatbot

A low-latency, production-style conversational AI system for a local community pharmacy. The system runs entirely locally on CPU, combining **Retrieval-Augmented Generation (RAG)** and **four callable tools** with a quantized local LLM to answer pharmacy-specific questions accurately and in real time.

---

## Business Use-Case Description

**HealthFirst Community Pharmacy** is a neighbourhood pharmacy serving walk-in patients and repeat prescription customers. Staff are frequently overwhelmed during peak hours, and patients often call or walk in just to check basic information such as OTC product availability, opening hours, drug interactions, or dosage guidance.

This chatbot acts as a first-line virtual assistant available 24/7, handling high-frequency queries that do not require a licensed pharmacist's direct attention. RAG ensures answers are grounded in real pharmacy documents; tools provide precise, patient-specific calculations and personalised service.

**Scope of the assistant:**
- Answer questions about OTC medication availability, uses, and side effects (RAG + Medication Info Tool).
- Provide pharmacy operating hours and policies (RAG retrieval).
- Check drug-drug interactions with severity ratings (Drug Interaction Tool).
- Calculate weight- and age-appropriate OTC dosages (Dosage Calculator Tool).
- Greet returning customers by name and recall preferences (CRM Tool).
- Give general, non-diagnostic wellness advice (RAG retrieval).
- Refuse — politely and clearly — any request for prescription drugs or medical diagnoses.

**Out of scope (by design):**
- Prescription drug dispensing or advice.
- Medical diagnosis or triage.
- Live inventory or pricing lookups.

---

## Architecture Overview

```
┌──────────────────────────────────────────────────────────────────────┐
│                          Browser Client                              │
│                    (HTML + Vanilla JS + CSS)                          │
│                                                                      │
│  • ChatGPT-style UI          • Session sidebar (localStorage)        │
│  • Streaming token render    • Voice input/output (ASR / TTS)        │
└───────────────────────────────┬──────────────────────────────────────┘
                                │  WebSocket  ws://localhost:8000/ws/chat
                                │  REST       /sessions  /history/{id}
                                ▼
┌──────────────────────────────────────────────────────────────────────┐
│                         FastAPI Backend                              │
│                      (uvicorn · async · Docker)                      │
│                                                                      │
│   /ws/chat ──► ConversationManager ──► _enrich_message()            │
│                                              │                       │
│                              ┌───────────────┴──────────────┐        │
│                              ▼                              ▼        │
│                    ┌──────────────────┐   ┌──────────────────────┐  │
│                    │  RAG Retriever   │   │  Tool Orchestrator   │  │
│                    │  (concurrent)    │   │  (concurrent)        │  │
│                    └────────┬─────────┘   └──────────┬───────────┘  │
│                             │                        │              │
│                             └──────────┬─────────────┘              │
│                                        ▼                            │
│                            build_augmented_messages()               │
│                                        │                            │
│                                        ▼                            │
│                              LLMEngine.stream_chat()                │
└──────────────────────────────────────────────────────────────────────┘
                                         │
               ┌─────────────────────────┴──────────────────────────┐
               ▼                                                     ▼
┌──────────────────────────┐                          ┌─────────────────────────┐
│    DocumentRetriever     │                          │    ToolOrchestrator     │
│                          │                          │                         │
│ • all-MiniLM-L6-v2 embed │                          │ • Intent detection      │
│ • ChromaDB cosine search │                          │ • CRM Tool (SQLite)     │
│ • Top-3 chunk retrieval  │                          │ • Drug Interaction      │
│ • LRU query cache        │                          │ • Dosage Calculator     │
└──────────────────────────┘                          │ • Medication Info       │
                                                      └─────────────────────────┘
                                         │
                                         ▼
                          ┌──────────────────────────────┐
                          │  Qwen2.5-0.5B-Instruct        │
                          │  Q4_K_M GGUF  (~400 MB)       │
                          │  CPU-only · llama-cpp-python   │
                          └──────────────────────────────┘
```

---

## Repository Structure

```
conversational-ai-system/
├── backend/
│   ├── main.py                    # FastAPI app, WebSocket endpoint, RAG+tool wiring
│   ├── conversation_manager.py    # Session management, SNR filtering, prompt augmentation
│   ├── llm_engine.py              # llama-cpp-python wrapper, async streaming
│   ├── tool_orchestrator.py       # Intent detection → tool dispatch → result formatting
│   ├── voice_engine.py            # Vosk ASR + Piper TTS (local, CPU)
│   ├── retrieval/
│   │   ├── indexer.py             # Offline: chunk → embed → store in ChromaDB
│   │   └── retriever.py           # Runtime: embed query → cosine search → top-k chunks
│   ├── tools/
│   │   ├── crm_tool.py            # SQLite CRM: get/create/update patient records
│   │   ├── drug_interaction.py    # Local DB of 20+ drug-drug interactions
│   │   ├── dosage_calculator.py   # Weight/age-based OTC dosing for 10 medications
│   │   └── medication_info.py     # Structured info lookup for 13 OTC medications
│   ├── models/                    # GGUF model + voice models (git-ignored)
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── index.html                 # Chat UI
│   ├── script.js                  # WebSocket client, streaming, voice, sessions
│   ├── style.css
│   └── Dockerfile
├── documents/                     # 55 pharmacy RAG documents (.txt)
├── scripts/
│   ├── index_documents.py         # CLI: run offline indexing pipeline
│   └── generate_documents.py      # Script that generated the document corpus
├── chroma_db/                     # ChromaDB vector store (created after indexing)
├── crm.db                         # SQLite CRM database (created at runtime)
├── docker-compose.yml
├── .env.example
└── README.md
```

---

## RAG (Retrieval-Augmented Generation)

### Document Corpus

55 pharmacy documents covering:

| Category | Count | Examples |
|---|---|---|
| OTC Medication Guides | 20 | Acetaminophen, Ibuprofen, Omeprazole, Melatonin, Omega-3 |
| Health Condition Guides | 13 | Headaches, Cold & Flu, Allergies, Acid Reflux, Wound Care |
| Pharmacy Policies | 10 | Refill policy, Insurance, Medication disposal, Storage guidelines |
| Drug Safety | 9 | Drug interactions overview, Pregnancy safety, Elderly medication safety |
| Wellness & First Aid | 3 | First aid kit essentials, Vitamin supplements, Healthy lifestyle |

### Indexing Pipeline

```
Documents (.txt) → Chunker (512 words, 64-word overlap) → Embedder (all-MiniLM-L6-v2)
    → ChromaDB (cosine similarity, persistent)
```

Run once before starting the server:

```bash
python scripts/index_documents.py
# Optional flags:
python scripts/index_documents.py --docs-dir ./documents --chunk-size 512 --overlap 64 --chroma-dir ./chroma_db
```

### Retrieval at Runtime

On every message:
1. Query is embedded with `all-MiniLM-L6-v2` (same model as indexing)
2. Top-3 most similar chunks retrieved via cosine search from ChromaDB
3. Chunks formatted into a context block and injected before the LLM call
4. Query-level LRU cache avoids re-embedding identical or recent queries

| Property | Value |
|---|---|
| Embedding model | `all-MiniLM-L6-v2` (Sentence-Transformers) |
| Vector store | ChromaDB (persistent, CPU-compatible) |
| Similarity metric | Cosine similarity |
| Top-k retrieved | 3 chunks |
| Chunk size | 512 words with 64-word overlap |

---

## Tools

All four tools are called **before** LLM generation begins. Results are injected into the prompt as context, preserving token-by-token streaming.

### Tool 1 — CRM Tool *(Mandatory)*

Stores and retrieves patient information across sessions using a persistent SQLite database.

| Property | Details |
|---|---|
| **Name** | `crm_tool` |
| **Backend** | SQLite via `aiosqlite` |
| **Actions** | `get_user`, `create_user`, `update_user` |
| **Fields** | `name`, `contact`, `preferences`, `last_visit`, `interaction_history` |

**Example:**
```
User:  "Hi, my name is Sarah."
→ crm_tool.create_user(user_id=session_id, name="Sarah")
→ Bot: "Welcome to HealthFirst, Sarah! How can I help you today?"

User:  "Do you remember me?" (on return visit)
→ crm_tool.get_user(user_id=session_id)
→ Bot: "Of course, Sarah! Welcome back. Your last visit was April 18th."
```

### Tool 2 — Drug Interaction Checker

Local database of 20+ clinically significant drug-drug interactions. No external API required.

| Property | Details |
|---|---|
| **Name** | `check_drug_interaction` |
| **Input** | `drug1: string`, `drug2: string` |
| **Output** | `severity` (major/moderate/minor/unknown), `description`, `recommendation` |
| **Coverage** | Warfarin, NSAIDs, alcohol, MAOIs, statins, PPIs, antihistamines, and more |

**Example:**
```
User:  "Is it safe to take warfarin and ibuprofen together?"
→ check_drug_interaction(drug1="warfarin", drug2="ibuprofen")
→ severity: MAJOR — increased bleeding risk
→ Bot: "Taking warfarin and ibuprofen together is a major interaction. NSAIDs
        significantly increase bleeding risk. Please use acetaminophen instead
        and consult your physician."
```

### Tool 3 — Dosage Calculator

Calculates weight- and age-appropriate OTC doses using standard evidence-based dosing tables.

| Property | Details |
|---|---|
| **Name** | `calculate_dosage` |
| **Input** | `medication: string`, `age_years: number`, `weight_kg: number (optional)` |
| **Output** | `recommended_dose_mg`, `frequency`, `max_daily_dose_mg`, `notes` |
| **Medications** | Acetaminophen, Ibuprofen, Naproxen, Diphenhydramine, Loratadine, Cetirizine, Guaifenesin, Loperamide, Omeprazole |

**Example:**
```
User:  "What dose of ibuprofen for a 4-year-old weighing 16 kg?"
→ calculate_dosage(medication="ibuprofen", age_years=4, weight_kg=16)
→ dose: 120 mg every 6–8 hours, max 640 mg/day
→ Bot: "For a 4-year-old weighing 16 kg, the recommended ibuprofen dose is
        120 mg every 6–8 hours. Do not exceed 640 mg in 24 hours, and always
        take with food. Please consult a pharmacist to confirm."
```

### Tool 4 — Medication Info Lookup

Returns structured medication information from a local database of 13 common OTC drugs.

| Property | Details |
|---|---|
| **Name** | `get_medication_info` |
| **Input** | `medication_name: string` (brand or generic) |
| **Output** | `uses`, `side_effects`, `key_warnings`, `OTC availability`, `forms available` |
| **Coverage** | Acetaminophen, Ibuprofen, Aspirin, Diphenhydramine, Loratadine, Cetirizine, Omeprazole, Pseudoephedrine, Guaifenesin, Loperamide, Melatonin, Hydrocortisone, Clotrimazole |

**Example:**
```
User:  "What are the side effects of omeprazole?"
→ get_medication_info(medication_name="omeprazole")
→ Bot: "Omeprazole (Prilosec) is a proton pump inhibitor used for frequent
        heartburn. Common side effects include headache, nausea, and diarrhea.
        With long-term use, watch for low magnesium and vitamin B12 deficiency.
        It's available OTC as a 20 mg delayed-release capsule."
```

---

## Conversation Flow Design

```
User message received
        │
        ▼
ConversationManager.add_user_message()
        │
        ▼
_enrich_message() — concurrent asyncio.gather()
  ├── RAG: embed query → ChromaDB top-3 chunks → format context block
  └── Tool: detect intent (regex/keyword) → call tool → format result
        │
        ▼
build_augmented_messages()
  └── Inject [RAG context + tool result] before last user message
        │
        ▼
LLMEngine.stream_chat(augmented_messages)
  └── ThreadPoolExecutor → asyncio.Queue → token stream
        │
        ▼
WebSocket: {"type":"tool_used", "tool":"..."} (if tool was called)
           {"type":"start"}
           {"type":"token", "content":"..."} × N
           {"type":"end"}
        │
        ▼
ConversationManager.add_assistant_message()
```

**Key design principle:** RAG retrieval and tool calls both complete *before* the LLM starts generating. The LLM receives one enriched prompt and streams a single response — no multi-pass or interrupted streaming.

---

## Context Memory Management

The `ConversationManager` uses two complementary strategies:

### 1. Sliding Window Pruning
After every turn, `_prune_history()` keeps the system prompt (index 0) plus the last `max_history` messages (default: 10). Older turns are dropped. This keeps input tokens well within the 4,096-token context window.

### 2. Signal-to-Noise (SNR) Filtering
When assembling the LLM context via `get_messages()`, the most recent 4 messages are always kept verbatim. Older user messages that match known filler phrases ("ok", "thanks", "sure", etc.) are silently dropped. This frees context budget for substantive content.

### 3. Prompt Augmentation (new)
`build_augmented_messages()` creates a non-destructive copy of the message list with RAG chunks and tool results prepended to the last user message. The raw session store is never mutated — only the LLM-facing view is enriched.

---

## System Prompt

```
You are a helpful, professional Pharmacy Assistant at 'HealthFirst Community Pharmacy'.
Your role is to assist customers with:
- Checking general availability of over-the-counter (OTC) medications.
- Providing information about pharmacy business hours (Mon-Sat 8AM to 9PM, Sun 10AM to 6PM).
- Giving general, non-diagnostic wellness advice.
- Answering questions about drug interactions, dosages, and medication details using retrieved information.
- Greeting returning customers by name using CRM records when available.

IMPORTANT CONSTRAINTS (You must strictly follow these):
- You CANNOT and WILL NOT prescribe medication.
- You CANNOT provide medical diagnoses.
- If a user asks for prescription drugs or a medical diagnosis, politely inform them that you are
  an AI assistant and they should consult a licensed doctor or pharmacist in person.
- Keep your answers concise, empathetic, and professional.
- When relevant pharmacy information or tool results are provided in the context, use them to give
  accurate, specific answers.
- Always add a disclaimer to consult a pharmacist or physician for personalised medical advice.
```

---

## Example Dialogues

### Dialogue 1 — Returning Customer (CRM Tool)

> **User:** Hi, my name is Sarah.
>
> **Assistant:** Welcome to HealthFirst Community Pharmacy, Sarah! It's great to have you here. How can I assist you today?
>
> **User:** Do you remember me?
>
> **Assistant:** Yes, I have your name on file, Sarah. How can I help you today?

---

### Dialogue 2 — Drug Interaction Check

> **User:** Is it safe to take ibuprofen and aspirin together?
>
> **Assistant:** Taking ibuprofen and aspirin together is generally not recommended. Ibuprofen can block aspirin's irreversible antiplatelet effect, which is important for cardiovascular protection. They also share GI risks — combined use significantly increases the chance of stomach bleeding. If you need pain relief alongside low-dose aspirin, acetaminophen is a safer alternative. Please consult our pharmacist before combining these.
>
> **User:** What about warfarin and ibuprofen?
>
> **Assistant:** This is a **major** interaction and should be avoided. Ibuprofen, like all NSAIDs, inhibits platelet function and can cause GI bleeding. Combined with warfarin, the risk of serious bleeding is significantly elevated. Please use acetaminophen for pain relief instead, and inform your prescribing physician. Our pharmacists at HealthFirst are also happy to help.

---

### Dialogue 3 — Dosage Calculation

> **User:** What is the correct dose of ibuprofen for a 4-year-old child weighing 16 kg?
>
> **Assistant:** For a 4-year-old weighing 16 kg, the recommended ibuprofen dose is **120 mg**, taken every 6–8 hours. The maximum daily dose is 640 mg. Always give ibuprofen with food or milk to reduce stomach upset, and do not use in children under 6 months. Please consult a pharmacist or physician to confirm dosing for your child.
>
> **User:** And how much acetaminophen can an adult take per day?
>
> **Assistant:** Adults can take **500 mg of acetaminophen** every 4–6 hours as needed, with a maximum of **4,000 mg per day**. If you drink alcohol regularly, keep the daily limit at 3,000 mg or less. Be sure to check all other medications you're taking for acetaminophen content to avoid accidentally exceeding the limit.

---

### Dialogue 4 — Medication Info (RAG + Tool)

> **User:** What is omeprazole used for?
>
> **Assistant:** Omeprazole (brand name: Prilosec OTC) is a **proton pump inhibitor (PPI)** used for frequent heartburn — specifically when symptoms occur two or more days per week. The OTC dose is 20 mg once daily before a meal for 14 consecutive days. Note that it is not for immediate relief — it takes 1–4 days to reach full effect. For occasional heartburn, an antacid like Tums or an H2 blocker like famotidine works faster.

---

### Dialogue 5 — Pharmacy Policy (RAG)

> **User:** What's the safest way to dispose of old medications?
>
> **Assistant:** The safest way is through a **DEA-authorized drug take-back program** — HealthFirst Pharmacy may have an in-store collection kiosk, and national take-back events are held twice a year. If no take-back is available, you can dispose of most medications at home by mixing them with coffee grounds or kitty litter, sealing the mixture in a bag, and placing it in the household trash. Do not flush medications unless they appear on the FDA's official Flush List (typically reserved for high-risk opioids). For sharps like needles, please use a certified sharps container — never put them in regular trash.

---

## Performance & Optimisation

| Strategy | Details |
|---|---|
| **Token streaming** | LLM generates tokens incrementally; WebSocket delivers them word-by-word for real-time rendering |
| **Concurrent enrichment** | RAG retrieval and tool calls run via `asyncio.gather()` — both complete before LLM starts, no sequential blocking |
| **Embedding + query cache** | `DocumentRetriever` maintains an in-memory LRU cache (256 entries) for repeated queries |
| **ThreadPoolExecutor offload** | Synchronous llama-cpp-python inference offloaded to thread pool; event loop remains responsive |
| **Async tool calls** | All tools implemented as `async` coroutines; no event-loop blocking |
| **SNR context filtering** | Filler messages pruned from older context; keeps effective token count low |
| **Sliding window pruning** | Hard cap of last 10 conversation turns keeps input tokens ≤ ~3,000 |

### Latency Benchmarks

Measured on **Intel Core i7-10750H, 16 GB RAM, no GPU**.

| Metric | Result |
|---|---|
| Time to First Token (TTFT) | 380–520 ms |
| Embedding + vector retrieval | ~150–200 ms |
| Tool call latency (local) | < 10 ms |
| Average token throughput | ~14–17 tokens/sec |
| Short reply (~50 tokens) | ~3.5 s |
| Medium reply (~150 tokens) | ~10–11 s |
| Peak RAM (model loaded) | ~900 MB |
| Model cold-start time | ~4–6 s |

---

## Setup Instructions

### Prerequisites
- Python 3.10+
- Docker and Docker Compose (for containerised run)

### 1. Clone and install dependencies

```bash
git clone <repo-url>
cd conversational-ai-system

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

pip install -r backend/requirements.txt
```

### 2. Download the LLM model

```bash
cd backend
python download_model.py
```

### 3. Configure environment variables

```bash
cp .env.example .env
# Edit .env if you want to change default paths
```

### 4. Index the document corpus *(run once)*

```bash
python scripts/index_documents.py
```

This embeds all 55 documents in `documents/` and saves the vector store to `chroma_db/`.

### 5. Run the backend

```bash
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 6. Serve the frontend

```bash
cd frontend
python3 -m http.server 8080
```

Open `http://localhost:8080` in your browser.

### 7. (Optional) Download voice models

```bash
cd backend
python download_voice_models.py
```

### Docker (full stack)

```bash
docker-compose up --build
```

- Frontend: `http://localhost:80`
- API docs: `http://localhost:8000/docs`

### Environment Variables

| Variable | Description | Default |
|---|---|---|
| `MODEL_PATH` | Path to the GGUF model file | `models/qwen2.5-0.5b-instruct-q4_k_m.gguf` |
| `CHROMA_PERSIST_DIR` | ChromaDB vector store directory | `./chroma_db` |
| `CRM_DB_PATH` | SQLite CRM database file path | `./crm.db` |
| `DOCS_DIR` | Document corpus directory | `./documents` |

---

## Model Selection

| Property | Details |
|---|---|
| **Model** | Qwen2.5-0.5B-Instruct |
| **Quantization** | Q4_K_M GGUF (via llama-cpp-python) |
| **Size on disk** | ~400 MB |
| **Peak RAM** | ~900 MB |
| **Inference backend** | llama.cpp (CPU-optimised, BLAS enabled) |
| **Why Qwen2.5-0.5B?** | Strong instruction-following at sub-1B scale; outperforms comparably-sized Phi variants on conversational coherence; fits comfortably in 4 GB RAM |
| **Why Q4_K_M?** | Best quality/speed trade-off in the K-quant family; minimal perplexity loss vs Q8 (~0.3 ppl) at ~40% smaller footprint |

---

## Known Limitations

| Limitation | Detail |
|---|---|
| **In-memory sessions** | Session history is lost on backend restart. CRM data (SQLite) and the vector store (ChromaDB) persist across restarts; conversation history does not. |
| **Intent detection is rule-based** | The tool orchestrator uses keyword/regex matching, not LLM-driven function calling. This is intentional for reliability with a 0.5B model. |
| **Tool database coverage** | The drug interaction and medication info databases cover common OTC medications only. Uncommon drugs return an "unknown" response. |
| **No real inventory data** | The assistant cannot verify live OTC stock levels or pricing — all availability answers are generic. |
| **Model size vs. quality** | The 0.5B Qwen model provides fast CPU inference but can produce slightly awkward responses on complex queries. A 1.5B–3B model would improve quality at ~2× RAM and latency. |
| **Concurrency ceiling** | Under heavy concurrent load (>10 simultaneous users), the ThreadPoolExecutor queue causes significant delays. CPU-only inference is the fundamental bottleneck. |
| **No authentication** | The WebSocket endpoint has no API key or session authentication. |
| **Embedding model limitations** | `all-MiniLM-L6-v2` is a general-purpose model. Domain-specific fine-tuning would improve retrieval precision for highly technical pharmacy queries. |
