import re
import time
from utils import normalize_label


# ==========================================
# 1. SAFETY AGENT (Deterministic / Regex)
# ==========================================
class SafetyAgent:
    def __init__(self):
        self.CRITICAL_FLAGS = [
            "cardiac arrest", "cpr", "resuscitation", "shock", "coma", "unconscious",
            "intubation", "massive bleed", "tamponade", "aortic dissection",
            "stemi", "st elevation", "vtach", "vfib", "ventricular fibrillation",
            "respiratory failure", "stridor", "oxygen < 85", "saturation < 85",
            "acute stroke", "large vessel occlusion", "lvo", "status epilepticus",
            "intracranial hemorrhage", "brain bleed", "subarachnoid",
            "ketoacidosis", "dka", "hhnk", "strangulated", "incarcerated", "peritonitis"
        ]
        self.IGNORED_CONTEXT = [
            "history of", "chronic", "old", "past", "prior", "stable", "resolved",
            "rule out", "r/o", "suspected", "possible", "potential", "question of"
        ]

    def analyze(self, details_text):
        if not details_text:
            return {"decision": "Discharge", "is_critical": False, "reason": None}

        text = str(details_text).lower()
        for flag in self.CRITICAL_FLAGS:
            pattern = r'\b' + re.escape(flag) + r'\b'
            match = re.search(pattern, text)
            if match:
                start_idx = match.start()
                context = text[max(0, start_idx - 35):start_idx]
                is_negated = False
                for ignore in self.IGNORED_CONTEXT:
                    if ignore in context:
                        is_negated = True
                        break
                if not is_negated:
                    # Critical flag found
                    return {"decision": "Admit", "is_critical": True, "reason": f"CRITICAL: {flag}"}

        return {"decision": "Discharge", "is_critical": False, "reason": "No critical keywords"}


# ==========================================
# 2. PATHOLOGY AGENT (Medical Risk)
# ==========================================
class PathologyAgent:
    def __init__(self, model):
        self.model = model

    def consult(self, patient_text):
        prompt = f"""Role: Internal Medicine Specialist.
        Task: Assess BIOLOGICAL RISK only.

        **DISTINCTION:**
        - **HIGH RISK (ADMIT):** 
            - **Active Instability:** Sepsis, Ischemia (Stroke/MI/Limb), Acute Organ Failure.
            - **Surgical Emergencies:** Incarcerated Hernia, Bowel Obstruction, Peritonitis.
            - **New Neurological Deficit:** Acute weakness/aphasia.
            - **Severe Vitals:** Hypotension (<90), Hypoxia (<90%), Severe Tachycardia (>140).
            - **Active Bleeding:** GI Bleed, Hemoptysis.

        - **LOW RISK (DISCHARGE):** 
            - **Risk Factors ONLY:** Age > 80, Dementia, or Comorbidities *without* acute instability.
            - **AFib / Tachycardia:** HR 100-130 with STABLE BP -> Low Risk (Rate control in ER).
            - **Syncope:** If currently alert and vitals stable -> Low Risk (Observation).
            - **Stable Conditions:** Cellulitis, Abscess, UTI, Renal Colic (pain controlled), Epistaxis (stopped).
            - **Chronic Issues:** Chronic Anemia, Chronic Hyponatremia (asymptomatic).
            - **"Rule Out" / Suspicion:** Chest Pain, Abdominal Pain, Headache *without* acute distress or instability.

        Patient Data:
        {patient_text}

        Format:
        DECISION: [Admit/Discharge]
        REASON: [Medical justification]
        """
        return self._call_llm(prompt)

    def _call_llm(self, prompt):
        try:
            res = self.model.generate_content(prompt)
            text = res.text.strip()
            vote = "Admit" if "DECISION: Admit" in text else "Discharge"
            reason = text.split("REASON:")[-1].strip() if "REASON:" in text else text
            return {"decision": vote, "reason": reason}
        except:
            return {"decision": "Uncertain", "reason": "Error"}


# ==========================================
# 3. DISCHARGE OFFICER (Resource Manager)
# ==========================================
class DischargeOfficerAgent:
    def __init__(self, model):
        self.model = model

    def consult(self, patient_text):
        prompt = f"""Role: ER Efficiency Manager.
        Task: Can this patient be treated in the ER and released?

        **YES (DISCHARGE) IF:**
        - Needs IV fluids/Antibiotics.
        - Needs Blood Transfusion.
        - Needs CT/Labs/Ultrasound.
        - **Observation Unit:** Needs monitoring/workup < 24 hours (Serial Troponins, Electrolyte correction).
        - **Fast Track:** Sutures, simple fractures.

        **NO (ADMIT) IF:**
        - Needs Urgent Surgery (OR).
        - Needs ICU / Telemetry / Multi-day observation (> 24h).
        - **Social/Functional Barrier:** Cannot care for self at home AND no nursing home available.

        Patient Data:
        {patient_text}

        Format:
        DECISION: [Admit/Discharge]
        REASON: [Discharge plan or why admission is unavoidable]
        """
        return self._call_llm(prompt)

    def _call_llm(self, prompt):
        try:
            res = self.model.generate_content(prompt)
            text = res.text.strip()
            vote = "Admit" if "DECISION: Admit" in text else "Discharge"
            reason = text.split("REASON:")[-1].strip() if "REASON:" in text else text
            return {"decision": vote, "reason": reason}
        except:
            return {"decision": "Uncertain", "reason": "Error"}


