"""
Medication Info Lookup Tool — returns structured information about common OTC medications.

Covers: uses, side effects, availability (OTC vs Rx), storage, and key warnings.
"""
import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)

TOOL_NAME = "get_medication_info"
TOOL_DESCRIPTION = (
    "Looks up detailed information about a medication: uses, side effects, "
    "OTC availability, dosage summary, and storage. "
    "Use when a customer asks what a specific medication is for or what its side effects are."
)
TOOL_SCHEMA = {
    "type": "object",
    "properties": {
        "medication_name": {
            "type": "string",
            "description": "The name of the medication (brand or generic).",
        }
    },
    "required": ["medication_name"],
}

_DB: Dict[str, Dict[str, Any]] = {
    "acetaminophen": {
        "brand_names": ["Tylenol", "Panadol", "Excedrin"],
        "category": "Analgesic / Antipyretic",
        "otc_available": True,
        "uses": [
            "Mild to moderate pain relief (headache, toothache, muscle aches, back pain)",
            "Fever reduction in adults and children",
            "Arthritis pain (temporary relief)",
        ],
        "side_effects": {
            "common": ["Generally well-tolerated at recommended doses"],
            "rare_serious": ["Liver damage (overdose)", "Skin rash", "Allergic reactions"],
        },
        "key_warnings": [
            "Maximum 4,000 mg/day (3,000 mg/day for regular alcohol users)",
            "Check all other medications for acetaminophen content to avoid double-dosing",
            "Overdose causes severe, potentially fatal liver damage",
        ],
        "storage": "Store at room temperature (59–77°F), away from heat and moisture.",
        "healthfirst_stock": True,
        "forms_available": ["Tablets (325 mg, 500 mg)", "Extended-release tablets (650 mg)", "Liquid (children's formulation)"],
    },
    "ibuprofen": {
        "brand_names": ["Advil", "Motrin"],
        "category": "NSAID (Non-Steroidal Anti-Inflammatory Drug)",
        "otc_available": True,
        "uses": [
            "Pain relief (headache, dental, menstrual, muscle, backache)",
            "Fever reduction",
            "Anti-inflammatory (sprains, arthritis flares)",
        ],
        "side_effects": {
            "common": ["Stomach upset", "Nausea", "Heartburn"],
            "rare_serious": ["GI bleeding", "Kidney impairment", "Elevated blood pressure", "Cardiovascular events (long-term high dose)"],
        },
        "key_warnings": [
            "Take with food or milk to reduce stomach upset",
            "Avoid in third trimester of pregnancy",
            "Use lowest effective dose for shortest duration",
            "Avoid if allergic to aspirin or NSAIDs",
        ],
        "storage": "Store below 77°F, away from moisture.",
        "healthfirst_stock": True,
        "forms_available": ["Tablets (200 mg)", "Liquid-gels (200 mg)"],
    },
    "aspirin": {
        "brand_names": ["Bayer Aspirin", "Ecotrin"],
        "category": "NSAID / Antiplatelet Agent",
        "otc_available": True,
        "uses": [
            "Mild to moderate pain relief",
            "Fever reduction (adults only)",
            "Anti-inflammatory",
            "Low-dose (81 mg) heart attack and stroke prevention (under physician direction)",
        ],
        "side_effects": {
            "common": ["Stomach irritation", "Nausea", "Heartburn"],
            "rare_serious": ["GI bleeding", "Tinnitus (high doses)", "Allergic reactions", "Reye's syndrome (children — do not use)"],
        },
        "key_warnings": [
            "NEVER give to children or teenagers — Reye's syndrome risk",
            "Avoid with blood thinners (warfarin) without physician guidance",
            "Take with food",
        ],
        "storage": "Cool, dry place. Discard if strong vinegar smell (decomposition sign).",
        "healthfirst_stock": True,
        "forms_available": ["81 mg (low-dose)", "325 mg", "500 mg coated tablets"],
    },
    "diphenhydramine": {
        "brand_names": ["Benadryl", "ZzzQuil", "Unisom SleepTabs"],
        "category": "First-generation antihistamine / Sleep aid",
        "otc_available": True,
        "uses": [
            "Seasonal and year-round allergy symptoms",
            "Hives and skin itching",
            "Short-term insomnia (sleep aid)",
            "Motion sickness",
        ],
        "side_effects": {
            "common": ["Drowsiness (significant)", "Dry mouth", "Blurred vision", "Urinary retention"],
            "rare_serious": ["Confusion (especially in elderly)", "Delirium", "Urinary obstruction"],
        },
        "key_warnings": [
            "Causes significant sedation — do not drive",
            "Tolerance develops quickly — not for chronic sleep use",
            "Avoid in elderly (Beers Criteria — high fall risk)",
            "Do not use under age 2",
        ],
        "storage": "Room temperature, away from heat and moisture.",
        "healthfirst_stock": True,
        "forms_available": ["25 mg tablets", "50 mg tablets", "Liquid", "Topical cream"],
    },
    "loratadine": {
        "brand_names": ["Claritin", "Alavert"],
        "category": "Second-generation antihistamine (non-sedating)",
        "otc_available": True,
        "uses": [
            "Seasonal allergic rhinitis (hay fever)",
            "Year-round allergies",
            "Chronic urticaria (hives)",
        ],
        "side_effects": {
            "common": ["Headache", "Dry mouth", "Fatigue (rare)"],
            "rare_serious": ["Allergic reactions to loratadine itself (rare)"],
        },
        "key_warnings": [
            "Non-sedating at standard doses — safe to drive",
            "24-hour coverage with once-daily dosing",
            "Children 2–5: 5 mg/day; 6+: 10 mg/day",
        ],
        "storage": "Room temperature, away from moisture.",
        "healthfirst_stock": True,
        "forms_available": ["10 mg tablets", "5 mg chewable (children's)", "5 mg/5 mL syrup"],
    },
    "cetirizine": {
        "brand_names": ["Zyrtec"],
        "category": "Second-generation antihistamine",
        "otc_available": True,
        "uses": [
            "Seasonal and year-round allergic rhinitis",
            "Chronic urticaria (hives)",
            "Allergic skin reactions",
        ],
        "side_effects": {
            "common": ["Mild drowsiness (more than loratadine)", "Dry mouth", "Fatigue"],
            "rare_serious": ["Urinary retention", "Dizziness"],
        },
        "key_warnings": [
            "May cause drowsiness — take at night if concerned",
            "Children 2–5: 2.5 mg/day; 6+: 5–10 mg/day",
        ],
        "storage": "Room temperature.",
        "healthfirst_stock": True,
        "forms_available": ["5 mg tablets", "10 mg tablets", "1 mg/mL syrup (children's)"],
    },
    "omeprazole": {
        "brand_names": ["Prilosec OTC"],
        "category": "Proton Pump Inhibitor (PPI)",
        "otc_available": True,
        "uses": [
            "Frequent heartburn (≥2 days/week)",
            "Acid reflux symptom relief",
        ],
        "side_effects": {
            "common": ["Headache", "Nausea", "Diarrhea", "Stomach pain"],
            "rare_serious": ["Low magnesium (long-term)", "C. difficile infection (long-term)", "Increased fracture risk (long-term high dose)"],
        },
        "key_warnings": [
            "Not for immediate heartburn relief — takes 1–4 days",
            "Use for 14 consecutive days only (OTC); wait 4 months before repeating",
            "May reduce clopidogrel's effectiveness — consult physician",
            "Adults 18+ only (OTC)",
        ],
        "storage": "Room temperature, away from moisture.",
        "healthfirst_stock": True,
        "forms_available": ["20 mg delayed-release capsules"],
    },
    "pseudoephedrine": {
        "brand_names": ["Sudafed"],
        "category": "Nasal decongestant (sympathomimetic)",
        "otc_available": True,
        "otc_notes": "Available from pharmacy counter (behind-the-counter) — requires photo ID per CMEA law.",
        "uses": [
            "Nasal and sinus congestion from colds, flu, hay fever",
            "Eustachian tube congestion",
        ],
        "side_effects": {
            "common": ["Elevated blood pressure", "Increased heart rate", "Nervousness", "Insomnia"],
            "rare_serious": ["Severe hypertension", "Arrhythmia"],
        },
        "key_warnings": [
            "Must purchase from pharmacy counter with photo ID",
            "Avoid with hypertension, coronary artery disease, hyperthyroidism",
            "Do not take within 14 days of an MAOI",
            "Not for children under 12 without physician direction",
        ],
        "storage": "Room temperature.",
        "healthfirst_stock": True,
        "forms_available": ["30 mg immediate-release", "120 mg extended-release", "240 mg extended-release"],
    },
    "guaifenesin": {
        "brand_names": ["Mucinex"],
        "category": "Expectorant",
        "otc_available": True,
        "uses": [
            "Chest congestion",
            "Productive cough (loosens mucus)",
            "Cough associated with cold, bronchitis, or sinusitis",
        ],
        "side_effects": {
            "common": ["Nausea (take with food)", "Vomiting at high doses"],
            "rare_serious": ["Kidney stones (theoretical at very high doses)", "Dizziness"],
        },
        "key_warnings": [
            "Drink 8+ glasses of water daily to maximise effectiveness",
            "Does not suppress cough — thins mucus to make cough productive",
            "Consult doctor if cough persists >7 days",
        ],
        "storage": "Room temperature.",
        "healthfirst_stock": True,
        "forms_available": ["200 mg immediate-release tablets", "600 mg extended-release", "1,200 mg extended-release"],
    },
    "loperamide": {
        "brand_names": ["Imodium A-D"],
        "category": "Antidiarrheal (opioid receptor agonist — GI tract only)",
        "otc_available": True,
        "uses": [
            "Acute diarrhea",
            "Traveler's diarrhea",
            "Chronic diarrhea (IBS-associated, under physician guidance)",
        ],
        "side_effects": {
            "common": ["Constipation", "Abdominal cramping", "Nausea"],
            "rare_serious": ["Serious cardiac events with overdose"],
        },
        "key_warnings": [
            "Do NOT exceed recommended OTC dose (8 mg/day)",
            "Do not use with high fever or blood in stool",
            "Do not use for diarrhea caused by antibiotics (C. diff risk)",
            "High doses associated with serious cardiac arrhythmias",
        ],
        "storage": "Room temperature.",
        "healthfirst_stock": True,
        "forms_available": ["2 mg capsules", "1 mg/5 mL liquid"],
    },
    "melatonin": {
        "brand_names": ["ZzzQuil Pure Zzzs", "Natrol", "various"],
        "category": "Sleep supplement (hormone)",
        "otc_available": True,
        "uses": [
            "Difficulty falling asleep",
            "Jet lag",
            "Shift-work sleep disruption",
            "Delayed sleep phase",
        ],
        "side_effects": {
            "common": ["Daytime drowsiness", "Dizziness", "Headache", "Vivid dreams (higher doses)"],
            "rare_serious": ["Interaction with blood thinners (increased bleeding risk)"],
        },
        "key_warnings": [
            "Start with lowest effective dose (0.5–1 mg)",
            "Doses >5 mg rarely more effective and may worsen sleep architecture",
            "Do not drive after taking",
            "Consult physician before using in children",
        ],
        "storage": "Cool, dry location away from light.",
        "healthfirst_stock": True,
        "forms_available": ["1 mg", "3 mg", "5 mg", "10 mg tablets", "gummies", "liquid drops"],
    },
    "hydrocortisone": {
        "brand_names": ["Cortaid", "Cortizone-10"],
        "category": "Topical corticosteroid (low potency)",
        "otc_available": True,
        "uses": [
            "Eczema and dermatitis",
            "Insect bites and stings",
            "Poison ivy/oak rash",
            "Minor skin irritations and rashes",
        ],
        "side_effects": {
            "common": ["Mild burning or stinging at application site"],
            "rare_serious": ["Skin thinning with prolonged use", "Systemic absorption (large area application)"],
        },
        "key_warnings": [
            "Do not use on face, groin, or underarms for more than 7 days without physician direction",
            "Do not use on open wounds or infected skin",
            "Keep away from eyes",
            "Not for children under 2 without physician guidance",
        ],
        "storage": "Room temperature.",
        "healthfirst_stock": True,
        "forms_available": ["1% cream", "1% ointment"],
    },
    "clotrimazole": {
        "brand_names": ["Lotrimin AF"],
        "category": "Topical antifungal",
        "otc_available": True,
        "uses": [
            "Athlete's foot (tinea pedis)",
            "Jock itch (tinea cruris)",
            "Ringworm (tinea corporis)",
            "Vaginal yeast infections (vaginal cream formulation)",
        ],
        "side_effects": {
            "common": ["Mild burning, stinging, or redness at site"],
            "rare_serious": ["Hypersensitivity/allergic reaction — discontinue if rash worsens"],
        },
        "key_warnings": [
            "For external use only",
            "Continue full treatment duration even if symptoms improve early",
            "Athlete's foot: treat for 4 weeks; jock itch/ringworm: 2 weeks",
        ],
        "storage": "Room temperature below 77°F.",
        "healthfirst_stock": True,
        "forms_available": ["1% cream", "1% solution", "2% vaginal cream"],
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
    "sudafed": "pseudoephedrine",
    "mucinex": "guaifenesin",
    "imodium": "loperamide",
    "cortaid": "hydrocortisone",
    "cortizone": "hydrocortisone",
    "lotrimin": "clotrimazole",
}


def _normalise(name: str) -> str:
    return _SYNONYMS.get(name.strip().lower(), name.strip().lower())


class MedicationInfoLookup:
    name = TOOL_NAME
    description = TOOL_DESCRIPTION
    schema = TOOL_SCHEMA

    async def execute(self, medication_name: str) -> Dict[str, Any]:
        key = _normalise(medication_name)
        info = _DB.get(key)

        if not info:
            return {
                "medication_name": medication_name,
                "found": False,
                "message": (
                    f"Detailed information for '{medication_name}' is not in our database. "
                    "Please ask a HealthFirst pharmacist for information about this medication."
                ),
            }

        return {
            "medication_name": medication_name,
            "found": True,
            **info,
            "healthfirst_availability": (
                "Available at HealthFirst Community Pharmacy"
                if info.get("healthfirst_stock")
                else "May need to be ordered — ask staff"
            ),
        }
