+++
title = "Integrating"
description = "Two rules that end dust, each from the replay of a real exploit, with worked code in FP127 and FP19."
path = "library/integrating"

[extra]
group = "library"
+++

More digits help only if you follow two rules. Each comes from replaying a real exploit, from its attack transaction, in FP127, FP19 and exact arithmetic.

1. **Store the state in the format.** Keep a running balance, index or accumulator as an FP127 or FP19 value. Do not round it to token units before you store it.
2. **Round toward the protocol at the token edge.** When a value becomes token units, round down what the protocol pays out and round up what it takes in. Never round to nearest there.

Between those two points the plain ops are fine. FP127's `add` and `sub` are exact, and its `mul`, `div` and `sqrt` are off by at most one unit of 2<sup>−128</sup>. FP19's undirected ops round to nearest, once. That includes `toFixed18` and `toFP127`, so at the edge use their `Down` and `Up` versions.

## Rule 1: Bunni v2

On 2 September 2025, 44 withdrawals each took their share of a Bunni pool's idle USDC balance. The code worked in whole wei and rounded the stored balance up every time, so the active balance the pool priced with fell from 28 wei to 4 ([`replay-bunni.md`]({{ config.extra.repo }}/blob/master/docs/benchmarks/replay-bunni.md)):

| idle balance stored as | active USDC after 44 withdrawals (wei) |
|---|---:|
| whole wei, as deployed (`mulDiv`) | 4 |
| whole wei, the fix (`mulDivUp`) | 48 |
| an FP127 value | 35.6278…, rounded down once to 35 |
| an FP19 value | 35.6278…, rounded down once to 35 |
| exact rational | 35.6278… |

The fix stops the attack but overshoots by 12.37 wei. FP127 ends within 10<sup>−37</sup> wei of exact, and fits the 255 bits Bunni already gives the balance. Storing the value is what does it: round it to wei before each store and you get 4 or 48 again.

```solidity
import {FP127Lib} from "fp127/FP127Lib.sol";

contract IdleBalance127 {
    int256 public idle; // wei × 2^128, never rounded before it is stored

    constructor(uint256 idleWei) { idle = q(idleWei); }

    function withdraw(uint256 shares, uint256 totalSupply) external {
        idle = FP127Lib.sub(idle,
            FP127Lib.div(FP127Lib.mul(idle, q(shares)), q(totalSupply)));
    }

    // the edge: what the pool may price with, in whole wei, rounded down
    function active(uint256 balanceWei) external view returns (uint256) {
        return uint256(FP127Lib.floor(FP127Lib.sub(q(balanceWei), idle)) >> 128);
    }
}

// FP127 has no fromUint: an integer below 2^127 is int256(x) << 128
function q(uint256 x) pure returns (int256) {
    require(x < 1 << 127, "FP127 range");
    return int256(x) << 128;
}
```

```solidity
import {FP19Lib} from "fp19/FP19Lib.sol";

contract IdleBalance19 {
    int256 public idle; // an FP19 value, never rounded before it is stored

    constructor(uint256 idleWei) { idle = FP19Lib.fromUint(idleWei); } // exact below 2^237

    function withdraw(uint256 shares, uint256 totalSupply) external {
        idle = FP19Lib.sub(idle, FP19Lib.div(FP19Lib.mul(idle, FP19Lib.fromUint(shares)),
                                               FP19Lib.fromUint(totalSupply)));
    }

    // the edge: what the pool may price with, in whole wei, rounded down
    function active(uint256 balanceWei) external view returns (uint256) {
        return FP19Lib.toUintDown(FP19Lib.sub(FP19Lib.fromUint(balanceWei), idle));
    }
}
```

## Rule 2: Resupply

On 26 June 2025 a Resupply market read an oracle price of 2,000,000,000,000,000,000,001,998,001,998,001,998 for an empty vault a donation had inflated. The exchange rate was `1e36 / price`, about one half, and integer division rounded it down to 0. With a rate of 0 the LTV was 0, so 10,000,000 reUSD were borrowed against 1 wei of collateral ([`replay-resupply.md`]({{ config.extra.repo }}/blob/master/docs/benchmarks/replay-resupply.md)).

In FP127 and FP19 the LTV is 499,999,999,999.99… (in units of 10<sup>−5</sup>) against a cap of 95,000, so the borrow reverts. At the edge, round against the borrower: the LTV rounds up to 500,000,000,000, and the most the position may borrow rounds down to 1.9 reUSD.

