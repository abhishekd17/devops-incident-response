from env.models import Reward

class RewardCalculator:
    def __init__(self, milestones):
        self.milestones = milestones
        self.achieved = {}
        self.cumulative_score = 0.0
        self.penalty = 0.0

    def award(self, milestone):
        if milestone in self.achieved:
            return 0.0, "Already achieved."
        if milestone not in self.milestones:
            return 0.0, "Unknown milestone."
        value = self.milestones[milestone]
        self.achieved[milestone] = value
        self.cumulative_score = min(1.0, sum(self.achieved.values()) - self.penalty)
        return value, "Milestone: " + milestone + " (+" + str(value) + ")"

    def penalize(self, amount, reason):
        self.penalty += amount
        self.cumulative_score = max(0.0, sum(self.achieved.values()) - self.penalty)
        return -amount, "Penalty: " + reason

    def get_reward(self, step_reward=0.0, message=""):
        return Reward(
            score=max(0.0, min(1.0, self.cumulative_score)),
            step_reward=step_reward,
            breakdown=dict(self.achieved),
            message=message,
        )

    def get_score(self):
        return max(0.0, min(1.0, self.cumulative_score))
