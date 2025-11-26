import pandas as pd

def normalize_label(text):
    """
    Normalizes the decision label to 'Admit' or 'Discharge'.
    Returns 'Uncertain' if unknown.
    """
    if not isinstance(text, str): return "Uncertain"
    text = text.strip().lower()
    if "שחרור" in text or "discharge" in text: return "Discharge"
    if "אשפוז" in text or "admit" in text: return "Admit"
    return "Uncertain"

def normalize_gender(text):
    """
    Normalizes gender to 'Male', 'Female', or 'Other'.
    Handles Hebrew and English inputs.
    """
    if not isinstance(text, str): return "Other"
    t = text.strip().lower()
    if any(x in t for x in ['zachar', 'male', 'm', 'זכר']): return 'Male'
    if any(x in t for x in ['nekeva', 'female', 'f', 'נקבה']): return 'Female'
    return "Other"

def categorize_complaint(text):
    """
    Categorizes the main complaint into broad medical groups.
    Used for generating dashboard graphs.
    """
    t = str(text).lower()
    if any(x in t for x in ['chest', 'heart', 'pain', 'cp', 'חזה', 'לב']): return 'Chest Pain/Cardiac'
    if any(x in t for x in ['breath', 'dyspnea', 'short', 'קוצר', 'נשימה']): return 'Respiratory'
    if any(x in t for x in ['abdo', 'belly', 'stomach', 'batan', 'בטן']): return 'Abdominal'
    if any(x in t for x in ['fall', 'trauma', 'hit', 'mva', 'accident', 'נפילה', 'חבלה', 'תאונה']): return 'Trauma/Fall'
    if any(x in t for x in ['weak', 'dizzy', 'syncope', 'faint', 'חולשה', 'סחרחורת']): return 'Neurological/Syncope'
    return 'Other'

def format_patient_data(patient_dict):
    """
    Formats a single row of patient data into a readable string for the LLM.
    Cleans up special characters and missing values.
    """
    def clean(text):
        if pd.isna(text) or text == "MISSING": return "N/A"
        # Remove Excel artifacts and excessive whitespace
        text = str(text).replace('_x000D_', ' ').replace('"', "'").replace('\\', '').replace('\n', ' ').replace('\r', '')
        return text.strip()

    return f"""
    Age: {clean(patient_dict.get('age'))}
    Gender: {clean(patient_dict.get('gender'))}
    Complaint: {clean(patient_dict.get('maincause'))}
    ESI: {clean(patient_dict.get('ESI'))}
    Vitals: {clean(patient_dict.get('Measurements'))}
    Summary: {clean(patient_dict.get('Cause_Remarks'))}
    Medical History: {clean(patient_dict.get('Anamnesis'))}
    """