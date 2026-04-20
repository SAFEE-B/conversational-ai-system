"""Generates 60 synthetic pharmacy documents for RAG corpus."""
import os

DOCS_DIR = os.path.join(os.path.dirname(__file__), "..", "documents")
os.makedirs(DOCS_DIR, exist_ok=True)

docs = {
    # --- OTC MEDICATION GUIDES (20) ---
    "acetaminophen_guide.txt": """
Acetaminophen (Tylenol) – Patient Guide
HealthFirst Community Pharmacy

WHAT IS ACETAMINOPHEN?
Acetaminophen is a widely used over-the-counter (OTC) pain reliever and fever reducer. It is available under brand names such as Tylenol, Panadol, and Excedrin.

USES:
- Mild to moderate pain relief (headache, toothache, backache, menstrual cramps, muscle aches)
- Fever reduction in adults and children
- Arthritis pain relief (temporarily)

DOSAGE (ADULTS):
- Standard dose: 325–650 mg every 4–6 hours as needed
- Extended-release: 650 mg every 8 hours
- Maximum daily dose: 4,000 mg (3,000 mg if you drink alcohol regularly)

DOSAGE (CHILDREN):
- Dosed by weight: 10–15 mg/kg every 4–6 hours
- Do not exceed 5 doses in 24 hours

SIDE EFFECTS:
Acetaminophen is generally well-tolerated at recommended doses. Rare side effects include skin rash, nausea, and stomach pain.

WARNINGS:
- Do NOT exceed the maximum daily dose — overdose causes severe liver damage
- Avoid alcohol while taking acetaminophen
- Check all other medications for acetaminophen content (many cold/flu products contain it)
- Consult a doctor if pain persists more than 10 days or fever exceeds 3 days

STORAGE:
Store at room temperature (59–77°F). Keep away from moisture and children.

AVAILABILITY AT HEALTHFIRST:
Available OTC in 325 mg, 500 mg, and 650 mg (ER) tablets and capsules. Liquid formulations available for children.
""",

    "ibuprofen_guide.txt": """
Ibuprofen (Advil / Motrin) – Patient Guide
HealthFirst Community Pharmacy

WHAT IS IBUPROFEN?
Ibuprofen is a nonsteroidal anti-inflammatory drug (NSAID) available OTC for pain, fever, and inflammation. Common brand names include Advil and Motrin.

USES:
- Headache, dental pain, menstrual cramps, muscle aches, minor arthritis
- Fever reduction
- Anti-inflammatory conditions (sprains, bruises)

DOSAGE (ADULTS):
- 200–400 mg every 4–6 hours as needed
- Maximum: 1,200 mg/day OTC (up to 3,200 mg/day under physician supervision)
- Take with food or milk to reduce stomach upset

DOSAGE (CHILDREN 6 months–12 years):
- 5–10 mg/kg every 6–8 hours
- Maximum 40 mg/kg/day
- Do not use in children under 6 months without doctor guidance

SIDE EFFECTS:
- Common: stomach upset, nausea, heartburn
- Less common: dizziness, headache, rash
- Serious (rare): gastrointestinal bleeding, kidney problems, elevated blood pressure

CONTRAINDICATIONS:
- Avoid if allergic to aspirin or other NSAIDs
- Use cautiously with stomach ulcers, kidney disease, or heart conditions
- Avoid during the third trimester of pregnancy

WARNINGS:
- Increases risk of cardiovascular events (heart attack, stroke) with long-term high-dose use
- Take the lowest effective dose for the shortest duration

STORAGE:
Store below 77°F, away from moisture. Keep out of reach of children.

AVAILABILITY AT HEALTHFIRST:
Available OTC in 200 mg tablets/capsules and liquid-gels.
""",

    "aspirin_guide.txt": """
Aspirin – Patient Guide
HealthFirst Community Pharmacy

WHAT IS ASPIRIN?
Aspirin (acetylsalicylic acid) is an NSAID with analgesic, antipyretic, and antiplatelet properties. Brands include Bayer Aspirin and Ecotrin.

USES:
- Pain and fever relief
- Anti-inflammatory
- Low-dose (81 mg) for cardiovascular event prevention under doctor supervision

DOSAGE (ADULTS — PAIN/FEVER):
- 325–650 mg every 4–6 hours
- Maximum: 4,000 mg/day
- Do not use for fever in children or teenagers (risk of Reye's syndrome)

DOSAGE (CARDIOPROTECTIVE):
- 81 mg daily — only as directed by a physician

SIDE EFFECTS:
- GI irritation, nausea, stomach bleeding
- Tinnitus (ringing ears) at high doses
- Allergic reactions in aspirin-sensitive individuals

CONTRAINDICATIONS:
- Children and teenagers with viral infections (Reye's syndrome risk)
- Patients on blood thinners (warfarin, clopidogrel) — consult physician
- Peptic ulcer disease

INTERACTIONS:
- Warfarin: increased bleeding risk
- Ibuprofen: may reduce aspirin's antiplatelet effect if taken together
- Methotrexate: increased toxicity

STORAGE:
Store in a cool, dry place. Do not use if tablet smells strongly of vinegar (sign of decomposition).

AVAILABILITY AT HEALTHFIRST:
Available in 81 mg (low-dose), 325 mg, and 500 mg coated tablets.
""",

    "naproxen_guide.txt": """
Naproxen Sodium (Aleve) – Patient Guide
HealthFirst Community Pharmacy

WHAT IS NAPROXEN?
Naproxen sodium is an NSAID providing longer-lasting pain and fever relief — typically every 8–12 hours. Brand name: Aleve.

USES:
- Minor arthritis, backache, menstrual cramps, headache, toothache, muscle aches
- Fever reduction

DOSAGE (ADULTS 12+):
- 220 mg every 8–12 hours
- Maximum: 440 mg in 12 hours; 660 mg/day
- Take with a full glass of water and food

DOSAGE (OLDER ADULTS 65+):
- Start with 220 mg every 12 hours; do not exceed unless directed by physician

SIDE EFFECTS:
- GI upset, heartburn, nausea
- Drowsiness, dizziness
- Fluid retention, elevated blood pressure

CONTRAINDICATIONS:
- History of allergic reactions to NSAIDs
- Heart bypass surgery (perioperative)
- Severe kidney or liver disease

WARNINGS:
- Not for children under 12 without physician direction
- Avoid with other NSAIDs or aspirin (unless aspirin is for cardioprotection)
- Prolonged use increases cardiovascular and GI risk

AVAILABILITY AT HEALTHFIRST:
Available OTC in 220 mg tablets and liquid-gels.
""",

    "diphenhydramine_guide.txt": """
Diphenhydramine (Benadryl) – Patient Guide
HealthFirst Community Pharmacy

WHAT IS DIPHENHYDRAMINE?
Diphenhydramine is a first-generation antihistamine available OTC. It relieves allergy symptoms and acts as a sleep aid. Brand: Benadryl.

USES:
- Seasonal and year-round allergies (sneezing, runny nose, itchy/watery eyes)
- Allergic skin reactions (hives, itching)
- Short-term sleep aid (25–50 mg)
- Motion sickness

DOSAGE (ADULTS):
- Allergy/Sleep: 25–50 mg every 4–6 hours; maximum 300 mg/day
- Motion sickness: 25–50 mg 30 minutes before travel

DOSAGE (CHILDREN 6–11):
- 12.5–25 mg every 4–6 hours; maximum 150 mg/day
- Not recommended under age 2

SIDE EFFECTS:
- Drowsiness (significant — do not drive)
- Dry mouth, blurred vision, urinary retention
- Constipation, dizziness

CONTRAINDICATIONS:
- Glaucoma (narrow-angle)
- Enlarged prostate
- Taking MAO inhibitors

WARNINGS:
- Causes significant sedation — avoid driving or operating machinery
- Elderly patients are more sensitive to side effects
- Tolerance to sleep effects develops quickly — not for long-term sleep use

AVAILABILITY AT HEALTHFIRST:
Available in 25 mg and 50 mg tablets, liquid, and topical cream for itch relief.
""",

    "loratadine_guide.txt": """
Loratadine (Claritin) – Patient Guide
HealthFirst Community Pharmacy

WHAT IS LORATADINE?
Loratadine is a second-generation antihistamine that provides 24-hour allergy relief with minimal sedation. Brand: Claritin.

USES:
- Seasonal allergic rhinitis (hay fever): sneezing, runny nose, itchy/watery eyes
- Chronic idiopathic urticaria (hives)
- Allergic skin reactions

DOSAGE (ADULTS AND CHILDREN 6+):
- 10 mg once daily

DOSAGE (CHILDREN 2–5):
- 5 mg once daily (liquid or chewable tablet)

SIDE EFFECTS:
- Generally very well-tolerated
- Mild: headache, drowsiness (less than first-generation antihistamines), dry mouth, fatigue

CONTRAINDICATIONS:
- Hypersensitivity to loratadine or desloratadine

DRUG INTERACTIONS:
- Ketoconazole and erythromycin may increase loratadine blood levels
- Cimetidine may increase loratadine levels

ADVANTAGES OVER DIPHENHYDRAMINE:
- Non-sedating at standard doses
- 24-hour coverage with once-daily dosing
- Does not impair driving

AVAILABILITY AT HEALTHFIRST:
Available in 10 mg tablets, 5 mg chewables, and 5 mg/5mL syrup.
""",

    "cetirizine_guide.txt": """
Cetirizine (Zyrtec) – Patient Guide
HealthFirst Community Pharmacy

WHAT IS CETIRIZINE?
Cetirizine is a second-generation antihistamine providing 24-hour relief for allergies and hives. Brand: Zyrtec.

USES:
- Hay fever (allergic rhinitis), indoor/outdoor allergens
- Chronic hives (urticaria)
- Itchy skin and eyes

DOSAGE (ADULTS AND CHILDREN 6+):
- 5–10 mg once daily

DOSAGE (CHILDREN 2–5):
- 2.5 mg once daily; may increase to 5 mg

SIDE EFFECTS:
- Mild drowsiness (more than loratadine but less than diphenhydramine)
- Dry mouth, fatigue, headache
- Rare: urinary retention, dizziness

NOTES:
- Can be taken with or without food
- May cause slightly more drowsiness than loratadine — consider timing if driving
- Effect begins within 1 hour

AVAILABILITY AT HEALTHFIRST:
Available in 5 mg and 10 mg tablets, liquid gels, and 1 mg/mL syrup for children.
""",

    "omeprazole_guide.txt": """
Omeprazole (Prilosec OTC) – Patient Guide
HealthFirst Community Pharmacy

WHAT IS OMEPRAZOLE?
Omeprazole is a proton pump inhibitor (PPI) that reduces stomach acid. OTC version is for frequent heartburn (2+ days/week). Brand: Prilosec OTC.

USES:
- Frequent heartburn (not for immediate relief)
- Acid reflux symptoms
- Stomach protection during NSAID therapy (prescription-only use)

DOSAGE (ADULTS 18+):
- 20 mg once daily before a meal for 14 days
- Wait 4 months before repeating a 14-day course
- Not for occasional heartburn (use antacids instead)

SIDE EFFECTS:
- Headache, nausea, diarrhea, stomach pain
- Long-term use: low magnesium, vitamin B12 deficiency, increased fracture risk
- Possible increased risk of C. difficile infection with prolonged use

CONTRAINDICATIONS:
- Do not use if you have difficulty swallowing
- Consult doctor if heartburn with lightheadedness, sweating, or dizziness

DRUG INTERACTIONS:
- Clopidogrel: omeprazole may reduce antiplatelet effect — consult physician
- Methotrexate: increased toxicity
- Warfarin: may increase INR

WARNINGS:
- Not for immediate heartburn relief — takes 1–4 days for full effect
- If symptoms persist after 14 days, see a doctor

AVAILABILITY AT HEALTHFIRST:
Available OTC in 20 mg delayed-release capsules.
""",

    "loperamide_guide.txt": """
Loperamide (Imodium) – Patient Guide
HealthFirst Community Pharmacy

WHAT IS LOPERAMIDE?
Loperamide is an OTC antidiarrheal that slows bowel movements. Brand: Imodium A-D.

USES:
- Acute diarrhea (non-infectious)
- Traveler's diarrhea
- Chronic diarrhea associated with inflammatory bowel disease (IBS) — under physician guidance

DOSAGE (ADULTS):
- Initial: 4 mg, then 2 mg after each loose stool
- Maximum: 8 mg/day OTC (16 mg/day under physician supervision)
- Stop use if no improvement within 48 hours

DOSAGE (CHILDREN 6–11):
- Based on weight; follow package instructions carefully
- Not for children under 6 without physician direction

SIDE EFFECTS:
- Constipation, abdominal cramping
- Dizziness, nausea (less common)

WARNINGS:
- Do NOT use if diarrhea is accompanied by high fever or blood in stool
- Do NOT use for diarrhea caused by antibiotics (C. difficile risk)
- Do not exceed recommended dose — high doses are associated with serious cardiac events

AVAILABILITY AT HEALTHFIRST:
Available in 2 mg capsules and 1 mg/5 mL liquid.
""",

    "bismuth_subsalicylate_guide.txt": """
Bismuth Subsalicylate (Pepto-Bismol) – Patient Guide
HealthFirst Community Pharmacy

WHAT IS BISMUTH SUBSALICYLATE?
Bismuth subsalicylate is an OTC medication for upset stomach, nausea, diarrhea, and heartburn. Brand: Pepto-Bismol.

USES:
- Heartburn, indigestion, nausea
- Diarrhea, traveler's diarrhea
- Stomach upset

DOSAGE (ADULTS):
- 524 mg (30 mL or 2 tablets) every 30–60 minutes as needed
- Maximum: 8 doses in 24 hours

DOSAGE (CHILDREN 12+):
- Same as adult dose
- Not recommended under 12 due to aspirin-like component (Reye's syndrome risk)

SIDE EFFECTS:
- Temporary black tongue and dark stools (harmless, bismuth-related)
- Nausea, constipation at high doses
- Tinnitus at excessive doses (salicylate effect)

WARNINGS:
- Contains salicylate — avoid if allergic to aspirin
- Not for children/teenagers with viral illness (Reye's syndrome risk)
- Avoid if on blood thinners or for gout

AVAILABILITY AT HEALTHFIRST:
Available in original, cherry, and ultra-strength liquid; regular and maximum-strength chewable tablets.
""",

    "pseudoephedrine_guide.txt": """
Pseudoephedrine (Sudafed) – Patient Guide
HealthFirst Community Pharmacy

WHAT IS PSEUDOEPHEDRINE?
Pseudoephedrine is an OTC nasal decongestant that relieves sinus and nasal congestion. Brand: Sudafed.

USES:
- Nasal and sinus congestion from colds, flu, hay fever
- Eustachian tube congestion

DOSAGE (ADULTS AND CHILDREN 12+):
- Immediate-release (30 mg): 1–2 tablets every 4–6 hours; max 240 mg/day
- Extended-release (120 mg): 1 tablet every 12 hours

PURCHASE REQUIREMENT:
Pseudoephedrine must be purchased from the pharmacy counter (behind-the-counter) and requires a valid photo ID per the Combat Methamphetamine Epidemic Act. Purchase limits apply.

SIDE EFFECTS:
- Elevated blood pressure and heart rate
- Nervousness, dizziness, insomnia
- Difficulty urinating

CONTRAINDICATIONS:
- Severe hypertension or coronary artery disease
- MAO inhibitor use within 14 days
- Hyperthyroidism

WARNINGS:
- Use cautiously in patients with hypertension, diabetes, or enlarged prostate
- Not for children under 12 without physician direction

AVAILABILITY AT HEALTHFIRST:
Available from pharmacy counter in 30 mg immediate-release and 120 mg/240 mg extended-release tablets.
""",

    "guaifenesin_guide.txt": """
Guaifenesin (Mucinex) – Patient Guide
HealthFirst Community Pharmacy

WHAT IS GUAIFENESIN?
Guaifenesin is an expectorant that thins and loosens mucus in the airways, making coughs more productive. Brand: Mucinex.

USES:
- Chest congestion
- Cough associated with colds, bronchitis, sinusitis
- Helps clear mucus from the lungs and throat

DOSAGE (ADULTS):
- Immediate-release (200 mg): 200–400 mg every 4 hours; max 2,400 mg/day
- Extended-release (600 mg, 1,200 mg): 1 tablet every 12 hours

DOSAGE (CHILDREN 6–11):
- 100–200 mg every 4 hours; follow package instructions

SIDE EFFECTS:
- Generally well-tolerated
- Nausea, vomiting (take with food to reduce)
- Dizziness, headache (uncommon)

TIPS FOR USE:
- Drink plenty of fluids (8+ glasses of water daily) to enhance effectiveness
- Does not suppress cough — meant to make cough more productive

WARNINGS:
- Stop use and consult a doctor if cough persists more than 7 days
- Do not use for chronic cough (smoking, asthma, emphysema) without medical supervision

AVAILABILITY AT HEALTHFIRST:
Available in 200 mg immediate-release tablets and 600 mg/1,200 mg extended-release tablets.
""",

    "hydrocortisone_cream_guide.txt": """
Hydrocortisone Cream 1% – Patient Guide
HealthFirst Community Pharmacy

WHAT IS HYDROCORTISONE CREAM?
Hydrocortisone 1% is a mild topical corticosteroid that relieves skin inflammation, itching, and redness.

USES:
- Eczema, dermatitis (contact, seborrheic)
- Insect bites and stings
- Poison ivy, poison oak, poison sumac rash
- Minor skin irritations and rashes
- Psoriasis (mild, limited areas)

APPLICATION (ADULTS AND CHILDREN 2+):
- Apply a thin layer to affected area 2–4 times daily
- Gently rub in until absorbed
- Do not bandage tightly unless directed by physician

SIDE EFFECTS:
- Burning, stinging, or irritation at application site
- Skin thinning with prolonged use
- Rare: systemic absorption (with large area use)

WARNINGS:
- Do not use on face, groin, or underarms for more than 7 days without physician direction
- Do not use on open wounds or infected skin
- Keep away from eyes
- Not for use in children under 2 without physician guidance
- Do not use more than 7 days without consulting a doctor if no improvement

AVAILABILITY AT HEALTHFIRST:
Available OTC as 1% cream and ointment in various tube sizes.
""",

    "clotrimazole_guide.txt": """
Clotrimazole (Lotrimin) – Patient Guide
HealthFirst Community Pharmacy

WHAT IS CLOTRIMAZOLE?
Clotrimazole is an OTC antifungal medication that treats skin and nail fungal infections.

USES:
- Athlete's foot (tinea pedis)
- Jock itch (tinea cruris)
- Ringworm (tinea corporis)
- Yeast infections (vaginal formulation)

APPLICATION:
- Athlete's foot: Apply twice daily for 4 weeks
- Jock itch/Ringworm: Apply twice daily for 2 weeks
- Continue treatment for full duration even if symptoms improve early

SIDE EFFECTS:
- Mild burning, stinging, redness, or irritation at site
- Rash (discontinue if severe)

WARNINGS:
- For external use only — do not swallow
- Avoid contact with eyes
- Consult a physician if no improvement after recommended treatment period
- Do not use for diaper rash

AVAILABILITY AT HEALTHFIRST:
Available as 1% cream, solution, and vaginal cream (2%) at HealthFirst Pharmacy.
""",

    "neosporin_guide.txt": """
Neosporin (Triple Antibiotic Ointment) – Patient Guide
HealthFirst Community Pharmacy

WHAT IS NEOSPORIN?
Neosporin contains three antibiotics (neomycin, polymyxin B, bacitracin) that prevent infection in minor cuts, scrapes, and burns.

USES:
- Minor cuts, scrapes, and abrasions
- Minor burns
- Prevention of skin infection in small wounds

APPLICATION:
- Clean the wound thoroughly with soap and water
- Apply a small amount (thin layer) 1–3 times daily
- Cover with a sterile bandage if desired
- Use for no more than 1 week

SIDE EFFECTS:
- Mild: temporary burning or stinging on application
- Rare: allergic contact dermatitis (especially to neomycin)
- If rash, itching, or swelling occurs, discontinue and consult pharmacist

WARNINGS:
- For external use only — do not use in eyes
- Do not use on large wounds, deep puncture wounds, or animal bites
- Do not use for more than 1 week without medical advice
- Consult a doctor if wound does not heal or shows signs of spreading infection (increasing redness, warmth, pus)

AVAILABILITY AT HEALTHFIRST:
Available OTC in standard and pain-relief formulations.
""",

    "vitamin_c_guide.txt": """
Vitamin C (Ascorbic Acid) – Supplement Guide
HealthFirst Community Pharmacy

WHAT IS VITAMIN C?
Vitamin C is an essential water-soluble vitamin that acts as an antioxidant and supports immune function, collagen synthesis, and iron absorption.

RECOMMENDED DAILY INTAKE:
- Adult men: 90 mg/day
- Adult women: 75 mg/day
- Pregnant women: 85 mg/day
- Smokers: +35 mg/day above standard recommendation

COMMON SUPPLEMENTAL DOSES:
- General immune support: 500–1,000 mg/day
- Therapeutic: up to 2,000 mg/day (Upper Tolerable Limit)

BENEFITS:
- Supports immune system function
- Antioxidant protection against free radicals
- Enhances non-heme iron absorption
- Supports wound healing and collagen formation

SIDE EFFECTS (at high doses):
- GI upset, diarrhea, nausea (doses >2,000 mg/day)
- Kidney stones (in predisposed individuals at high doses)

FOOD SOURCES:
Citrus fruits, strawberries, bell peppers, broccoli, kiwi

STORAGE:
Store in a cool, dry location away from light. Chewable tablets should be sealed tightly.

AVAILABILITY AT HEALTHFIRST:
Available in 250 mg, 500 mg, and 1,000 mg tablets, gummies, and chewable forms.
""",

    "melatonin_guide.txt": """
Melatonin – Sleep Supplement Guide
HealthFirst Community Pharmacy

WHAT IS MELATONIN?
Melatonin is a hormone naturally produced by the pineal gland that regulates the sleep-wake cycle. Supplemental melatonin helps manage sleep issues.

USES:
- Difficulty falling asleep
- Jet lag
- Shift-work sleep disruption
- Delayed sleep phase syndrome

DOSAGE:
- Start with the lowest effective dose: 0.5–1 mg, 30–60 minutes before bed
- Typical OTC doses: 1–5 mg; most people do not need more than 3 mg
- Higher doses (>5 mg) are not more effective and may disrupt sleep architecture

SIDE EFFECTS:
- Daytime drowsiness
- Dizziness, nausea, headache
- Vivid dreams or nightmares (higher doses)

DRUG INTERACTIONS:
- Blood thinners (warfarin): may increase bleeding risk
- Diabetes medications: may affect blood sugar
- Immunosuppressants: may reduce effectiveness
- Sedatives/CNS depressants: additive effect

WARNINGS:
- Not recommended for long-term daily use without physician guidance
- Do not drive or operate machinery after taking melatonin
- Consult a doctor for children's dosing

AVAILABILITY AT HEALTHFIRST:
Available in 1 mg, 3 mg, 5 mg, and 10 mg tablets, gummies, and liquid drops.
""",

    "zinc_guide.txt": """
Zinc Supplements – Patient Guide
HealthFirst Community Pharmacy

WHAT IS ZINC?
Zinc is an essential trace mineral involved in immune function, wound healing, protein synthesis, and DNA synthesis.

RECOMMENDED DAILY INTAKE:
- Adult men: 11 mg/day
- Adult women: 8 mg/day
- Upper tolerable limit: 40 mg/day

USES FOR SUPPLEMENTATION:
- Immune support (particularly during cold and flu season)
- Wound healing
- Treatment of zinc deficiency
- Acne management (in some formulations)

COMMON FORMS:
- Zinc gluconate, zinc acetate, zinc sulfate, zinc picolinate
- Zinc lozenges for cold symptom relief (best taken within 24 hours of symptom onset)

SIDE EFFECTS:
- Nausea, vomiting, stomach cramps (most common when taken on empty stomach)
- Long-term high doses: copper deficiency, impaired immune function

DRUG INTERACTIONS:
- Reduces absorption of antibiotics (tetracyclines, fluoroquinolones) — space 2 hours apart
- Reduces absorption of iron supplements — space 2 hours apart

AVAILABILITY AT HEALTHFIRST:
Available in 15 mg, 25 mg, and 50 mg tablets and lozenges.
""",

    "omega3_guide.txt": """
Omega-3 Fish Oil – Supplement Guide
HealthFirst Community Pharmacy

WHAT ARE OMEGA-3 FATTY ACIDS?
Omega-3s (EPA and DHA) are essential polyunsaturated fatty acids important for heart, brain, and joint health.

RECOMMENDED DOSES:
- General health: 250–500 mg combined EPA+DHA per day
- High triglycerides: 2,000–4,000 mg/day (under physician supervision)
- Anti-inflammatory: 1,000–2,000 mg/day

BENEFITS:
- Cardiovascular: reduces triglycerides, mild blood pressure lowering
- Anti-inflammatory: benefits for arthritis and joint stiffness
- Brain health: supports cognitive function
- Eye health: DHA is a major structural component of the retina

FORMS AVAILABLE:
- Fish oil capsules (various concentrations)
- Algae-based omega-3 (vegetarian/vegan alternative)
- Liquid fish oil

SIDE EFFECTS:
- Fishy burp/aftertaste (enteric-coated forms reduce this)
- GI upset, loose stools at high doses
- Slight blood-thinning effect at high doses

DRUG INTERACTIONS:
- Blood thinners (warfarin): additive blood-thinning effect — consult physician
- Blood pressure medications: may have additive effect

TIPS:
- Take with food to reduce GI side effects
- Store in refrigerator to prevent rancidity

AVAILABILITY AT HEALTHFIRST:
Available in various concentrations (500 mg, 1,000 mg per capsule). Enteric-coated options available.
""",

    "probiotics_guide.txt": """
Probiotics – Supplement Guide
HealthFirst Community Pharmacy

WHAT ARE PROBIOTICS?
Probiotics are live beneficial bacteria and yeasts that support gut health when consumed in adequate amounts.

COMMON STRAINS:
- Lactobacillus acidophilus: IBS, antibiotic-associated diarrhea
- Bifidobacterium longum: constipation, IBS
- Lactobacillus rhamnosus GG: traveler's diarrhea, rotavirus
- Saccharomyces boulardii: C. difficile prevention, traveler's diarrhea

USES:
- Restoring gut flora after antibiotic use
- IBS symptom management
- Prevention of traveler's diarrhea
- Immune system support
- Vaginal health

DOSAGE:
- CFU (colony-forming units): 1–10 billion CFU/day for general wellness
- Higher doses (10–50 billion CFU) for specific conditions
- Best taken with a meal, or as directed

SIDE EFFECTS:
- Temporary bloating and gas (usually resolves in 1–2 weeks)
- Rare: serious infections in immunocompromised individuals

TIPS:
- Take probiotics 2 hours after antibiotics to prevent them being killed
- Refrigerated probiotics generally have higher viability
- Effectiveness is strain-specific

AVAILABILITY AT HEALTHFIRST:
Multiple brands and strains available. Ask our pharmacist for guidance on selecting the right probiotic.
""",

    # --- HEALTH CONDITIONS (15) ---
    "managing_headaches.txt": """
Managing Headaches – Patient Information
HealthFirst Community Pharmacy

TYPES OF HEADACHES:
1. Tension headaches: Most common; dull, band-like pressure around the head
2. Migraine: Throbbing pain, often one-sided; may include nausea, light/sound sensitivity
3. Cluster headaches: Severe pain around one eye; less common
4. Sinus headaches: Pressure/pain behind forehead, cheeks, or eyes; associated with sinus congestion

OTC TREATMENT OPTIONS:
- Tension/Mild pain: Acetaminophen (500–1,000 mg), Ibuprofen (200–400 mg), Aspirin (325–650 mg), Naproxen (220 mg)
- Migraine (OTC): Excedrin Migraine (acetaminophen + aspirin + caffeine)

NON-MEDICATION STRATEGIES:
- Rest in a quiet, dark room
- Apply cold or warm compress to forehead/neck
- Stay hydrated — dehydration is a common trigger
- Manage stress through relaxation techniques

WHEN TO SEE A DOCTOR:
- "Thunderclap" headache (sudden, worst headache of your life)
- Headache with fever, stiff neck, confusion, vision changes (possible meningitis)
- Headache after head injury
- Progressively worsening headaches
- Headaches more than 15 days/month (medication overuse headache risk)

PREVENTION:
- Maintain regular sleep schedule
- Stay hydrated
- Limit caffeine and alcohol
- Keep a headache diary to identify triggers

Our pharmacists at HealthFirst can help you select the appropriate pain reliever.
""",

    "cold_and_flu_guide.txt": """
Cold and Flu – Symptoms and OTC Treatment Guide
HealthFirst Community Pharmacy

COLD VS. FLU:
- Cold: Gradual onset; mainly affects nose/throat; mild fever possible; rarely serious
- Flu: Sudden onset; body aches, high fever (100–104°F), fatigue, headache; can be serious

OTC TREATMENT — SYMPTOMS:
Fever and body aches:
- Acetaminophen 500–1,000 mg every 4–6 hours (max 4,000 mg/day)
- Ibuprofen 200–400 mg every 4–6 hours (with food)

Nasal congestion:
- Pseudoephedrine 30–60 mg every 4–6 hours (from pharmacy counter)
- Oxymetazoline nasal spray (use max 3 days to avoid rebound congestion)

Runny nose/sneezing:
- Loratadine 10 mg once daily (non-drowsy)
- Diphenhydramine 25–50 mg every 4–6 hours (sedating)

Cough:
- Productive (wet) cough: Guaifenesin 200–400 mg every 4 hours
- Dry/nonproductive cough: Dextromethorphan 10–20 mg every 4 hours

GENERAL CARE:
- Rest and stay well-hydrated (water, clear broths, herbal teas)
- Honey (1–2 teaspoons) can help soothe cough in adults and children over 1
- Saline nasal rinse to clear congestion

WHEN TO SEE A DOCTOR:
- Fever above 103°F (39.4°C) or fever lasting more than 3 days
- Difficulty breathing or shortness of breath
- Severe chest pain or pressure
- Confusion or altered mental status
- Symptoms not improving after 10 days

Note: Antibiotics do not treat viral illnesses (colds and flu).
""",

    "allergy_relief.txt": """
Allergy Relief – Patient Information
HealthFirst Community Pharmacy

TYPES OF ALLERGIES MANAGED OTC:
1. Seasonal allergic rhinitis (hay fever)
2. Perennial allergic rhinitis (year-round: dust mites, pet dander, mold)
3. Allergic conjunctivitis (itchy/watery eyes)
4. Hives (urticaria)

COMMON TRIGGERS:
- Outdoor: pollen (tree, grass, weed), mold spores
- Indoor: dust mites, pet dander, cockroaches, mold
- Food allergies: nuts, shellfish, dairy (require physician management if severe)

OTC ANTIHISTAMINES:
Non-sedating (preferred for daytime use):
- Loratadine (Claritin) 10 mg once daily
- Cetirizine (Zyrtec) 10 mg once daily — may cause mild drowsiness
- Fexofenadine (Allegra) 180 mg once daily — least sedating

Sedating (useful for night time or itching):
- Diphenhydramine (Benadryl) 25–50 mg every 4–6 hours

OTC NASAL SPRAYS:
- Fluticasone propionate (Flonase) — steroid, most effective for nasal symptoms; takes days for full effect
- Cromolyn sodium (NasalCrom) — preventive, begin before allergy season

OTC EYE DROPS:
- Ketotifen (Zaditor) — antihistamine eye drops, 1 drop twice daily

NON-MEDICATION STRATEGIES:
- Keep windows closed during high pollen periods
- Use HEPA air purifiers indoors
- Shower after being outdoors
- Monitor local pollen counts

Ask our HealthFirst pharmacist which antihistamine is best suited for your symptoms.
""",

    "digestive_health.txt": """
Digestive Health – Common Conditions and OTC Remedies
HealthFirst Community Pharmacy

ACID REFLUX / HEARTBURN:
- Antacids (calcium carbonate, magnesium hydroxide): fast relief within minutes
  - Tums, Rolaids: chew 2–4 tablets as needed after meals
- H2 Blockers (famotidine/Pepcid, ranitidine): 10–20 mg, longer relief
- PPI (omeprazole/Prilosec OTC): 20 mg daily for 14 days — for frequent heartburn only

IBS (IRRITABLE BOWEL SYNDROME) — OTC OPTIONS:
- For diarrhea-predominant IBS: loperamide (Imodium) as needed
- For constipation-predominant IBS: psyllium fiber, MiraLax (polyethylene glycol)
- Gas/bloating: simethicone (Gas-X) 125 mg after meals

CONSTIPATION:
- Bulk-forming: psyllium (Metamucil), methylcellulose (Citrucel) — gentle, daily use safe
- Osmotic: MiraLax (polyethylene glycol) — 17 g once daily in beverage
- Stimulant (short-term only): bisacodyl (Dulcolax), senna

DIARRHEA:
- Loperamide (Imodium A-D) — 4 mg initial dose, 2 mg after each loose stool
- Bismuth subsalicylate (Pepto-Bismol) — useful for traveler's diarrhea
- Rehydration: oral rehydration salts (Pedialyte for children)

NAUSEA:
- Bismuth subsalicylate (Pepto-Bismol)
- Dimenhydrinate (Dramamine) for motion sickness-related nausea
- Vitamin B6 (25 mg three times daily) for mild nausea — often used in pregnancy

WHEN TO SEE A DOCTOR:
- Blood in stool, unexplained weight loss
- Diarrhea lasting more than 2 days in adults (24 hours in infants)
- Severe abdominal pain
- Fever with GI symptoms
""",

    "fever_management.txt": """
Fever Management – Patient Information
HealthFirst Community Pharmacy

WHAT IS A FEVER?
A fever is a body temperature above 100.4°F (38°C). It is typically the body's immune response to infection.

TEMPERATURE RANGES:
- Normal: 97–99°F (36.1–37.2°C)
- Low-grade fever: 99–100.4°F
- Fever: ≥100.4°F (38°C)
- High fever: ≥103°F (39.4°C)
- Dangerous: ≥104°F (40°C) — seek immediate medical care

OTC FEVER REDUCERS:
Adults:
- Acetaminophen 500–1,000 mg every 4–6 hours (max 4,000 mg/day)
- Ibuprofen 200–400 mg every 4–6 hours (max 1,200 mg/day OTC)
- Aspirin 325–650 mg every 4–6 hours (adults only)

Children:
- Acetaminophen: 10–15 mg/kg every 4–6 hours
- Ibuprofen: 5–10 mg/kg every 6–8 hours (not for infants under 6 months)
- NEVER give aspirin to children or teenagers (Reye's syndrome risk)

GENERAL CARE:
- Stay hydrated — fever increases fluid loss
- Light clothing and bedding
- Cool (not cold) damp cloth on forehead
- Room temperature should be comfortable — do not over-bundle

WHEN TO SEEK EMERGENCY CARE:
- Infants under 3 months: any fever ≥100.4°F
- Children: fever >104°F, or fever with rash, stiff neck, difficulty breathing
- Adults: fever >103°F lasting more than 3 days, difficulty breathing, confusion

Note: Treating a moderate fever is optional — fever can help fight infection.
""",

    "wound_care.txt": """
Wound Care and First Aid – Patient Guide
HealthFirst Community Pharmacy

BASIC WOUND CARE (MINOR CUTS, SCRAPES, ABRASIONS):
1. Stop the bleeding: Apply gentle pressure with a clean cloth for 5–15 minutes
2. Clean the wound: Rinse thoroughly with clean running water for 5 minutes; use mild soap around (not in) the wound
3. Apply antiseptic (optional): Hydrogen peroxide or iodine can delay healing — saline rinse is preferred
4. Apply antibiotic ointment: Thin layer of Neosporin or Bacitracin to prevent infection
5. Cover the wound: Use an adhesive bandage or sterile gauze

WOUND CARE PRODUCTS AT HEALTHFIRST:
- Antiseptics: Hydrogen peroxide 3%, povidone-iodine (Betadine)
- Antibiotic ointments: Neosporin, Bacitracin
- Dressings: Adhesive bandages, sterile gauze, non-adherent pads
- Medical tape: Paper, silk, waterproof

SIGNS OF INFECTION (see a doctor):
- Increasing redness, warmth, or swelling around the wound
- Pus or discharge
- Red streaks spreading from the wound
- Fever (≥100.4°F)
- Wound not healing after 2 weeks

SPECIAL WOUND TYPES:
- Deep cuts (may need stitches): Apply pressure, go to emergency care
- Animal bites: Clean thoroughly; seek medical care — may need rabies prophylaxis
- Burns: Cool water for 10–20 minutes; do NOT use ice; cover loosely; see doctor for burns larger than your palm

TETANUS:
- Ensure tetanus vaccination is up to date (booster every 10 years; every 5 years for dirty wounds)
""",

    "pain_management.txt": """
Pain Management – OTC Options Guide
HealthFirst Community Pharmacy

TYPES OF PAIN AND RECOMMENDED OTC TREATMENTS:

HEADACHE:
- Acetaminophen 500–1,000 mg or Ibuprofen 200–400 mg
- Excedrin Migraine for migraine headaches

BACK PAIN:
- NSAIDs (ibuprofen, naproxen) — preferred for inflammatory back pain
- Acetaminophen — for patients who cannot take NSAIDs
- Topical: diclofenac gel (Voltaren OTC), lidocaine patches, menthol/camphor rubs (Bengay, Icy Hot)

MUSCLE ACHES AND STRAINS:
- Ibuprofen 400 mg every 6 hours for 3–5 days
- Naproxen 220 mg every 8–12 hours
- Topical NSAIDs: Voltaren Arthritis Pain Gel — apply 4x/day

DENTAL PAIN:
- Acetaminophen or ibuprofen (alternating can provide better coverage)
- Topical benzocaine gel (Orajel) for temporary numbing of gums/teeth

ARTHRITIS PAIN:
- Acetaminophen (first-line for osteoarthritis per guidelines)
- Ibuprofen or naproxen for inflammatory arthritis flares
- Topical: Voltaren OTC gel, capsaicin cream

MENSTRUAL CRAMPS (DYSMENORRHEA):
- NSAIDs are most effective: Ibuprofen 400–600 mg every 6 hours, started 1–2 days before expected period
- Naproxen 440 mg loading, then 220 mg every 8 hours

TOPICAL ANALGESICS AVAILABLE AT HEALTHFIRST:
- Menthol-based (Icy Hot, Bengay, Biofreeze)
- Capsaicin cream (Zostrix)
- Diclofenac gel 1% (Voltaren OTC)
- Lidocaine patches

Ask our pharmacist for personalized pain management recommendations.
""",

    "sleep_disorders.txt": """
Sleep Disorders and OTC Sleep Aids
HealthFirst Community Pharmacy

COMMON SLEEP PROBLEMS:
1. Transient insomnia: Difficulty sleeping due to stress, travel, or schedule changes
2. Chronic insomnia: Persistent difficulty falling or staying asleep (>3 nights/week for >3 months)
3. Jet lag: Disrupted sleep-wake cycle from rapid time zone changes

OTC SLEEP AIDS:

Antihistamine-based (sedating side effect):
- Diphenhydramine (ZzzQuil, Benadryl, Unisom SleepTabs): 25–50 mg at bedtime
- Doxylamine succinate (Unisom SleepTabs): 25 mg at bedtime
- Caution: tolerance develops quickly; not for chronic use

Melatonin (hormone-based):
- 0.5–3 mg, 30–60 minutes before bed
- Best for jet lag and delayed sleep phase
- Non-habit forming; safer for longer-term occasional use

Herbal Supplements (evidence limited):
- Valerian root: 300–600 mg at bedtime
- Chamomile tea: mild relaxant
- Magnesium glycinate: may improve sleep quality

SLEEP HYGIENE TIPS (FIRST-LINE TREATMENT):
- Maintain a consistent sleep/wake schedule — even on weekends
- Avoid screens 1 hour before bed
- Keep bedroom cool, dark, and quiet
- Limit caffeine after noon
- Avoid large meals, alcohol, and nicotine near bedtime
- Regular physical activity (but not within 2 hours of bedtime)

WHEN TO SEE A DOCTOR:
- Chronic insomnia (>3 months)
- Suspected sleep apnea (loud snoring, waking gasping)
- Restless legs syndrome
- Excessive daytime sleepiness despite adequate night sleep
""",

    "skin_conditions.txt": """
Common Skin Conditions and OTC Treatments
HealthFirst Community Pharmacy

ECZEMA (ATOPIC DERMATITIS):
- Symptoms: Dry, itchy, red, inflamed skin; may have blisters
- OTC Treatment:
  - Hydrocortisone 1% cream: apply 2–4x/day during flares (short-term)
  - Moisturizers (Cetaphil, CeraVe, Eucerin): apply daily to maintain skin barrier
  - Antihistamines (diphenhydramine at night) for itch relief
  - Colloidal oatmeal baths (Aveeno) to soothe inflammation

CONTACT DERMATITIS (rash from irritant/allergen):
- OTC Treatment:
  - Hydrocortisone 1%: 2–4x/day for up to 7 days
  - Calamine lotion for mild cases
  - Diphenhydramine for itch

PSORIASIS (mild, limited areas):
- OTC Treatment:
  - Coal tar shampoo (T-Gel) for scalp psoriasis
  - Salicylic acid lotions for scaling
  - Hydrocortisone 1% for mild flares

ACNE:
- Benzoyl peroxide 2.5–10%: kills bacteria; start low to avoid irritation
- Salicylic acid 0.5–2%: unclogs pores; best for blackheads/whiteheads
- Adapalene 0.1% gel (Differin) — first OTC retinoid; use nightly

FUNGAL INFECTIONS:
- Clotrimazole 1% or miconazole 2% for athlete's foot, ringworm, jock itch

DRY SKIN:
- Thick moisturizers: petroleum jelly, CeraVe Moisturizing Cream, Eucerin
- Apply immediately after bathing to lock in moisture

SUNBURN:
- Cool water/cool compresses
- Aloe vera gel (refrigerated for extra relief)
- Ibuprofen for pain and inflammation
- Moisturizer with no fragrance
""",

    "cough_treatment.txt": """
Cough Treatment – Patient Guide
HealthFirst Community Pharmacy

TYPES OF COUGH:
1. Productive (wet) cough: Produces mucus; associated with infections or bronchitis
2. Dry (non-productive) cough: Tickling, irritating, no mucus; common post-viral, from ACE inhibitors, allergies
3. Croup cough: Barking cough in children; stridor; usually viral
4. Pertussis (whooping cough): Severe, prolonged coughing spells; vaccination-preventable

OTC COUGH MEDICATIONS:

Expectorants (loosen mucus for productive coughs):
- Guaifenesin (Mucinex): 200–400 mg every 4 hours; drink plenty of water

Cough suppressants (for dry cough):
- Dextromethorphan (DXM): 10–20 mg every 4 hours; max 120 mg/day
- Available in Robitussin DM, NyQuil, Delsym

Combination products:
- Robitussin DM: guaifenesin + dextromethorphan (both wet and dry cough)
- NyQuil Cold & Flu: DXM + antihistamine + acetaminophen (nighttime)

Topical:
- Menthol lozenges (Halls, Ricola): soothes throat irritation
- Vicks VapoRub (topical): menthol/camphor on chest or under nose

NON-MEDICATION APPROACHES:
- Stay well-hydrated
- Honey: 1–2 teaspoons (adults); 1/2 teaspoon (children 1–5)
- Steam inhalation or humidifier
- Elevate head while sleeping

WHEN TO SEE A DOCTOR:
- Cough lasting more than 3 weeks
- Coughing up blood or rust-colored mucus
- Shortness of breath, wheezing, chest pain
- High fever with cough
- Suspected pertussis (whooping sound, coughing fits)
""",

    "acid_reflux.txt": """
Acid Reflux and Heartburn – Patient Guide
HealthFirst Community Pharmacy

WHAT IS ACID REFLUX / GERD?
Acid reflux occurs when stomach acid flows back into the esophagus, causing heartburn (burning chest sensation). Frequent reflux (≥2x/week) is called GERD (Gastroesophageal Reflux Disease).

SYMPTOMS:
- Heartburn (burning in chest, worse after eating or lying down)
- Regurgitation (sour/bitter taste in throat/mouth)
- Difficulty swallowing
- Chronic cough, hoarseness
- Feeling of food stuck in throat

OTC TREATMENT OPTIONS:

Antacids (fastest relief — within minutes):
- Calcium carbonate (Tums): 500–1,000 mg after meals and at bedtime
- Aluminum/magnesium hydroxide (Maalox, Mylanta)
- Sodium bicarbonate (Alka-Seltzer) — avoid with high blood pressure

H2 Blockers (reduce acid production — 30–45 min onset, lasts hours):
- Famotidine (Pepcid AC): 10–20 mg before meals or at bedtime
- Best for predictable heartburn (before a known trigger meal)

Proton Pump Inhibitors (most powerful — days for full effect):
- Omeprazole (Prilosec OTC) 20 mg once daily for 14 days
- Lansoprazole (Prevacid 24HR) 15 mg once daily for 14 days
- For frequent heartburn (≥2 days/week)

LIFESTYLE MODIFICATIONS (key to long-term management):
- Eat smaller, more frequent meals
- Avoid trigger foods: spicy food, citrus, tomato, chocolate, coffee, alcohol, fatty foods
- Do not lie down within 2–3 hours after eating
- Elevate head of bed 6–8 inches
- Maintain healthy weight
- Quit smoking

WHEN TO SEE A DOCTOR:
- Symptoms not responding to OTC therapy after 2 weeks
- Difficulty swallowing or painful swallowing
- Unexplained weight loss
- Vomiting blood or black/tarry stools
""",

    "eye_care_otc.txt": """
Eye Care – OTC Products and Guidance
HealthFirst Community Pharmacy

COMMON EYE CONDITIONS MANAGED OTC:

DRY EYES:
- Artificial tears (Systane, Refresh, TheraTears): 1–2 drops as needed; preservative-free for frequent use (>4x/day)
- Gel drops for overnight use (Systane Gel, GenTeal Gel)
- Avoid: reading in dry/windy environments; use humidifier indoors

ALLERGIC CONJUNCTIVITIS (itchy, watery, red eyes from allergens):
- Ketotifen fumarate (Zaditor, Alaway): antihistamine eye drops; 1 drop twice daily
- Naphazoline/pheniramine (Naphcon-A, Visine-A): decongestant + antihistamine; for short-term use only

RED EYE (due to minor irritation):
- Naphazoline (Visine Original, Clear Eyes): vasoconstrictor; reduces redness; use max 3 days
- Note: does not treat underlying cause; chronic redness should be evaluated

EYE WASH:
- Sterile saline eyewash (Bausch & Lomb Eye Wash): for flushing out foreign bodies, mild irritants, and chlorine

CONTACT LENS CARE:
- Multipurpose solution (ReNu, Optifree): daily cleaning/rinsing/storage
- Hydrogen peroxide systems (Clear Care): deep clean; NEVER put in eye directly
- Saline only: rinsing; not for storing

FIRST AID — CHEMICAL SPLASH:
- Flush immediately with clean water or eyewash for 15–20 minutes
- Seek emergency medical care afterward

WHEN TO SEE AN EYE DOCTOR:
- Eye pain or foreign body that cannot be flushed out
- Sudden vision changes or vision loss
- Severe redness not responding to OTC drops
- Discharge (green/yellow pus) suggesting bacterial infection
- Flashes of light, floaters suddenly appearing
""",

    "oral_health.txt": """
Oral Health – OTC Products and Patient Guide
HealthFirst Community Pharmacy

TOOTHACHE PAIN RELIEF:
- Benzocaine topical gel (Orajel, Anbesol): apply directly to affected tooth/gum for temporary numbing
- Acetaminophen or ibuprofen: systemic pain relief (ibuprofen preferred for dental inflammation)
- Clove oil: natural alternative; apply with cotton ball to affected area

CANKER SORES (aphthous ulcers):
- Benzocaine gel (Orabase with Benzocaine): numbs pain on contact
- Amlexanox paste (Aphthasol — OTC in some stores): reduces healing time
- Mouthwash with hydrogen peroxide or salt water rinse

COLD SORES (herpes labialis):
- Docosanol 10% cream (Abreva): OTC antiviral; apply at first tingle sign 5x/day; shortens duration
- Lysine supplements may reduce frequency
- Avoid touching sore; do not share utensils

GUM HEALTH:
- Antiseptic mouthwash (Listerine): reduces plaque and gingivitis; use twice daily
- Chlorhexidine gluconate (by prescription for severe gingivitis)
- Water flossers: effective for removing plaque between teeth

FLUORIDE PRODUCTS:
- Standard fluoride toothpaste: 1,000–1,100 ppm fluoride (Colgate Total, Crest Pro-Health)
- High-fluoride toothpaste (Prevident 5000): prescription-only for high cavity risk
- Fluoride mouth rinse (ACT): for additional cavity protection; rinse after brushing

DRY MOUTH (XEROSTOMIA):
- Biotene products (mouthwash, gel, spray): specially formulated for dry mouth
- Stay well-hydrated; chew sugar-free gum to stimulate saliva
- Avoid alcohol-based mouthwashes (drying effect)

AVAILABILITY AT HEALTHFIRST:
All listed OTC oral health products available. Ask our pharmacist for recommendations.
""",

    # --- PHARMACY POLICIES (10) ---
    "prescription_refill_policy.txt": """
Prescription Refill Policy
HealthFirst Community Pharmacy

REFILL PROCESS:
At HealthFirst Community Pharmacy, we make refilling your prescriptions convenient and simple.

HOW TO REQUEST A REFILL:
1. In-store: Bring your prescription bottle to the pharmacy counter
2. Phone: Call us during pharmacy hours and provide your Rx number
3. Pharmacy website/app: Submit a refill request online 24/7
4. Auto-refill enrollment: Enroll in our auto-refill program for eligible maintenance medications

PROCESSING TIMES:
- Standard refills: Ready within 30 minutes for in-store pickup
- Complex or special-order medications: May require 24–48 hours
- Controlled substances: Cannot be processed early; must comply with state refill restrictions

CONTROLLED SUBSTANCES:
- Schedule II (e.g., Adderall, OxyContin): Require a new written or e-prescription for each fill. No refills permitted.
- Schedule III–V: Limited refills; cannot be refilled earlier than allowed by law

EARLY REFILL POLICY:
- Most medications may be refilled when 75% of the previous supply is used (approximately 3 days early for a 30-day supply)
- Exceptions apply for travel or vacation overrides — ask the pharmacist for a vacation supply

INSURANCE:
- Insurance plans often limit early refills — check with your insurer or ask our staff
- Out-of-pocket pricing available if insurance is not accepted for early refills

TRANSFER REFILLS:
- Prescriptions can be transferred from other pharmacies (except Schedule II)
- Call us or have the other pharmacy initiate the transfer

PHARMACY HOURS FOR REFILL PICKUP:
Monday–Saturday: 8:00 AM – 9:00 PM
Sunday: 10:00 AM – 6:00 PM
""",

    "insurance_and_billing.txt": """
Insurance and Billing Information
HealthFirst Community Pharmacy

ACCEPTED INSURANCE PLANS:
HealthFirst Community Pharmacy accepts most major insurance and prescription benefit plans, including:
- Most commercial health insurance plans
- Medicare Part D
- Medicaid and state assistance programs
- Workers' Compensation
- Most PBM (Pharmacy Benefit Manager) networks

HOW TO USE YOUR INSURANCE:
1. Provide your insurance card at the time of prescription drop-off
2. Ensure the pharmacy has up-to-date insurance information on file
3. We will verify your coverage and provide you with your copay amount before dispensing

COPAY AND COST TRANSPARENCY:
- We will always inform you of the cost before dispensing
- If your medication is expensive, ask about generic alternatives or manufacturer coupons

GENERIC MEDICATIONS:
- We substitute generics for brand-name medications whenever legally permitted and unless "dispense as written" is specified
- Generics contain the same active ingredients as brand-name equivalents and meet the same FDA standards
- Generics can reduce copays significantly

PATIENT ASSISTANCE AND COUPONS:
- GoodRx, SingleCare, and similar discount cards accepted (may be better than insurance in some cases)
- We can assist with manufacturer patient assistance programs for high-cost brand medications

BILLING QUESTIONS:
- Contact us at the pharmacy counter or by phone during business hours
- Itemized receipts available upon request for FSA/HSA submissions
- Flexible Spending Account (FSA) and Health Savings Account (HSA) cards accepted
""",

    "medication_returns_policy.txt": """
Medication Returns and Disposal Policy
HealthFirst Community Pharmacy

MEDICATION RETURNS:
For safety and regulatory reasons, HealthFirst Community Pharmacy is generally unable to accept returned medications that have left the pharmacy. This policy applies regardless of the reason.

WHY WE CANNOT ACCEPT RETURNS:
- Once a medication leaves our pharmacy, we cannot verify it has been stored properly or remained tamper-free
- Federal and state regulations prohibit the re-dispensing of returned medications

EXCEPTIONS:
- Dispensing errors made by our pharmacy staff: If we dispensed the wrong medication, wrong dose, or wrong quantity, we will correct this at no additional charge and provide the proper medication
- Please bring the medication back promptly and retain all packaging

REFUNDS:
- If we made an error, a full refund will be provided
- Other refund requests will be reviewed on a case-by-case basis — please speak with the pharmacist in charge

MEDICATION DISPOSAL — HOW TO SAFELY DISPOSE OF UNUSED MEDICATIONS:

Drug Take-Back Programs (preferred):
- HealthFirst Pharmacy participates in DEA-authorized drug take-back events (schedule posted in-store)
- Ask the pharmacy about our in-store medication drop box availability

At-Home Disposal:
- Mix medication with an undesirable substance (coffee grounds, dirt, or kitty litter)
- Place in a sealed bag
- Remove personal information from labels
- Dispose in household trash
- Do NOT flush unless the FDA Flush List specifies it is safe to do so

DO NOT:
- Flush medications down the drain (unless on FDA Flush List) — environmental contamination risk
- Give medications to others — sharing prescription medications is illegal

For questions, speak with a HealthFirst pharmacist.
""",

    "storage_guidelines.txt": """
Medication Storage Guidelines
HealthFirst Community Pharmacy

PROPER MEDICATION STORAGE IS CRITICAL for maintaining effectiveness and safety.

GENERAL STORAGE RULES:
- Cool, dry place: Most medications should be stored at room temperature (59–77°F / 15–25°C)
- Away from heat and humidity: Avoid bathrooms (steam and heat), kitchens near the stove, or windowsills
- Away from light: Direct sunlight can degrade medications — amber bottles provide UV protection
- Out of reach of children: Use child-resistant caps; consider a locked medicine cabinet

SPECIFIC STORAGE REQUIREMENTS:

Room Temperature (59–77°F):
- Most oral tablets, capsules, and OTC medications
- Topical creams and ointments (unless otherwise labeled)

Refrigerator (36–46°F / 2–8°C):
- Insulin and some injectable medications
- Liquid antibiotics (amoxicillin suspension, azithromycin suspension)
- Eye drops (some formulations)
- Certain vaccines
- Suppositories (to maintain shape)
- Probiotics (for better viability)

Freezer (below 32°F):
- Some vaccines
- Certain biologics — only if specifically directed

DO NOT FREEZE:
- Insulin (freezing destroys the protein structure)
- Liquid nitroglycerin
- Most oral liquid medications unless labeled for freezer storage

TRAVEL TIPS:
- Keep medications in original, labeled containers
- Carry medications in carry-on luggage (not checked baggage — temperature extremes)
- Use a small insulated pouch for refrigerated medications during short travel
- For international travel: check country regulations for controlled substances; carry physician letter

MEDICATION ORGANIZERS:
- Weekly pill organizers can simplify adherence
- Keep out of excessive heat (car glove compartments can reach 140°F+ in summer)
""",

    "pharmacy_hours_services.txt": """
HealthFirst Community Pharmacy – Hours and Services
HealthFirst Community Pharmacy

PHARMACY HOURS:
Monday – Saturday: 8:00 AM – 9:00 PM
Sunday: 10:00 AM – 6:00 PM

Holiday hours may vary — call ahead or check our website for updates.

SERVICES OFFERED:

Dispensing Services:
- Prescription filling and refills
- Compounding (custom medication preparations) — ask for availability
- Blister pack/compliance packaging for patients managing multiple medications
- Emergency prescription supply (limited quantity while awaiting prescription authorization)

Clinical Services:
- Free blood pressure checks (walk-in)
- Immunizations: Flu, COVID-19, Shingles, Pneumonia, Tdap, Hepatitis A & B, Travel vaccines
- Medication Therapy Management (MTM) consultations — for patients on multiple medications
- Diabetes management counseling

OTC and Health Products:
- Full selection of OTC medications
- Vitamins, supplements, and herbal products
- Medical devices: blood pressure monitors, thermometers, glucometers, nebulizers
- First aid supplies, skincare, and personal health products

Delivery and Convenience:
- Free home delivery within local service area (ask for details)
- Drive-through window available
- Medication synchronization (MedSync) — align all refills to one convenient pickup date

CONTACT US:
- Phone: Available during pharmacy hours
- Pharmacy Counter: Walk-in any time during hours

We look forward to serving your healthcare needs at HealthFirst Community Pharmacy.
""",

    "generic_vs_brand.txt": """
Generic vs. Brand-Name Medications – What You Need to Know
HealthFirst Community Pharmacy

WHAT IS A GENERIC MEDICATION?
A generic medication contains the same active ingredient(s), in the same dosage form, strength, and route of administration as the corresponding brand-name drug.

FDA REQUIREMENTS FOR GENERICS:
- Must demonstrate bioequivalence to the brand-name drug (within 80–125% of brand absorption)
- Must meet the same quality, safety, and purity standards
- Must be manufactured under the same FDA good manufacturing practice (GMP) regulations

WHAT IS DIFFERENT IN GENERICS?
- Inactive ingredients (fillers, binders, colorants) may differ
- Appearance (size, shape, color) may differ
- Price is typically 80–85% less than brand-name

ARE GENERICS AS EFFECTIVE?
Yes, for the vast majority of medications. The FDA bioequivalence standard ensures they work the same way in the body.
Exception: Narrow therapeutic index drugs (warfarin, levothyroxine, lithium, anti-epileptics) — your doctor may prefer you stay on the same formulation; consult before switching.

COST SAVINGS:
- Brand-name medications can cost 3–10x more than generics
- Ask our pharmacist whether a generic is available for your prescription
- We automatically substitute generics unless "Dispense as Written (DAW)" is specified

AB RATING:
- Generics rated "AB" by the FDA are fully substitutable for brand-name drugs
- You can ask to see the generic substitution rating for your medication

COMMON BRAND/GENERIC PAIRS (EXAMPLES):
- Tylenol → Acetaminophen
- Advil → Ibuprofen
- Prilosec → Omeprazole
- Claritin → Loratadine
- Lipitor → Atorvastatin
- Zithromax → Azithromycin

Ask our HealthFirst pharmacist about generic savings on your prescriptions.
""",

    "medication_disposal.txt": """
Safe Medication Disposal Guide
HealthFirst Community Pharmacy

WHY PROPER DISPOSAL MATTERS:
Unused and expired medications pose risks:
- Environmental: Flushed medications contaminate water supplies and harm aquatic life
- Safety: Stored medications can be misused, especially opioids and controlled substances
- Children: Improperly stored medications are a leading cause of pediatric poisoning

BEST OPTION — DRUG TAKE-BACK:
DEA-authorized drug take-back programs are the safest and most environmentally responsible way to dispose of medications.
- HealthFirst Pharmacy may have an in-store collection kiosk (ask staff)
- DEA Take-Back Day events (held twice yearly; we post schedule in-store)
- Find a drop-off location at DEA's website

MAIL-BACK PROGRAMS:
- The DEA offers prepaid mail-back envelopes for safe disposal of most medications
- Available at some pharmacies — ask at HealthFirst

AT-HOME DISPOSAL (if no take-back available):
1. Remove medication from original container
2. Mix with undesirable material: coffee grounds, kitty litter, or dirt
3. Seal in a container (a Ziploc bag)
4. Scratch out personal info on original label
5. Throw in household trash — do NOT recycle

MEDICATIONS THAT CAN BE FLUSHED (FDA Flush List only):
Certain highly dangerous medications (strong opioids, fentanyl patches) are recommended for flushing to prevent accidental access. Examples: oxycodone, hydrocodone, methadone, fentanyl patches.
Refer to the FDA's current Flush List for the most up-to-date guidance.

SHARPS (NEEDLES, LANCETS):
- Never throw sharps in regular trash — risk of needlestick injury
- Use FDA-cleared sharps containers
- Return full containers to HealthFirst Pharmacy or a licensed sharps disposal site
""",

    "medication_counseling.txt": """
Medication Counseling Services
HealthFirst Community Pharmacy

WHAT IS MEDICATION COUNSELING?
Medication counseling is a pharmacist-provided service where we review your medications with you to ensure safe and effective use.

WHEN IS COUNSELING OFFERED?
- New prescriptions: Our pharmacists offer counseling for every new prescription
- Changes in therapy: New doses, new medications added to your regimen
- High-risk medications: Blood thinners, insulin, narrow therapeutic index drugs
- Upon request: Any time you have questions about your medications

WHAT WE COVER IN COUNSELING:
- Purpose of the medication
- How and when to take it (with or without food, timing)
- Common and serious side effects to watch for
- Drug interactions with your other medications
- What to do if you miss a dose
- Storage instructions
- How to monitor the medication's effectiveness

MEDICATION THERAPY MANAGEMENT (MTM):
For patients on multiple chronic medications, we offer comprehensive MTM consultations:
- Complete medication review
- Identification of drug interactions or duplications
- Adherence support
- Coordinating with your prescribers

MEDICATION ADHERENCE SUPPORT:
- Pill organizers available in-store
- MedSync (medication synchronization): align all refills to the same day monthly
- Blister packaging for complex regimens
- Refill reminders

CONFIDENTIALITY:
All medication counseling is private and confidential. Consultation areas are available for private discussions.

SCHEDULE A CONSULTATION:
Speak with our pharmacist at the counter or call during pharmacy hours to schedule a dedicated MTM consultation.
""",

    "prior_authorization.txt": """
Prior Authorization (PA) – What Patients Need to Know
HealthFirst Community Pharmacy

WHAT IS PRIOR AUTHORIZATION?
Prior authorization (PA) is a process required by many insurance plans before they will cover certain medications. The insurance company must approve coverage before the prescription can be filled at the covered price.

COMMON REASONS FOR PA:
- The prescribed medication is a brand-name when a generic is available
- High-cost specialty medications
- Medications used off-label (for a condition not in the approved indication)
- Quantity limits exceeded
- Step therapy requirements (insurer requires trying a less expensive alternative first)

HOW THE PROCESS WORKS:
1. We receive your prescription and discover PA is required
2. We notify you of the PA requirement
3. Your prescriber contacts the insurance company to initiate the PA request
4. The insurance company reviews medical records and either approves or denies
5. If approved: we fill your prescription at the covered price
6. If denied: we assist with an appeal or alternative options

HOW LONG DOES PA TAKE?
- Routine PA: 1–3 business days
- Urgent/emergency PA: May be processed same-day
- Appeals: 7–30 days depending on plan

WHAT YOU CAN DO:
- Ensure your doctor's office has submitted the PA request
- Ask us to fill the prescription at out-of-pocket price in the interim (if urgent)
- Ask about therapeutic alternatives that don't require PA
- We can provide a GoodRx or manufacturer coupon price as a backup

APPEALS:
If the PA is denied, your prescriber can appeal. We can provide documentation support.

For PA status questions, our pharmacy staff is here to help.
""",

    "prescription_transfer.txt": """
Prescription Transfer Policy
HealthFirst Community Pharmacy

TRANSFERRING PRESCRIPTIONS TO HEALTHFIRST:
We make it easy to transfer your prescriptions from another pharmacy to HealthFirst Community Pharmacy.

HOW TO REQUEST A TRANSFER IN:
Option 1 – Call Us: Provide the name and phone number of your current pharmacy, your name, date of birth, and the medication(s) to transfer. We'll do the rest.
Option 2 – In Store: Visit our pharmacy counter with your prescription bottle or the name of your current pharmacy.

WHAT WE NEED:
- Your full name and date of birth
- Name and address/phone number of the pharmacy you are transferring from
- Medication name, dosage, and Rx number (on label if available)

TIMELINE:
- Most transfers are completed within 1–4 hours
- Electronic transfers: typically 30–60 minutes
- Out-of-state transfers: may take longer depending on state law

CONTROLLED SUBSTANCES:
- Schedule II controlled substances (e.g., Adderall, Percocet) CANNOT be transferred — a new prescription from your provider is required
- Schedule III–V controlled substances: One transfer allowed per prescription in most states

TRANSFERRING OUT FROM HEALTHFIRST:
- We can transfer prescriptions to another pharmacy upon your request
- Provide the receiving pharmacy with our name and phone number — they will initiate the transfer
- We cannot transfer prescriptions out that have already been transferred in (one transfer per Rx per federal law)

MULTI-PHARMACY PATIENTS:
Consolidating all medications at one pharmacy allows us to perform comprehensive drug interaction checks. Ask about our MedSync (medication synchronization) program.
""",

    # --- DRUG SAFETY (10) ---
    "drug_interactions_overview.txt": """
Drug Interactions – What Every Patient Should Know
HealthFirst Community Pharmacy

WHAT IS A DRUG INTERACTION?
A drug interaction occurs when the effect of one medication is altered by another substance — this can be another drug, food, herbal supplement, or even alcohol.

TYPES OF DRUG INTERACTIONS:

Drug–Drug Interactions:
- Pharmacodynamic: Two drugs with similar effects act together (additive or antagonistic)
  Example: Two blood pressure medications causing excessive drop in BP
- Pharmacokinetic: One drug alters how another is absorbed, distributed, metabolized, or eliminated
  Example: Clarithromycin inhibiting the metabolism of simvastatin → increased statin levels → muscle toxicity risk

Drug–Food Interactions:
- Grapefruit juice: Inhibits CYP3A4 enzyme → increases blood levels of statins, calcium channel blockers, some antihistamines
- Vitamin K foods (leafy greens): Reduce the effect of warfarin (blood thinner)
- Dairy/calcium: Can reduce absorption of certain antibiotics (tetracyclines, fluoroquinolones)

Drug–Supplement Interactions:
- St. John's Wort: Induces CYP enzymes → reduces effectiveness of oral contraceptives, HIV medications, anticoagulants
- Ginkgo, ginseng, garlic, fish oil: May increase bleeding risk with anticoagulants
- Melatonin: May interact with blood thinners and diabetes medications

Drug–Alcohol Interactions:
- Enhanced sedation with CNS depressants (benzodiazepines, opioids, antihistamines, sleep aids)
- Increased bleeding risk with aspirin/NSAIDs
- Disulfiram-like reaction with metronidazole (severe nausea/vomiting)
- Acetaminophen + alcohol → increased liver toxicity risk

REDUCING INTERACTION RISK:
- Tell your pharmacist ALL medications you take (prescription, OTC, vitamins, supplements)
- Use one pharmacy for all medications (interaction checking advantage)
- Read medication guides and warning labels
- Ask your pharmacist before starting a new supplement or OTC medication

HealthFirst pharmacists perform drug interaction checks on every prescription.
""",

    "medication_expiration.txt": """
Medication Expiration Dates – Patient Guide
HealthFirst Community Pharmacy

WHAT DOES THE EXPIRATION DATE MEAN?
The expiration date is the date through which the manufacturer guarantees full potency and safety of the medication, when stored according to label conditions.

ARE EXPIRED MEDICATIONS DANGEROUS?
- Most medications lose potency gradually after expiration rather than becoming toxic
- However, some medications should NEVER be used after expiration:
  - Tetracycline antibiotics: Can become nephrotoxic (kidney-damaging) after expiration
  - Insulin: Expired insulin may not control blood sugar adequately
  - Nitroglycerin: Loses effectiveness rapidly; critical for angina emergencies
  - Liquid medications (suspensions, eye drops): Degrade faster, risk of contamination
  - Epinephrine auto-injectors (EpiPen): Critical emergency medication — always replace expired devices

MEDICATIONS GENERALLY STABLE PAST EXPIRATION (but not recommended):
- Many solid dosage forms (tablets, capsules) may retain 70–90%+ potency for years if stored well
- However, relying on expired medications is not recommended, especially for critical conditions

PROPER MANAGEMENT:
- Check expiration dates periodically (e.g., when daylight saving time changes)
- Replace expired medications in first aid kits and medicine cabinets annually
- Dispose of expired medications safely (see our medication disposal guide)

STORAGE EXTENDS SHELF LIFE:
- Proper storage (cool, dry, away from light) helps medications remain stable through their expiration
- Exposure to heat, humidity, or light can cause medications to degrade before their expiration date

If you're unsure whether a medication is still safe and effective, ask a HealthFirst pharmacist.
""",

    "pregnancy_medication_safety.txt": """
Medication Safety During Pregnancy
HealthFirst Community Pharmacy

IMPORTANT: Always consult your obstetrician before taking any medication during pregnancy.

FDA PREGNANCY CATEGORIES (older system) / CURRENT LABELING:
The FDA now uses a narrative labeling system (since 2015). Medications are categorized based on available risk data for pregnancy, lactation, and reproductive potential.

GENERALLY CONSIDERED SAFER OTC OPTIONS DURING PREGNANCY:

Pain/Fever:
- Acetaminophen: Generally considered safe at recommended doses throughout pregnancy
- Avoid NSAIDs (ibuprofen, naproxen, aspirin) — especially in the third trimester (risk of premature closure of ductus arteriosus); short-term first/second trimester use may be acceptable with physician guidance

Heartburn/Nausea:
- Antacids (calcium carbonate, magnesium hydroxide, aluminum hydroxide): Generally safe in moderation
- Omeprazole: Use only if clearly needed (data reassuring but limited)
- Vitamin B6 (25 mg 3x/day) ± doxylamine: first-line treatment for nausea/vomiting of pregnancy
- Ginger: Generally considered safe in modest amounts

Allergies:
- Loratadine and cetirizine: Most commonly recommended non-sedating antihistamines in pregnancy
- Diphenhydramine: Generally considered safe but sedating

Cough/Cold:
- Dextromethorphan: Generally considered safe in second/third trimester (avoid first trimester if possible)
- Guaifenesin: Avoid in first trimester; generally accepted after
- Avoid pseudoephedrine (decongestant) in first trimester

AVOID DURING PREGNANCY:
- NSAIDs (especially 3rd trimester)
- Aspirin at full analgesic doses
- Bismuth subsalicylate (Pepto-Bismol) — contains salicylate
- High-dose vitamin A (>10,000 IU/day) — teratogenic
- Herbal remedies (unless confirmed safe by physician)

Always speak with your OB-GYN or our HealthFirst pharmacist before starting any medication during pregnancy.
""",

    "pediatric_dosing.txt": """
Pediatric Medication Dosing Guide
HealthFirst Community Pharmacy

KEY PRINCIPLE: Children are NOT small adults. Medication doses for children must be calculated based on weight and age.

GENERAL RULES:
- Always use weight-based dosing when possible
- Use the measuring device provided with liquid medications — kitchen spoons are inaccurate
- NEVER give adult medications to children without physician or pharmacist guidance

ACETAMINOPHEN (Children's Tylenol):
- Dose: 10–15 mg/kg every 4–6 hours as needed
- Maximum: 5 doses in 24 hours; do not exceed 75 mg/kg/day or 4,000 mg/day
- Available in: 160 mg/5 mL oral suspension (most common)
- Infants (<3 months): Physician guidance required

IBUPROFEN (Children's Advil/Motrin):
- Dose: 5–10 mg/kg every 6–8 hours
- Maximum: 40 mg/kg/day
- Age restriction: Do not use in infants under 6 months
- Available in: 100 mg/5 mL oral suspension; 50 mg chewables

ANTIHISTAMINES:
- Loratadine (Children's Claritin): 5 mg for ages 2–5; 10 mg for ages 6+
- Cetirizine (Children's Zyrtec): 2.5 mg ages 2–5; 5–10 mg ages 6+
- Diphenhydramine: NOT recommended under age 2; 12.5 mg for ages 2–5; 25 mg for ages 6–11

DO NOT GIVE CHILDREN:
- Aspirin — Reye's syndrome risk in viral illness
- Bismuth subsalicylate (Pepto-Bismol) — contains salicylate
- Adult formulations without explicit pediatric dosing guidance
- OTC cough and cold medications in children under 4 (FDA warning)

ASK A PHARMACIST:
Our HealthFirst pharmacists can calculate the right dose for your child based on their weight and provide measuring syringes at no charge.
""",

    "elderly_medication_safety.txt": """
Medication Safety in Older Adults
HealthFirst Community Pharmacy

WHY OLDER ADULTS NEED SPECIAL ATTENTION:
Aging changes how the body processes medications:
- Reduced kidney function: slower elimination of renally-cleared drugs → drug accumulation
- Reduced liver function: slower metabolism of hepatically-cleared drugs
- Decreased body water: higher concentration of water-soluble drugs
- Increased body fat: longer half-life for fat-soluble drugs
- Polypharmacy: increased drug interaction risk with multiple medications

THE BEERS CRITERIA:
The American Geriatrics Society's Beers Criteria lists medications that are potentially inappropriate for adults aged 65+. Key categories:

Sedatives/Hypnotics:
- Benzodiazepines (diazepam, alprazolam, lorazepam): increased fall and fracture risk, cognitive impairment
- Diphenhydramine-based sleep aids: strong anticholinergic effects, delirium, falls

Anticholinergic Medications:
- Diphenhydramine, oxybutynin, some antidepressants: confusion, constipation, urinary retention, blurred vision

NSAIDs:
- Ibuprofen, naproxen, aspirin at high doses: increased GI bleeding, kidney injury, fluid retention

Muscle Relaxants:
- Cyclobenzaprine, carisoprodol: sedation, anticholinergic effects, falls

SAFER ALTERNATIVES FOR COMMON CONDITIONS IN ELDERLY:
- Pain: Acetaminophen preferred over NSAIDs; topical diclofenac gel for localized pain
- Sleep: Melatonin (0.5–3 mg) preferred over antihistamines or benzodiazepines
- Allergies: Loratadine or fexofenadine (non-sedating) preferred over diphenhydramine

POLYPHARMACY MANAGEMENT:
- Keep an updated medication list (include OTC, vitamins, herbal supplements)
- Bring all medications to every doctor's appointment (brown bag review)
- Ask about medication reconciliation at HealthFirst — our pharmacists can perform comprehensive medication reviews

Fall Prevention:
- Medications causing dizziness or sedation increase fall risk
- Review all medications annually with your pharmacist for age-appropriateness
""",

    "alcohol_drug_interactions.txt": """
Alcohol and Medication Interactions
HealthFirst Community Pharmacy

ALCOHOL IS A DRUG that can interact with many medications, altering their effects or causing dangerous reactions.

CATEGORIES OF ALCOHOL-DRUG INTERACTIONS:

1. ENHANCED SEDATION / CNS DEPRESSION:
Combining alcohol with CNS depressants amplifies sedation, impairs coordination, and can dangerously slow breathing.
- Opioid pain medications (oxycodone, hydrocodone, codeine) — DANGEROUS COMBINATION
- Benzodiazepines (Xanax, Valium, Ativan, Klonopin)
- Sleep medications (zolpidem/Ambien, diphenhydramine)
- Muscle relaxants (cyclobenzaprine, methocarbamol)
- Antihistamines (diphenhydramine)
- Anticonvulsants (gabapentin, pregabalin)
- Antidepressants (tricyclics, some SSRIs)

2. LIVER TOXICITY:
- Acetaminophen + alcohol: Both are processed by the liver; regular alcohol use significantly increases the risk of acetaminophen-induced liver damage. LIMIT TO 3,000 mg/day if you drink; AVOID if you drink heavily.

3. DISULFIRAM-LIKE REACTIONS (severe flushing, nausea, vomiting):
- Metronidazole (Flagyl) — avoid alcohol during treatment AND 48 hours after completion
- Tinidazole: similar to metronidazole
- Certain cephalosporin antibiotics

4. BLOOD SUGAR EFFECTS:
- Alcohol can cause hypoglycemia (low blood sugar) in diabetics, especially with insulin or sulfonylureas
- Can also cause hyperglycemia with chronic heavy use

5. BLOOD PRESSURE MEDICATIONS:
- Alcohol can lower blood pressure further, causing dizziness and falls
- Can also counteract antihypertensive therapy

6. BLOOD THINNERS:
- Warfarin: Acute alcohol intake may increase INR (bleeding risk); chronic heavy use may decrease INR
- Aspirin/NSAIDs + alcohol: Increased GI bleeding risk

RULE OF THUMB:
When in doubt, avoid alcohol with any medication. Ask your HealthFirst pharmacist whether alcohol interacts with your specific medications.
""",

    "food_drug_interactions.txt": """
Food and Drug Interactions – Patient Guide
HealthFirst Community Pharmacy

FOOD CAN SIGNIFICANTLY AFFECT HOW MEDICATIONS WORK. Here are the most important interactions:

GRAPEFRUIT AND GRAPEFRUIT JUICE:
- Mechanism: Contains furanocoumarins that inhibit the CYP3A4 enzyme in the gut
- Effect: Increases blood levels of affected medications → increased side effects or toxicity
- Affected drugs (many — confirm with pharmacist):
  - Statins: Simvastatin, lovastatin (avoid grapefruit); atorvastatin (less affected)
  - Calcium channel blockers: Amlodipine, felodipine, nifedipine
  - Immunosuppressants: Cyclosporine, tacrolimus
  - Some antihistamines: Fexofenadine (grapefruit can REDUCE its effect)
  - Psychiatric: Some benzodiazepines, buspirone
  - Duration: ONE glass can affect metabolism for 24–72 hours

VITAMIN K AND WARFARIN:
- Warfarin is a blood thinner that works by blocking Vitamin K
- Sudden large increases in Vitamin K foods can DECREASE warfarin's effect (increase clotting)
- Sudden decreases can INCREASE warfarin's effect (increased bleeding risk)
- Key: Be CONSISTENT with Vitamin K intake (don't dramatically change diet)
- High Vitamin K foods: kale, spinach, collard greens, broccoli, Brussels sprouts, green onions

DAIRY AND ANTIBIOTICS:
- Tetracyclines (doxycycline, tetracycline): Calcium binds to the drug, reducing absorption significantly — take 2 hours before or after dairy
- Fluoroquinolones (ciprofloxacin, levofloxacin): Similar calcium interaction — avoid dairy/calcium within 2 hours

HIGH-FAT MEALS:
- Some medications require food for proper absorption: itraconazole, isotretinoin, certain HIV medications
- Other medications are best taken on an empty stomach for faster absorption

TYRAMINE-RICH FOODS AND MAOIs:
- Patients on MAO inhibitors must avoid tyramine-rich foods: aged cheeses, cured meats, fermented products, red wine
- Can cause a dangerous hypertensive crisis

LICORICE:
- Natural licorice (glycyrrhizin) can raise blood pressure and reduce potassium levels, counteracting antihypertensive and diuretic medications

Always check with your HealthFirst pharmacist about food interactions with your specific medications.
""",

    "otc_safety_tips.txt": """
Safe Use of Over-the-Counter (OTC) Medications – Tips
HealthFirst Community Pharmacy

OTC MEDICATIONS ARE GENERALLY SAFE WHEN USED AS DIRECTED. Follow these key principles:

1. READ THE LABEL COMPLETELY:
- Active ingredients
- Uses (indications)
- Dosage instructions (including pediatric doses)
- Warnings and contraindications
- Drug interaction warnings
- Expiration date

2. AVOID DUPLICATE INGREDIENTS:
Many combination products contain multiple active ingredients.
- Common example: NyQuil contains acetaminophen. If you ALSO take Tylenol, you may accidentally overdose on acetaminophen.
- Always check the active ingredient list of ALL products you take

3. USE THE CORRECT MEASURING DEVICE:
- Liquid medications: Use the measuring cup/syringe provided — kitchen teaspoons vary greatly in volume
- 5 mL = 1 teaspoon (standard); confirm with measuring device

4. DON'T EXCEED RECOMMENDED DOSES:
- More is not better — exceeding doses increases side effects and toxicity risk
- Acetaminophen: Max 4,000 mg/day (3,000 mg if regular alcohol drinker)
- NSAIDs: Take lowest effective dose for the shortest time

5. PEDIATRIC CAUTION:
- Use weight-based dosing for children whenever possible
- Do not give adult formulations to children
- Avoid OTC cough/cold medications in children under 4

6. DURATION LIMITS:
- Topical decongestant nasal sprays: max 3 days (rebound congestion)
- Hydrocortisone cream: max 7 days without physician guidance
- Antacids: consult doctor if heartburn persists more than 2 weeks

7. DRUG INTERACTIONS:
- Tell your pharmacist about all medications (including OTC, vitamins, supplements) before starting a new OTC product
- Our HealthFirst pharmacists will check for interactions at no charge

8. SPECIAL POPULATIONS:
- Elderly: More sensitive to many OTC medications (especially antihistamines, sleep aids)
- Pregnant: Consult healthcare provider before any OTC medication
- Kidney/liver disease: Some OTC medications require dose adjustment

When in doubt, ask a HealthFirst pharmacist — it's free!
""",

    "polypharmacy_risks.txt": """
Polypharmacy – Managing Multiple Medications Safely
HealthFirst Community Pharmacy

WHAT IS POLYPHARMACY?
Polypharmacy refers to the concurrent use of 5 or more medications. It is very common in older adults and patients with multiple chronic conditions.

RISKS OF POLYPHARMACY:
- Drug–drug interactions: More medications = exponentially higher interaction risk
- Adverse drug events: Unintended side effects from combinations
- Medication non-adherence: Complexity reduces the likelihood of proper adherence
- Prescribing cascade: A new medication is prescribed to treat a side effect of another
- Falls and hospitalizations: Particularly in elderly patients

HOW TO MINIMIZE POLYPHARMACY RISKS:

1. KEEP AN UP-TO-DATE MEDICATION LIST:
Include ALL medications: prescriptions, OTC, vitamins, herbs, and supplements. Share with ALL healthcare providers at every visit.

2. USE ONE PHARMACY:
HealthFirst performs drug interaction checks for your entire medication profile. Using multiple pharmacies fragments this safety check.

3. MEDICATION THERAPY MANAGEMENT (MTM):
Our pharmacists offer comprehensive MTM consultations to review all your medications for:
- Necessary vs. unnecessary medications
- Drug interactions
- Duplicate therapies
- Adherence issues

4. BROWN BAG REVIEW:
Bring all your medications in a bag to your annual primary care visit or to HealthFirst for a complete review.

5. ASK BEFORE ADDING NEW MEDICATIONS:
Before starting any new prescription, OTC, or supplement, ask your pharmacist to check for interactions with your current regimen.

6. RECOGNIZE THE PRESCRIBING CASCADE:
Example: NSAID causes increased blood pressure → doctor prescribes antihypertensive → antihypertensive causes leg edema → diuretic prescribed.
Ask if a new medication is being prescribed to treat a side effect of an existing one.

HEALTHFIRST SUPPORT:
Our pharmacy team is available to help you manage complex medication regimens. Schedule a free medication review consultation.
""",

    # --- WELLNESS AND FIRST AID (5) ---
    "first_aid_kit_essentials.txt": """
First Aid Kit Essentials
HealthFirst Community Pharmacy

A well-stocked home first aid kit is an important part of household safety preparedness.

BASIC FIRST AID KIT CHECKLIST:

WOUND CARE:
□ Adhesive bandages (assorted sizes — 1", 2", knuckle, fingertip)
□ Sterile gauze pads (2x2 and 4x4 inches)
□ Rolled gauze (elastic bandage roll)
□ Medical tape (paper, silk, or waterproof)
□ Antiseptic wipes (alcohol swabs)
□ Triple antibiotic ointment (Neosporin/Bacitracin)
□ Sterile saline wound wash
□ Butterfly closure strips (for larger cuts)

MEDICATIONS:
□ Acetaminophen (adult and children's formulations)
□ Ibuprofen (adult and children's formulations)
□ Antihistamine (diphenhydramine or loratadine)
□ Antacid (calcium carbonate/Tums)
□ Electrolyte solution (Pedialyte) or oral rehydration salts
□ Hydrocortisone 1% cream
□ Calamine lotion (for itching/rashes)
□ Antidiarrheal medication (loperamide)
□ Antinausea medication (dimenhydrinate)

TOOLS AND EQUIPMENT:
□ Digital thermometer
□ Tweezers (for splinters)
□ Scissors (blunt-tipped for bandages)
□ Disposable gloves (latex-free)
□ CPR face shield
□ Cold pack (instant)
□ Hot water bottle or heating pad
□ Penlight/small flashlight
□ First aid manual

EMERGENCY ITEMS:
□ Emergency contact list (doctor, pharmacy, poison control: 1-800-222-1222)
□ List of all household medications and allergies
□ EpiPen (if prescribed for anaphylaxis)

MAINTENANCE:
- Check expiration dates every 6 months (e.g., when clocks change)
- Restock used or expired items promptly
- Store in a cool, dry location — not the bathroom (humidity degrades medications)
- Keep out of reach of children but accessible to adults in an emergency

HealthFirst Pharmacy stocks all first aid essentials. Ask our staff for recommendations.
""",

    "healthy_lifestyle_tips.txt": """
Healthy Lifestyle Tips – Preventive Health Guide
HealthFirst Community Pharmacy

At HealthFirst Community Pharmacy, we believe prevention is the best medicine. These evidence-based lifestyle habits can significantly reduce your risk of chronic disease.

PHYSICAL ACTIVITY:
- Adults: at least 150 minutes of moderate aerobic activity OR 75 minutes of vigorous activity per week
- Strength training: at least 2 days/week for muscle and bone health
- Reduce prolonged sitting: stand and move briefly every 30–60 minutes
- Even 10-minute activity bouts count — cumulative throughout the day

NUTRITION:
- Eat a balanced diet rich in whole foods: fruits, vegetables, whole grains, lean proteins, healthy fats
- Limit: processed/ultra-processed foods, added sugars, refined carbohydrates, sodium, saturated fats
- Stay hydrated: 8 cups (2 L) of water daily (more with exercise and heat)
- Mediterranean diet pattern has the strongest evidence base for chronic disease prevention

SLEEP:
- Adults: 7–9 hours per night
- Consistent sleep/wake schedule — even on weekends
- Dark, cool, quiet bedroom environment
- Limit caffeine after noon; limit alcohol near bedtime

STRESS MANAGEMENT:
- Chronic stress contributes to cardiovascular disease, diabetes, and depression
- Evidence-based strategies: mindfulness meditation, yoga, regular exercise, social connection
- Seek professional support (therapist, counselor) for chronic stress or anxiety

PREVENTIVE SCREENINGS (ask your doctor):
- Blood pressure: Every 1–2 years (more frequent if elevated)
- Cholesterol: Every 4–6 years for healthy adults (more frequent with risk factors)
- Diabetes screening: Starting at age 35–40 or earlier with risk factors
- Colorectal cancer: Starting at age 45 (colonoscopy every 10 years, or stool tests annually)
- Breast cancer mammography: Starting at age 40–50 (per guidelines/physician advice)

VACCINATIONS AVAILABLE AT HEALTHFIRST:
- Annual flu vaccine (recommended for everyone 6 months+)
- COVID-19 (updated formulations)
- Shingles (Shingrix) — recommended for adults 50+
- Pneumonia (PPSV23, PCV15, PCV20) — adults 65+ and at-risk groups
- Tdap/Td booster — every 10 years
- Hepatitis A and B

Ask our pharmacists about which vaccines you may be due for.
""",

    "vitamin_supplements_guide.txt": """
Vitamins and Supplements Guide
HealthFirst Community Pharmacy

COMMON VITAMINS AND THEIR USES:

VITAMIN D:
- Function: Bone health (calcium absorption), immune function, mood regulation
- Deficiency signs: Fatigue, bone pain, muscle weakness, depression
- Recommended dose: 600–800 IU/day (adults); 1,000–2,000 IU/day for deficiency replacement
- Upper limit: 4,000 IU/day without medical supervision
- Who needs it: Older adults, people with limited sun exposure, dark skin, obesity, malabsorption

VITAMIN B12:
- Function: Red blood cell formation, nerve function, DNA synthesis
- Deficiency signs: Fatigue, weakness, numbness, balance problems, memory issues
- At risk: Vegans/vegetarians, adults over 50 (reduced absorption), metformin users
- Supplement forms: Cyanocobalamin or methylcobalamin; sublinguals or B12 shots for malabsorption
- OTC dose: 500–1,000 mcg/day for maintenance

IRON:
- Function: Hemoglobin production, oxygen transport
- Deficiency signs: Fatigue, pale skin, cold hands/feet, brittle nails
- Who needs it: Women of childbearing age, pregnant women, vegans, athletes
- Caution: Do NOT take extra iron without confirmed deficiency (blood test) — iron excess is toxic
- Tip: Take with Vitamin C to enhance absorption; separate from calcium/antacids by 2 hours

FOLATE / FOLIC ACID:
- Function: DNA synthesis, cell division, neural tube development
- Critical for: Women of childbearing potential — take 400–800 mcg daily before and during early pregnancy
- Deficiency: Neural tube defects in developing fetus

MAGNESIUM:
- Function: Muscle and nerve function, energy production, bone health
- Uses: Constipation (magnesium citrate/oxide), muscle cramps, migraine prevention
- Common forms: Glycinate (best tolerated), citrate, oxide (laxative effect)
- Dose: 200–400 mg/day elemental magnesium

IMPORTANT NOTES:
- Supplements are not substitutes for a balanced diet
- More is not always better — fat-soluble vitamins (A, D, E, K) accumulate and can be toxic at high doses
- Inform your pharmacist and doctor about all supplements you take — many interact with medications

Ask our HealthFirst pharmacist for guidance on choosing quality supplements.
""",
}

count = 0
for filename, content in docs.items():
    filepath = os.path.join(DOCS_DIR, filename)
    with open(filepath, "w") as f:
        f.write(content.strip())
    count += 1

print(f"Generated {count} documents in {DOCS_DIR}")
