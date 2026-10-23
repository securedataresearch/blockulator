# @blockulator/contracts

**Precision math for the EVM, correctly rounded and verified on chain.**
One `int256` per number: FP127 (signed 127.128 fixed point, 38 digits at 1) and FP256 (a 256-bit binary float, 71 digits over 10^±78,913). Plus BlockulatorWad, Solady's WAD API correct to the last wei. [blockulator.com](https://blockulator.com)

## Install

```sh
npm install @blockulator/contracts        # or: yarn add / pnpm add
```

Hardhat resolves the imports from `node_modules` as they are. Foundry needs one remapping:

```sh
echo "@blockulator/contracts/=node_modules/@blockulator/contracts/" >> remappings.txt
```

```solidity
import {FP127Lib} from "@blockulator/contracts/fp127/FP127Lib.sol";
import {FP256Lib} from "@blockulator/contracts/fp256/FP256Lib.sol";
import {BlockulatorWad} from "@blockulator/contracts/wad/BlockulatorWad.sol";
```

The libraries use the CLZ opcode (EIP-7939): compile with solc ≥ 0.8.31 and `evmVersion: "osaka"`, and deploy only to a chain with CLZ ([the list](https://github.com/securedataresearch/blockulator/blob/master/contracts/deployments/README.md#chains-clz-osaka-required)). Compile with `viaIR` as well: it takes another 10–33% off FP127Lib's and FP256Lib's gas ([profile](https://github.com/securedataresearch/blockulator/blob/master/docs/benchmarks/profile.md)).

## What is in it

| path | contents |
|---|---|
| `fp127/` | `FP127Lib.sol` (inline library), `IFP127.sol`, `FP127Caller.sol`, the deployed object `FP127.yul`, `abi.json` |
| `fp256/` | `FP256Lib.sol`, `IFP256.sol`, `IFP256E.sol`, `IFP256H.sol`, `IFP256S.sol`, the four objects `FP256*.yul`, `abi*.json` |
| `wad/` | `BlockulatorWad.sol` (inline only, no deployed object) |
| `deployments/` | one JSON record per deployed contract (address, chain, salt, compiler, verification links) and `RELEASE.json` |

Tooling can read addresses from the records, for example `require("@blockulator/contracts/deployments/FP127.json").address`.

Same sources, same paths, with `forge install securedataresearch/blockulator` or `forge soldeer install blockulator~<version>`: see the [install guide](https://github.com/securedataresearch/blockulator#use-it).

MIT licensed. [Source](https://github.com/securedataresearch/blockulator), [security](https://github.com/securedataresearch/blockulator/blob/master/SECURITY.md).
