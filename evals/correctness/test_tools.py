"""
Additional Tools Evaluation
============================
Part 1A — DrugInteractionChecker    (direct, no server)
Part 1B — DosageCalculator          (direct, no server)
Part 1C — MedicationInfoLookup      (direct, no server)
Part 2  — LLM tool-calling accuracy (requires live chatbot server)

Run only Part 1:
    pytest evals/correctness/test_tools.py -m "not live" -v

Run everything (server must be running):
    pytest evals/correctness/test_tools.py -v
"""
import json
import os
import sys
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from conftest import ws_chat_turn, RESULTS_DIR  # noqa: E402

from tools.drug_interaction import DrugInteractionChecker
from tools.dosage_calculator import DosageCalculator
from tools.medication_info import MedicationInfoLookup
from config import TOOL_TESTS_DIR, THRESHOLDS


# ── Module-scoped fixtures (constructed once, stateless tools) ─────────────

@pytest.fixture(scope="module")
def drug_checker():
    return DrugInteractionChecker()


@pytest.fixture(scope="module")
def dosage_calc():
    return DosageCalculator()


@pytest.fixture(scope="module")
def med_info():
    return MedicationInfoLookup()


# ══════════════════════════════════════════════════════════════════════════════
# PART 1A — DrugInteractionChecker
# ══════════════════════════════════════════════════════════════════════════════

async def test_interaction_major_warfarin_aspirin(drug_checker):
    r = await drug_checker.execute(drug1="warfarin", drug2="aspirin")
    assert r["severity"] == "major"
    assert "description" in r
    assert "recommendation" in r


async def test_interaction_lookup_is_order_independent(drug_checker):
    """frozenset key — swapping args must return the same severity."""
    r1 = await drug_checker.execute(drug1="aspirin", drug2="warfarin")
    r2 = await drug_checker.execute(drug1="warfarin", drug2="aspirin")
    assert r1["severity"] == r2["severity"]


async def test_interaction_moderate_warfarin_acetaminophen(drug_checker):
    r = await drug_checker.execute(drug1="warfarin", drug2="acetaminophen")
    assert r["severity"] == "moderate"


async def test_interaction_minor_ibuprofen_metformin(drug_checker):
    r = await drug_checker.execute(drug1="ibuprofen", drug2="metformin")
    assert r["severity"] == "minor"


async def test_interaction_brand_synonym_tylenol_coumadin(drug_checker):
    """Tylenol → acetaminophen, Coumadin → warfarin → moderate interaction."""
    r = await drug_checker.execute(drug1="tylenol", drug2="coumadin")
    assert r["severity"] == "moderate"


async def test_interaction_same_drug_returns_none(drug_checker):
    """ibuprofen + advil (same drug) → severity='none'."""
    r = await drug_checker.execute(drug1="ibuprofen", drug2="advil")
    assert r["severity"] == "none"
    assert "error" not in r


async def test_interaction_unknown_pair_is_graceful(drug_checker):
    """No known entry → severity='unknown', not an exception or error key."""
    r = await drug_checker.execute(drug1="cetirizine", drug2="melatonin")
    assert r["severity"] == "unknown"
    assert "error" not in r


async def test_interaction_two_nsaids_major(drug_checker):
    r = await drug_checker.execute(drug1="ibuprofen", drug2="naproxen")
    assert r["severity"] == "major"


async def test_interaction_major_metronidazole_alcohol(drug_checker):
    r = await drug_checker.execute(drug1="metronidazole", drug2="alcohol")
    assert r["severity"] == "major"


# ══════════════════════════════════════════════════════════════════════════════
# PART 1B — DosageCalculator
# ══════════════════════════════════════════════════════════════════════════════

async def test_dosage_adult_acetaminophen(dosage_calc):
    r = await dosage_calc.execute(medication="acetaminophen", age_years=35)
    assert r["recommended_dose_mg"] == 500
    assert "4 hours" in r["frequency"]
    assert r["max_daily_dose_mg"] == 4000.0


async def test_dosage_adult_ibuprofen(dosage_calc):
    r = await dosage_calc.execute(medication="ibuprofen", age_years=28)
    assert r["recommended_dose_mg"] == 400
    assert "6 hours" in r["frequency"]


async def test_dosage_pediatric_ibuprofen_weight_based(dosage_calc):
    """7.5 mg/kg × 20 kg = 150 mg."""
    r = await dosage_calc.execute(medication="ibuprofen", age_years=5, weight_kg=20)
    assert r["recommended_dose_mg"] == pytest.approx(150.0, abs=1)
    assert "6 hours" in r["frequency"]


async def test_dosage_pediatric_acetaminophen_weight_based(dosage_calc):
    """12.5 mg/kg × 30 kg = 375 mg."""
    r = await dosage_calc.execute(medication="acetaminophen", age_years=8, weight_kg=30)
    assert r["recommended_dose_mg"] == pytest.approx(375.0, abs=1)


