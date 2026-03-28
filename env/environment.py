import copy
from env.models import Action, EnvironmentState, Observation, StepResult, TaskConfig
from env.reward import RewardCalculator
from env.tasks.easy import get_easy_task
from env.tasks.medium import get_medium_task
from env.tasks.hard import get_hard_task

AVAILABLE_ACTIONS = ["view_log","check_status","restart_service","rollback_deploy","scale_service","run_diagnostic","submit_diagnosis"]
TASK_REGISTRY = {"easy_oom_crash": get_easy_task, "medium_cascade": get_medium_task, "hard_race_condition": get_hard_task}

class IncidentResponseEnv:
    def __init__(self):
        self.task = None
        self.step_number = 0
        self.system_status = {}
        self.done = False
        self.reward_calc = None
        self.actions_taken = []
        self.logs_viewed = []
        self.diagnosis_submitted = False
        self.services_restarted = []
        self.last_message = ""
        self.last_log = None

    def reset(self, task_id="easy_oom_crash"):
        if task_id not in TASK_REGISTRY:
            raise ValueError("Unknown task_id: " + task_id)
        self.task = TASK_REGISTRY[task_id]()
        self.step_number = 0
        self.system_status = copy.deepcopy(self.task.initial_status)
        self.done = False
        self.reward_calc = RewardCalculator(self.task.milestones)
        self.actions_taken = []
        self.logs_viewed = []
        self.diagnosis_submitted = False
        self.services_restarted = []
        self.last_message = "Incident alert received. Begin investigation."
        self.last_log = None
        return StepResult(observation=self._get_obs(), reward=self.reward_calc.get_reward(0.0, "Environment reset."), done=False, info={"task_id": task_id, "difficulty": self.task.difficulty})

    def step(self, action):
        if self.task is None:
            raise RuntimeError("Call reset() first.")
        if self.done:
            return StepResult(observation=self._get_obs(), reward=self.reward_calc.get_reward(0.0, "Episode finished."), done=True, info={})
        self.step_number += 1
        self.last_log = None
        sr = 0.0
        msgs = []
        self.actions_taken.append(action.action_type + "(" + str(action.target or "") + ")")
        if action.action_type not in AVAILABLE_ACTIONS:
            p, m = self.reward_calc.penalize(0.05, "Invalid action")
            sr += p; msgs.append(m)
        else:
            h = getattr(self, "_h_" + action.action_type, None)
            if h:
                r, m = h(action)
                sr += r
                msgs.extend(m if isinstance(m, list) else [m])
        if self.step_number >= self.task.max_steps and not self.done:
            self.done = True; msgs.append("Max steps reached.")
        self.last_message = " | ".join(msgs)
        return StepResult(observation=self._get_obs(), reward=self.reward_calc.get_reward(sr, self.last_message), done=self.done, info={"step": self.step_number, "milestones": list(self.reward_calc.achieved.keys())})

    def state(self):
        return EnvironmentState(task_id=self.task.task_id if self.task else "", step_number=self.step_number, max_steps=self.task.max_steps if self.task else 0, system_status=dict(self.system_status), done=self.done, cumulative_reward=self.reward_calc.get_score() if self.reward_calc else 0.0, milestones_achieved=list(self.reward_calc.achieved.keys()) if self.reward_calc else [], actions_taken=list(self.actions_taken))

    def _h_view_log(self, a):
        t = a.target
        if not t or t not in self.task.services: return 0.0, "Unknown service"
        self.last_log = self.task.logs.get(t, "No logs."); self.logs_viewed.append(t)
        r = 0.0; msgs = ["Logs for " + t]
        r += self._log_ms(t, msgs); return r, msgs

    def _h_check_status(self, a):
        t = a.target; msgs = []
        if t and t in self.system_status: msgs.append(t + ": " + self.system_status[t])
        else:
            for s, v in self.system_status.items(): msgs.append(s + ": " + v)
        return 0.0, msgs

    def _h_restart_service(self, a):
        t = a.target
        if not t or t not in self.task.services: return 0.0, "Unknown service"
        self.services_restarted.append(t)
        tid = self.task.task_id
        if tid == "easy_oom_crash": return self._re(t)
        elif tid == "medium_cascade": return self._rm(t)
        elif tid == "hard_race_condition": return self._rh(t)
        return 0.0, "Restarted."

    def _h_rollback_deploy(self, a):
        t = a.target
        if not t or t not in self.task.services: return 0.0, "Unknown service"
        if self.task.task_id == "hard_race_condition" and t == "batch-reconciliation-job":
            r = 0.0; msgs = ["Rolling back " + t]; self.system_status[t] = "UP"
            v, m = self.reward_calc.award("correct_remediation"); r += v
            if v > 0: msgs.append(m)
            v2, m2 = self.reward_calc.award("services_restored"); r += v2
            if v2 > 0: msgs.append(m2); self.done = True
            return r, msgs
        p, m = self.reward_calc.penalize(0.02, "Rollback not effective"); return p, [m]

    def _h_scale_service(self, a):
        p, m = self.reward_calc.penalize(0.02, "Scaling doesnt fix root cause"); return p, [m]

    def _h_run_diagnostic(self, a):
        t = a.target
        if not t or t not in self.task.services: return 0.0, "Unknown service"
        s = self.system_status.get(t, "UNKNOWN"); return 0.0, ["Diagnostic: " + t + " status=" + s]

    def _h_submit_diagnosis(self, a):
        p = a.parameters or {}; rc = str(p.get("root_cause", "")).lower(); af = p.get("affected_services", [])
        if isinstance(af, str): af = [af]
        self.diagnosis_submitted = True; r = 0.0; msgs = ["Diagnosis submitted"]
        kw = {"easy_oom_crash": ["oom","memory","heap","out_of_memory"], "medium_cascade": ["disk","full","space","wal","storage"], "hard_race_condition": ["lock","race","contention","batch","reconciliation"]}
        for k in kw.get(self.task.task_id, []):
            if k in rc:
                v, m = self.reward_calc.award("identified_root_cause"); r += v
                if v > 0: msgs.append(m)
                break
        rs = self.task.root_cause_service
        if rs in af or rs in rc:
            mn = "identified_root_service" if "identified_root_service" in self.task.milestones else "identified_affected_service"
            v, m = self.reward_calc.award(mn); r += v
            if v > 0: msgs.append(m)
        return r, msgs

    def _re(self, t):
        r = 0.0; msgs = []
        if t == "payment-service":
            self.system_status[t] = "UP"; msgs.append("Restarted OK")
            v, m = self.reward_calc.award("correct_remediation"); r += v
            if v > 0: msgs.append(m)
            v2, m2 = self.reward_calc.award("services_restored"); r += v2
            if v2 > 0: msgs.append(m2); self.done = True
        else:
            p, m = self.reward_calc.penalize(0.03, "Wrong service"); r += p; msgs.append(m)
        return r, msgs

    def _rm(self, t):
        r = 0.0; msgs = []
        if t == "database":
            self.system_status["database"] = "UP"; msgs.append("Database restarted")
            if not any(s in self.services_restarted for s in ["payment-service","order-service"]):
                v, m = self.reward_calc.award("fixed_root_service_first"); r += v
                if v > 0: msgs.append(m)
            v, m = self.reward_calc.award("correct_remediation"); r += v
            if v > 0: msgs.append(m)
        elif t in ("payment-service","order-service"):
            if self.system_status.get("database") == "UP":
                self.system_status[t] = "UP"; msgs.append(t + " restarted OK")
            else:
                p, m = self.reward_calc.penalize(0.05, t + " needs database"); r += p; msgs.append(m)
        else:
            p, m = self.reward_calc.penalize(0.02, "Unnecessary restart"); r += p; msgs.append(m)
        if all(self.system_status.get(s) == "UP" for s in self.task.affected_services):
            v, m = self.reward_calc.award("all_services_restored"); r += v
            if v > 0: msgs.append(m); self.done = True
        return r, msgs

    def _rh(self, t):
        r = 0.0; msgs = []
        if t == "batch-reconciliation-job":
            self.system_status[t] = "UP"; msgs.append("Batch job restarted")
            v, m = self.reward_calc.award("correct_remediation"); r += v
            if v > 0: msgs.append(m)
            v2, m2 = self.reward_calc.award("services_restored"); r += v2
            if v2 > 0: msgs.append(m2); self.done = True
        else:
            p, m = self.reward_calc.penalize(0.03, "Wrong service"); r += p; msgs.append(m)
        return r, msgs

    def _log_ms(self, svc, msgs):
        r = 0.0; tid = self.task.task_id
        if tid == "easy_oom_crash" and svc == "payment-service":
            for ms in ["viewed_relevant_log","found_error_message","identified_affected_service"]:
                v, m = self.reward_calc.award(ms); r += v
                if v > 0: msgs.append(m)
        elif tid == "medium_cascade":
            if svc in ("payment-service","order-service"):
                for ms in ["viewed_relevant_log","found_error_in_downstream"]:
                    v, m = self.reward_calc.award(ms); r += v
                    if v > 0: msgs.append(m)
            if svc == "database":
                for ms in ["viewed_relevant_log","found_error_in_root_service"]:
                    v, m = self.reward_calc.award(ms); r += v
                    if v > 0: msgs.append(m)
        elif tid == "hard_race_condition":
            if svc == "checkout-service":
                v, m = self.reward_calc.award("viewed_checkout_log"); r += v
                if v > 0: msgs.append(m)
            if svc == "payment-service":
                for ms in ["viewed_payment_log","identified_lock_timeout"]:
                    v, m = self.reward_calc.award(ms); r += v
                    if v > 0: msgs.append(m)
            if svc in ("redis","batch-reconciliation-job"):
                v, m = self.reward_calc.award("viewed_redis_or_batch_log"); r += v
                if v > 0: msgs.append(m)
                if svc == "batch-reconciliation-job":
                    v2, m2 = self.reward_calc.award("identified_batch_job_conflict"); r += v2
                    if v2 > 0: msgs.append(m2)
        return r

    def _get_obs(self):
        return Observation(alert_message=self.task.alert_message if self.task else "", available_services=self.task.services if self.task else [], system_status=dict(self.system_status), current_log=self.last_log, available_actions=AVAILABLE_ACTIONS, step_number=self.step_number, max_steps=self.task.max_steps if self.task else 0, message=self.last_message, task_id=self.task.task_id if self.task else "", done=self.done)
