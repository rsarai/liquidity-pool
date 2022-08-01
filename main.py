from multiprocessing import pool
from lp import Factory, ERC20

factory = Factory("ETH pool factory", "0x1")

def create_exchange(name, add, symbol, _factory):
    if _factory:
        factory = _factory

    erc20 = ERC20(name, add)
    eth = ERC20("ETH", "0x09")
    pool = factory.create_exchange(erc20, eth, symbol)
    return pool
