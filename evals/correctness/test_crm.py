"""
CRM Tool Evaluation
===================
Part 1 — Direct CRUD unit tests  (no LLM, no server required)
Part 2 — LLM tool-calling accuracy  (requires live chatbot server)

Run only Part 1:
    pytest evals/correctness/test_crm.py -m "not live" -v

Run everything (server must be running):
    pytest evals/correctness/test_crm.py -v
"""
import json
import os
import sys
import pytest

# conftest.py already added backend to sys.path
from tools.crm_tool import CRMTool
from config import TOOL_TESTS_DIR, THRESHOLDS

# ── Import WebSocket helpers from conftest ─────────────────────────────────
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from conftest import ws_chat_turn, RESULTS_DIR  # noqa: E402


# ══════════════════════════════════════════════════════════════════════════════
# PART 1 — Direct CRUD  (pure async, no server)
# ══════════════════════════════════════════════════════════════════════════════

async def test_get_nonexistent_user(crm):
    result = await crm.execute(action="get_user", user_id="ghost_001")
    assert result["found"] is False
    assert result["user_id"] == "ghost_001"


async def test_create_user_returns_created_true(crm):
    result = await crm.execute(action="create_user", user_id="sess_001", name="Alice")
    assert result["created"] is True
    assert result["user_id"] == "sess_001"


async def test_get_user_after_create(crm):
    await crm.execute(action="create_user", user_id="sess_002", name="Bob")
    result = await crm.execute(action="get_user", user_id="sess_002")
    assert result["found"] is True
    assert result["name"] == "Bob"
    assert result["last_visit"] is not None


async def test_update_user_name(crm):
    await crm.execute(action="create_user", user_id="sess_003", name="Charlie")
    await crm.execute(action="update_user", user_id="sess_003", field="name", value="Charles")
    result = await crm.execute(action="get_user", user_id="sess_003")
    assert result["name"] == "Charles"


async def test_update_user_contact(crm):
    await crm.execute(action="create_user", user_id="sess_004")
    await crm.execute(action="update_user", user_id="sess_004", field="contact", value="0321-9999999")
    result = await crm.execute(action="get_user", user_id="sess_004")
    assert result["contact"] == "0321-9999999"


async def test_create_duplicate_returns_error(crm):
    await crm.execute(action="create_user", user_id="sess_005", name="Diana")
    result = await crm.execute(action="create_user", user_id="sess_005", name="Diana Again")
    assert result["created"] is False
    assert "error" in result


async def test_update_invalid_field_rejected(crm):
    await crm.execute(action="create_user", user_id="sess_006")
    result = await crm.execute(action="update_user", user_id="sess_006", field="user_id", value="hacked")
    assert "error" in result


async def test_update_nonexistent_user_returns_failure(crm):
    result = await crm.execute(action="update_user", user_id="no_such_user", field="name", value="Ghost")
    assert result.get("updated") is False or "error" in result


async def test_update_preferences_valid_json(crm):
    await crm.execute(action="create_user", user_id="sess_007")
    prefs = json.dumps({"language": "en", "contact_method": "phone"})
    result = await crm.execute(action="update_user", user_id="sess_007", field="preferences", value=prefs)
    assert result.get("updated") is True


async def test_update_preferences_invalid_json_rejected(crm):
    await crm.execute(action="create_user", user_id="sess_008")
    result = await crm.execute(action="update_user", user_id="sess_008", field="preferences", value="not{{json")
    assert "error" in result


async def test_append_interaction_history(crm):
    await crm.execute(action="create_user", user_id="sess_009")
    await crm.append_interaction(user_id="sess_009", summary="Asked about ibuprofen dosage")
    result = await crm.execute(action="get_user", user_id="sess_009")
    history = result["interaction_history"]
    assert len(history) == 1
    assert "ibuprofen" in history[0]["summary"]


async def test_unknown_action_returns_error(crm):
    result = await crm.execute(action="delete_user", user_id="sess_010")
    assert "error" in result


# ══════════════════════════════════════════════════════════════════════════════
# PART 2 — LLM Tool-Calling Accuracy  (requires live server)
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.live
async def test_crm_tool_invocation_accuracy(live_server):
    """
    Sends each utterance from crm_tests.json to the live chatbot and records
    whether the CRM tool was actually invoked.

    Metrics computed:
      - TPR (true positive rate): correct invocations / expected invocations
      - FPR (false positive rate): false invocations / expected non-invocations
      - argument_accuracy: for name-extraction cases, % where response contains the expected name

    Results saved to evals/results/crm_results.json.
    """
    test_cases = json.load(
        open(os.path.join(TOOL_TESTS_DIR, "crm_tests.json"))
    )

    tp = fp = fn = tn = 0
    arg_correct = arg_total = 0
    per_case = []

    for case in test_cases:
        result = await ws_chat_turn(case["utterance"])
        invoked = result["tool_used"] == "crm_tool"
        expected = case["should_invoke"]

        if expected and invoked:
            tp += 1
        elif expected and not invoked:
            fn += 1
        elif not expected and invoked:
            fp += 1
        else:
            tn += 1

        # Argument accuracy: check if the expected name appears in the response
        expected_name = (
            (case.get("expected_tool_call") or {})
            .get("args", {})
            .get("name")
        )
        arg_match = None
        if expected_name and invoked:
            arg_match = expected_name.split()[0].lower() in result["response"].lower()
            arg_total += 1
            if arg_match:
                arg_correct += 1

        per_case.append({
            "test_id":       case["test_id"],
            "utterance":     case["utterance"],
            "should_invoke": expected,
            "did_invoke":    invoked,
            "correct":       expected == invoked,
            "arg_match":     arg_match,
            "response_preview": result["response"][:120],
        })

    total_pos = tp + fn
    total_neg = tn + fp
    tpr = tp / total_pos if total_pos else 0.0
    fpr = fp / total_neg if total_neg else 0.0
    arg_acc = arg_correct / arg_total if arg_total else None

    metrics = {
        "tp": tp, "fp": fp, "fn": fn, "tn": tn,
        "tpr": round(tpr, 4),
        "fpr": round(fpr, 4),
        "argument_accuracy": round(arg_acc, 4) if arg_acc is not None else None,
        "per_case": per_case,
    }

    results_path = os.path.join(RESULTS_DIR, "crm_results.json")
    with open(results_path, "w") as f:
        json.dump(metrics, f, indent=2)

    print(f"\n[CRM] TPR={tpr:.2f}  FPR={fpr:.2f}  ArgAcc={arg_acc}")
    print(f"[CRM] Results saved → {results_path}")

    assert tpr >= THRESHOLDS["tool_invocation_tpr"], (
        f"CRM TPR {tpr:.2f} is below threshold {THRESHOLDS['tool_invocation_tpr']}"
    )
    assert fpr <= THRESHOLDS["tool_invocation_fpr"], (
        f"CRM FPR {fpr:.2f} exceeds threshold {THRESHOLDS['tool_invocation_fpr']}"
    )
