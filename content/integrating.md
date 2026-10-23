+++
title = "Integrating"
description = "Two rules that end dust, each from the replay of a real exploit, with the worked code in FP127 and FP256."
path = "library/integrating"

[extra]
group = "library"
+++

A better ruler only helps if you follow two rules. Each one comes from a replay of a real exploit: the deployed arithmetic, bit for bit from the attack transaction, then the same step in FP127, FP256 and exact arithmetic. Every number below is from those write-ups.

1. **Store the state in the format.** Keep the running quantity (a balance, an index, an accumulator) as an FP127 or FP256 word. Do not round it to token units before you store it.
2. **Round toward the protocol at the token edge.** When a value becomes token units, floor what the protocol pays out and ceil what it takes in. Never round to nearest there.

Inside the format, the plain ops are fine for the state. In FP127, `add` and `sub` are exact, and `mul`, `div` and `sqrt` are off by at most one unit of 2<sup>−128</sup>, far below a token unit. In FP256, every op without a direction in its name rounds to nearest, once: it is correctly rounded, off by at most half a unit in the last of 237 bits. Direction matters where a value lands on the token grid or meets a limit. In particular FP256's `toFixed18` and `toFP127` round to nearest; at the edge use the `Down` and `Up` forms.

## Rule 1: Bunni v2

On 2 September 2025, 44 withdrawals each took their share of a Bunni pool's idle USDC balance. The code worked in whole wei, and its floor sat on the amount subtracted, so the stored balance rounded up every time. The active balance the pool priced with fell from 28 wei to 4. Here is the same sequence with the idle balance stored five ways ([`replay-bunni.md`]({{ config.extra.repo }}/blob/master/docs/benchmarks/replay-bunni.md)):

| idle balance stored as | active USDC after 44 withdrawals (wei) |
|---|---:|
| whole wei, as deployed (`mulDiv`) | 4 |
| whole wei, the fix (`mulDivUp`) | 48 |
| an FP127 word | 35.6278…, floored once to 35 |
| an FP256 word | 35.6278…, floored once to 35 |
| exact rational | 35.6278… |

The fix stops this sequence, but it ends 12.37 wei high where the deployed code ended 31.63 low. The FP127 word ends within 10<sup>−37</sup> wei of exact, the FP256 word 1.17 × 10<sup>−59</sup> wei from it. A non-negative 127.128 word is below 2<sup>255</sup>, so it fits the 255 bits Bunni already gives the balance.

The format alone does not do this; storing it does. Round the result to wei before each store and the integer answers come back: rounded up, you get the deployed code's 4 wei; rounded down, the fix's 48. The example test checks both.

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
import {FP256Lib} from "fp256/FP256Lib.sol";

contract IdleBalance256 {
    int256 public idle; // an FP256 word, never rounded before it is stored

    constructor(uint256 idleWei) { idle = FP256Lib.fromUint(idleWei); } // exact below 2^237

    function withdraw(uint256 shares, uint256 totalSupply) external {
        idle = FP256Lib.sub(idle, FP256Lib.div(FP256Lib.mul(idle, FP256Lib.fromUint(shares)),
                                               FP256Lib.fromUint(totalSupply)));
    }

    // the edge: what the pool may price with, in whole wei, rounded down
    function active(uint256 balanceWei) external view returns (uint256) {
        return FP256Lib.toUintDown(FP256Lib.sub(FP256Lib.fromUint(balanceWei), idle));
    }
}
```

## Rule 2: Resupply

On 26 June 2025 a Resupply market read an oracle price of 2,000,000,000,000,000,000,001,998,001,998,001,998 for an empty vault a donation had inflated. The exchange rate was `1e36 / price`. The true rate is one half; the floor made it 0. With a rate of 0 the LTV was 0, so 10,000,000 reUSD were borrowed against 1 wei of collateral ([`replay-resupply.md`]({{ config.extra.repo }}/blob/master/docs/benchmarks/replay-resupply.md)).

In FP127 the rate keeps its half (38.58 correct digits), in FP256 71.90, and the LTV is 499,999,999,999.99… in units of 10<sup>−5</sup>, against a cap of 95,000. The borrow reverts. Now the edge. The LTV is held against the borrower, so if it must become an integer it rounds up: 500,000,000,000. The most this position may borrow is paid out, so it rounds down: 1.9 reUSD.

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
int256 rate = FP256Lib.divUp(FP256Lib.fromUint(1e36), FP256Lib.fromUint(price)); // never below the truth
int256 ltv  = FP256Lib.divUp(FP256Lib.divUp(
    FP256Lib.mulUp(FP256Lib.mulUp(FP256Lib.fromUint(debt), rate), FP256Lib.fromUint(1e5)),
    FP256Lib.fromUint(1e18)), FP256Lib.fromUint(collateral));
bool solvent = FP256Lib.cmp(ltv, FP256Lib.fromUint(maxLTV)) <= 0;
uint256 ltvOnGrid = FP256Lib.toUintUp(ltv);                                         // 500,000,000,000

int256 maxTokens = FP256Lib.divDown(
    FP256Lib.mulDown(FP256Lib.fromUint(collateral), FP256Lib.fromUint(maxLTV)),
    FP256Lib.mulUp(rate, FP256Lib.fromUint(1e5)));
uint256 maxBorrowWei = uint256(FP256Lib.toFixed18Down(maxTokens));                  // 1.9e18
```

