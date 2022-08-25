import pytest

from main import create_exchange
from lp import Factory

def test_create_liquidity_pool():
    factory = Factory("ETH pool factory", "0x1")
    lp = create_exchange("test-coin", "0x111", "TST1", factory)

    token = factory.exchange_to_tokens[lp.name]["test-coin"]
    assert token.token_addr == "0x111"
    assert lp.name == "test-coin/ETH"
    assert lp.symbol == "TST1"

def test_doesnt_create_two_equal_pools():
    factory = Factory("ETH pool factory", "0x1")
    create_exchange("test-coin", "0x111", "TST1", factory)

    with pytest.raises(Exception, match="Exchange already created for token"):
        create_exchange("test-coin", "0x111", "TST1", factory)

def test_add_liquidity_to_pool():
    factory = Factory("ETH pool factory", "0x1")
    lp = create_exchange("test-coin", "0x111", "TST1", factory)
    assert lp.reserve0 == 0
    assert lp.reserve1 == 0

    eth_amount = 50000
    tst_amount = 50000
    lp.add_liquidity("rsarai", eth_amount, tst_amount, eth_amount, tst_amount)
    assert lp.reserve0 == 50000
    assert lp.reserve1 == 50000

def test_add_liquidity_to_pool_multiple_times():
    factory = Factory("ETH pool factory", "0x1")
    lp = create_exchange("test-coin", "0x111", "TST1", factory)
    assert lp.reserve0 == 0
    assert lp.reserve1 == 0

    eth_amount = 500
    tst_amount = 500
    lp.add_liquidity("rsarai", eth_amount, tst_amount, eth_amount, tst_amount)
    assert lp.reserve0 == 500
    assert lp.reserve1 == 500

    eth_amount = 500
    tst_amount = 500
    lp.add_liquidity("rsarai", eth_amount, tst_amount, eth_amount, tst_amount)
    assert lp.reserve0 == 1000
    assert lp.reserve1 == 1000

    eth_amount = 500
    tst_amount = 500
    lp.add_liquidity("rsarai", eth_amount, tst_amount, eth_amount, tst_amount)
    assert lp.reserve0 == 1500
    assert lp.reserve1 == 1500

def test_add_liquidity_to_pool_with_unbalanced_amounts():
    factory = Factory("ETH pool factory", "0x1")
    lp = create_exchange("test-coin", "0x111", "TST1", factory)
    assert lp.reserve0 == 0
    assert lp.reserve1 == 0

    eth_amount = 500
    tst_amount = 500
    lp.add_liquidity("rsarai", eth_amount, tst_amount, eth_amount, tst_amount)
    assert lp.reserve0 == 500
    assert lp.reserve1 == 500

    eth_amount = 501
    tst_amount = 499
    with pytest.raises(Exception, match="UniswapV2Router: INSUFFICIENT_A_AMOUNT"):
        lp.add_liquidity("rsarai", eth_amount, tst_amount, eth_amount, tst_amount)

    eth_amount = 499
    tst_amount = 501
    with pytest.raises(Exception, match="UniswapV2Router: INSUFFICIENT_B_AMOUNT"):
        lp.add_liquidity("rsarai", eth_amount, tst_amount, eth_amount, tst_amount)

def test_swapExactTokensForTokens():
    factory = Factory("ETH pool factory", "0x1")
    lp = create_exchange("test-coin", "0x111", "TST1", factory)
    assert lp.reserve0 == 0
    assert lp.reserve1 == 0

    eth_amount = 1000
    tst_amount = 1000
    lp.add_liquidity("rsarai", eth_amount, tst_amount, eth_amount, tst_amount)
    assert lp.reserve0 == 1000
    assert lp.reserve1 == 1000

    lp.swapExactTokensForTokens(600, 375, "rsarai")
    assert lp.reserve0 == 1600
    assert lp.reserve1 == 625


def test_add_and_remove_liquidity_to_pool():
    factory = Factory("ETH pool factory", "0x1")
    lp = create_exchange("test-coin", "0x111", "TST1", factory)
    assert lp.reserve0 == 0
    assert lp.reserve1 == 0

    eth_amount = 50000
    tst_amount = 50000
    lp.add_liquidity("rsarai", eth_amount, tst_amount, eth_amount, tst_amount)
    assert lp.reserve0 == 50000
    assert lp.reserve1 == 50000
    assert lp.liquidity_providers["0"] == 10
    assert lp.liquidity_providers["rsarai"] == 49990.0

    amount0, amount1 = lp.remove_liquidity("rsarai", 29990, 1, 1)

    assert amount0 == 29990.0
    assert amount1 == 29990.0
    assert lp.liquidity_providers == {"0": 10, "rsarai": 20000.0}

