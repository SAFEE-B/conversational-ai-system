"""
Dosage Calculator Tool — computes recommended OTC medication doses by weight and age.

Uses standard evidence-based dosing tables. For informational purposes only;
always advise consultation with a pharmacist or physician for clinical decisions.
"""
import logging
import math
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

TOOL_NAME = "calculate_dosage"
TOOL_DESCRIPTION = (
    "Calculates the recommended OTC dose for a medication based on the patient's weight and age. "
    "Use when a customer asks how much of a medication to take for themselves or their child."
)
TOOL_SCHEMA = {
    "type": "object",
    "properties": {
        "medication": {
            "type": "string",
            "description": "Medication name (e.g., acetaminophen, ibuprofen, loratadine, cetirizine, diphenhydramine).",
        },
        "weight_kg": {
            "type": "number",
            "description": "Patient weight in kilograms (optional; required for weight-based paediatric dosing).",
        },
        "age_years": {
            "type": "number",
            "description": "Patient age in years.",
        },
    },
    "required": ["medication", "age_years"],
}

# Dosing tables: each entry has:
#   mg_per_kg: for weight-based dosing (children)
#   adult_dose_mg: fixed adult dose (age >= 12)
#   frequency_hours: dosing interval
#   max_daily_mg: maximum dose per 24 hours
#   min_age_years: minimum age for use
#   notes: any clinical notes
_DOSING_TABLES = {
    "acetaminophen": {
        "mg_per_kg": 12.5,          # midpoint of 10–15 mg/kg
        "adult_dose_mg": 500,
        "frequency_hours": 4,
        "max_daily_mg_per_kg": 75,
        "adult_max_daily_mg": 4000,
        "min_age_years": 0,         # requires weight-based calculation for infants
        "notes": (
            "Take with or without food. "
            "Reduce maximum to 2,000–3,000 mg/day for patients who drink alcohol regularly. "
            "Do not combine with other acetaminophen-containing products."
        ),
    },
    "ibuprofen": {
        "mg_per_kg": 7.5,           # midpoint of 5–10 mg/kg
        "adult_dose_mg": 400,
        "frequency_hours": 6,
        "max_daily_mg_per_kg": 40,
        "adult_max_daily_mg": 1200,  # OTC limit
        "min_age_years": 0.5,        # 6 months
        "notes": (
            "Take with food or milk to reduce stomach upset. "
            "Do not use in children under 6 months. "
            "Avoid in third trimester of pregnancy and with kidney disease."
        ),
    },
    "aspirin": {
        "mg_per_kg": None,           # weight-based not used for aspirin (adults only)
        "adult_dose_mg": 325,
        "frequency_hours": 4,
        "max_daily_mg_per_kg": None,
        "adult_max_daily_mg": 4000,
        "min_age_years": 18,
        "notes": (
            "Aspirin is NOT for children or teenagers (Reye's syndrome risk). "
            "Take with food. "
            "Low-dose (81 mg) for cardioprotection is taken once daily — only as directed by a physician."
        ),
    },
    "naproxen": {
        "mg_per_kg": None,
        "adult_dose_mg": 220,
        "frequency_hours": 8,
        "max_daily_mg_per_kg": None,
        "adult_max_daily_mg": 660,
        "min_age_years": 12,
        "notes": (
            "Take with a full glass of water and food. "
            "Not recommended for children under 12 without physician direction. "
            "Older adults (65+): do not exceed 220 mg every 12 hours."
        ),
    },
    "diphenhydramine": {
        "mg_per_kg": None,
        "adult_dose_mg": 25,
        "frequency_hours": 4,
        "max_daily_mg_per_kg": None,
        "adult_max_daily_mg": 300,
        "min_age_years": 6,
        "notes": (
            "Causes significant drowsiness — do not drive. "
            "Children 2–5: 6.25 mg every 4–6 hours (use liquid; ask pharmacist). "
            "Children 6–11: 12.5–25 mg every 4–6 hours. "
            "Not recommended under age 2."
        ),
    },
    "loratadine": {
        "mg_per_kg": None,
        "adult_dose_mg": 10,
        "frequency_hours": 24,
        "max_daily_mg_per_kg": None,
        "adult_max_daily_mg": 10,
        "min_age_years": 2,
        "notes": (
            "Children 2–5: 5 mg once daily (chewable or syrup). "
            "Children 6+: 10 mg once daily. "
            "Non-sedating — safe to take in the morning."
        ),
    },
    "cetirizine": {
        "mg_per_kg": None,
        "adult_dose_mg": 10,
        "frequency_hours": 24,
        "max_daily_mg_per_kg": None,
        "adult_max_daily_mg": 10,
        "min_age_years": 2,
        "notes": (
            "Children 2–5: 2.5 mg once daily. "
            "Children 6–11: 5–10 mg once daily. "
            "Adults: 5–10 mg once daily. "
            "May cause mild drowsiness — consider taking at bedtime."
        ),
    },
    "guaifenesin": {
        "mg_per_kg": None,
        "adult_dose_mg": 400,
        "frequency_hours": 4,
        "max_daily_mg_per_kg": None,
        "adult_max_daily_mg": 2400,
        "min_age_years": 6,
        "notes": (
            "Drink plenty of fluids (8+ glasses/day) to enhance effectiveness. "
            "Children 6–11: 100–200 mg every 4 hours. "
            "Extended-release: 600–1,200 mg every 12 hours for adults."
        ),
    },
    "loperamide": {
        "mg_per_kg": None,
        "adult_dose_mg": 4,          # initial dose; then 2 mg after each loose stool
        "frequency_hours": 0,        # variable
        "max_daily_mg_per_kg": None,
        "adult_max_daily_mg": 8,
        "min_age_years": 6,
        "notes": (
            "Adults: 4 mg initial dose, then 2 mg after each loose stool. Max 8 mg/day OTC. "
            "Children 6–11: 2 mg initial dose, then 1 mg after each loose stool. Max 6 mg/day. "
            "Do not use if diarrhea is accompanied by high fever or blood in stool."
        ),
    },
    "omeprazole": {
        "mg_per_kg": None,
        "adult_dose_mg": 20,
        "frequency_hours": 24,
        "max_daily_mg_per_kg": None,
        "adult_max_daily_mg": 20,
        "min_age_years": 18,
        "notes": (
            "Take 30 minutes before a meal. "
            "Use for 14 consecutive days only (OTC indication). "
            "Not for immediate heartburn relief — takes 1–4 days for full effect."
        ),
    },
}