Here every step is directed, not only the last, because the result meets a limit. A value can sit a hair below the truth and still pass a check it should fail. With `mulUp` and `divUp` all the way, the LTV is never below the true one. With `mulDown` and `divDown` over a denominator rounded up, the borrow limit is never above it. FP127's plain `mul` rounds down and `div` toward zero, so on a path that charges, they are on the wrong side by one unit of 2<sup>−128</sup>; FP256's plain ops round to nearest, which can land on either side.

The replay's own caveat holds here too: this fixes one division. Nothing on this page stops a market from going live against an empty vault whose share price a donation sets.

## Rule 2: Balancer V2

On 3 November 2025 two Balancer V2 stable pools were drained through many tiny swaps. `_upscale` truncated a given-out amount of 17 osETH-wei, times a rate of 1.058132408689971699, to 17. On the first such swap the pool charged 625,492 WETH-wei; the exact charge is 957,169, so it undercharged by 34.7% ([`replay-balancer.md`]({{ config.extra.repo }}/blob/master/docs/benchmarks/replay-balancer.md)).

In FP127 the upscaled amount stays 17.988250947729518883 to within 2<sup>−128</sup>, and the only step onto the wei grid is the last, a ceil. In the FP256 run, too, the amounts and balances are never truncated and the charge is rounded up to wei once, at the end. In both, on all 90 + 75 calls of the two pools the charge equals the exact one, and no call lowers the pool's invariant.

```solidity
// amountIn: the solver's answer, an FP256 word. amountIn / (1 - fee), rounded up once, to wei.
uint256 charge = FP256Lib.toUintUp(FP256Lib.divUp(
    FP256Lib.mulUp(amountIn, FP256Lib.fromUint(1e18)), FP256Lib.fromUint(1e18 - feeWad)));
```

Two checks show why both rules are needed. Fix only the direction of one rounding in the middle (`mulUp` on the given-out amount), and all 30 + 25 restore calls still lower the invariant, because the balances are still truncated to wei. Keep exact maths inside but round to nearest at the wei boundary, and 14 + 5 calls still lower the invariant. The 0.01% fee kept that run net positive, but the claim depends on the direction.

## Rule 2: Balancer V1, the counter-example

On 31 August 2026 five Balancer V1 pools were drained by joins and exits of one token unit against a balance pushed down to 3 units. The ratio inside had 18 correct digits. The loss was one rounding to nearest: 3 × 1.499999999999999997 = 4.499999999999999991 became 4, so a join worth 1.5056 units was charged 1 ([`replay-balancer-v1.md`]({{ config.extra.repo }}/blob/master/docs/benchmarks/replay-balancer-v1.md)).

More digits do not close this. Evaluate the exact formula in FP127, in FP256 (at least 70.87 digits on every call) or at 200 digits, round once to nearest, and let the attacker re-tune to that rule: one join/exit cycle in the first pool still nets 6.987% of the BPT supply (deployed: 7.035%). Round toward the pool, ceil in and floor out, and the same cycle nets −0.05482%: the swap fee stays in the pool.