def test_swapExactTokensForTokens_mulitple_times():
    factory = Factory("ETH pool factory", "0x1")
    lp = create_exchange("test-coin", "0x111", "TST1", factory)
    assert lp.reserve0 == 0
    assert lp.reserve1 == 0

    eth_amount = 1000
    tst_amount = 1000
    lp.add_liquidity("rsarai", eth_amount, tst_amount, eth_amount, tst_amount)
    assert lp.reserve0 == 1000
    assert lp.reserve1 == 1000

    lp.swapExactTokensForTokens(600, 375, "rsarai")
    assert lp.reserve0 == 1600
    assert lp.reserve1 == 625

    lp.swapExactTokensForTokens(400, 125, "rsarai")
    assert lp.reserve0 == 2000
    assert lp.reserve1 == 500

def test_swapExactTokensForTokens_with_more_than_optimal():
    factory = Factory("ETH pool factory", "0x1")
    lp = create_exchange("test-coin", "0x111", "TST1", factory)
    assert lp.reserve0 == 0
    assert lp.reserve1 == 0

    eth_amount = 1000
    tst_amount = 1000
    lp.add_liquidity("rsarai", eth_amount, tst_amount, eth_amount, tst_amount)
    assert lp.reserve0 == 1000
    assert lp.reserve1 == 1000

    with pytest.raises(Exception, match="UniswapV2Router: INSUFFICIENT_OUTPUT_AMOUNT"):
        lp.swapExactTokensForTokens(600, 675, "rsarai")

def test_swapExactTokensForTokens_with_less_than_optimal():
    factory = Factory("ETH pool factory", "0x1")
    lp = create_exchange("test-coin", "0x111", "TST1", factory)
    assert lp.reserve0 == 0
    assert lp.reserve1 == 0

    eth_amount = 1000
    tst_amount = 1000
    lp.add_liquidity("rsarai", eth_amount, tst_amount, eth_amount, tst_amount)
    assert lp.reserve0 == 1000
    assert lp.reserve1 == 1000

    token1 = lp.swapExactTokensForTokens(600, 374, "rsarai")
    assert lp.reserve0 == 1600
    assert lp.reserve1 == 625
    assert token1 == 375

def test_swapExactTokensForTokens_with_way_less_than_optimal():
    factory = Factory("ETH pool factory", "0x1")
    lp = create_exchange("test-coin", "0x111", "TST1", factory)
    assert lp.reserve0 == 0
    assert lp.reserve1 == 0

    eth_amount = 1000
    tst_amount = 1000
    lp.add_liquidity("rsarai", eth_amount, tst_amount, eth_amount, tst_amount)
    assert lp.reserve0 == 1000
    assert lp.reserve1 == 1000

    token1 = lp.swapExactTokensForTokens(600, 200, "rsarai")
    assert lp.reserve0 == 1600
    assert lp.reserve1 == 625
    assert token1 == 375

def test_remove_liquidity_after_swap():
    factory = Factory("ETH pool factory", "0x1")
    lp = create_exchange("test-coin", "0x111", "TST1", factory)
    assert lp.reserve0 == 0
    assert lp.reserve1 == 0

    eth_amount = 1000
    tst_amount = 1000
    lp.add_liquidity("rsarai", eth_amount, tst_amount, eth_amount, tst_amount)
    assert lp.reserve0 == 1000
    assert lp.reserve1 == 1000

    token1 = lp.swapExactTokensForTokens(50, 30, "x")
    assert lp.reserve0 == 1050
    assert lp.reserve1 == pytest.approx(952.38, 0.01)
    assert token1 == pytest.approx(47.62, 0.01)

    amount0, amount1 = lp.remove_liquidity("rsarai", 100, 1, 1)

    assert amount0 == 105.0
    assert amount1 == pytest.approx(95.23, 0.01)
    assert lp.liquidity_providers == {"0": 10, "rsarai": 890.0}

def test_get_amount_out():
    factory = Factory("ETH pool factory", "0x1")
    lp = create_exchange("test-coin", "0x111", "TST1", factory)
    assert lp.reserve0 == 0
    assert lp.reserve1 == 0

    eth_amount = 1000
    tst_amount = 1000
    lp.add_liquidity("rsarai", eth_amount, tst_amount, eth_amount, tst_amount)

    assert lp.get_amount_out(50) == pytest.approx(47.62, 0.01)
    assert lp.get_amount_out(5) == pytest.approx(4.97, 0.01)
    assert lp.get_amount_out(135) == pytest.approx(118.94, 0.01)
    assert lp.get_amount_out(35) == pytest.approx(33.81, 0.01)
    assert lp.get_amount_out(209) == pytest.approx(172.87, 0.01)
    assert lp.get_amount_out(13) == pytest.approx(12.83, 0.01)