```solidity
int256 rate = FP127Lib.divUp(q(1e36), q(price));          // never below the true rate
int256 ltv  = FP127Lib.divUp(FP127Lib.divUp(
    FP127Lib.mulUp(FP127Lib.mulUp(q(debt), rate), q(1e5)), q(1e18)), q(collateral));
bool solvent = ltv <= q(maxLTV);
uint256 ltvOnGrid = uint256(FP127Lib.ceil(ltv) >> 128);   // 500,000,000,000

int256 maxTokens = FP127Lib.divDown(FP127Lib.mulDown(q(collateral), q(maxLTV)),
                                    FP127Lib.mulUp(rate, q(1e5)));
uint256 maxBorrowWei = uint256(FP127Lib.toFixed18Down(maxTokens)); // 1.9e18
```

```solidity
int256 rate = FP19Lib.divUp(FP19Lib.fromUint(1e36), FP19Lib.fromUint(price)); // never below the truth
int256 ltv  = FP19Lib.divUp(FP19Lib.divUp(
    FP19Lib.mulUp(FP19Lib.mulUp(FP19Lib.fromUint(debt), rate), FP19Lib.fromUint(1e5)),
    FP19Lib.fromUint(1e18)), FP19Lib.fromUint(collateral));
bool solvent = FP19Lib.cmp(ltv, FP19Lib.fromUint(maxLTV)) <= 0;
uint256 ltvOnGrid = FP19Lib.toUintUp(ltv);                                         // 500,000,000,000

int256 maxTokens = FP19Lib.divDown(
    FP19Lib.mulDown(FP19Lib.fromUint(collateral), FP19Lib.fromUint(maxLTV)),
    FP19Lib.mulUp(rate, FP19Lib.fromUint(1e5)));
uint256 maxBorrowWei = uint256(FP19Lib.toFixed18Down(maxTokens));                  // 1.9e18
```

Here every step is directed, because the result meets a limit. Rounding up all the way keeps the LTV at or above the true one, and rounding down over a denominator rounded up keeps the borrow limit at or below it. The plain ops can land on the wrong side. This fixes one division; it does not stop a market going live against an empty vault.

## Rule 2: Balancer V2

On 3 November 2025 two Balancer V2 stable pools were drained through many tiny swaps. `_upscale` rounded 17 osETH-wei, times a rate of 1.058, down to 17, and the first such swap charged 34.7% too little ([`replay-balancer.md`]({{ config.extra.repo }}/blob/master/docs/benchmarks/replay-balancer.md)).

In FP127 and FP19 nothing is truncated and the charge is rounded up to wei once, at the end. On all 165 calls the charge equals the exact one, and no call lowers the pool's invariant.

```solidity
// amountIn: the solver's answer, an FP19 value. amountIn / (1 - fee), rounded up once, to wei.
uint256 charge = FP19Lib.toUintUp(FP19Lib.divUp(
    FP19Lib.mulUp(amountIn, FP19Lib.fromUint(1e18)), FP19Lib.fromUint(1e18 - feeWad)));
```

Either rule alone falls short. Round up in the middle but keep balances in wei, and every restore call still lowers the invariant. Keep exact maths but round to nearest at the edge, and 19 calls still do.

## Rule 2: Balancer V1, the counter-example

On 31 August 2026 five Balancer V1 pools were drained by one-unit joins and exits against a balance of 3 units. The ratio had 18 correct digits. The loss was one rounding to nearest: a join worth 1.5056 units was charged 1 ([`replay-balancer-v1.md`]({{ config.extra.repo }}/blob/master/docs/benchmarks/replay-balancer-v1.md)).

More digits do not close this. With the exact formula rounded once to nearest, a re-tuned attack still nets 6.987% of the pool tokens per cycle. Round up on the way in and down on the way out, and the same cycle loses money: the swap fee stays in the pool.

```solidity
uint256 amountIn  = FP19Lib.toUintUp(joinCost);   // taken in: round up
uint256 amountOut = FP19Lib.toUintDown(exitValue); // paid out: round down
```

Neither format would have stopped Radiant's empty-market exploit, which used the same half unit. What carries over is the direction at the edge.

## The edge ops

FP127:

| the value | paid out: round down | taken in: round up |
|---|---|---|
| whole tokens of an 18-decimal token | `toFixed18Down(x)` | `toFixed18Up(x)` |
| raw token units (wei, satoshi) | `FP127Lib.floor(x) >> 128` | `FP127Lib.ceil(x) >> 128` |
| a product or quotient on the way there | `mulDown(a, b)`, `divDown(a, b)` | `mulUp(a, b)`, `divUp(a, b)` |

All take and return `int256`. `ceil` reverts with `Overflow` when the integer is 2<sup>127</sup>, and `toFixed18` is `toFixed18Down`. The directed ops are in the inline library and the deployed v5 and v6 contracts; the v4 contract has only `floor` and `ceil`.

FP19:

