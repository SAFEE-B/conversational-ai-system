"""
Tool Orchestrator — intent detection, tool dispatch, and result formatting.

Architecture:
  User message → detect_intent() → call tool → return structured result

Intent detection is keyword/pattern-based (reliable for 0.5B LLM; avoids a
second LLM pass and keeps streaming intact).

All tool calls are async and complete BEFORE LLM generation starts so that
results can be injected into the prompt context.
"""
import logging
import re
from typing import Any, Dict, List, Optional, Tuple

from tools.crm_tool import CRMTool
from tools.drug_interaction import DrugInteractionChecker
from tools.dosage_calculator import DosageCalculator
from tools.medication_info import MedicationInfoLookup

logger = logging.getLogger(__name__)

# ─── Intent patterns ──────────────────────────────────────────────────────────

_INTERACTION_PATTERNS = [
    r"\binteract\w*\b",
    r"\bmix\w*\b",
    r"\btake together\b",
    r"\bsafe (to take|with)\b",
    r"\bcombine\b",
    r"\btogether\b.{0,30}\b(medication|drug|pill|medicine|tablet)\b",
    r"\bcan i take\b.{0,40}\band\b",
]

_DOSAGE_PATTERNS = [
    r"\bdosage\b",
    r"\bhow much\b",
    r"\bhow many\b.{0,20}\bmg\b",
    r"\bdose\b",
    r"\bdosing\b",
    r"\bwhat('s| is) the (dose|dosage|amount)\b",
    r"\bhow (often|frequently) (should|do|can)\b",
]

_MED_INFO_PATTERNS = [
    r"\bwhat is\b.{0,40}\bfor\b",
    r"\bwhat('s| is) .{0,30}\bused for\b",
    r"\bside effect\w*\b",
    r"\bwhat does .{0,30}\bdo\b",
    r"\btell me about\b",
    r"\binformation (about|on)\b",
    r"\blearn about\b",
    r"\bwhat (is|are) the .{0,20}(effects|uses|warnings)\b",
]

_CRM_PATTERNS = [
    r"\bmy name is\b",
    r"\bi'?m\b.{0,5}\b([A-Z][a-z]+)\b",
    r"\bremember (me|my)\b",
    r"\bwho am i\b",
    r"\bmy (number|phone|email|contact)\b",
    r"\bdo you (know|remember) me\b",
    r"\blast (time|visit|visit)\b",
    r"\bprefer\w*\b.{0,20}\b(medication|language|contact)\b",
]

_MEDICATION_NAMES = {
    "acetaminophen", "ibuprofen", "aspirin", "naproxen", "diphenhydramine",
    "loratadine", "cetirizine", "omeprazole", "pseudoephedrine", "guaifenesin",
    "loperamide", "melatonin", "clotrimazole", "hydrocortisone", "bismuth",
    "dextromethorphan", "famotidine", "ranitidine", "simvastatin", "atorvastatin",
    "warfarin", "metformin", "metronidazole", "clopidogrel",
    # Brand names
    "tylenol", "advil", "motrin", "aleve", "benadryl", "claritin", "zyrtec",
    "prilosec", "sudafed", "mucinex", "imodium", "pepto", "pepto-bismol",
    "neosporin", "cortaid", "cortizone", "lotrimin",
}


def _find_medications_in_text(text: str) -> List[str]:
    """Extract known medication names mentioned in the text."""
    lower = text.lower()
    found = []
    for med in _MEDICATION_NAMES:
        if re.search(r"\b" + re.escape(med) + r"\b", lower):
            found.append(med)
    return found


def _matches_any(text: str, patterns: List[str]) -> bool:
    lower = text.lower()
    return any(re.search(p, lower) for p in patterns)


