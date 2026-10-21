+++
title = "FP127"
description = "Signed 127.128 fixed point. One int256, 128 fractional bits (38 digits at 1), 55 ops in v5, every transcendental the nearest word. One Yul source, two forms: a deployed object and an inline library."

[extra]
group = "library"
+++

Both forms are generated from one file and fuzzed equal across the full `int256` domain, reverts included.

## Encoding

`value × 2^128` in an `int256`, two's complement. `ONE` is `2^128`. Range ±1.7 × 10^38, 128 fractional bits: 38 digits at 1, 32 at 10^−6, 8 at 10^−30. Every op takes and returns this one type. `fromFixed18` and `toFixed18` convert to and from WAD.

Errors: `Overflow()`, `DivisionByZero()`, `OutOfRange()`. Nothing wraps.

## Deployed form

{{ <deployment /> }}

No storage, no owner, no upgrade path. A new version is a new salt and a new address. The address above is v4 (49 ops); v5, the source the op table below is generated from, adds the directed `mulUp`, `mulDown`, `divUp`, `divDown`, `toFixed18Up` and `toFixed18Down` and rounds every transcendental to the nearest word, and is not yet deployed.

`sqrt(2)` from the command line:

```sh
cast call 0x6cFbCB928Ac068E84Ef793Dd1DFce4f8e9Cac1d1 "sqrt(int256)(int256)" \
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
    IFP127 public constant FP127 = IFP127(0x6cFbCB928Ac068E84Ef793Dd1DFce4f8e9Cac1d1);
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

`FP127Lib.sol`: the same Yul in `memory-safe` assembly, one `internal pure` function per op. No external call: about 1,300 gas cheaper than the `staticcall` on `add` and `mul`, 240 on `sqrt` and 470 on `exp`; on `pow`, the erf family and Lambert W the deployed object is cheaper.

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

`mulUp`, `mulDown`, `divUp`, `divDown`, `toFixed18Up` and `toFixed18Down` are new in v5, which is the source you get with `forge install`. The deployed v4 object at the address above does not have them yet; until v5 is deployed, use the inline library for them. `floor` and `ceil` are in v4.

The snippets on this page are compiled and run on the replays' own integers in [`test/examples/Integrating.t.sol`]({{ config.extra.repo }}/blob/master/test/examples/Integrating.t.sol).

## The ops

{{ <optable /> }}

## For agents

[`/.well-known/agent.json`](/.well-known/agent.json), [`/llms.txt`](/llms.txt), ABI at [`/data/abi.json`](/data/abi.json). Reads are `eth_call`: no gas, no wallet.
