import time


class Factory:

    def __init__(self, address) -> None:
        self.address = address


class StakingRewards:
    """
    LP stakers will be assigned their % amount of SNX rewards based on their % of staked
    uni tokens against the pool of LP providers.
    """

    def __init__(self) -> None:
        self.last_update_time = 0
        self.reward_per_token = None
        self.reward_rate = 0
        self.rewards_duration = 31536000    # 365 days = 60*60*24*365
        self.total_supply = 0
        self.period_finish = 0

        self.user_reward_per_token_paid = []
        self.rewards = []
        self.balances = {}

    def add_rewards(self, reward):
        current_timestamp = time.time()
        if current_timestamp >= self.period_finish:
            self.reward_rate = reward / self.rewards_duration
        else:
            remaining = self.period_finish - current_timestamp
            leftover = remaining * self.reward_rate
            self.reward_rate = reward + leftover / self.rewards_duration

        self.last_update_time = current_timestamp
        self.period_finish = current_timestamp + self.rewards_duration

    def stake(self, _from: str,  amount):
        assert amount > 0, "Cannot stake 0"
        self.total_supply += amount
        if self.balances.get(_from):
            self.balances[_from] = amount
        else:
            self.balances[_from] += amount
        self.update_reward(_from)

    def withdraw(self, _from, amount):
        assert amount > 0, "Cannot stake 0"
        self.total_supply -= amount
        self.balances[_from] -= amount
        self.update_reward(_from)

    def get_reward(self, _from):
        self.update_reward(_from)
        reward = self.rewards[_from]
        if (reward > 0):
            self.rewards[_from] = 0

        return reward

    def last_time_reward_applicable(self):
        return min(time.time(), self.period_finish)

    def reward_per_token(self):
        if (self.total_supply == 0):
            return self.reward_per_token

        return self.reward_per_token + (
            self.last_time_reward_applicable() - self.last_update_time * self.reward_rate * 1e18 / self.total_supply
        )

    def earned(self, _from):
        return self.balances[_from] * (
            self.reward_per_token() - self.user_reward_per_token_paid[_from]
        ) / 1e18 + self.rewards[_from]

    def update_reward(self, _from):
        self.reward_per_token = self.reward_per_token()
        self.last_update_time = self.last_time_reward_applicable()

        self.rewards[_from] = self.earned(_from)
        self.user_reward_per_token_paid[_from] = self.reward_per_token
