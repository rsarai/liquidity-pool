import time
import pytest
from freezegun import freeze_time

from main import create_exchange, create_staking_rewards
from lp import Factory


def setup():
    factory = Factory("ETH pool factory", "0x1")
    lp = create_exchange("test-coin", "0x111", "TST1", factory)
    assert lp.reserve0 == 0
    assert lp.reserve1 == 0

    eth_amount = 50000
    tst_amount = 50000
    lp.add_liquidity("rsarai", eth_amount, tst_amount, eth_amount, tst_amount)

    assert lp.reserve0 == 50000
    assert lp.reserve1 == 50000
    return lp

def test_creates_staking_rewards_raises_exception_if_not_staked():
    lp = setup()
    st = create_staking_rewards(lp, 1_000_000)

    with pytest.raises(Exception, match="Not enough provided liquidity"):
        st.stake("random", 1000)

def test_creates_staking_rewards():
    with freeze_time('2022-08-20 14:49:07'):
        lp = setup()
        st = create_staking_rewards(lp, 1_000_000)
        st.stake("rsarai", 49990.0)

        assert st.balances["rsarai"] == 49990.0
        assert st.last_update_time == time.time()   # 1661006947.0
        assert round(st.reward_rate, 3) == 0.032
        assert st.total_supply == 49990.0
        assert st.period_finish == 1692542947.0

def test_earned_amount():
    with freeze_time('2022-08-20 14:49:07'):
        lp = setup()
        st = create_staking_rewards(lp, 1_000_000)
        st.stake("rsarai", 49990.0)

        assert st.balances["rsarai"] == 49990.0
        assert st.last_update_time == time.time()   # 1661006947.0
        assert round(st.reward_rate, 3) == 0.032
        assert st.total_supply == 49990.0
        assert st.period_finish == 1692542947.0

    with freeze_time('2022-08-20 14:49:12'):
        res = st.earned("rsarai")

        # 5s after it should have 5 * reward rate
        assert res > 0
        assert res == st.reward_rate * 5

    with freeze_time('2022-08-20 14:49:17'):
        res = st.earned("rsarai")

        # 10s after it should have 10 * reward rate
        assert res == st.reward_rate * 10


def test_earned_amount_with_multiple_staked():
    with freeze_time('2022-08-20 14:49:07'):
        lp = setup()
        eth_amount = 50000
        tst_amount = 50000
        lp.add_liquidity("garrincha", eth_amount, tst_amount, eth_amount, tst_amount)

        st = create_staking_rewards(lp, 1_000_000)
        st.stake("rsarai", 49990.0)

        assert st.balances["rsarai"] == 49990.0
        assert st.last_update_time == time.time()   # 1661006947.0
        assert round(st.reward_rate, 3) == 0.032
        assert st.total_supply == 49990.0
        assert st.period_finish == 1692542947.0

    with freeze_time('2022-08-20 14:49:12'):
        res_5s = st.earned("rsarai")

        # 5s after it should have 5 * reward rate
        assert res_5s == st.reward_rate * 5

        st.stake("garrincha", 25000.0)

        # calls update_reward
        assert round(st.reward_rate, 3) == 0.032
        assert st.last_update_time == 1661006952.0

    with freeze_time('2022-08-20 14:49:17'):
        res = st.earned("rsarai")

        assert round(st.reward_rate, 3) == 0.032
        assert res != st.reward_rate * 10
        assert res < st.reward_rate * 10
        assert res > st.reward_rate * 5
        assert round(res, 4) == 0.2114

        res_2 = st.earned("garrincha")
        assert res_2 < res
        assert round(res_2, 4) == 0.1057


def test_earned_amount_one_year_after():
    with freeze_time('2022-08-20 14:49:07'):
        lp = setup()
        st = create_staking_rewards(lp, 1_000_000)
        st.stake("rsarai", 49990.0)

        assert st.balances["rsarai"] == 49990.0
        assert st.last_update_time == time.time()   # 1661006947.0
        assert round(st.reward_rate, 3) == 0.032
        assert st.total_supply == 49990.0
        assert st.period_finish == 1692542947.0

    with freeze_time('2023-08-20 14:49:12'):
        res = st.earned("rsarai")
        assert res == 1000000.0


def test_get_reward_one_year_after():
    with freeze_time('2022-08-20 14:49:07'):
        lp = setup()
        st = create_staking_rewards(lp, 1_000_000)
        st.stake("rsarai", 49990.0)

        assert st.balances["rsarai"] == 49990.0
        assert st.last_update_time == time.time()   # 1661006947.0
        assert round(st.reward_rate, 3) == 0.032
        assert st.total_supply == 49990.0
        assert st.period_finish == 1692542947.0

    with freeze_time('2023-08-20 14:49:12'):
        res = st.get_reward("rsarai")
        assert res == 1000000.0
        assert st.rewards.get("rsarai") == 0
