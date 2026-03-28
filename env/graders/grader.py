from env.environment import IncidentResponseEnv
from env.models import Action

def grade_episode(env):
    if env.reward_calc is None:
        return 0.0
    return env.reward_calc.get_score()
