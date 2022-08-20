import math


MINIMUM_LIQUIDITY = 10


class ERC20:
    """
    https://docs.uniswap.org/protocol/V1/guides/connect-to-uniswap#token-interface
    """

    def __init__(self, name: str, addr: str) -> None:
        self.name = name
        self.token_addr = addr
        self.total_supply = 1_000_000_000
        self.total = 0

    def deposit(self, _from, value):
        self.total += value

    def transfer(self, _to, value):
        self.total -= value


class Factory:
    """
        Create liquidity pools to a given pair.
        https://docs.uniswap.org/protocol/V1/guides/connect-to-uniswap
    """

    def __init__(self, name: str, address: str) -> None:
        self.name = name
        self.address = address
        self.token_to_exchange = {}
        self.exchange_to_tokens = {}

    def create_exchange(self, token0: ERC20, token1: ERC20, symbol: str):
        if self.token_to_exchange.get(token0.name):
            raise Exception("Exchange already created for token")

        new_exchange = Exchange(
            self,
            token0.name,
            token1.name,
            f"{token0.name}/{token1.name}",
            symbol
        )
        self.token_to_exchange[token0.name] = new_exchange
        self.exchange_to_tokens[new_exchange.name] = {token0.name: token0, token1.name: token1}
        return new_exchange

    def get_exchange(self, token):
        return self.token_to_exchange.get(token)

    def get_token(self, exchange):
        return self.exchange_to_token.get(exchange)

    def token_count(self):
        return len(self.token_to_exchange)