async def test_dosage_pediatric_missing_weight_returns_error(dosage_calc):
    """Paediatric weight-based drug without weight_kg must return an error, not crash."""
    r = await dosage_calc.execute(medication="ibuprofen", age_years=5)
    assert "error" in r


async def test_dosage_age_below_minimum_returns_error(dosage_calc):
    """Aspirin min_age=18; a 10-year-old must get an error."""
    r = await dosage_calc.execute(medication="aspirin", age_years=10)
    assert "error" in r


async def test_dosage_brand_synonym_resolves(dosage_calc):
    """Tylenol → acetaminophen; should return a valid dose, not an error."""
    r = await dosage_calc.execute(medication="tylenol", age_years=30)
    assert "recommended_dose_mg" in r
    assert "error" not in r


async def test_dosage_unknown_medication_returns_error(dosage_calc):
    r = await dosage_calc.execute(medication="completely_unknown_xyz", age_years=30)
    assert "error" in r


async def test_dosage_result_always_has_disclaimer(dosage_calc):
    r = await dosage_calc.execute(medication="loratadine", age_years=25)
    assert "disclaimer" in r


async def test_dosage_once_daily_frequency(dosage_calc):
    """Loratadine and cetirizine are once-daily; frequency string should say 24 hours."""
    r = await dosage_calc.execute(medication="cetirizine", age_years=30)
    assert "24 hours" in r["frequency"]


# ══════════════════════════════════════════════════════════════════════════════
# PART 1C — MedicationInfoLookup
# ══════════════════════════════════════════════════════════════════════════════

async def test_med_info_known_medication_found(med_info):
    r = await med_info.execute(medication_name="omeprazole")
    assert r["found"] is True
    assert "Proton Pump Inhibitor" in r["category"]
    assert r["otc_available"] is True


async def test_med_info_brand_name_benadryl_resolves(med_info):
    """Benadryl → diphenhydramine."""
    r = await med_info.execute(medication_name="benadryl")
    assert r["found"] is True
    assert "antihistamine" in r["category"].lower()


async def test_med_info_brand_name_tylenol_resolves(med_info):
    r = await med_info.execute(medication_name="tylenol")
    assert r["found"] is True


async def test_med_info_unknown_medication_graceful(med_info):
    """Unknown drug → found=False with a message, not a crash or exception."""
    r = await med_info.execute(medication_name="nonexistent_drug_xyz")
    assert r["found"] is False
    assert "message" in r
    assert "error" not in r


async def test_med_info_includes_uses_and_warnings(med_info):
    r = await med_info.execute(medication_name="aspirin")
    assert r["found"] is True
    assert len(r.get("uses", [])) > 0
    assert len(r.get("key_warnings", [])) > 0
    # Aspirin must warn about children (Reye's syndrome)
    assert any("children" in w.lower() or "reye" in w.lower() for w in r["key_warnings"])


async def test_med_info_side_effects_structure(med_info):
    r = await med_info.execute(medication_name="ibuprofen")
    se = r.get("side_effects", {})
    assert "common" in se
    assert isinstance(se["common"], list)
    assert len(se["common"]) > 0


async def test_med_info_healthfirst_availability_string(med_info):
    r = await med_info.execute(medication_name="cetirizine")
    assert isinstance(r.get("healthfirst_availability"), str)
    assert "HealthFirst" in r["healthfirst_availability"]


async def test_med_info_diphenhydramine_warns_driving(med_info):
    """Diphenhydramine must list drowsiness/driving warning."""
    r = await med_info.execute(medication_name="diphenhydramine")
    warnings_text = " ".join(r.get("key_warnings", [])).lower()
    assert "drive" in warnings_text or "drowsiness" in warnings_text or "sedation" in warnings_text


# ══════════════════════════════════════════════════════════════════════════════
# PART 2 — LLM Tool-Calling Accuracy  (requires live server)
# ══════════════════════════════════════════════════════════════════════════════

def _compute_metrics(test_cases: list, ws_results: list, tool_name: str) -> dict:
    tp = fp = fn = tn = 0
    per_case = []

    for case, res in zip(test_cases, ws_results):
        invoked = res["tool_used"] == tool_name
        expected = case["should_invoke"]

        if expected and invoked:
            tp += 1
        elif expected and not invoked:
            fn += 1
        elif not expected and invoked:
            fp += 1
        else:
            tn += 1

        per_case.append({
            "test_id":        case["test_id"],
            "utterance":      case["utterance"],
            "should_invoke":  expected,
            "did_invoke":     invoked,
            "correct":        expected == invoked,
            "response_preview": res["response"][:150],
        })

    total_pos = tp + fn
    total_neg = tn + fp
    return {
        "tp": tp, "fp": fp, "fn": fn, "tn": tn,
        "tpr": round(tp / total_pos, 4) if total_pos else 0.0,
        "fpr": round(fp / total_neg, 4) if total_neg else 0.0,
        "per_case": per_case,
    }


