# Blockulator

**Precision math for the EVM, correctly rounded and verified on chain.**
One `int256` per number, two formats, every op tested against exact arithmetic.
[blockulator.com](https://blockulator.com)

| | what it is | precision | range |
|---|---|---|---|
| **FP127** | signed 127.128 fixed point | 38 digits at 1 | money-sized numbers |
| **FP256** | 256-bit binary float | 71 digits, everywhere | 10^±78,913 |

- **Round once.** Every FP256 op is correctly rounded: 0 misrounded in 360,590 random inputs, with a stated error bound behind each result. Every FP127 transcendental returns the nearest word (one known exception: `pow` with an exponent near 2^90).
- **Twice the digits, at the same gas.** FP256 carries twice binary128's digits and is cheaper than ABDKMathQuad on add, mul, div, exp, ln and pow. FP127 carries twice PRBMath's digits and is cheaper on add, mul, ln and pow.
- **More than arithmetic.** exp, ln, pow, compound, the hyperbolics, erf and normCdf, Lambert W, cbrt, hypot, and directed rounding at the token edge: 53 ops in FP127, 65 in FP256.
- **Checked on chain.** Thirteen real calculations, 87 inputs, N up to 10,000 steps, plus 139 edge probes. They are re-run through the deployed contracts wherever a public RPC can execute them, with 0 mismatches (the corrected ladder's on-chain re-check follows its v11 redeploy).

## Gas

Inline library, median gas per call: exp, ln and pow over random inputs that take no shortcut, the arithmetic over the input ladder (the site's basis). The digits column is precision at 1.

| | digits | add | mul | div | exp | ln | pow |
|---|---:|---:|---:|---:|---:|---:|---:|
| **FP256** | **71** | 662 | 530 | 800 | 3,278 | 3,043 | 5,901 |
| ABDKMathQuad | 34 | 734 | 709 | 818 | 5,668 | 16,356 | 23,467 |
| **FP127** | **38** | 128 | 267 | 412 | 2,716 | 1,944 | 3,317 |
| PRBMath SD59x18 | 18 | 189 | 485 | 509 | 2,816 | 7,083 | 10,065 |
| Solady | 18 | 3 | 126 | 93 | 430 | 556 | 1,279 |

Solady's `add` is its unchecked `rawAdd`. The full tables cover every op and library: [`gas.md`](docs/benchmarks/gas.md) and [`gas256.md`](docs/benchmarks/gas256.md). Compile with `via_ir = true`; it takes another 10–33% off the inline libraries.

## Use it

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
import {FP256Lib} from "@blockulator/contracts/fp256/FP256Lib.sol";

int256 grown = FP256Lib.pow(FP256Lib.add(FP256Lib.ONE, rate), FP256Lib.fromUint(31536000));
uint256 paid = FP256Lib.toUintDown(grown);          // to the user: floor
int256  ltv  = FP127Lib.divUp(debt, collateral);    // a limit check: never below the truth
```

Or call the deployed contracts, where every op is a free `eth_call`: `IFP127(0xb349…CBe4).ln(x)`. Agents can start from [`/llms.txt`](https://blockulator.com/llms.txt).

**Requires the CLZ opcode** (EIP-7939, the Osaka EVM). Supported: Ethereum, Arbitrum, OP Mainnet, Base, Unichain, Polygon PoS, BNB Chain, Gnosis, Scroll, Linea. Not supported: zkSync Era, Avalanche C-Chain. Check any chain with `make probe-clz RPC=<url>`.

## Two rules that end dust

Each rule comes from replaying a real exploit bit for bit, then running the same step in FP127, FP256 and exact arithmetic ([replays](docs/benchmarks/README.md)).

1. **Store the state in the format.** Keep running balances as FP127 or FP256 words, and round to token units only on the way out. In Bunni v2's replay this alone turns a balance drained from 28 wei to 4 into 35.6 wei, within 10^−37 of exact.
2. **Round toward the protocol at the token edge.** Floor what you pay out and ceil what you take in, never to nearest. Under this rule Resupply's borrow against 1 wei of collateral reverts, and Balancer V2's charge matches the exact one on every call.

The [integration guide](https://blockulator.com/library/#integrating) has the worked examples and the edge-op table.

## Blockulator 2.2 on Sepolia

| contract | address |
|---|---|
| FP127 v6 | `0xb349DB36D51b0BC10Dd43aF70009b7B6E7c1CBe4` |
| FP256 (the number) | `0xAa1f71B7B08d568379b28E1488c6B737a1C6eb52` |
| FP256E (exp, log, pow) | `0x017F68A57dD53a6dF2043c24B712b287F9549AE2` |
| FP256H (hyperbolic) | `0xEfefa2B63A173d56F9db79C5dd8A607F4aA859A5` |
| FP256S (erf, Lambert W) | `0x73E8809F163d4358773cc5F25c134997B4b842F4` |

Every contract is verified on Sourcify and Blockscout. Each library is one Yul source that generates both the deployed object and the inline library, fuzzed to agree bit for bit. More detail: [records](contracts/deployments/RELEASE.md), [FP127](contracts/src/fp127/README.md), [FP256](contracts/src/fp256/README.md), [precision](docs/fp256/precision.md), [the ladder](docs/benchmarks/ladder.md), [the edges](docs/benchmarks/edges.md), [changelog](CHANGELOG.md).

## Learn more

- [The write-up](https://blockulator.com/writeup/): the story, with sources.
- ["Dust is Over"](docs/talks/outline.md): the talk.
- [Developing](docs/DEVELOPING.md): layout, build, `make gates`.
- [History](docs/fp127/HISTORY.md), and the [EthCC[9] talk](https://www.youtube.com/watch?v=a_tL99NY-yc) from the Huff era.

MIT licensed. [Security](SECURITY.md).