class Exchange:
    """
        Exchanges is how uniswap calls the liquidity pools
        https://docs.uniswap.org/protocol/V1/guides/connect-to-uniswap#exchange-interface

        Each exchange is associated with a single ERC20 token and hold a liquidity pool of ETH and the token.
        - The algorithm used is the constant product automated market maker
            - which works by maintaning the relationship token_1 * token_2 = invariant
            - This invariant is held constant during trades

    """
    def __init__(self, creator: Factory, token0_name: str, token1_name: str, name: str, symbol: str) -> None:
        self.factory = creator
        self.token0 = token0_name      # addresses or names. Actual tokens get stored in another place
        self.token1 = token1_name      # addresses or names. Actual tokens get stored in another place
        self.reserve0 = 0               # single storage slot
        self.reserve1 = 0               # single storage slot
        self.fee = 0

        self.name = name
        self.symbol = symbol
        self.liquidity_providers = {}
        self.total_supply = 0

    def info(self):
        print(f"Exchange {self.name} ({self.symbol})")
        print(f"Moedas: {self.token0}/{self.token1}")
        print(f"Reservas: {self.token0} = {self.reserve0} | {self.token1} = {self.reserve1}")
        k = self.reserve0 * self.reserve1
        print(f"Invariante: {self.reserve0} * {self.reserve1} = {k}\n")

    def doc(self):
        print(f"Funcionalidades disponíveis:\n- Adicionar liquidez\n- Remover liquidez\n- Trocar tokens\n")

    def add_liquidity(self, _from, balance0, balance1, balance0Min, balance1Min):
        """
        You always need to add liquidity to both types of coins
        """
        tokens = self.factory.exchange_to_tokens[self.name]
        assert tokens.get(self.token0) and tokens.get(self.token1), "Error"
        amount0, amount1 = self._add_liquidity(balance0, balance1, balance0Min, balance1Min)

        tokens.get(self.token0).deposit(_from, amount0)
        tokens.get(self.token1).deposit(_from, amount1)

        self.mint(_from, amount0, amount1)
        return amount0, amount1

    def _add_liquidity(self, balance0, balance1, balance0Min, balance1Min):
        """
        In practice, Uniswap applies a 0.30% fee to trades, which is added to
        reserves. As a result, each trade actually increases k. This functions
        as a payout to liquidity providers, for simplicity I have removed fee
        related logic.
        """
        tokens = self.factory.exchange_to_tokens[self.name]
        assert tokens.get(self.token0) and tokens.get(self.token1), "Error"

        if self.reserve0 == 0 and self.reserve1 == 0:
            amount0 = balance0
            amount1 = balance1
        else:
            balance1Optimal = self.quote(balance0, self.reserve0, self.reserve1)
            if balance1Optimal <= balance1:
                assert balance1Optimal >= balance1Min, 'UniswapV2Router: INSUFFICIENT_B_AMOUNT'
                amount0 = balance0
                amount1 = balance1Optimal
            else:
                balance0Optimal = self.quote(balance1, self.reserve1, self.reserve0)
                assert balance0Optimal <= balance0
                assert balance0Optimal >= balance0Min, 'UniswapV2Router: INSUFFICIENT_A_AMOUNT'
                amount0 = balance0Optimal
                amount1 = balance1

        return amount0, amount1

    def remove_liquidity(self, to, liquidity, amount0_min, amount1_min):
        tokens = self.factory.exchange_to_tokens[self.name]
        assert tokens.get(self.token0) and tokens.get(self.token1), "Error"
        assert self.liquidity_providers.get(to)

        balance0 = tokens.get(self.token0).total
        balance1 = tokens.get(self.token1).total
        total_liquidity = self.liquidity_providers[to]
        if liquidity >= total_liquidity:
            liquidity = total_liquidity

        amount0 = liquidity * balance0 / self.total_supply      # using balances ensures pro-rata distribution
        amount1 = liquidity * balance1 / self.total_supply      # using balances ensures pro-rata distribution
        assert amount0 > 0 and amount1 > 0, 'UniswapV2: INSUFFICIENT_LIQUIDITY_BURNED'
        assert amount0 >= amount0_min, 'UniswapV2Router: INSUFFICIENT_A_AMOUNT'
        assert amount1 >= amount1_min, 'UniswapV2Router: INSUFFICIENT_B_AMOUNT'

        self.burn(to, liquidity, amount0, amount1)
        return amount0, amount1

    def swapExactTokensForTokens(self, amount0_in, amount1_out_min, to):
        amount1_out_expected = self.get_amount_out(amount0_in)
        assert amount1_out_expected >= amount1_out_min, 'UniswapV2Router: INSUFFICIENT_OUTPUT_AMOUNT'

        tokens = self.factory.exchange_to_tokens[self.name]
        tokens.get(self.token0).deposit(to, amount0_in)

        self.swap(0, amount1_out_expected, to)

        return amount1_out_expected

    def burn(self, to, liquidity, amount0, amount1):
        self._burn(to, liquidity)

        tokens = self.factory.exchange_to_tokens[self.name]
        tokens.get(self.token0).transfer(to, amount0)
        tokens.get(self.token1).transfer(to, amount1)

        balance0 = tokens.get(self.token0).total
        balance1 = tokens.get(self.token1).total

        self._update(balance0, balance1)

    def _burn(self, to, value):
        available_liquidity = self.liquidity_providers.get(to)
        self.liquidity_providers[to] = available_liquidity - value
        self.total_supply -= value

    def mint(self, to, _amount0, _amount1):
        tokens = self.factory.exchange_to_tokens[self.name]
        assert tokens.get(self.token0) and tokens.get(self.token1), "Error"

        balance0 = tokens.get(self.token0).total
        balance1 = tokens.get(self.token1).total

        amount0 = balance0 - self.reserve0
        amount1 = balance1 - self.reserve1
        assert amount0 == _amount0
        assert amount1 == _amount1

        self._update(balance0, balance1)

        # keeping track of the liquidity providers
        if self.total_supply != 0:
            liquidity = min(
                amount0 * self.total_supply / self.reserve0,
                amount1 * self.total_supply / self.reserve1
            )
        else:
            liquidity = math.sqrt(amount0 * amount1) - MINIMUM_LIQUIDITY
            self._mint("0", MINIMUM_LIQUIDITY)

        assert liquidity > 0, 'UniswapV2: INSUFFICIENT_LIQUIDITY_MINTED'
        self._mint(to, liquidity)

    def _update(self, balance0, balance1):
        self.reserve0 = balance0
        self.reserve1 = balance1

    def _mint(self, to, value):
        if self.liquidity_providers.get(to):
            self.liquidity_providers[to] += value
        else:
            self.liquidity_providers[to] = value

        self.total_supply += value

    def swap(self, amount0_out, amount1_out, to):
        assert amount0_out > 0 or amount1_out > 0, 'UniswapV2: INSUFFICIENT_OUTPUT_AMOUNT'
        assert amount0_out < self.reserve0 and amount1_out < self.reserve1, 'UniswapV2: INSUFFICIENT_LIQUIDITY'

        tokens = self.factory.exchange_to_tokens[self.name]
        assert tokens.get(self.token0).token_addr != to, 'UniswapV2: INVALID_TO'
        assert tokens.get(self.token1).token_addr != to, 'UniswapV2: INVALID_TO'

        balance0 = tokens.get(self.token0).total - amount0_out
        balance1 = tokens.get(self.token1).total - amount1_out

        amount0_in = balance0 - (self.reserve0 - amount0_out) if balance0 > self.reserve0 - amount0_out else 0
        amount1_in = balance1 - (self.reserve1 - amount1_out) if balance1 > self.reserve1 - amount1_out else 0
        assert amount0_in > 0 or amount1_in > 0, 'UniswapV2: INSUFFICIENT_INPUT_AMOUNT'

        # disregarding trading fee here
        # balance0_adjusted = balance0 * 1000 - amount0_in * 3  # trading fee
        # balance1_adjusted = balance1 * 1000 - amount1_in * 3  # trading fee

        balance0_adjusted = balance0 * 1000
        balance1_adjusted = balance1 * 1000
        assert balance0_adjusted * balance1_adjusted == self.reserve0 * self.reserve1 * 1000**2, 'UniswapV2: K'

        tokens.get(self.token0).transfer(to, amount0_out)
        tokens.get(self.token1).transfer(to, amount1_out)

        self._update(balance0, balance1)

    def quote(self, amount0, reserve0, reserve1):
        """
        Given some amount of an asset and pair reserves, returns an equivalent amount of
        the other asset
        """
        assert amount0 > 0, 'UniswapV2Library: INSUFFICIENT_AMOUNT'
        assert reserve0 > 0 and reserve1 > 0, 'UniswapV2Library: INSUFFICIENT_LIQUIDITY'
        return (amount0 * reserve1) / reserve0;

    def get_amount_out(self, amount_in):
        """
        Given an input amount of an asset and pair reserves, returns the maximum output amount of the
        other asset

        (reserve0 + amount_in_with_fee) * (reserve1 - amount_out) = reserve1 * reserve0
        """
        assert amount_in > 0, 'UniswapV2Library: INSUFFICIENT_INPUT_AMOUNT'
        assert self.reserve0 > 0 and self.reserve1 > 0, 'UniswapV2Library: INSUFFICIENT_LIQUIDITY'

        amount_in_with_fee = amount_in * 1000              # disconsidering the fee here: amount_in * 997
        numerator = amount_in_with_fee * self.reserve1
        denominator = self.reserve0 * 1000 + amount_in_with_fee
        amount_out = numerator / denominator

        return amount_out

    def simulate_transaction(self, amount_t0):
        result = self.get_amount_out(amount_t0)
        print(f"{amount_t0} {self.token0} recebe {round(result, 2)} {self.token1}")