```solidity
uint256 amountIn  = FP256Lib.toUintUp(joinCost);   // taken in: ceil
uint256 amountOut = FP256Lib.toUintDown(exitValue); // paid out: floor
```

Radiant's empty-market exploit used the same half unit: its share burn rounded to nearest. Neither format would have stopped that exploit. The direction at the edge is the part that carries over.

## The edge ops

FP127:

| the value | paid out: round down | taken in: round up |
|---|---|---|
| whole tokens of an 18-decimal token | `toFixed18Down(x)` | `toFixed18Up(x)` |
| raw token units (wei, satoshi) | `FP127Lib.floor(x) >> 128` | `FP127Lib.ceil(x) >> 128` |
| a product or quotient on the way there | `mulDown(a, b)`, `divDown(a, b)` | `mulUp(a, b)`, `divUp(a, b)` |

All take and return `int256`. `ceil` reverts with `Overflow` when the integer is 2<sup>127</sup>. `toFixed18` rounds down, the same as `toFixed18Down`. `mulUp`, `mulDown`, `divUp`, `divDown`, `toFixed18Up` and `toFixed18Down` are new in FP127 v5 (Blockulator 2.1): the v5 and v6 objects have them, and so does the inline library you get with `forge install`. The v4 object has `floor` and `ceil` but not these.

FP256:

| the value | paid out: round down | taken in: round up |
|---|---|---|
| raw token units (wei, satoshi), as `uint256` | `toUintDown(x)` | `toUintUp(x)` |
| a signed amount, as `int256` | `toIntDown(x)` | `toIntUp(x)` |
| an 18-decimal word | `toFixed18Down(x)` | `toFixed18Up(x)` |
| an integral FP256 word, staying in the format | `floor(x)` | `ceil(x)` |
| a product or quotient on the way there | `mulDown(a, b)`, `divDown(a, b)` | `mulUp(a, b)`, `divUp(a, b)` |
| an integer above 2<sup>237</sup>, coming in | `fromUintDown(x)` | `fromUintUp(x)` |

