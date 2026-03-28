import os, json
from openai import OpenAI
from env.environment import IncidentResponseEnv
from env.models import Action
from env.graders.grader import grade_episode

API_BASE_URL = os.environ.get("API_BASE_URL", "https://api.openai.com/v1")
MODEL_NAME = os.environ.get("MODEL_NAME", "gpt-4o-mini")
HF_TOKEN = os.environ.get("HF_TOKEN", "")
API_KEY = os.environ.get("OPENAI_API_KEY", HF_TOKEN)
client = OpenAI(base_url=API_BASE_URL, api_key=API_KEY)

SYSTEM_PROMPT = """You are an expert SRE responding to a production incident.
Available actions (respond with ONE JSON object only):
1. {"action_type": "view_log", "target": "service-name"}
2. {"action_type": "check_status", "target": "service-name"}
3. {"action_type": "restart_service", "target": "service-name"}
4. {"action_type": "rollback_deploy", "target": "service-name"}
5. {"action_type": "scale_service", "target": "service-name", "parameters": {"replicas": 3}}
6. {"action_type": "run_diagnostic", "target": "service-name", "parameters": {"type": "health"}}
7. {"action_type": "submit_diagnosis", "parameters": {"root_cause": "desc", "affected_services": ["svc"], "fix": "desc"}}
Investigate first, then fix. Respond with ONLY JSON."""

def parse_action(text):
    text = text.strip()
    s = text.find("{"); e = text.rfind("}") + 1
    if s >= 0 and e > s:
        try:
            d = json.loads(text[s:e])
            return Action(action_type=d.get("action_type","check_status"), target=d.get("target"), parameters=d.get("parameters"))
        except: pass
    return Action(action_type="check_status")

def build_prompt(obs, step):
    p = "STEP " + str(step) + "/" + str(obs.max_steps) + "\nALERT:\n" + obs.alert_message + "\nSTATUS:\n"
    for s, v in obs.system_status.items(): p += "  " + s + ": " + v + "\n"
    p += "SERVICES: " + ", ".join(obs.available_services) + "\n"
    if obs.current_log: p += "LOG:\n" + obs.current_log + "\n"
    if obs.message: p += "LAST: " + obs.message + "\n"
    return p + "\nWhat action? JSON only."

def run_task(task_id, name):
    print("\n" + "="*50 + "\nTASK: " + name + "\n" + "="*50)
    env = IncidentResponseEnv(); result = env.reset(task_id=task_id); obs = result.observation
    for s in range(1, obs.max_steps + 1):
        if result.done: break
        try:
            c = client.chat.completions.create(model=MODEL_NAME, messages=[{"role":"system","content":SYSTEM_PROMPT},{"role":"user","content":build_prompt(obs,s)}], temperature=0.1, max_tokens=500)
            resp = c.choices[0].message.content or ""
        except Exception as ex:
            resp = '{"action_type":"check_status"}'
        action = parse_action(resp)
        print("  Step " + str(s) + ": " + action.action_type + "(" + str(action.target or "") + ")")
        result = env.step(action); obs = result.observation
    score = grade_episode(env)
    print("  SCORE: " + str(score)); return score

def main():
    tasks = [("easy_oom_crash","OOM Crash"),("medium_cascade","Cascade Failure"),("hard_race_condition","Race Condition")]
    scores = {}
    for tid, name in tasks: scores[tid] = run_task(tid, name)
    print("\n" + "="*50 + "\nRESULTS")
    for t, s in scores.items(): print("  " + t + ": " + str(s))
    print("  AVG: " + str(round(sum(scores.values())/len(scores), 2)))

if __name__ == "__main__":
    main()