class ToolOrchestrator:
    def __init__(
        self,
        crm_db_path: str,
    ):
        self.crm = CRMTool(db_path=crm_db_path)
        self.interaction_checker = DrugInteractionChecker()
        self.dosage_calc = DosageCalculator()
        self.med_info = MedicationInfoLookup()

        self._tool_result_cache: Dict[str, Any] = {}

    # ─── Public API ─────────────────────────────────────────────────────────

    async def process(
        self,
        message: str,
        session_id: str,
    ) -> Tuple[Optional[str], Optional[Dict[str, Any]]]:
        """
        Detect intent from message and run the appropriate tool (if any).

        Returns (tool_name, tool_result) or (None, None) if no tool is needed.
        Results are cached per (session_id, message) pair to avoid redundant calls.
        """
        cache_key = f"{session_id}::{message}"
        if cache_key in self._tool_result_cache:
            return self._tool_result_cache[cache_key]

        result = await self._dispatch(message, session_id)
        self._tool_result_cache[cache_key] = result
        return result

    def format_tool_result(self, tool_name: str, result: Dict[str, Any]) -> str:
        """Convert a tool result dict into a concise natural-language context block."""
        if not result:
            return ""

        if "error" in result:
            return f"[Tool: {tool_name}]\nNote: {result['error']}"

        lines = [f"[Tool result: {tool_name}]"]

        if tool_name == "crm_tool":
            if result.get("found"):
                lines.append(f"Customer on file: {result.get('name', 'Unknown')}")
                if result.get("contact"):
                    lines.append(f"Contact: {result['contact']}")
                if result.get("last_visit"):
                    lines.append(f"Last visit: {result['last_visit'][:10]}")
                hist = result.get("interaction_history", [])
                if hist:
                    lines.append(f"Previous interaction: {hist[-1].get('summary', '')}")
            else:
                lines.append("No customer record found for this session.")

        elif tool_name == "check_drug_interaction":
            sev = result.get("severity", "unknown").upper()
            lines.append(f"Interaction between {result.get('drug1')} and {result.get('drug2')}: {sev}")
            lines.append(f"Details: {result.get('description', '')}")
            lines.append(f"Recommendation: {result.get('recommendation', '')}")

        elif tool_name == "calculate_dosage":
            lines.append(f"Medication: {result.get('medication')}")
            lines.append(f"Recommended dose: {result.get('recommended_dose_mg')} mg {result.get('frequency', '')}")
            lines.append(f"Max daily dose: {result.get('max_daily_dose_mg')} mg/day")
            lines.append(f"Notes: {result.get('notes', '')}")
            lines.append(f"Disclaimer: {result.get('disclaimer', '')}")

        elif tool_name == "get_medication_info":
            if result.get("found"):
                lines.append(f"Medication: {result.get('medication_name')} (Brands: {', '.join(result.get('brand_names', []))})")
                lines.append(f"Category: {result.get('category', '')}")
                lines.append(f"OTC available: {'Yes' if result.get('otc_available') else 'Prescription required'}")
                uses = result.get("uses", [])
                if uses:
                    lines.append("Uses: " + "; ".join(uses[:3]))
                common_se = result.get("side_effects", {}).get("common", [])
                if common_se:
                    lines.append("Common side effects: " + "; ".join(common_se[:3]))
                warnings = result.get("key_warnings", [])
                if warnings:
                    lines.append("Key warnings: " + "; ".join(warnings[:2]))
                lines.append(result.get("healthfirst_availability", ""))
            else:
                lines.append(result.get("message", "No information found."))

        else:
            lines.append(str(result))

        return "\n".join(lines)

    # ─── Intent dispatch ────────────────────────────────────────────────────

    async def _dispatch(
        self, message: str, session_id: str
    ) -> Tuple[Optional[str], Optional[Dict[str, Any]]]:

        # CRM — check first so returning users get personalised greeting
        if _matches_any(message, _CRM_PATTERNS):
            result = await self._handle_crm(message, session_id)
            return ("crm_tool", result)

        meds = _find_medications_in_text(message)

        # Drug interaction check — needs exactly 2 medications
        if _matches_any(message, _INTERACTION_PATTERNS) and len(meds) >= 2:
            result = await self.interaction_checker.execute(drug1=meds[0], drug2=meds[1])
            return ("check_drug_interaction", result)

        # Dosage calculation
        if _matches_any(message, _DOSAGE_PATTERNS) and meds:
            result = await self._handle_dosage(message, meds[0])
            return ("calculate_dosage", result)

        # Medication info lookup
        if _matches_any(message, _MED_INFO_PATTERNS) and meds:
            result = await self.med_info.execute(medication_name=meds[0])
            return ("get_medication_info", result)

        # Single medication mentioned with no other intent → default to info lookup
        if len(meds) == 1 and len(message.split()) <= 15:
            result = await self.med_info.execute(medication_name=meds[0])
            return ("get_medication_info", result)

        return (None, None)

    async def _handle_crm(self, message: str, session_id: str) -> Dict[str, Any]:
        """Auto-create or retrieve CRM record; update name if provided."""
        record = await self.crm.execute(action="get_user", user_id=session_id)

        # Extract name from "my name is X" or "I'm X"
        name_match = re.search(r"\bmy name is ([A-Z][a-z]+(?:\s[A-Z][a-z]+)?)\b", message, re.IGNORECASE)
        if not name_match:
            name_match = re.search(r"\bi'?m\s+([A-Z][a-z]+)\b", message, re.IGNORECASE)

        if name_match:
            name = name_match.group(1).strip()
            if not record.get("found"):
                record = await self.crm.execute(action="create_user", user_id=session_id, name=name)
            else:
                await self.crm.execute(action="update_user", user_id=session_id, field="name", value=name)
                record["name"] = name

        if not record.get("found") and not name_match:
            record = await self.crm.execute(action="create_user", user_id=session_id)

        return record

    async def _handle_dosage(self, message: str, medication: str) -> Dict[str, Any]:
        """Parse age and optional weight from message for dosage calculation."""
        age: Optional[float] = None
        weight: Optional[float] = None

        # Age detection: "2 year old", "5-year-old", "for a 3 year old", "I'm 28"
        age_match = re.search(
            r"(\d+(?:\.\d+)?)\s*[\-\s]?(?:year|yr)s?(?:\s*old)?", message, re.IGNORECASE
        )
        if not age_match:
            age_match = re.search(r"\baged?\s+(\d+(?:\.\d+)?)\b", message, re.IGNORECASE)
        if not age_match:
            age_match = re.search(r"\bi'?m\s+(\d+)\b", message, re.IGNORECASE)

        if age_match:
            age = float(age_match.group(1))

        # Weight detection: "20 kg", "45 lbs", "weighs 30kg"
        weight_match = re.search(r"(\d+(?:\.\d+)?)\s*kg", message, re.IGNORECASE)
        if weight_match:
            weight = float(weight_match.group(1))
        else:
            lbs_match = re.search(r"(\d+(?:\.\d+)?)\s*(?:lb|lbs|pound)", message, re.IGNORECASE)
            if lbs_match:
                weight = round(float(lbs_match.group(1)) * 0.453592, 1)

        if age is None:
            return {
                "medication": medication,
                "error": (
                    "I need to know the patient's age to calculate the correct dose. "
                    "Please tell me the patient's age (and weight for children under 12)."
                ),
            }

        return await self.dosage_calc.execute(
            medication=medication,
            age_years=age,
            weight_kg=weight,
        )
