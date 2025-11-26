from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
import pandas as pd
from config import get_model
from agents import SafetyAgent, PathologyAgent, DischargeOfficerAgent, GeriatricAgent, SupervisorAgent

app = FastAPI(title="SMARTriage API", version="1.0")

# Allow CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Frontend (Static Files)
# We mount it at the root, but we must ensure API routes are defined first or handle conflicts.
# Actually, it's better to mount static files at /static or just serve index.html at root.
# But for simplicity, let's assume the user opens /index.html or we serve it.


# Initialize Model & Agents
print("Initializing Agents...")
try:
    vertex_model = get_model()
    safety_agent = SafetyAgent()
    pathology_agent = PathologyAgent(vertex_model)
    discharge_agent = DischargeOfficerAgent(vertex_model)
    geriatric_agent = GeriatricAgent(vertex_model)
    supervisor_agent = SupervisorAgent(vertex_model)
    print("Agents initialized successfully.")
except Exception as e:
    print(f"Error initializing agents: {e}")
    # We don't raise error here to allow app to start, but requests will fail if agents aren't ready

class PatientInput(BaseModel):
    age: str
    gender: str
    complaint: str
    esi: float
    vitals: str # Keeping it simple as a string for now, or could be dict
    background: str
    remarks: str

@app.get("/")
def health_check():
    return {"status": "ok", "message": "SMARTriage API is running"}

@app.post("/triage")
async def triage_patient(data: PatientInput):
    print(f"Received triage request for: {data.complaint}")
    
    # Construct "details_text" for SafetyAgent (Regex)
    # SafetyAgent looks for keywords in the text.
    details_text = f"{data.complaint} {data.remarks} {data.background}"
    
    # Construct "patient_text" for LLM Agents
    # This mimics the format in utils.format_patient_data
    patient_text = f"""
    Age: {data.age}
    Gender: {data.gender}
    Complaint: {data.complaint}
    ESI: {data.esi}
    Vitals: {data.vitals}
    Summary: {data.remarks}
    Medical History: {data.background}
    """
    
    try:
        # 1. Safety
        safety_res = safety_agent.analyze(details_text)
        
        # 2. Parallel LLM Calls (Sequential for simplicity here)
        path_res = pathology_agent.consult(patient_text)
        disch_res = discharge_agent.consult(patient_text)
        geri_res = geriatric_agent.consult(patient_text)
        
        # 3. Supervisor
        final_res = supervisor_agent.make_final_decision(
            safety_res, path_res, disch_res, geri_res, data.esi, patient_text
        )
        
        return {
            "final_decision": final_res["final_decision"],
            "reason": final_res["override_reason"],
            "source": final_res["decision_source"],
            "votes": {
                "safety": safety_res,
                "pathology": path_res,
                "discharge": disch_res,
                "geriatric": geri_res
            }
        }
    except Exception as e:
        print(f"Error processing request: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Mount static files
frontend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../frontend"))
if os.path.exists(frontend_path):
    app.mount("/", StaticFiles(directory=frontend_path, html=True), name="static")
else:
    print(f"Warning: Frontend directory not found at {frontend_path}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
