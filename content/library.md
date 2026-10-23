+++
title = "FP127"
description = "Signed 127.128 fixed point. One int256, 128 fractional bits (38 digits at 1), 53 ops, every transcendental the nearest word. One Yul source, two forms: a deployed object and an inline library."

[extra]
group = "library"
+++

Both forms are generated from one file and fuzzed equal across the full `int256` domain, reverts included.

## Encoding

`value × 2^128` in an `int256`, two's complement. `ONE` is `2^128`. Range ±1.7 × 10^38, 128 fractional bits: 38 digits at 1, 32 at 10^−6, 8 at 10^−30. Every op takes and returns this one type. `fromFixed18` and `toFixed18` convert to and from WAD.

{{ <wordstrip format="fp127,wad" /> }}

Errors: `Overflow()`, `DivisionByZero()`, `OutOfRange()`. Nothing wraps.

## Deployed form

{{ <deployment /> }}

No storage, no owner, no upgrade path. A new version is a new salt and a new address. The address above is v6 (53 ops, Blockulator 2.2): `pi` is now the constant `FP127Lib.PI` (π · 2^128 to the nearest integer) and `gcd` is gone, and every other op returns the same word as v5 for less gas. v6 is an evmVersion osaka build and needs the CLZ opcode (EIP-7939): it runs on Ethereum, Sepolia and the other chains with CLZ, not on zkSync Era, Avalanche C-Chain or Polygon zkEVM ([the list]({{ config.extra.repo }}/blob/master/contracts/deployments/README.md#chains-clz-osaka-required)). v5 (Blockulator 2.1, `0x619176d72D7a12390F8970802943D344c0fd3fE2`) added the directed `mulUp`, `mulDown`, `divUp`, `divDown`, `toFixed18Up` and `toFixed18Down` and rounded every transcendental to the nearest word. v1 to v5 stay deployed at the addresses in the record.

`sqrt(2)` from the command line:

```sh
cast call 0xb349DB36D51b0BC10Dd43aF70009b7B6E7c1CBe4 "sqrt(int256)(int256)" \
  680564733841876926926749214863536422912 \
  --rpc-url https://ethereum-sepolia-rpc.publicnode.com
# 481231938336009023090067544955250113854
python3 -c "print(481231938336009023090067544955250113854 / 2**128)"
# 1.4142135623730951
```

From Solidity:

```solidity
import {IFP127} from "fp127/IFP127.sol";

contract StaticcallExample {
    IFP127 public constant FP127 = IFP127(0xb349DB36D51b0BC10Dd43aF70009b7B6E7c1CBe4);
    int256 internal constant ONE = int256(1) << 128;

    function accrue(int256 principalWad, int256 rateWad, uint256 steps) external view returns (int256 balanceWad) {
        int256 b = FP127.fromFixed18(principalWad);
        int256 growth = FP127.add(ONE, FP127.fromFixed18(rateWad));
        for (uint256 i = 0; i < steps; i++) {
            b = FP127.mul(b, growth);
        }
        return FP127.toFixed18(b);
    }
}
```

## Inline form

`FP127Lib.sol`: the same Yul in `memory-safe` assembly, one `internal pure` function per op. No external call: about 570 gas cheaper than the `staticcall` on `add`, 630 on `mul` and 430 on `sqrt`; on `exp`, the erf family and Lambert W the deployed object is cheaper (medians in [`gas.md`]({{ config.extra.repo }}/blob/master/docs/benchmarks/gas.md)).

Compile it with `via_ir = true` (in `foundry.toml`): solc's legacy pipeline leaves the heavy ops 5–14% dearer than the same Yul in the object (net of its call), and through the IR they come within about −7% to +3% of it, `add` 124 → 83 and `ln` 600 → 409 gas; the build takes about 5.5× as long ([`profile.md`]({{ config.extra.repo }}/blob/master/docs/benchmarks/profile.md)).

```sh
forge install securedataresearch/blockulator
echo "fp127/=lib/blockulator/contracts/src/fp127/" >> remappings.txt
```

```solidity
import {FP127Lib} from "fp127/FP127Lib.sol";

contract CompoundExample {
    function accrue(int256 principalWad, int256 rateWad, uint256 steps) external pure returns (int256 balanceWad) {
        int256 b = FP127Lib.fromFixed18(principalWad);
        int256 growth = FP127Lib.add(FP127Lib.ONE, FP127Lib.fromFixed18(rateWad));
        for (uint256 i = 0; i < steps; i++) {
            b = FP127Lib.mul(b, growth);
        }
        return FP127Lib.toFixed18(b);
    }
}
```

Both examples are compiled and tested in `test/examples/` against the [ladder's](/results/ladder/#compound) compound scenario.

## Integrating

A better ruler only helps if you follow two rules. Each one comes from a replay of a real exploit: the deployed arithmetic, bit for bit from the attack transaction, then the same step in FP127, FP256 and exact arithmetic. Every number below is from those write-ups.

1. **Store the state in the format.** Keep the running quantity (a balance, an index, an accumulator) as an FP127 word. Do not round it to token units before you store it.
2. **Round toward the protocol at the token edge.** When a value becomes token units, floor what the protocol pays out and ceil what it takes in. Never round to nearest there.

Inside the format, the plain ops are fine for the state: `add` and `sub` are exact, and `mul`, `div` and `sqrt` are off by at most one unit of 2^−128, far below a token unit. Direction matters where a value lands on the token grid or meets a limit.

### Rule 1: Bunni v2

On 2 September 2025, 44 withdrawals each took their share of a Bunni pool's idle USDC balance. The code worked in whole wei, and its floor sat on the amount subtracted, so the stored balance rounded up every time. The active balance the pool priced with fell from 28 wei to 4. Here is the same sequence with the idle balance stored four ways ([`replay-bunni.md`]({{ config.extra.repo }}/blob/master/docs/benchmarks/replay-bunni.md)):

| idle balance stored as | active USDC after 44 withdrawals (wei) |
|---|---:|
| whole wei, as deployed (`mulDiv`) | 4 |
| whole wei, the fix (`mulDivUp`) | 48 |
| an FP127 word | 35.6278…, floored once to 35 |
| exact rational | 35.6278… |

The fix stops this sequence, but it ends 12.37 wei high where the deployed code ended 31.63 low. The FP127 word ends within 10^−37 wei of exact. A non-negative 127.128 word is below 2^255, so it fits the 255 bits Bunni already gives the balance.

The format alone does not do this; storing it does. Round the FP127 result to wei before each store and the integer answers come back: rounded up, you get the deployed code's 4 wei; rounded down, the fix's 48. The example test checks both.

```solidity
import {FP127Lib} from "fp127/FP127Lib.sol";

contract IdleBalance127 {
    int256 public idle; // wei × 2^128, never rounded before it is stored

    constructor(uint256 idleWei) { idle = q(idleWei); }

    function withdraw(uint256 shares, uint256 totalSupply) external {
        idle = FP127Lib.sub(idle, FP127Lib.div(FP127Lib.mul(idle, q(shares)), q(totalSupply)));
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

### Rule 2: Resupply

On 26 June 2025 a Resupply market read an oracle price of 2,000,000,000,000,000,000,001,998,001,998,001,998 for an empty vault a donation had inflated. The exchange rate was `1e36 / price`. The true rate is one half; the floor made it 0. With a rate of 0 the LTV was 0, so 10,000,000 reUSD were borrowed against 1 wei of collateral ([`replay-resupply.md`]({{ config.extra.repo }}/blob/master/docs/benchmarks/replay-resupply.md)).

In FP127 the rate keeps its half (38.58 correct digits) and the LTV is 499,999,999,999.99… in units of 10^−5, against a cap of 95,000. The borrow reverts. Now the edge. The LTV is held against the borrower, so if it must become an integer it rounds up: 500,000,000,000. The most this position may borrow is paid out, so it rounds down: 1.9 reUSD.

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

Here every step is directed, not only the last. A value can sit a hair below the truth and still pass a check it should fail. With `mulUp` and `divUp` all the way, the LTV is never below the true one. With `mulDown` and `divDown` over a denominator rounded up, the borrow limit is never above it. FP127's plain `mul` rounds down and `div` toward zero, so on a path that charges, they are on the wrong side by one unit of 2^−128.

The replay's own caveat holds here too: this fixes one division. Nothing on this page stops a market from going live against an empty vault whose share price a donation sets.

### Rule 2: Balancer V2

On 3 November 2025 two Balancer V2 stable pools were drained through many tiny swaps. `_upscale` truncated a given-out amount of 17 osETH-wei, times a rate of 1.058132408689971699, to 17. On the first such swap the pool charged 625,492 WETH-wei; the exact charge is 957,169, so it undercharged by 34.7% ([`replay-balancer.md`]({{ config.extra.repo }}/blob/master/docs/benchmarks/replay-balancer.md)).

In FP127 the upscaled amount stays 17.988250947729518883 to within 2^−128, and the only step onto the wei grid is the last, a ceil. On all 90 + 75 calls of the two pools the charge equals the exact one, and no call lowers the pool's invariant.

Two checks show why both rules are needed. Fix only the direction of one rounding in the middle (`mulUp` on the given-out amount), and all 30 + 25 restore calls still lower the invariant, because the balances are still truncated to wei. Keep exact maths inside but round to nearest at the wei boundary, and 14 + 5 calls still lower the invariant. The 0.01% fee kept that run net positive, but the claim depends on the direction.

### Rule 2: Balancer V1, the counter-example

On 31 August 2026 five Balancer V1 pools were drained by joins and exits of one token unit against a balance of 3 units. The ratio inside had 18 correct digits. The loss was one rounding to nearest: 3 × 1.499999999999999997 = 4.499999999999999991 became 4, so a join worth 1.5056 units was charged 1 ([`replay-balancer-v1.md`]({{ config.extra.repo }}/blob/master/docs/benchmarks/replay-balancer-v1.md)).

More digits do not close this. Evaluate the exact formula in FP127, FP256 or at 200 digits, round once to nearest, and let the attacker re-tune to that rule: one join/exit cycle in the first pool still nets 6.987% of the BPT supply (deployed: 7.035%). Round toward the pool, ceil in and floor out, and the same cycle nets −0.05482%: the swap fee stays in the pool.

Radiant's empty-market exploit used the same half unit: its share burn rounded to nearest. FP127 would not have stopped that exploit. The direction at the edge is the part that carries over.

### The edge ops

| the value | paid out: round down | taken in: round up |
|---|---|---|
| whole tokens of an 18-decimal token | `toFixed18Down(x)` | `toFixed18Up(x)` |
| raw token units (wei, satoshi) | `FP127Lib.floor(x) >> 128` | `FP127Lib.ceil(x) >> 128` |
| a product or quotient on the way there | `mulDown(a, b)`, `divDown(a, b)` | `mulUp(a, b)`, `divUp(a, b)` |

All take and return `int256`. `ceil` reverts with `Overflow` when the integer is 2^127. `toFixed18` rounds down, the same as `toFixed18Down`.

`mulUp`, `mulDown`, `divUp`, `divDown`, `toFixed18Up` and `toFixed18Down` are new in v5: the v5 and v6 objects have them, and so does the inline library you get with `forge install`. The v4 object has `floor` and `ceil` but not these.

### Divide last

The rules say where to round. You can also move the maths so it rounds fewer times. The first move: multiply everything, then divide once.

Resupply divided first. `1e36 / price` floored the rate to 0 before anything was multiplied by it. Put the division at the end and the LTV is `debt × 10^23 / (price × collateral)`, since 10^36 × 10^5 / 10^18 = 10^23. That is one product, one division and one rounding. Rounded up it is 500,000,000,000 and the borrow reverts. Rounded down it is 499,999,999,999: the same verdict. This fix needs no new library ([`replay-resupply.md`]({{ config.extra.repo }}/blob/master/docs/benchmarks/replay-resupply.md)).

```solidity
import {FixedPointMathLib as M} from "solady/utils/FixedPointMathLib.sol";

uint256 ltv = M.fullMulDivUp(debt, 1e23, price * collateral);         // 500,000,000,000
uint256 maxBorrowWei = M.fullMulDiv(collateral * maxLTV, price, 1e23); // 1.9e18
```

`fullMulDiv` keeps the whole 512-bit product, so `debt × 10^23` cannot overflow. The checked `*` reverts rather than wraps. `fullMulDivUp` rounds up, `fullMulDiv` down: pick the direction the protocol needs.

The same holds inside FP127. `div(mul(a, b), c)` rounds twice, and a product of two small words can floor to zero before the division: 2^−100 × 2^−40 is below 2^−128, so `mul` returns 0 and the quotient by 2^−60 is 0, not 2^−80. For words a, b ≥ 0 and c > 0 the 2^128 scales cancel. The word a·b/c is `fullMulDiv(a, b, c)` on the raw integers, rounded once.

```solidity
uint256 r = M.fullMulDiv(uint256(a), uint256(b), uint256(c)); // the word a·b/c, rounded down
require(r < 1 << 255);                                         // it must fit an int256
```

### Keep an index as its logarithm

An interest index multiplied by its growth each accrual rounds each accrual. Store L = ln(index) instead. With a continuous rate (ln of the growth per second), an accrual adds rate × dt to L. A word times a whole number is an integer product, and `add` never rounds; it can only overflow. So every accrual is exact. `exp(L)` runs only when the index is read, and rounds once.

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

The example test runs both forms at random rates up to about 12% a year, with random gaps of up to a day, three times. After one accrual they are the same single `exp`, so they match. After 10, the multiplied index is 3.3 to 6.6 units of 2^−128 off, and after 1,000 it is 511 to 546 off: about half a unit per accrual. From 10 on, every run ends low, because `mul` floors. The log read stays within half a unit every time. The reference is e^L in FP256.

The trade-offs:

- **An `exp` on every read.** An accrual drops from an `exp` and a `mul` (6,006 + 263 gas, median) to an `add` (124). A read rises from a storage load to an `exp` ([`gas.md`]({{ config.extra.repo }}/blob/master/docs/benchmarks/gas.md)). If you read the index every time you accrue it, you save almost nothing.
- **Nearest since v5.** `exp` returns the nearest word in v5 and v6, deployed and inline. The v4 object does not promise that.
- **A wall at 88.** FP127's `exp` reverts above 88, an index of about 1.65 × 10^38. For more room, read through FP256: `FP256Lib.exp(FP256Lib.fromFP127(logIndex))`.
- **A continuous rate only.** With a rate per period, L gains n × `log1p(r)`. `log1p` rounds once, and that rounding is added n times. In two runs of 100 accruals, each of up to 86,400 periods, that read was 136,497 and 156,064 units off. `mul(index, compound(r, n))` was 47.6 and 48.4 off. For a rate per period, use `compound`.

The snippets on this page are compiled and run on the replays' own integers in [`test/examples/Integrating.t.sol`]({{ config.extra.repo }}/blob/master/test/examples/Integrating.t.sol).

## The ops

{{ <optable /> }}

## For agents

[`/.well-known/agent.json`](/.well-known/agent.json), [`/llms.txt`](/llms.txt), ABI at [`/data/abi.json`](/data/abi.json). Reads are `eth_call`: no gas, no wallet.