Each rounds once from the exact value. A positive `Up` result never underflows to zero: `toUintUp` and `toFixed18Up` charge one unit for any positive dust. `toUintDown` and `toUintUp` revert with `OutOfRange` below zero. All fourteen are new in FP256 v4 (Blockulator 2.1): the v4 and v5 objects have them, and so does the inline library you get with `forge install`. The FP256 v3 object (Blockulator 2.0) does not. `round` and `frac` (#79, also v4) are not edge ops: `round` rounds to nearest, halves away from zero.

## Divide last

The rules say where to round. You can also move the maths so it rounds fewer times. The first move: multiply everything, then divide once.

Resupply divided first. `1e36 / price` floored the rate to 0 before anything was multiplied by it. Put the division at the end and the LTV is `debt × 10^23 / (price × collateral)`, since 10<sup>36</sup> × 10<sup>5</sup> / 10<sup>18</sup> = 10<sup>23</sup>. That is one product, one division and one rounding. Rounded up it is 500,000,000,000 and the borrow reverts. Rounded down it is 499,999,999,999: the same verdict. This fix needs no new library ([`replay-resupply.md`]({{ config.extra.repo }}/blob/master/docs/benchmarks/replay-resupply.md)).

```solidity
import {FixedPointMathLib as M} from "solady/utils/FixedPointMathLib.sol";

uint256 ltv = M.fullMulDivUp(debt, 1e23, price * collateral);         // 500,000,000,000
uint256 maxBorrowWei = M.fullMulDiv(collateral * maxLTV, price, 1e23); // 1.9e18
```

`fullMulDiv` keeps the whole 512-bit product, so `debt × 10^23` cannot overflow. The checked `*` reverts rather than wraps. `fullMulDivUp` rounds up, `fullMulDiv` down: pick the direction the protocol needs.

The same holds inside FP127. `div(mul(a, b), c)` rounds twice, and a product of two small words can floor to zero before the division: 2<sup>−100</sup> × 2<sup>−40</sup> is below 2<sup>−128</sup>, so `mul` returns 0 and the quotient by 2<sup>−60</sup> is 0, not 2<sup>−80</sup>. For words a, b ≥ 0 and c > 0 the 2<sup>128</sup> scales cancel. The word a·b/c is `fullMulDiv(a, b, c)` on the raw integers, rounded once.

```solidity
uint256 r = M.fullMulDiv(uint256(a), uint256(b), uint256(c)); // the word a·b/c, rounded down
require(r < 1 << 255);                                         // it must fit an int256
```

Inside FP256 the order matters much less. A quotient keeps its 237 significant bits at any size inside the walls, so `div(a, c)` never floors to zero the way `1e36 / price` did. `mul(div(a, c), b)` still rounds twice, each time by at most half a unit in the last place. The cliff is in the integers, before they enter the format.

## Keep an index as its logarithm

An interest index multiplied by its growth each accrual rounds each accrual. Store L = ln(index) instead. With a continuous rate (ln of the growth per second), an accrual adds rate × dt to L. In FP127 a word times a whole number is an integer product, and `add` never rounds; it can only overflow. So every accrual is exact. `exp(L)` runs only when the index is read, and rounds once.

```solidity
contract LogIndex127 {
    int256 public logIndex; // ln(index); 0 is an index of 1

    function accrue(int256 ratePerSecond, uint256 dt) external {
        logIndex = FP127Lib.add(logIndex, ratePerSecond * int256(dt)); // exact
    }

    function index() external view returns (int256) {
        return FP127Lib.exp(logIndex); // the one rounding: the nearest word
    }
}
```

The example test runs both forms at random rates up to about 12% a year, with random gaps of up to a day, three times. After one accrual they are the same single `exp`, so they match. After 10, the multiplied index is 3.3 to 6.6 units of 2<sup>−128</sup> off, and after 1,000 it is 511 to 546 off: about half a unit per accrual. From 10 on, every run ends low, because `mul` floors. The log read stays within half a unit every time. The reference is e<sup>L</sup> in FP256.

The trade-offs:

- **An `exp` on every read.** An accrual drops from an `exp` and a `mul` ({{ <gas op="exp" /> }} + {{ <gas op="mul" /> }} gas, median) to an `add` ({{ <gas op="add" /> }}). A read rises from a storage load to an `exp` ([`gas.md`]({{ config.extra.repo }}/blob/master/docs/benchmarks/gas.md)). If you read the index every time you accrue it, you save almost nothing.
- **Nearest since FP127 v5.** `exp` returns the nearest word in v5 and v6, deployed and inline. The v4 object does not promise that.
- **A wall at 88.** FP127's `exp` reverts above 88, an index of about 1.65 × 10<sup>38</sup>. For more room, read through FP256: `FP256Lib.exp(FP256Lib.fromFP127(logIndex))`. `fromFP127` is exact below 2<sup>109</sup> and FP256's `exp` is correctly rounded, so the read is e<sup>L</sup> rounded once.
- **A continuous rate only.** With a rate per period, L gains n × `log1p(r)`. `log1p` rounds once, and that rounding is added n times. In two runs of 100 accruals, each of up to 86,400 periods, that read was 136,497 and 156,064 units off. `mul(index, compound(r, n))` was 47.6 and 48.4 off. For a rate per period, use `compound`.

Keep L as an FP127 word even when you read it through FP256: FP256's `add` rounds, like any float add, and FP127's does not.

```solidity
int256 public logIndex; // an FP127 word: ln(index)

function accrue(int256 ratePerSecond, uint256 dt) external {
    logIndex = FP127Lib.add(logIndex, ratePerSecond * int256(dt)); // exact
}

function index() external view returns (int256) {
    return FP256Lib.exp(FP256Lib.fromFP127(logIndex)); // the one rounding
}
```

In FP256 the gain is gas more than digits. In the example test, an FP256 index multiplied 1,000 times ends 9.2 to 13.8 parts in 2<sup>236</sup> from the log read. Each `exp` and `mul` rounds to nearest at 237 bits, so the errors stay tiny and partly cancel. What you save is the `exp` and `mul` on every accrual ({{ <gas op="exp" lib="fp256" /> }} + {{ <gas op="mul" lib="fp256" /> }} gas, median, in [`gas256.md`]({{ config.extra.repo }}/blob/master/docs/benchmarks/gas256.md)). You pay an `exp` on every read instead.

The snippets on this page are compiled and run on the replays' own integers in [`test/examples/Integrating.t.sol`]({{ config.extra.repo }}/blob/master/test/examples/Integrating.t.sol).