| the value | paid out: round down | taken in: round up |
|---|---|---|
| raw token units (wei, satoshi), as `uint256` | `toUintDown(x)` | `toUintUp(x)` |
| a signed amount, as `int256` | `toIntDown(x)` | `toIntUp(x)` |
| an 18-decimal value | `toFixed18Down(x)` | `toFixed18Up(x)` |
| a whole number, staying in FP19 | `floor(x)` | `ceil(x)` |
| a product or quotient on the way there | `mulDown(a, b)`, `divDown(a, b)` | `mulUp(a, b)`, `divUp(a, b)` |
| an integer above 2<sup>237</sup>, coming in | `fromUintDown(x)` | `fromUintUp(x)` |

Each rounds once from the exact value. `toUintUp` and `toFixed18Up` charge one unit for any positive dust, and `toUintDown` and `toUintUp` revert with `OutOfRange` below zero. All fourteen are in the inline library and the deployed v4 and v5 contracts, not v3.

## Divide last

Multiply everything, then divide once, and the maths rounds once. Resupply divided first: `1e36 / price` rounded the rate to 0. Divide at the end and the LTV is `debt × 10^23 / (price × collateral)`, which reverts the borrow whichever way it rounds. This fix needs no new library.

```solidity
import {FixedPointMathLib as M} from "solady/utils/FixedPointMathLib.sol";

uint256 ltv = M.fullMulDivUp(debt, 1e23, price * collateral);         // 500,000,000,000
uint256 maxBorrowWei = M.fullMulDiv(collateral * maxLTV, price, 1e23); // 1.9e18
```

`fullMulDiv` keeps the whole 512-bit product, so `debt × 10^23` cannot overflow, and the checked `*` reverts rather than wraps. `fullMulDivUp` rounds up and `fullMulDiv` down.

Inside FP127, `div(mul(a, b), c)` rounds twice, and a small product can round to zero first: 2<sup>−100</sup> × 2<sup>−40</sup> is below 2<sup>−128</sup>. For a, b ≥ 0 and c > 0 the 2<sup>128</sup> scales cancel, so call `fullMulDiv` on the raw integers and round once.

```solidity
uint256 r = M.fullMulDiv(uint256(a), uint256(b), uint256(c)); // the FP127 value a·b/c, rounded down
require(r < 1 << 255);                                         // it must fit an int256
```

In FP19 the order matters much less: a quotient keeps 237 bits at any size.

## Keep an index as its logarithm

An index multiplied by its growth rounds on every accrual. Store L = ln(index) instead. With a continuous rate, an accrual adds rate × dt to L, which is exact in FP127, and `exp(L)` rounds once, when the index is read.

```solidity
contract LogIndex127 {
    int256 public logIndex; // ln(index); 0 is an index of 1

    function accrue(int256 ratePerSecond, uint256 dt) external {
        logIndex = FP127Lib.add(logIndex, ratePerSecond * int256(dt)); // exact
    }

    function index() external view returns (int256) {
        return FP127Lib.exp(logIndex); // the one rounding: the nearest value
    }
}
```

In the example test, after 1,000 accruals the multiplied index is 511 to 546 units of 2<sup>−128</sup> low. The log read stays within half a unit.

The trade-offs:

- **An `exp` on every read.** An accrual drops from an `exp` and a `mul` ({{ <gas op="exp" /> }} + {{ <gas op="mul" /> }} gas, median) to an `add` ({{ <gas op="add" /> }}), but each read costs an `exp`.
- **Nearest since FP127 v5.** The v4 contract's `exp` does not promise the nearest value.
- **A wall at 88.** FP127's `exp` reverts above 88. For more room, read through FP19, as below.
- **A continuous rate only.** With a rate per period, `log1p(r)`'s rounding is added n times, and the test ends about 3,000 times further off than `mul(index, compound(r, n))`. Use `compound`.

Keep L as an FP127 value even then, because FP19's `add` rounds.

```solidity
int256 public logIndex; // an FP127 value: ln(index)

function accrue(int256 ratePerSecond, uint256 dt) external {
    logIndex = FP127Lib.add(logIndex, ratePerSecond * int256(dt)); // exact
}

function index() external view returns (int256) {
    return FP19Lib.exp(FP19Lib.fromFP127(logIndex)); // the one rounding
}
```

In FP19 alone the gain is gas, not digits: a multiplied index stays within 13.8 parts in 2<sup>236</sup> after 1,000 accruals. You save {{ <gas op="exp" lib="fp19" /> }} + {{ <gas op="mul" lib="fp19" /> }} gas per accrual and pay an `exp` per read.

The snippets on this page are compiled and run on the replays' own integers in [`test/examples/Integrating.t.sol`]({{ config.extra.repo }}/blob/master/test/examples/Integrating.t.sol).
