+++
title = "FP256"
description = "256-bit binary float. One word, 71 digits at any magnitude, every op but Lambert W rounded once."
path = "library/fp256"
aliases = ["/float/"]

[extra]
group = "library"
+++

FP127 has 38 digits at 1, 8 at 10^−30 and nothing outside 2^−128 to 2^127; the [edges](/results/edges/) show where that ends. FP256 fills the whole word, so the digits travel with the value.

## The word

Sign in bit 255, a 19-bit exponent (bias 262,143), a 236-bit fraction with an implicit one: 237 significant bits, about 71 digits, from 10^−78,900 to 10^78,900. No NaN, no infinity, no subnormals, no negative zero. Zero is the all-zero word; any other word with exponent 0 reverts `OutOfRange`. Equality is bit equality.

{{ <wordstrip format="fp256" /> }}

`value = (-1)^s (1 + F / 2^236) 2^(E - 262143)`, with s the sign, E the exponent and F the significand field.

Rounding: once per op (Lambert W iterates), ties away from zero. Overflow reverts; underflow rounds to zero. `ONE` is `0x3ffff << 236`.

| | digits | range |
|---|---:|---|
| FP127 | 38 at 1 | 2^−128 to 2^127 (±1.7 × 10^38) |
| ABDKMathQuad | 34 | 10^±4,932 |
| FP256 | 71 | 10^±78,900 |

## Deployed form

{{ <deployment lib="fp256" /> }}

Release four (Blockulator 2.1) is four objects from one source; the record above is FP256's. The other three, on the same CREATE2 proxy:

| object | ops | address |
|---|---|---|
| FP256X | `erf`, `erfc`, `normCdf`, `lambertW0`, `lambertWm1` | `0x175246B258Cc0dC3efEFe74b5fac8cC52C0c40d0` |
| FP256X2 | `exp2`, `exp10`, `log2`, `log10`, `log2Up`, `cbrt`, `sinh`, `cosh`, `tanh`, `atanh` | `0xE655bB8b1Cf848cAf3FD69F381289d144f5Bc697` |
| FP256X3 | `min`, `max`, `clamp`, `avg`, `dist`, `zeroFloorSub`, `inv`, `lerp`, `frac`, `round`, `gcd`, `factorial`, `pi`, `gavg`, `hypot` | `0x59D51481cb2EA924EC17FE263cd05b90CEF22383` |

The inline library holds all 67 ops. Records: [`FP256.md`](/contracts/deployments/FP256.md).

## Inline form

```sh
forge install securedataresearch/blockulator
echo "fp256/=lib/blockulator/contracts/src/fp256/" >> remappings.txt
```

Compile `FP256Lib.sol` with `via_ir = true` (in `foundry.toml`): solc's legacy pipeline leaves the heavy ops 9–27% dearer than the same Yul in the deployed objects, and through the IR they match them ([`profile.md`]({{ config.extra.repo }}/blob/master/docs/benchmarks/profile.md)).

```solidity
import {FP256Lib} from "fp256/FP256Lib.sol";

// a per-second rate over a year, with the rate itself held to 71 digits
int256 r = FP256Lib.div(FP256Lib.fromFixed18(0.05e18), FP256Lib.fromUint(31536000));
int256 g = FP256Lib.compound(r, 31536000);   // (1 + r)^n without ever rounding 1 + r
int256 balanceWad = FP256Lib.toFixed18(FP256Lib.mul(FP256Lib.fromFixed18(principalWad), g));
```

`fromFP127` is exact below 2^109 and rounds once above, `toFP127` rounds to the nearest 2^−128; `fromFixed18` / `toFixed18` convert to WAD.

## Integrating

A better ruler only helps if you follow two rules. Each one comes from a replay of a real exploit: the deployed arithmetic, bit for bit from the attack transaction, then the same step in FP127, FP256 and exact arithmetic. Every number below is from those write-ups.

1. **Store the state in the format.** Keep the running quantity (a balance, an index, an accumulator) as an FP256 word. Do not round it to token units before you store it.
2. **Round toward the protocol at the token edge.** When a value becomes token units, floor what the protocol pays out and ceil what it takes in. Never round to nearest there.

Every FP256 op without a direction in its name rounds to nearest, once. That is right for the state: in release four every such op is correctly rounded, off by at most half a unit in the last of 237 bits. It is wrong at the edge. In particular `toFixed18` and `toFP127` round to nearest; at the edge use the `Down` and `Up` forms.

### Rule 1: Bunni v2

