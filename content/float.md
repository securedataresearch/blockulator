+++
title = "FP19"
description = "256-bit binary float. One word, 71 digits at any magnitude, every op correctly rounded: 0 misrounded in 360,590 random inputs."
path = "library/fp19"
aliases = ["/float/", "/library/fp256/"]

[extra]
group = "library"
# anchors of the integration section, now on /library/integrating/: page.html forwards them
moved = ["rule-1-bunni-v2", "rule-2-resupply", "rule-2-balancer-v2", "rule-2-balancer-v1-the-counter-example", "the-edge-ops", "divide-last", "keep-an-index-as-its-logarithm"]
moved_to = "/library/integrating/"
+++

FP127 has 38 digits at 1, 8 at 10<sup>−30</sup> and nothing outside 2<sup>−128</sup> to 2<sup>127</sup>; the [edges](/results/edges/) show where that ends. FP19 fills the whole word, so the digits travel with the value. Every op rounds once, to the correctly rounded word: 0 misrounded in 360,590 random inputs, Lambert W included ([sweep]({{ config.extra.repo }}/blob/master/docs/benchmarks/sweep.md)), with a stated error bound behind each result.

## The word

Sign in bit 255, a 19-bit exponent (bias 262,143), a 236-bit fraction with an implicit one: 237 significant bits, about 71 digits, from 10<sup>−78,913</sup> to 10<sup>78,913</sup>. No NaN, no infinity, no subnormals, no negative zero. Zero is the all-zero word; any other word with exponent 0 reverts `OutOfRange`. Equality is bit equality.

{{ <wordstrip format="fp19" /> }}

`value = (-1)^s (1 + F / 2^236) 2^(E - 262143)`, with s the sign, E the exponent and F the significand field.

Rounding: once per op, ties away from zero. Overflow reverts; underflow rounds to zero. `ONE` is `0x3ffff << 236`.

| | digits | range | add | mul | div | exp | ln | pow | sqrt |
|---|---:|---|---:|---:|---:|---:|---:|---:|---:|
| **FP19** | **71** | 10<sup>±78,913</sup> | {{ <gas op="add" lib="fp19" form="lib" /> }} | {{ <gas op="mul" lib="fp19" form="lib" /> }} | {{ <gas op="div" lib="fp19" form="lib" /> }} | {{ <gas op="exp" lib="fp19" form="lib" /> }} | {{ <gas op="ln" lib="fp19" form="lib" /> }} | {{ <gas op="pow" lib="fp19" form="lib" /> }} | {{ <gas op="sqrt" lib="fp19" form="lib" /> }} |
| ABDKMathQuad | 34 | 10<sup>±4,932</sup> | {{ <gas op="add" lib="fp19" form="quad" /> }} | {{ <gas op="mul" lib="fp19" form="quad" /> }} | {{ <gas op="div" lib="fp19" form="quad" /> }} | {{ <gas op="exp" lib="fp19" form="quad" /> }} | {{ <gas op="ln" lib="fp19" form="quad" /> }} | {{ <gas op="pow" lib="fp19" form="quad" /> }} | {{ <gas op="sqrt" lib="fp19" form="quad" /> }} |
| FP127 | 38 at 1 | 2<sup>−128</sup> to 2<sup>127</sup> (±1.7 × 10<sup>38</sup>) | {{ <gas op="add" lib="fp19" form="fp127lib" /> }} | {{ <gas op="mul" lib="fp19" form="fp127lib" /> }} | {{ <gas op="div" lib="fp19" form="fp127lib" /> }} | {{ <gas op="exp" lib="fp19" form="fp127lib" /> }} | {{ <gas op="ln" lib="fp19" form="fp127lib" /> }} | {{ <gas op="pow" lib="fp19" form="fp127lib" /> }} | {{ <gas op="sqrt" lib="fp19" form="fp127lib" /> }} |

