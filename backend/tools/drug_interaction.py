"""
Drug Interaction Checker Tool — local lookup for common drug-drug interactions.

Returns interaction severity (major / moderate / minor / none) and clinical guidance.
No external API required.
"""
import logging
from typing import Any, Dict, Tuple

logger = logging.getLogger(__name__)

TOOL_NAME = "check_drug_interaction"
TOOL_DESCRIPTION = (
    "Checks for known interactions between two medications. "
    "Returns the severity (major/moderate/minor/none) and clinical guidance. "
    "Use when a customer asks if two medications are safe to take together."
)
TOOL_SCHEMA = {
    "type": "object",
    "properties": {
        "drug1": {"type": "string", "description": "Name of the first medication."},
        "drug2": {"type": "string", "description": "Name of the second medication."},
    },
    "required": ["drug1", "drug2"],
}

# Interaction database: key = frozenset of normalised names → {severity, description, recommendation}
# Severity levels: major, moderate, minor, none
_INTERACTIONS: Dict[Tuple[str, str], Dict[str, str]] = {
    ("warfarin", "aspirin"): {
        "severity": "major",
        "description": "Both warfarin and aspirin increase bleeding risk. Aspirin inhibits platelet aggregation and can displace warfarin from protein-binding sites, raising INR unpredictably.",
        "recommendation": "Avoid concurrent use unless directed by a physician. Monitor INR closely if combination is necessary.",
    },
    ("warfarin", "ibuprofen"): {
        "severity": "major",
        "description": "Ibuprofen (and NSAIDs generally) inhibit platelet function and can cause GI bleeding. Combined with warfarin, this significantly increases major bleeding risk.",
        "recommendation": "Avoid combination. Use acetaminophen for pain relief instead. Inform your prescriber.",
    },
    ("warfarin", "naproxen"): {
        "severity": "major",
        "description": "Naproxen, like all NSAIDs, potentiates the anticoagulant effect of warfarin and increases GI bleeding risk.",
        "recommendation": "Avoid unless medically necessary. Use acetaminophen as safer alternative.",
    },
    ("warfarin", "acetaminophen"): {
        "severity": "moderate",
        "description": "Regular use of acetaminophen (>2 g/day for several days) can increase INR in warfarin patients, raising bleeding risk.",
        "recommendation": "Acceptable short-term at low doses. Avoid >2,000 mg/day for extended periods. Monitor INR.",
    },
    ("warfarin", "omeprazole"): {
        "severity": "moderate",
        "description": "Omeprazole inhibits CYP2C19, which metabolises the S-enantiomer of warfarin. This can increase warfarin levels and INR.",
        "recommendation": "Monitor INR more frequently when starting or stopping omeprazole.",
    },
    ("ibuprofen", "aspirin"): {
        "severity": "moderate",
        "description": "Ibuprofen can block aspirin's irreversible binding to COX-1 platelets, potentially reducing aspirin's cardioprotective effect. Also additive GI toxicity.",
        "recommendation": "Take aspirin at least 30 minutes before ibuprofen, or use acetaminophen for pain instead.",
    },
    ("ibuprofen", "naproxen"): {
        "severity": "major",
        "description": "Taking two NSAIDs together doubles the risk of GI bleeding, ulcers, and renal toxicity with no added benefit.",
        "recommendation": "Never take two NSAIDs simultaneously. Choose one.",
    },
    ("metronidazole", "alcohol"): {
        "severity": "major",
        "description": "Metronidazole inhibits aldehyde dehydrogenase, causing a disulfiram-like reaction with alcohol: severe nausea, vomiting, flushing, tachycardia.",
        "recommendation": "Avoid all alcohol during metronidazole treatment and for 48 hours after the last dose.",
    },
    ("acetaminophen", "alcohol"): {
        "severity": "moderate",
        "description": "Chronic alcohol use induces CYP2E1, increasing production of the hepatotoxic acetaminophen metabolite NAPQI. This raises the risk of liver damage at doses that are safe in non-drinkers.",
        "recommendation": "Limit acetaminophen to 2,000 mg/day or less if you drink regularly. Avoid if you drink heavily.",
    },
    ("omeprazole", "clopidogrel"): {
        "severity": "major",
        "description": "Omeprazole inhibits CYP2C19, the enzyme that activates clopidogrel (a prodrug). This reduces clopidogrel's antiplatelet effect, potentially increasing cardiovascular event risk.",
        "recommendation": "Consider using pantoprazole (weaker CYP2C19 inhibitor) as an alternative. Consult your physician.",
    },
    ("diphenhydramine", "lorazepam"): {
        "severity": "major",
        "description": "Both drugs cause CNS depression and sedation. Combined use dramatically increases sedation, cognitive impairment, respiratory depression, and fall risk.",
        "recommendation": "Avoid combination. Use non-sedating antihistamine (loratadine, cetirizine) if an antihistamine is needed.",
    },
    ("diphenhydramine", "alcohol"): {
        "severity": "major",
        "description": "Diphenhydramine is a CNS depressant. Combined with alcohol, sedation and impairment are greatly enhanced, increasing risk of accidents and respiratory depression.",
        "recommendation": "Do not drink alcohol while taking diphenhydramine.",
    },
    ("ibuprofen", "lisinopril"): {
        "severity": "moderate",
        "description": "NSAIDs like ibuprofen can reduce the antihypertensive effect of ACE inhibitors (e.g., lisinopril) and may worsen kidney function, particularly in at-risk patients.",
        "recommendation": "Use cautiously and for the shortest duration possible. Monitor blood pressure and kidney function.",
    },
    ("ibuprofen", "metformin"): {
        "severity": "minor",
        "description": "NSAIDs can reduce renal blood flow and impair metformin excretion, potentially increasing lactic acidosis risk (rare, mainly in patients with pre-existing renal impairment).",
        "recommendation": "Generally safe short-term in healthy patients. Use cautiously with kidney disease.",
    },
    ("simvastatin", "clarithromycin"): {
        "severity": "major",
        "description": "Clarithromycin strongly inhibits CYP3A4, the main enzyme metabolising simvastatin. This causes a dramatic increase in simvastatin levels, greatly elevating myopathy and rhabdomyolysis risk.",
        "recommendation": "Suspend simvastatin during clarithromycin therapy. Switch to a non-CYP3A4-metabolised statin (pravastatin, rosuvastatin) if concurrent therapy needed.",
    },
    ("metformin", "alcohol"): {
        "severity": "moderate",
        "description": "Both metformin and alcohol can cause lactic acidosis. Concurrent use, especially with heavy drinking, increases this risk.",
        "recommendation": "Avoid heavy alcohol use while taking metformin.",
    },
    ("melatonin", "warfarin"): {
        "severity": "moderate",
        "description": "Melatonin may have mild anticoagulant effects and can potentially increase warfarin's effect, raising INR.",
        "recommendation": "Monitor INR when starting or stopping melatonin. Inform your anticoagulation clinic.",
    },
    ("pseudoephedrine", "maoi"): {
        "severity": "major",
        "description": "MAO inhibitors prevent breakdown of sympathomimetic amines. Pseudoephedrine with an MAOI can cause severe hypertension (hypertensive crisis), which can be life-threatening.",
        "recommendation": "Contraindicated — do not use pseudoephedrine within 14 days of an MAOI.",
    },
    ("aspirin", "alcohol"): {
        "severity": "moderate",
        "description": "Aspirin and alcohol both irritate the gastric mucosa and inhibit platelet function. Combined use significantly increases the risk of GI bleeding.",
        "recommendation": "Avoid alcohol while taking aspirin, especially on a regular basis.",
    },
    ("loratadine", "ketoconazole"): {
        "severity": "moderate",
        "description": "Ketoconazole inhibits CYP3A4 and P-glycoprotein, increasing loratadine blood levels. This may increase the risk of loratadine side effects.",
        "recommendation": "Use with caution. Monitor for increased loratadine side effects.",
    },
}

