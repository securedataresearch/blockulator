# Blockulator

<!-- badges:begin -->
[![CI](https://github.com/securedataresearch/blockulator/actions/workflows/ci.yml/badge.svg)](https://github.com/securedataresearch/blockulator/actions/workflows/ci.yml) [![proofs](https://img.shields.io/badge/proofs-15%20ops%20proven-00694e)](docs/proofs.md) [![tests](https://img.shields.io/badge/tests-507%20forge%20tests-3f6d9c)](test) [![to the last wei](https://img.shields.io/badge/WAD-0%20wrong%20of%20108%2C000-00694e)](docs/benchmarks/wad.md) [![licence](https://img.shields.io/badge/licence-MIT-525252)](LICENSE)
<!-- badges:end -->

**The definitive source for precision.** FP127 and FP19 put precision maths in one `int256`: 38 digits and 71, every op correctly rounded, checked on chain, and now competitive on gas. When the amounts are large or the call is free, they are the only choice. [blockulator.com](https://blockulator.com)

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="docs/img/digits-dark.svg">
  <img alt="Correct digits of one accrual after 1 to 10,000 days without an update: FP19 and FP127 stay flat, binary128 and the WAD libraries hold their format, Aave and Morpho's three-term expansion falls to 1 digit." src="docs/img/digits-light.svg" width="820">
</picture>

| | what it is | precision | range |
|---|---|---|---|
| **FP19** | 256-bit binary float | 71 digits, everywhere | 10^±78,913 |
| **FP127** | signed 127.128 fixed point | 38 digits at 1 | money-sized numbers |

## Correct to the last wei

<!-- wad:begin -->
Share of results off by at least one wei, against the exact value rounded in each library's own direction, on the same seeded inputs. BlockulatorWad keeps Solady's names and is wrong on **0 of 108,000** results across 27 functions and rounding directions.

| function | **BlockulatorWad** | Solady | PRBMath SD59x18 | PRBMath UD60x18 | Solmate | snekmate |
|---|---:|---:|---:|---:|---:|---:|
| `cbrtWad` | **0 of 4,000** | 0 | — | — | — | 23% |
| `expWad` | **0 of 3,995** | 48% | 72% | 93% | 48% | 48% |
| `lnWad` | **0 of 3,998** | 24% | 98% | 98% | 24% | 24% |
| `log2Wad` | **0 of 3,998** | — | 93% | 90% | — | — |
| `log10Wad` | **0 of 3,998** | — | 88% | 90% | — | — |
| `powWad` | **0 of 3,461** | 66% | 71% | 85% | 66% | — |
| `lambertW0Wad` | **0 of 3,999** | 28% | — | — | — | — |

Where they offer them, Solady, PRBMath, Solmate, OpenZeppelin Math, Uniswap FullMath and snekmate are exact on `divWad`, `divWadUp`, `mulWad`, `mulWadUp`, `sDivWad`, `sMulWad`, `sqrtWad`, `sqrtWadUp`. Versions: BlockulatorWad fc19340, Solady v0.1.26, PRBMath SD59x18 v4.2.0, PRBMath UD60x18 v4.2.0, Solmate main@89365b8, OpenZeppelin Math v5.7.0 (vendored), Uniswap FullMath v4-core v4.0.0 (vendored), snekmate v0.1.2 (vyper 0.4.3); counts in [`wad.md`](docs/benchmarks/wad.md).
<!-- wad:end -->

## Twice the digits, at the same gas

<!-- gas:begin -->
| | digits | add | mul | div | exp<sup>t</sup> | ln<sup>t</sup> | pow<sup>t</sup> | sqrt<sup>t</sup> |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| *floating point* | | | | | | | | |
| **FP19** | **71** | **662** | **530** | **800** | **3,278** | **3,043** | **5,901** | **1,205** |
| ABDKMathQuad | 34 | 734 | 709 | 818 | 5,668 | 16,356 | 23,467 | 760 |
| *fixed point* | | | | | | | | |
| **FP127** | **38** | **128** | **267** | **412** | **2,716** | **1,944** | **3,317** | **469** |
| ABDKMath64x64 | 19 | 162 | 171 | 221 | 3,380 | 7,080 |  | 828 |
| PRBMath SD59x18 | 18 | 189 | 485 | 509 | 2,816 | 7,083 | 10,065 | 978 |
| PRBMath UD60x18 | 18 | 150 | 237 | 261 | 2,720 | 6,474 | 9,544 | 824 |
| Solady | 18 | 3 | 126 | 93 | 430 | 556 | 1,279 | 393 |
| Solmate | 18 |  | 131 | 97 | 430 | 632 | 1,355 | 456 |
| Balancer LogExpMath | 18 |  |  |  | 1,040 | 1,091 | 2,223 | 2,349 |
| snekmate | 18 |  |  |  | 604 | 1,226 |  |  |
| OpenZeppelin Math | 18 |  |  |  |  |  |  | 766 |

Median gas per inline call, over random inputs that take no shortcut (<sup>t</sup>) or the op's input ladder; digits are precision at 1. FP19 is cheaper than ABDKMathQuad on `add`, `mul`, `div`, `exp`, `ln` and `pow`, not `sqrt`, and over these 7 ops carries 2.1× its digits at 32% of its mean gas. FP127 carries twice the digits of every fixed-point library here; it is cheaper than PRBMath SD59x18 and OpenZeppelin Math on every op they share, and than ABDKMath64x64 on `add`, `exp`, `ln` and `sqrt`, and than PRBMath UD60x18 on `add`, `exp`, `ln`, `pow` and `sqrt`. Solady, Solmate, Balancer LogExpMath and snekmate are cheaper on most ops, at 18 digits; Solady's `add` is the unchecked `rawAdd`.
<!-- gas:end -->

Every op and library: [`gas.md`](docs/benchmarks/gas.md), [`gas19.md`](docs/benchmarks/gas19.md). Compile with `via_ir = true`; it takes another 10–33% off the inline libraries.

## Install

One import path, three ways in:

```bash
# Foundry, from git
forge install securedataresearch/blockulator
echo "@blockulator/contracts/=lib/blockulator/contracts/src/" >> remappings.txt

# npm, yarn or pnpm: Hardhat needs no remapping; Foundry reading node_modules needs this one
npm install @blockulator/contracts
echo "@blockulator/contracts/=node_modules/@blockulator/contracts/" >> remappings.txt

# Soldeer
forge soldeer install blockulator~<version>
echo "@blockulator/contracts/=dependencies/blockulator-<version>/" >> remappings.txt
```

```solidity
import {FP127Lib} from "@blockulator/contracts/fp127/FP127Lib.sol";
import {FP19Lib} from "@blockulator/contracts/fp19/FP19Lib.sol";

int256 grown = FP19Lib.pow(FP19Lib.add(FP19Lib.ONE, rate), FP19Lib.fromUint(31536000));
uint256 paid = FP19Lib.toUintDown(grown);          // to the user: floor
int256  ltv  = FP127Lib.divUp(debt, collateral);    // a limit check: never below the truth
```

Or call the deployed contracts, where every op is a free `eth_call`: `IFP127(0xb349…CBe4).ln(x)`. Agents can start from [`/llms.txt`](https://blockulator.com/llms.txt).

**Requires the CLZ opcode** (EIP-7939, the Osaka EVM). Supported: Ethereum, Arbitrum, OP Mainnet, Base, Unichain, Polygon PoS, BNB Chain, Gnosis, Scroll, Linea. Not supported: zkSync Era, Avalanche C-Chain. Check any chain with `make probe-clz RPC=<url>`.

## Two rules that end dust

Each rule comes from replaying a real exploit bit for bit, then running the same step in FP127, FP19 and exact arithmetic ([replays](docs/benchmarks/README.md)).

1. **Store the state in the format.** Keep running balances as FP127 or FP19 words, and round to token units only on the way out. In Bunni v2's replay this alone turns a balance drained from 28 wei to 4 into 35.6 wei, within 10^−37 of exact.
2. **Round toward the protocol at the token edge.** Floor what you pay out and ceil what you take in, never to nearest. Under this rule Resupply's borrow against 1 wei of collateral reverts, and Balancer V2's charge matches the exact one on every call.

The [integration guide](https://blockulator.com/library/#integrating) has the worked examples and the edge-op table.

## Blockulator 2.2 on Sepolia

| contract | address |
|---|---|
| FP127 v6 | `0xb349DB36D51b0BC10Dd43aF70009b7B6E7c1CBe4` |
| FP19 (the number) | `0xAa1f71B7B08d568379b28E1488c6B737a1C6eb52` |
| FP19E (exp, log, pow) | `0x017F68A57dD53a6dF2043c24B712b287F9549AE2` |
| FP19H (hyperbolic) | `0xEfefa2B63A173d56F9db79C5dd8A607F4aA859A5` |
| FP19S (erf, Lambert W) | `0x73E8809F163d4358773cc5F25c134997B4b842F4` |

Every contract is verified on Sourcify and Blockscout. Each library is one Yul source that generates both the deployed object and the inline library, fuzzed to agree bit for bit. More detail: [records](contracts/deployments/RELEASE.md), [FP127](contracts/src/fp127/README.md), [FP19](contracts/src/fp19/README.md), [precision](docs/fp19/precision.md), [the ladder](docs/benchmarks/ladder.md), [the edges](docs/benchmarks/edges.md), [proofs](docs/proofs.md), [changelog](CHANGELOG.md).

## Learn more

- [The write-up](https://blockulator.com/writeup/): the story, with sources.
- ["Dust is Over"](docs/talks/outline.md): the talk.
- [Developing](docs/DEVELOPING.md): layout, build, `make gates`. The tables and chart above are `make readme-assets`.
- [History](docs/fp127/HISTORY.md), and the [EthCC[9] talk](https://www.youtube.com/watch?v=a_tL99NY-yc) from the Huff era.

MIT licensed: FP127, FP19 and BlockulatorWad never import AGPL code. Three benchmark-only files link the AGPL-3.0 Solmate and snekmate libraries and carry that licence: `LadderSolmate.sol`, `SnekmateMath.vy` and `test/fp127/GasLibs.sol` ([details](contracts/src/ladder/vendor/README.md)). [Security](SECURITY.md).
