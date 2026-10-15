# Vendored library sources

Single files copied unchanged from their upstream repositories so the ladder
can run them without pulling in a monorepo. Each keeps its own SPDX header
and license; nothing here is part of FP127.

| path | upstream | pinned at | license |
|---|---|---|---|
| `balancer/LogExpMath.sol` | [balancer/balancer-v3-monorepo](https://github.com/balancer/balancer-v3-monorepo) `pkg/solidity-utils/contracts/math/LogExpMath.sol` | main @ `2b9ce4b1b8ad`, fetched 2026-10-15 | MIT |

Two more libraries are in the ladder without being vendored, because their
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
