from typing import Dict, List, Optional
from pydantic import BaseModel, Field

class Observation(BaseModel):
    alert_message: str = ""
    available_services: List[str] = []
    system_status: Dict[str, str] = {}
    current_log: Optional[str] = None
    available_actions: List[str] = []
    step_number: int = 0
    max_steps: int = 0
    message: str = ""
    task_id: str = ""
    done: bool = False

class Action(BaseModel):
    action_type: str = ""
    target: Optional[str] = None
    parameters: Optional[Dict] = None

class Reward(BaseModel):
    score: float = Field(default=0.0, ge=0.0, le=1.0)
    step_reward: float = 0.0
    breakdown: Dict[str, float] = {}
    message: str = ""

class StepResult(BaseModel):
    observation: Observation
    reward: Reward
    done: bool = False
    info: Dict = {}

class EnvironmentState(BaseModel):
    task_id: str = ""
    step_number: int = 0
    max_steps: int = 0
    system_status: Dict[str, str] = {}
    done: bool = False
    cumulative_reward: float = 0.0
    milestones_achieved: List[str] = []
    actions_taken: List[str] = []

class TaskConfig(BaseModel):
    task_id: str
    name: str
    difficulty: str
    description: str
    max_steps: int
    services: List[str]
    initial_status: Dict[str, str]
    alert_message: str
    root_cause: str
    root_cause_service: str
    affected_services: List[str]
    correct_fix: str
    logs: Dict[str, str]
    milestones: Dict[str, float]
