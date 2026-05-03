"""Central configuration for the eval suite. Override via environment variables."""
import os

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ── Chatbot API ───────────────────────────────────────────────────────────────
CHATBOT_BASE_URL = os.environ.get("CHATBOT_BASE_URL", "http://localhost:8000")
CHATBOT_WS_URL   = os.environ.get("CHATBOT_WS_URL",   "ws://localhost:8000/ws/chat")

# ── Judge LLM (for LLM-as-judge correctness evals) ───────────────────────────
# Any OpenAI-compatible model string. Requires ANTHROPIC_API_KEY or OPENAI_API_KEY.
JUDGE_PROVIDER = os.environ.get("JUDGE_PROVIDER", "google")     # "google" | "anthropic" | "openai"
JUDGE_MODEL    = os.environ.get("JUDGE_MODEL",    "gemini-2.5-flash-preview-05-20")

# ── RAG configuration (mirrors backend/retrieval/retriever.py) ────────────────
CHROMA_PERSIST_DIR  = os.environ.get("CHROMA_PERSIST_DIR", os.path.join(ROOT_DIR, "chroma_db"))
CHROMA_COLLECTION   = "pharmacy_docs"
EMBEDDING_MODEL     = "all-MiniLM-L6-v2"
RAG_TOP_K_VALUES    = [3, 5]   # precision@k and recall@k evaluated at these k values

# ── CRM database ──────────────────────────────────────────────────────────────
CRM_DB_PATH = os.environ.get("CRM_DB_PATH", os.path.join(ROOT_DIR, "crm.db"))
# Separate test DB so eval runs never touch production data
CRM_TEST_DB_PATH = os.environ.get("CRM_TEST_DB_PATH", os.path.join(ROOT_DIR, "crm_test.db"))

# ── Backend source path (for importing tools/retriever directly) ──────────────
BACKEND_DIR = os.path.join(ROOT_DIR, "backend")

# ── Correctness thresholds ────────────────────────────────────────────────────
THRESHOLDS = {
    "task_completion_rate":   0.80,
    "policy_adherence_rate":  0.85,
    "coherence_score":        0.60,   # 0–1 normalised from 1–5 scale
    # Note: this corpus has 1 chunk per document (no sub-document splitting).
    # Most queries have exactly 1 relevant chunk → theoretical max precision@3 = 0.33.
    # Thresholds are set accordingly; recall and MRR are the primary quality signals.
    "rag_precision_at_3":     0.35,
    "rag_recall_at_3":        0.85,
    "rag_mrr":                0.80,
    "rag_faithfulness":       0.70,
    "crm_crud_accuracy":      1.00,
    "tool_invocation_tpr":    0.80,   # true-positive rate
    "tool_invocation_fpr":    0.10,   # false-positive rate (must stay BELOW)
    "tool_argument_accuracy": 0.75,
}

# ── Performance thresholds ────────────────────────────────────────────────────
LATENCY_TRIALS          = 30
TTFT_MEDIAN_LIMIT_S     = 2.0    # median TTFT must be below this
E2E_MEDIAN_LIMIT_S      = 10.0   # median end-to-end must be below this
THROUGHPUT_LEVELS       = [1, 2, 5, 10, 20]   # concurrent users to test

# ── Data file paths ───────────────────────────────────────────────────────────
DATA_DIR          = os.path.join(os.path.dirname(__file__), "data")
CONVERSATIONS_DIR = os.path.join(DATA_DIR, "conversations")
RAG_GT_DIR        = os.path.join(DATA_DIR, "rag_ground_truth")
TOOL_TESTS_DIR    = os.path.join(DATA_DIR, "tool_test_sets")

# ── Report output ─────────────────────────────────────────────────────────────
REPORT_DIR = os.path.join(os.path.dirname(__file__), "report")