_SYNONYMS = {
    "tylenol": "acetaminophen",
    "panadol": "acetaminophen",
    "advil": "ibuprofen",
    "motrin": "ibuprofen",
    "aleve": "naproxen",
    "benadryl": "diphenhydramine",
    "claritin": "loratadine",
    "zyrtec": "cetirizine",
    "prilosec": "omeprazole",
    "mucinex": "guaifenesin",
    "imodium": "loperamide",
}


def _normalise(name: str) -> str:
    return _SYNONYMS.get(name.strip().lower(), name.strip().lower())


class DosageCalculator:
    name = TOOL_NAME
    description = TOOL_DESCRIPTION
    schema = TOOL_SCHEMA

    async def execute(
        self,
        medication: str,
        age_years: float,
        weight_kg: Optional[float] = None,
    ) -> Dict[str, Any]:
        key = _normalise(medication)
        table = _DOSING_TABLES.get(key)

        if not table:
            return {
                "medication": medication,
                "error": (
                    f"Dosing information for '{medication}' is not available in our calculator. "
                    "Please consult a HealthFirst pharmacist for personalised dosing guidance."
                ),
            }

        if age_years < table["min_age_years"]:
            return {
                "medication": medication,
                "age_years": age_years,
                "error": (
                    f"{medication.title()} is not recommended for patients under "
                    f"{table['min_age_years']} years old. "
                    "Please consult a physician before use."
                ),
            }

        is_adult = age_years >= 12

        if is_adult:
            dose_mg = table["adult_dose_mg"]
            max_daily = table["adult_max_daily_mg"]
        else:
            # Paediatric weight-based dosing
            if table["mg_per_kg"] is None:
                return {
                    "medication": medication,
                    "age_years": age_years,
                    "error": (
                        f"{medication.title()} is only available for adults (12+) OTC. "
                        "Please consult a physician for children's dosing."
                    ),
                }
            if weight_kg is None:
                return {
                    "medication": medication,
                    "age_years": age_years,
                    "error": "Weight (weight_kg) is required for paediatric dosing. Please provide the child's weight.",
                }
            dose_mg = round(table["mg_per_kg"] * weight_kg, 1)
            max_daily_from_weight = table["max_daily_mg_per_kg"] * weight_kg
            max_daily = min(max_daily_from_weight, table.get("adult_max_daily_mg", max_daily_from_weight))

        freq = table["frequency_hours"]
        freq_text = f"every {freq} hours" if freq > 0 else "as directed (variable)"
        max_doses_per_day = math.floor(24 / freq) if freq > 0 else None

        result: Dict[str, Any] = {
            "medication": medication,
            "age_years": age_years,
            "recommended_dose_mg": dose_mg,
            "frequency": freq_text,
            "max_daily_dose_mg": round(max_daily, 1),
            "notes": table["notes"],
            "disclaimer": (
                "This is an informational estimate based on standard OTC dosing guidelines. "
                "Always read the product label and consult a pharmacist or physician for personalised advice."
            ),
        }
        if weight_kg is not None:
            result["weight_kg"] = weight_kg
        if max_doses_per_day:
            result["max_doses_per_day"] = max_doses_per_day

        return result
