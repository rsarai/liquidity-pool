from multiprocessing import pool
from lp import Factory, ERC20
from staking_rewards import StakingRewards

factory = Factory("ETH pool factory", "0x1")

def create_exchange(name, address, symbol, _factory):
    if _factory:
        factory = _factory

    erc20 = ERC20(name, address)
    eth = ERC20("ETH", "0x09")
    pool = factory.create_exchange(erc20, eth, symbol)
    return pool


def create_staking_rewards(lp, rewards):
    st = StakingRewards(lp)
    st.add_rewards(rewards)
    return st