"""
# References
- Uniswap is made up of a series of ETH-ERC20 exchange contracts. There is exactly one exchange contract per ERC20 token. If a token does not yet have an exchange it can be created by anyone using the Uniswap factory contract. The factory serves as a public registry and is used to look up all token and exchange addresses added to the system.
- Each exchange holds reserves of both ETH and its associated ERC20 token. Anyone can become a liquidity provider on an exchange and contribute to its reserves. This is different than buying or selling; it requires depositing an equivalent value of both ETH and the relevant ERC20 token.
- Liquidity is pooled across all providers and an internal "pool token" (ERC20) is used to track each providers relative contribution. Pool tokens are minted when liquidity is deposited into the system and can be burned at any time to withdraw a proportional share of the reserves.
- Exchange contracts are automated market makers between an ETH-ERC20 pair. Traders can swap between the two in either direction by adding to the liquidity reserve of one and withdrawing from the reserve of the other.
- Uniswap uses a "constant product" market making formula which sets the exchange rate based off of the relative size of the ETH and ERC20 reserves, and the amount with which an incoming trade shifts this ratio.
- A small liquidity provider fee (0.30%) is taken out of each trade and added to the reserves.
- This functions as a payout to liquidity providers that is collected when they burn their pool tokens to withdraw their portion of total reserves.


https://docs.uniswap.org/protocol/V1/reference/interfaces
https://docs.uniswap.org/protocol/V1/introduction
https://hackmd.io/@HaydenAdams/HJ9jLsfTz?type=view#%F0%9F%A6%84-Uniswap-Whitepaper
https://github.com/Uniswap/v1-contracts/blob/c10c08d81d6114f694baa8bd32f555a40f6264da/contracts/uniswap_exchange.vy
https://github.dev/Uniswap/v2-core/blob/master/contracts/UniswapV2Factory.sol
https://github.dev/Uniswap/v2-periphery/blob/master/contracts/UniswapV2Router02.sol
https://docs.uniswap.org/protocol/V1/guides/pool-liquidity
https://docs.uniswap.org/protocol/V2/concepts/core-concepts/pools
https://uniswap.org/whitepaper.pdf
https://betterprogramming.pub/uniswap-smart-contract-breakdown-ea20edf1a0ff
https://coinsbench.com/erc20-smart-contract-breakdown-9dab65cec671
https://betterprogramming.pub/uniswap-smart-contract-breakdown-part-2-b9ea2fca65d1
https://medium.com/scalar-capital/uniswap-a-unique-exchange-f4ef44f807bf
https://ethereum.org/pt-br/developers/tutorials/uniswap-v2-annotated-code/
https://ethereum.org/en/developers/tutorials/uniswap-v2-annotated-code/#add-liquidity-flow
https://jeiwan.net/posts/programming-defi-uniswapv2-1/
https://docs.uniswap.org/protocol/V2/concepts/protocol-overview/ecosystem-participants
"""