Inline library, median gas per call: over random inputs that take no shortcut for `exp`, `ln`, `pow` and `sqrt`, over the input ladder for the rest; FP127 and Quad on the same values ([the full table](#gas-against-fp127-and-quad)). FP19 carries twice binary128's digits and is cheaper than Quad on `add`, `mul`, `div`, `exp`, `ln` and `pow`, not on `sqrt`. FP127 is cheaper than FP19 on everything here but `exp`, with 38 digits at 1 to FP19's 71.

## Deployed form

{{ <deployment lib="fp19" /> }}

FP19 v5 (Blockulator 2.2) is live as four objects from one source, one idea each, with ops that share a kernel in one object. The record above is FP19's; [`FP19.md`](/contracts/deployments/FP19.md) has all four.

| object | the idea | address | ops |
|---|---|---|---|
| FP19 | the number | `0xAa1f71B7B08d568379b28E1488c6B737a1C6eb52` | `add` `sub` `mul` `div` `inv` `sqrt` `cbrt` `hypot` `gavg`; `neg` `abs` `sign`; `cmp` `lt` `eq` `min` `max` `clamp`; `floor` `ceil` `round` `frac`; `avg` `dist` `zeroFloorSub` `lerp`; `mulDown` `mulUp` `divDown` `divUp`; every conversion |
| FP19E | the elementary functions, on one exp/log kernel | `0x017F68A57dD53a6dF2043c24B712b287F9549AE2` | `exp` `exp2` `exp10` `expm1` `ln` `log2` `log10` `log2Up` `log1p` `pow` `powu` `compound` |
| FP19H | the hyperbolic functions | `0xEfefa2B63A173d56F9db79C5dd8A607F4aA859A5` | `sinh` `cosh` `tanh` `atanh` |
| FP19S | the special functions | `0x73E8809F163d4358773cc5F25c134997B4b842F4` | `erf` `erfc` `normCdf` `lambertW0` `lambertWm1` `factorial` |

The hyperbolics are elementary functions too, but FP19E with them measured 27,308 bytes, over the 24,576 limit, so FP19H carries its own copy of the exp/log kernel at its own address: bytes at deployment, no gas per call. A smaller kernel may fold it back into FP19E. `pi` is the constant `FP19Lib.PI`, the word nearest π; `gcd` is gone. The inline library holds all 65 ops. The objects are evmVersion osaka builds and need the CLZ opcode (EIP-7939): they run on Ethereum, Sepolia and the other chains with CLZ, not on zkSync Era, Avalanche C-Chain or Polygon zkEVM ([the list]({{ config.extra.repo }}/blob/master/contracts/deployments/README.md#chains-clz-osaka-required)). FP19 v4 (Blockulator 2.1: FP19, FP19X, FP19X2 and FP19X3) and FP19 v3 (Blockulator 2.0) stay live at the addresses in the record.

## Inline form

```sh
forge install securedataresearch/blockulator
echo "fp19/=lib/blockulator/contracts/src/fp19/" >> remappings.txt
```

Compile `FP19Lib.sol` with `via_ir = true` (in `foundry.toml`): solc's legacy pipeline leaves the heavy ops 6–19% dearer than the same Yul in the deployed objects (net of the call), and through the IR they come within about −7% to +3% of them, `add` 677 → 545 and `exp` 3,277 → 2,848 gas on typical inputs; the build takes about 5.5× as long ([`profile.md`]({{ config.extra.repo }}/blob/master/docs/benchmarks/profile.md)).

```solidity
import {FP19Lib} from "fp19/FP19Lib.sol";

// a per-second rate over a year, with the rate itself held to 71 digits
int256 r = FP19Lib.div(FP19Lib.fromFixed18(0.05e18), FP19Lib.fromUint(31536000));
int256 g = FP19Lib.compound(r, 31536000);   // (1 + r)^n without ever rounding 1 + r
int256 balanceWad = FP19Lib.toFixed18(FP19Lib.mul(FP19Lib.fromFixed18(principalWad), g));
```

`fromFP127` is exact below 2<sup>109</sup> and rounds once above, `toFP127` rounds to the nearest 2<sup>−128</sup>; `fromFixed18` / `toFixed18` convert to WAD.

## Typed API

`FP19Type.sol` is opt-in: `type FP19 is int256`, with `+ - * /`, unary `-` and `< > <= >= == !=` bound to the library, and every other op attached (`x.exp()`, `a.mulUp(b)`). `fp19FromWad`, `fp19FromInt` and `fp19FromUint` convert in, `toWadDown`, `toUintUp` and the rest convert out, `y.toFP127()` and `toFP19(x)` cross to FP127's type, and `ONE` and `PI` are typed constants. Each function only re-types its arguments, so the words and reverts are `FP19Lib`'s, checked under fuzzing in `test/typed/`. Through the IR every op costs the same gas as the raw call; under the legacy pipeline the wrapper is one more internal call, 36 to 56 gas.

```solidity
import {FP19, ONE, fp19FromWad, fp19FromInt} from "fp19/FP19Type.sol";
import {FP127} from "fp127/FP127Type.sol";

FP19 b = fp19FromWad(1.5e18) * ONE.exp();  // 1.5e; * is FP19Lib.mul
bool between = b > fp19FromInt(4) && b < fp19FromInt(5);
uint256 charged = b.toUintUp();              // 5, ceiled
FP127 n = b.toFP127();                       // the nearest 127.128 word
```

## Integrating

Two rules, each from the replay of a real exploit. The [integration page](/library/integrating/) has the replays, the code in both formats and the edge-op tables.

1. **Store the state in the format.** Keep a running balance, index or accumulator as an FP19 word, and round to token units only on the way out. In Bunni v2's replay this alone turns a balance drained from 28 wei to 4 into 35.6 wei, 1.17 × 10<sup>−59</sup> wei from exact.
2. **Round toward the protocol at the token edge.** Floor what you pay out and ceil what you take in: `toUintDown` and `toUintUp`, `toFixed18Down` and `toFixed18Up`, `mulDown` and `mulUp`, `divDown` and `divUp`. Under this rule Resupply's borrow against 1 wei of collateral reverts, and Balancer V2's charge matches the exact one on every call.

## The ops

{{ <optable lib="fp19" /> }}

### Gas against FP127 and Quad

{{ <gastable repo={config.extra.repo} lib="fp19" /> }}

Source: `contracts/src/fp19/FP19.yul.src`, built by FP127's generator; object and library fuzzed equal across all of `int256`. Full reference: [`contracts/src/fp19/README.md`]({{ config.extra.repo }}/blob/master/contracts/src/fp19/README.md).
