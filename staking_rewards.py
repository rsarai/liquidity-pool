import time


class Factory:

    def __init__(self, address) -> None:
        self.address = address


class StakingRewards:
    """
    Liquidity provider can stake a % of their deposits amount against the pool of LP providers.
    """

    def __init__(self, liquidity_pool) -> None:
        self.last_update_time = 0
        self.reward_rate = 0
        self.rewards_duration = 31536000    # 365 days = 60*60*24*365
        self.total_supply = 0
        self.period_finish = 0
        self.lp = liquidity_pool

        self.reward_per_token = 0        # changes frequently
        self.user_reward_per_token_paid = {}

        self.rewards = {}
        self.balances = {}

    def doc(self):
        print("Funcionalidades disponíveis: \n- [public] Stake\n- [public] Withdraw\n- [public] Get rewards\n- [private] Add rewards")

    def add_rewards(self, reward, duration=None):
        if duration:
            self.rewards_duration = duration

        current_timestamp = time.time()
        if current_timestamp >= self.period_finish:
            self.reward_rate = reward / self.rewards_duration
        else:
            remaining = self.period_finish - current_timestamp
            leftover = remaining * self.reward_rate
            self.reward_rate = reward + leftover / self.rewards_duration

        self.last_update_time = current_timestamp
        self.period_finish = current_timestamp + self.rewards_duration
        self.update_reward("deployer")

    def stake(self, _from: str,  amount):
        assert amount > 0, "Cannot stake 0"

        provided_liquidity = self.lp.liquidity_providers.get(_from, 0)
        assert provided_liquidity > 0, "Not enough provided liquidity"

        staking_total_for_user = self.balances.get(_from, 0) + amount
        assert staking_total_for_user <= provided_liquidity, "Not enough provided liquidity"

        self.total_supply += amount
        if not self.balances.get(_from):
            self.balances[_from] = amount
        else:
            self.balances[_from] += amount
        self.update_reward(_from)

    def withdraw(self, _from, amount):
        assert amount > 0, "Cannot withdraw 0"
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

    def _reward_per_token(self):
        if (self.total_supply == 0):
            return self.reward_per_token

        return self.reward_per_token + (
            (self.last_time_reward_applicable() - self.last_update_time) * (self.reward_rate / self.total_supply)
        )

    def earned(self, _from, debug=False):
        if not self.user_reward_per_token_paid.get(_from):
            self.user_reward_per_token_paid[_from] = 0

        if not self.balances.get(_from):
            self.balances[_from] = 0

        if not self.rewards.get(_from):
            self.rewards[_from] = 0

        return self.balances[_from] * (
            self._reward_per_token() - self.user_reward_per_token_paid[_from]
        ) + self.rewards[_from]

    def update_reward(self, _from):
        self.reward_per_token = self._reward_per_token()
        self.last_update_time = self.last_time_reward_applicable()

        self.rewards[_from] = self.earned(_from)
        self.user_reward_per_token_paid[_from] = self.reward_per_token