# Build a normalised lookup: frozenset for order-independent matching
_LOOKUP: Dict[frozenset, Dict[str, str]] = {
    frozenset(pair): info for pair, info in _INTERACTIONS.items()
}

# Synonym mapping for common brand/generic names
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
    "nexium": "esomeprazole",
    "pepcid": "famotidine",
    "aspirin": "aspirin",
    "plavix": "clopidogrel",
    "coumadin": "warfarin",
    "zocor": "simvastatin",
    "lipitor": "atorvastatin",
    "flagyl": "metronidazole",
    "sudafed": "pseudoephedrine",
}


def _normalise(name: str) -> str:
    return _SYNONYMS.get(name.strip().lower(), name.strip().lower())


class DrugInteractionChecker:
    name = TOOL_NAME
    description = TOOL_DESCRIPTION
    schema = TOOL_SCHEMA

    async def execute(self, drug1: str, drug2: str) -> Dict[str, Any]:
        n1 = _normalise(drug1)
        n2 = _normalise(drug2)

        if n1 == n2:
            return {
                "drug1": drug1,
                "drug2": drug2,
                "severity": "none",
                "description": "These appear to be the same medication.",
                "recommendation": "Do not double-dose. Take only the prescribed or recommended amount.",
            }

        key = frozenset({n1, n2})
        result = _LOOKUP.get(key)

        if result:
            return {
                "drug1": drug1,
                "drug2": drug2,
                **result,
            }

        # Not in database — return a safe "unknown" response
        return {
            "drug1": drug1,
            "drug2": drug2,
            "severity": "unknown",
            "description": (
                f"No known interaction found between {drug1} and {drug2} in our database. "
                "This does not guarantee safety — our database covers common interactions only."
            ),
            "recommendation": (
                "Please consult our pharmacist or your physician to verify this combination is safe "
                "for your specific health situation."
            ),
        }
