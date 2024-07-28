"""Uniswap v3 pool data."""
from dataclasses import dataclass
from decimal import Decimal
from typing import Union, Optional

from eth_typing import HexAddress
from web3 import Web3
from web3.contract import Contract

from eth_defi.abi import get_deployed_contract
from eth_defi.token import TokenDetails, fetch_erc20_details


@dataclass
class PoolDetails:
    """Uniswap v3 trading pool info.

    See :py:func:`fetch_pool_details` on how to construct.
    """

    #: Pool address
    address: HexAddress

    #: One pair of tokens
    token0: TokenDetails

    #: One pair of tokens
    token1: TokenDetails

    #: Pool fee as expressed in smart contracts (100*bps)
    #: e.g. 0.3% = 30bps so raw_fee = 3000
    raw_fee: int

    #: Pool fee as % multiplier, 1 = 100%
    fee: float

    #: Pool contract proxy
    pool: Contract

    def __repr__(self):
        return f"Pool {self.address} is {self.token0.symbol}-{self.token1.symbol}, with the fee {self.fee * 100:.04f}%"

    def convert_price_to_human(self, tick: int, reverse_token_order=False) -> Decimal:
        """Convert the price obtained through

        :param tick:
            Logarithmic tick from the Uniswap pool

        :param reverse_token_order:
            For natural base - quote token order. If set,
            assume quote token is token0.
        """
        raw_price = Decimal("1.0001") ** tick

        if reverse_token_order:
            return (Decimal(1) / raw_price) / Decimal(10 ** (self.token0.decimals - self.token1.decimals))
        else:
            return raw_price / Decimal(10 ** (self.token1.decimals - self.token0.decimals))

    def get_token_details(self, token_address: str) -> TokenDetails:
        if token_address == self.token0.address:
            return self.token0
        elif token_address == self.token1.address:
            return self.token1


@dataclass
class PoolDetailsCutted:
    """Uniswap v3 trading pool info, cutted version.
    See :py:func:`fetch_pool_details` on how to construct.
    """

    #: Pool address
    address: HexAddress

    #: One pair of tokens
    token0_address: HexAddress

    #: One pair of tokens
    token1_address: HexAddress

    def __repr__(self):
        return f"Pool {self.address} is {self.token0_address}-{self.token1_address}"


def fetch_pool_details(web3, pool_contact_address: Union[str, HexAddress], cutted: Optional[bool] = False) -> PoolDetails | PoolDetailsCutted:
    """Resolve Uniswap v3 pool information."""
    if not cutted:
        pool_contact_address = Web3.to_checksum_address(pool_contact_address)
        pool = get_deployed_contract(web3, "uniswap_v3/UniswapV3Pool.json", pool_contact_address)
        token0_address = pool.functions.token0().call()
        token1_address = pool.functions.token1().call()

        token0 = fetch_erc20_details(web3, token0_address)
        token1 = fetch_erc20_details(web3, token1_address)

        raw_fee = pool.functions.fee().call()

        return PoolDetails(
            pool.address,
            token0,
            token1,
            raw_fee,
            raw_fee / 1_000_000,
            pool,
        )
    else:
        pool_contact_address = Web3.to_checksum_address(pool_contact_address)
        pool = get_deployed_contract(web3, "uniswap_v3/UniswapV3Pool.json", pool_contact_address)
        token0_address = pool.functions.token0().call()
        token1_address = pool.functions.token1().call()

        return PoolDetailsCutted(
            pool.address,
            token0_address,
            token1_address,
        )


def get_raw_fee_from_pool_address(web3, pool_contract_address: HexAddress):
    """Get the swap fee for a pool, given the pool contract address

    :param web3:
        Web3 instance

    :param pool_contract_address:
        Address of pool contract

    :return:
        Swap fee expressed as uint24"""
    pool = get_deployed_contract(web3, "uniswap_v3/UniswapV3Pool.json", pool_contract_address)
    return pool.functions.fee().call()