# ==========================================
# 4. GERIATRIC AGENT (Functional Safety)
# ==========================================
class GeriatricAgent:
    def __init__(self, model):
        self.model = model

    def consult(self, patient_text):
        prompt = f"""Role: Geriatric Social Worker.
        Task: Assess FUNCTIONAL SAFETY.

        **ADMIT ONLY IF:**
        - **NEW** inability to walk (Acute Immobility) or "Functional Decline" that prevents self-care.
        - Acute Confusion (Delirium) with unknown cause.
        - Severe, unmanageable pain in elderly (>80).
        - Active Suicidal Ideation.
        - **Social Safety:** No support system for a dependent patient.

        **DISCHARGE IF:**
        - Chronic dementia / Chronic weakness (Baseline).
        - **Stable Fracture:** Pelvic/Rib fracture with pain control and mobility/support (or Nursing Home).
        - **Psychiatric:** Behavioral issues or known Psych history -> Discharge (Psych Consult).
        - "General decline" BUT safe to discharge to nursing home/family care.

        Patient Data:
        {patient_text}

        Format:
        DECISION: [Admit/Discharge]
        REASON: [Functional justification]
        """
        return self._call_llm(prompt)

    def _call_llm(self, prompt):
        try:
            res = self.model.generate_content(prompt)
            text = res.text.strip()
            vote = "Admit" if "DECISION: Admit" in text else "Discharge"
            reason = text.split("REASON:")[-1].strip() if "REASON:" in text else text
            return {"decision": vote, "reason": reason}
        except:
            return {"decision": "Uncertain", "reason": "Error"}


# ==========================================
# 5. SUPERVISOR (The Judge)
# ==========================================
class SupervisorAgent:
    def __init__(self, model):
        self.model = model

    def make_final_decision(self, safety_res, path_res, disch_res, geri_res, esi_score, patient_text):

        # 1. HARD RULES (Safety Net)
        # Returns formatted keys for main.py compatibility
        if safety_res['is_critical']:
            return {
                "final_decision": "Admit",
                "override_reason": f"Safety Protocol: {safety_res['reason']}",
                "decision_source": "SafetyAgent"
            }

        if esi_score == 1:
            return {
                "final_decision": "Admit",
                "override_reason": "Protocol: ESI 1 (Resuscitation)",
                "decision_source": "ESI_Protocol"
            }

        # 2. THE TRIAL (LLM Synthesis)
        prompt = f"""You are the Chief of Medicine. Make the final decision.

        PATIENT SUMMARY:
        {patient_text}

        THE COUNCIL'S VOTES:
        1. PATHOLOGIST (Medical Risk): {path_res['decision']} -> {path_res['reason']}
        2. DISCHARGE OFFICER (Logistics): {disch_res['decision']} -> {disch_res['reason']}
        3. GERIATRICIAN (Functional/Social): {geri_res['decision']} -> {geri_res['reason']}

        **CONFLICT RESOLUTION - FOLLOW STRICTLY:**

        A. **SAFETY FIRST (Criticals):**
           - If Pathologist votes ADMIT for **Sepsis**, **Ischemia** (Heart/Brain/Limb), **Acute Abdomen**, or **Active Bleeding** -> **ADMIT**.
           - If Geriatrician votes ADMIT for **New Immobility** or **Acute Confusion** -> **ADMIT**.
           - **EXCEPTION:** If the reason is "Rule Out", "Suspicion", "AFib", or "Risk Factors" ONLY, and patient is stable -> Go to Rule B.

        B. **RESOURCE MANAGEMENT (Reduce False Positives):**
           - If Discharge Officer votes **DISCHARGE** (citing "Observation Unit", "Short Stay", or "ER Treatment") AND Patient is Hemodynamically Stable -> **DISCHARGE**.
           - If Pathologist votes ADMIT only for "Rule Out", "Suspicion", or "Risk Factors" without active instability -> **DISCHARGE**.

        C. **TIE BREAKER:**
           - If opinions clash on a stable patient -> **DISCHARGE**.
           - Only admit if there is a specific, acute, life-threatening reason.

        Format:
        DECISION: [Admit/Discharge]
        WINNER: [PathologyAgent/DischargeOfficer/GeriatricAgent]
        REASON: [Synthesized reason]
        """

        max_retries = 5
        for attempt in range(max_retries):
            try:
                res = self.model.generate_content(prompt)
                text = res.text.strip()

                decision = "Admit" if "DECISION: Admit" in text else "Discharge"

                winner = "Supervisor"
                if "WINNER: PathologyAgent" in text:
                    winner = "PathologyAgent"
                elif "WINNER: DischargeOfficer" in text:
                    winner = "DischargeOfficer"
                elif "WINNER: GeriatricAgent" in text:
                    winner = "GeriatricAgent"

                reason = text.split("REASON:")[-1].strip() if "REASON:" in text else text

                # Corrected keys to match main.py
                return {
                    "final_decision": decision,
                    "override_reason": reason,
                    "decision_source": winner
                }

            except Exception as e:
                time.sleep(1)

        # Fail-safe default
        return {
            "final_decision": "Admit",
            "override_reason": "System Error",
            "decision_source": "Error_Fallback"
        }