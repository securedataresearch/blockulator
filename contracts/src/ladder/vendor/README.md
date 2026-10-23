# Vendored library sources

Single files copied unchanged from their upstream repositories so the ladder
can run them without pulling in a monorepo. Each keeps its own SPDX header
and license; nothing here is part of FP127.

| path | upstream | pinned at | license |
|---|---|---|---|
| `balancer/LogExpMath.sol` | [balancer/balancer-v3-monorepo](https://github.com/balancer/balancer-v3-monorepo) `pkg/solidity-utils/contracts/math/LogExpMath.sol` | main @ `2b9ce4b1b8ad`, fetched 2026-10-15 | MIT |
| `openzeppelin/utils/math/{Math,SignedMath,SafeCast}.sol`, `openzeppelin/utils/Panic.sol` | [OpenZeppelin/openzeppelin-contracts](https://github.com/OpenZeppelin/openzeppelin-contracts) `contracts/utils/...` | tag v5.7.0, fetched 2026-10-23 | MIT |
| `uniswap/FullMath.sol` | [Uniswap/v4-core](https://github.com/Uniswap/v4-core) `src/libraries/FullMath.sol` | tag v4.0.0, fetched 2026-10-23 | MIT |

Two comparison libraries are AGPL-3.0-only and are submodules instead, never
copied here: Solmate (`lib/solmate`, main @ `89365b8`; its only tag, v6,
predates `SignedWadMath`) and snekmate (`lib/snekmate`, tag v0.1.2). The files
that link them carry the same licence: `../LadderSolmate.sol`,
`../vyper/SnekmateMath.vy` and `test/fp127/GasLibs.sol`. snekmate is Vyper;
`scripts/ladder/vyper.py` compiles the wrapper with Vyper 0.4.3, the version
snekmate v0.1.2 pins.

Three more libraries are in the ladder without being vendored, because their
licenses (Aave v3: BUSL-1.1; Morpho Blue: GPL-2.0-or-later; Maker's pot.sol:
AGPL-3.0) do not sit inside an MIT repository. Their accrual formulas are a
few lines each and are transcribed into the adapters, with the rounding of
the original reproduced and the source named:

| adapter | formula | upstream, pinned at |
|---|---|---|
| `../LadderAave.sol` | `MathUtils.calculateCompoundedInterest` (three-term expansion of e^(rate·t)) with `WadRayMath.rayMul` (half up) | [aave-dao/aave-v3-origin](https://github.com/aave-dao/aave-v3-origin) `src/contracts/protocol/libraries/math/{MathUtils,WadRayMath}.sol`, main @ `8305565ae342` |
| `../LadderMorpho.sol` | `MathLib.wTaylorCompounded` (three-term Taylor of e^(nx) − 1) with `wMulDown` | [morpho-org/morpho-blue](https://github.com/morpho-org/morpho-blue) `src/libraries/MathLib.sol`, main @ `8e26ca6a8dbc` |
| `../LadderMaker.sol` | `rpow` (squaring, half-up at every step) as Solady's MIT `FixedPointMathLib.rpow`, which mirrors DSS `_rpow` | [makerdao/dss](https://github.com/makerdao/dss) `src/pot.sol`; Solady v0.1.26 |

`scripts/fp127/gas_to_json.py versions()` records these pins in every
generated dataset.

The mainnet deployments are pinned as submodules for
`docs/benchmarks/accrual-deployed.md`: `lib/aave-v3-origin` at v3.7.0
(`cff15de6`, the Core Pool implementation `0x728a138a…03cf`, POOL_REVISION
11), `lib/morpho-blue` at v1.0.0 (`55d2d993`, `0xBBBBBbbB…EFFCb`) and
`lib/morpho-blue-irm` at v1.0.0 (`a7d9cce3`, AdaptiveCurveIrm
`0x870aC11D…00BC`); `make accrual-verify` recompiles them and compares the
runtime bytecode to mainnet. The transcriptions above are pinned to later
`main` commits; the files they transcribe (MathUtils, WadRayMath, MathLib)
are byte-identical at the deployed tags, and
`test/accrual/DeployedAccrual.t.sol` checks LadderAave and LadderMorpho
against the deployed libraries cell for cell. Two notes on the table: the
deployed Morpho.sol (v1.0.0) carries a BUSL-1.1 header (MathLib.sol is
GPL-2.0-or-later; later `main` relicensed Morpho.sol to GPL), and
LadderMorpho models a constant per-second rate, not the AdaptiveCurveIrm,
whose rate-path approximations are measured in the accrual study.
