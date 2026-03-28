from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict
from env.environment import IncidentResponseEnv
from env.models import Action

app = FastAPI(title="DevOps Incident Response Environment", version="1.0.0")
environments = {}

class ResetRequest(BaseModel):
    task_id: str = "easy_oom_crash"
    session_id: str = "default"

class StepRequest(BaseModel):
    action_type: str
    target: Optional[str] = None
    parameters: Optional[Dict] = None
    session_id: str = "default"

def get_env(sid):
    if sid not in environments:
        environments[sid] = IncidentResponseEnv()
    return environments[sid]

@app.get("/")
def root():
    return {"name": "devops-incident-response", "version": "1.0.0"}

@app.get("/health")
def health():
    return {"status": "healthy"}

@app.get("/tasks")
def list_tasks():
    return {"tasks": [
        {"id": "easy_oom_crash", "name": "Single Service OOM Crash", "difficulty": "easy"},
        {"id": "medium_cascade", "name": "Cascading Dependency Failure", "difficulty": "medium"},
        {"id": "hard_race_condition", "name": "Intermittent Race Condition", "difficulty": "hard"},
    ]}

@app.post("/reset")
def reset(request: Optional[ResetRequest] = None):
    try:
        task_id = request.task_id if request else "easy_oom_crash"
        session_id = request.session_id if request else "default"
        env = get_env(session_id)
        result = env.reset(task_id=task_id)
        return result.model_dump()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/step")
def step(request: StepRequest):
    env = get_env(request.session_id)
    if env.task is None:
        raise HTTPException(status_code=400, detail="Call /reset first")
    action = Action(action_type=request.action_type, target=request.target, parameters=request.parameters)
    result = env.step(action)
    return result.model_dump()

@app.get("/state")
def state(session_id: str = "default"):
    env = get_env(session_id)
    if env.task is None:
        raise HTTPException(status_code=400, detail="Call /reset first")
    return env.state().model_dump()

def main():
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7860)

if __name__ == "__main__":
    main()