On 2 September 2025, 44 withdrawals each took their share of a Bunni pool's idle USDC balance, in whole wei, with the stored balance rounded up every time. The active balance the pool priced with fell from 28 wei to 4. The fix (`mulDivUp`) ends at 48. The exact answer is 35.6278… wei. With the idle balance stored as an FP256 word, the active balance ends 1.17 × 10^−59 wei from exact and floors once to 35 ([`replay-bunni.md`]({{ config.extra.repo }}/blob/master/docs/benchmarks/replay-bunni.md)). Round the word to wei before each store and you are back at 4 or 48.

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

### Rule 2: Resupply

On 26 June 2025 a Resupply market computed its exchange rate as `1e36 / price` with a price of 2,000,000,000,000,000,000,001,998,001,998,001,998. The true rate is one half; the floor made it 0, the LTV read 0, and 10,000,000 reUSD were borrowed against 1 wei of collateral. In FP256 the rate has 71.90 correct digits and the LTV is 499,999,999,999.99… in units of 10^−5, against a cap of 95,000: the borrow reverts ([`replay-resupply.md`]({{ config.extra.repo }}/blob/master/docs/benchmarks/replay-resupply.md)). At the edge, the LTV is held against the borrower, so it rounds up (500,000,000,000). The borrow limit is paid out, so it rounds down (1.9 reUSD).

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

Every step is directed here, not only the last, because the result meets a limit. A word that rounds to nearest can sit just below the truth and pass a check it should fail. With `mulUp` and `divUp` all the way, the LTV is never below the true one; with `mulDown` and `divDown` over a denominator rounded up, the limit is never above it. This fixes one division. It does not stop a market from going live against an empty vault whose share price a donation sets.

### Rule 2: Balancer V2

On 3 November 2025 two Balancer V2 stable pools were drained through many tiny swaps. `_upscale` read 17 osETH-wei times a rate of 1.058132408689971699 as 17, and the pool charged 625,492 WETH-wei for a swap whose exact charge is 957,169 ([`replay-balancer.md`]({{ config.extra.repo }}/blob/master/docs/benchmarks/replay-balancer.md)). In the replay's FP256 run the amounts and balances are never truncated and the charge is rounded up to wei once, at the end. On all 90 + 75 calls it equals the exact charge, and no call lowers the pool's invariant. With exact maths inside but round-to-nearest at the wei boundary, 14 + 5 calls still lower it.

```solidity
// amountIn: the solver's answer, an FP256 word. amountIn / (1 - fee), rounded up once, to wei.
uint256 charge = FP256Lib.toUintUp(FP256Lib.divUp(
    FP256Lib.mulUp(amountIn, FP256Lib.fromUint(1e18)), FP256Lib.fromUint(1e18 - feeWad)));
```

### Rule 2: Balancer V1, the counter-example

On 31 August 2026 five Balancer V1 pools were drained by joins and exits of one token unit against a balance pushed down to 3 units. The ratio inside had 18 correct digits. The loss was one rounding to nearest: a join worth 1.5056 units was charged 1 ([`replay-balancer-v1.md`]({{ config.extra.repo }}/blob/master/docs/benchmarks/replay-balancer-v1.md)). Evaluate the exact formula in FP256 (at least 70.87 digits on every call), round once to nearest, and let the attacker re-tune: one join/exit cycle in the first pool still nets 6.987% of the BPT supply (deployed: 7.035%). Round toward the pool and the cycle nets −0.05482%.

```solidity
uint256 amountIn  = FP256Lib.toUintUp(joinCost);   // taken in: ceil
uint256 amountOut = FP256Lib.toUintDown(exitValue); // paid out: floor
```

Radiant's empty-market exploit used the same half unit: its share burn rounded to nearest. FP256 would not have stopped that exploit. The direction at the edge is the part that carries over.

### The edge ops

| the value | paid out: round down | taken in: round up |
|---|---|---|
| raw token units (wei, satoshi), as `uint256` | `toUintDown(x)` | `toUintUp(x)` |
| a signed amount, as `int256` | `toIntDown(x)` | `toIntUp(x)` |
| an 18-decimal word | `toFixed18Down(x)` | `toFixed18Up(x)` |
| an integral FP256 word, staying in the format | `floor(x)` | `ceil(x)` |
| a product or quotient on the way there | `mulDown(a, b)`, `divDown(a, b)` | `mulUp(a, b)`, `divUp(a, b)` |
| an integer above 2^237, coming in | `fromUintDown(x)` | `fromUintUp(x)` |

Each rounds once from the exact value. A positive `Up` result never underflows to zero: `toUintUp` and `toFixed18Up` charge one unit for any positive dust. `toUintDown` and `toUintUp` revert with `OutOfRange` below zero.