def _save(filename: str, data: dict):
    path = os.path.join(RESULTS_DIR, filename)
    with open(path, "w") as f:
        json.dump(data, f, indent=2)
    print(f"  → saved {path}")


@pytest.mark.live
async def test_drug_interaction_tool_invocation_accuracy(live_server):
    test_cases = json.load(open(os.path.join(TOOL_TESTS_DIR, "drug_interaction_tests.json")))
    ws_results = [await ws_chat_turn(c["utterance"]) for c in test_cases]
    metrics = _compute_metrics(test_cases, ws_results, "check_drug_interaction")

    # Argument accuracy: expected severity appears in the response
    arg_ok = arg_total = 0
    for case, res in zip(test_cases, ws_results):
        expected_sev = (case.get("expected_result") or {}).get("severity")
        if case["should_invoke"] and res["tool_used"] == "check_drug_interaction" and expected_sev:
            arg_total += 1
            if expected_sev.lower() in res["response"].lower():
                arg_ok += 1
    metrics["argument_accuracy"] = round(arg_ok / arg_total, 4) if arg_total else None

    _save("drug_interaction_results.json", metrics)
    print(f"\n[DrugInteraction] TPR={metrics['tpr']}  FPR={metrics['fpr']}  ArgAcc={metrics['argument_accuracy']}")

    assert metrics["tpr"] >= THRESHOLDS["tool_invocation_tpr"], \
        f"Drug interaction TPR {metrics['tpr']} below threshold {THRESHOLDS['tool_invocation_tpr']}"
    assert metrics["fpr"] <= THRESHOLDS["tool_invocation_fpr"], \
        f"Drug interaction FPR {metrics['fpr']} above threshold {THRESHOLDS['tool_invocation_fpr']}"


@pytest.mark.live
async def test_dosage_tool_invocation_accuracy(live_server):
    test_cases = json.load(open(os.path.join(TOOL_TESTS_DIR, "dosage_tests.json")))
    ws_results = [await ws_chat_turn(c["utterance"]) for c in test_cases]
    metrics = _compute_metrics(test_cases, ws_results, "calculate_dosage")

    # Argument accuracy: expected dose (mg number) appears in the response
    arg_ok = arg_total = 0
    for case, res in zip(test_cases, ws_results):
        expected_dose = (case.get("expected_result") or {}).get("recommended_dose_mg")
        if case["should_invoke"] and res["tool_used"] == "calculate_dosage" and expected_dose:
            arg_total += 1
            if str(int(expected_dose)) in res["response"]:
                arg_ok += 1
    metrics["argument_accuracy"] = round(arg_ok / arg_total, 4) if arg_total else None

    _save("dosage_results.json", metrics)
    print(f"\n[Dosage] TPR={metrics['tpr']}  FPR={metrics['fpr']}  ArgAcc={metrics['argument_accuracy']}")

    assert metrics["tpr"] >= THRESHOLDS["tool_invocation_tpr"], \
        f"Dosage TPR {metrics['tpr']} below threshold {THRESHOLDS['tool_invocation_tpr']}"
    assert metrics["fpr"] <= THRESHOLDS["tool_invocation_fpr"], \
        f"Dosage FPR {metrics['fpr']} above threshold {THRESHOLDS['tool_invocation_fpr']}"


@pytest.mark.live
async def test_medication_info_tool_invocation_accuracy(live_server):
    test_cases = json.load(open(os.path.join(TOOL_TESTS_DIR, "medication_info_tests.json")))
    ws_results = [await ws_chat_turn(c["utterance"]) for c in test_cases]
    metrics = _compute_metrics(test_cases, ws_results, "get_medication_info")

    # Argument accuracy: first word of expected category appears in response
    arg_ok = arg_total = 0
    for case, res in zip(test_cases, ws_results):
        expected_cat = (case.get("expected_result") or {}).get("category", "")
        if case["should_invoke"] and res["tool_used"] == "get_medication_info" and expected_cat:
            arg_total += 1
            # e.g. "Proton Pump Inhibitor (PPI)" → check "proton" or "ppi"
            keyword = expected_cat.lower().split("(")[0].strip().split()[0]
            if keyword in res["response"].lower():
                arg_ok += 1
    metrics["argument_accuracy"] = round(arg_ok / arg_total, 4) if arg_total else None

    _save("medication_info_results.json", metrics)
    print(f"\n[MedInfo] TPR={metrics['tpr']}  FPR={metrics['fpr']}  ArgAcc={metrics['argument_accuracy']}")

    assert metrics["tpr"] >= THRESHOLDS["tool_invocation_tpr"], \
        f"Med info TPR {metrics['tpr']} below threshold {THRESHOLDS['tool_invocation_tpr']}"
    assert metrics["fpr"] <= THRESHOLDS["tool_invocation_fpr"], \
        f"Med info FPR {metrics['fpr']} above threshold {THRESHOLDS['tool_invocation_fpr']}"
