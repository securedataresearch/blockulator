# pragma version ~=0.4.3
# pragma nonreentrancy off
# SPDX-License-Identifier: AGPL-3.0-only
"""
@title SnekmateMath
@license GNU Affero General Public License v3.0 only (it links snekmate's
         AGPL-3.0-only `math` module)
@notice snekmate's `math` module (lib/snekmate, v0.1.2) exported for the
        comparison tables. Each function returns the module's result and the
        gas of the module call alone: `msg.gas` read on either side of the
        one internal call, the same window `noop` puts around an assignment,
        so a caller subtracts `noop`'s figure to get what the call costs
        inside a Vyper contract. Built by scripts/ladder/vyper.py with the
        compiler snekmate pins (0.4.3); the ladder's LadderSnekmate adapter
        and the gas and WAD harnesses call it.

        `wad_sqrt` is not snekmate's: snekmate has no square root, and a
        Vyper contract takes one with the language's built-in `isqrt` on
        x 10^18. It is here for the ladder's scenarios that need a root.
"""

from snekmate.utils import math


@external
@view
def noop(x: int256) -> (int256, uint256):
    g0: uint256 = msg.gas
    r: int256 = x
    g1: uint256 = msg.gas
    return r, g0 - g1


@external
@view
def wad_exp(x: int256) -> (int256, uint256):
    g0: uint256 = msg.gas
    r: int256 = math._wad_exp(x)
    g1: uint256 = msg.gas
    return r, g0 - g1


@external
@view
def wad_ln(x: int256) -> (int256, uint256):
    g0: uint256 = msg.gas
    r: int256 = math._wad_ln(x)
    g1: uint256 = msg.gas
    return r, g0 - g1


@external
@view
def wad_cbrt(x: uint256) -> (uint256, uint256):
    g0: uint256 = msg.gas
    r: uint256 = math._wad_cbrt(x)
    g1: uint256 = msg.gas
    return r, g0 - g1


@external
@view
def mul_div(x: uint256, y: uint256, d: uint256, roundup: bool) -> (uint256, uint256):
    g0: uint256 = msg.gas
    r: uint256 = math._mul_div(x, y, d, roundup)
    g1: uint256 = msg.gas
    return r, g0 - g1


@external
@view
def log2(x: uint256, roundup: bool) -> (uint256, uint256):
    g0: uint256 = msg.gas
    r: uint256 = math._log2(x, roundup)
    g1: uint256 = msg.gas
    return r, g0 - g1


@external
@view
def int256_average(x: int256, y: int256) -> (int256, uint256):
    g0: uint256 = msg.gas
    r: int256 = math._int256_average(x, y)
    g1: uint256 = msg.gas
    return r, g0 - g1


@external
@view
def signum(x: int256) -> (int256, uint256):
    g0: uint256 = msg.gas
    r: int256 = math._signum(x)
    g1: uint256 = msg.gas
    return r, g0 - g1


@external
@view
def wad_sqrt(x: uint256) -> (uint256, uint256):
    g0: uint256 = msg.gas
    r: uint256 = isqrt(x * 10**18)
    g1: uint256 = msg.gas
    return r, g0 - g1