All fourteen are new in release four: the deployed FP256 object has them, and so does the inline library you get with `forge install`. The release three object does not. `round` and `frac` (#79, also release four) are not edge ops: `round` rounds to nearest, halves away from zero.

### Divide last

The rules say where to round. You can also move the maths so it rounds fewer times. The first move: multiply everything, then divide once.

Resupply divided first. `1e36 / price` floored the rate to 0 before anything was multiplied by it. Put the division at the end and the LTV is `debt × 10^23 / (price × collateral)`: one product, one division, one rounding. Rounded up it is 500,000,000,000 and the borrow reverts; rounded down it is 499,999,999,999, the same verdict. This fix needs no new library ([`replay-resupply.md`]({{ config.extra.repo }}/blob/master/docs/benchmarks/replay-resupply.md)).

```solidity
import {FixedPointMathLib as M} from "solady/utils/FixedPointMathLib.sol";

uint256 ltv = M.fullMulDivUp(debt, 1e23, price * collateral);         // 500,000,000,000
uint256 maxBorrowWei = M.fullMulDiv(collateral * maxLTV, price, 1e23); // 1.9e18
```

Inside FP256 the order matters much less. A quotient keeps its 237 significant bits at any size inside the walls, so `div(a, c)` never floors to zero the way `1e36 / price` did. `mul(div(a, c), b)` still rounds twice, each time by at most half a unit in the last place. The cliff is in the integers, before they enter the format.

### Keep an index as its logarithm

An interest index multiplied by its growth each accrual rounds each accrual. Store L = ln(index) instead, and add rate × dt to it for a continuous rate. FP256's `add` rounds, like any float add. FP127's does not, so keep L as an FP127 word and read it through FP256. `fromFP127` is exact below 2^109, and `exp` is correctly rounded in release four, so the read is e^L rounded once. It is not capped at FP127's 88.

```solidity
int256 public logIndex; // an FP127 word: ln(index)

function accrue(int256 ratePerSecond, uint256 dt) external {
    logIndex = FP127Lib.add(logIndex, ratePerSecond * int256(dt)); // exact
}

function index() external view returns (int256) {
    return FP256Lib.exp(FP256Lib.fromFP127(logIndex)); // the one rounding
}
```

In FP256 the gain is gas more than digits. In the example test, an FP256 index multiplied 1,000 times ends 9.2 to 13.8 parts in 2^236 from the log read. Each `exp` and `mul` rounds to nearest at 237 bits, so the errors stay tiny and partly cancel. What you save is the `exp` and `mul` on every accrual (7,866 + 1,388 gas, median, in [`gas256.md`]({{ config.extra.repo }}/blob/master/docs/benchmarks/gas256.md)). You pay an `exp` on every read instead. This fits a continuous rate only. With a rate per period r, L gains n × log1p(r), and that rounding is added n times; use `compound(r, n)` there. The [FP127 page](/library/#keep-an-index-as-its-logarithm) has the measured numbers.

The snippets are compiled and run on the replays' own integers in [`test/examples/Integrating.t.sol`]({{ config.extra.repo }}/blob/master/test/examples/Integrating.t.sol).

## Release three

Blockulator 2.0's FP256, still deployed at `0x67eFfb11bF93c79a2B12cc7872cBaC12b3eB61be`: 28 ops. `exp`, `ln`, `log1p`, `expm1`, `erf`, `erfc`, `normCdf` and every non-transcendental op return the correctly rounded word at every committed vector. `pow`, `powu` and `compound` are within one unit in the last place while |y log2 x| stays below about 2^13; the Lambert branches are within two units away from −1/e. On random inputs (4,000 to 20,000 per op) `add`, `mul`, `div`, `sqrt`, `exp`, `log1p`, `expm1`, `erf` and `erfc` were correctly rounded every time; `ln`, `normCdf` and `pow` were one unit off on 1 in 20,000, 4,000 and 2,500. The kernels run at 2^−254 with 512-bit products: 2^f from a 16-entry table and a degree-26 polynomial, log2 from twelve reduction stages and a degree-17 polynomial, `erfc` as e^(−y²) times a scaled series or continued fraction (never 1 − erf). Release one borrowed FP127's kernels (146, 149 and 123 bits on exp, ln and pow); release two refit them for the wide word; release three added nine ops.

## The ops

{{ <optable lib="fp256" /> }}

Source: `contracts/src/fp256/FP256.yul.src`, built by FP127's generator; object and library fuzzed equal across all of `int256`. Full reference: [`contracts/src/fp256/README.md`]({{ config.extra.repo }}/blob/master/contracts/src/fp256/README.md).
