# Vendored library sources

Single files copied unchanged from their upstream repositories so the ladder
can run them without pulling in a monorepo. Each keeps its own SPDX header
and license; nothing here is part of FP127.

| path | upstream | pinned at | license |
|---|---|---|---|
| `balancer/LogExpMath.sol` | [balancer/balancer-v3-monorepo](https://github.com/balancer/balancer-v3-monorepo) `pkg/solidity-utils/contracts/math/LogExpMath.sol` | main @ `2b9ce4b1b8ad`, fetched 2026-10-15 | MIT |
| `openzeppelin/utils/math/{Math,SignedMath,SafeCast}.sol`, `openzeppelin/utils/Panic.sol` | [OpenZeppelin/openzeppelin-contracts](https://github.com/OpenZeppelin/openzeppelin-contracts) `contracts/utils/...` | tag v5.7.0, fetched 2026-10-23 | MIT |
| `uniswap/FullMath.sol` | [Uniswap/v4-core](https://github.com/Uniswap/v4-core) `src/libraries/FullMath.sol` | tag v4.0.0, fetched 2026-10-23 | MIT |
| `lyra/libraries/{BlackScholes,FixedPointMathLib,Math}.sol`, `lyra/synthetix/{DecimalMath,SignedDecimalMath}.sol` | [lyra-finance/lyra-protocol](https://github.com/lyra-finance/lyra-protocol) `contracts/...` | master @ `ea9e36a`, fetched 2026-10-27; the one change is `pragma solidity 0.8.16` to `^0.8.16`, so they build with this repo's solc | ISC (DecimalMath, SignedDecimalMath: MIT) |

Three comparison libraries are AGPL-3.0-only (or link AGPL code) and are submodules instead, never
copied here: Solmate (`lib/solmate`, main @ `89365b8`; its only tag, v6,
predates `SignedWadMath`), snekmate (`lib/snekmate`, tag v0.1.2) and solstat
(`lib/solstat`, [primitivefinance/solstat](https://github.com/primitivefinance/solstat) main @ `80c603f`, for the
normal CDF and erfc; its `Gaussian.sol` is MIT but links solmate v7, `lib/solstat/lib/solmate` @ `ed67fed`, through
the `lib/solstat/:solmate/` remapping). The files that link them carry the same licence: `../LadderSolmate.sol`,
`../vyper/SnekmateMath.vy`, `test/fp127/GasLibs.sol` and `test/cdf/Cdf.t.sol`. None of them is imported by FP127,
FP19 or BlockulatorWad: they are benchmarks only. snekmate is Vyper;
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

Two rate models are transcribed the same way, though their licences would
allow vendoring, because the ladder needs their formula, not their contract
(storage, access control, the vault and pair plumbing). Each adapter file
carries the source's own licence and notice, keeps the original's integer
types, operation order and rounding line for line, and reads the contract's
immutables from a `Config` struct:

| adapter | formula | upstream, pinned at | license |
|---|---|---|---|
| `../LadderFraxlend.sol` (`FraxlendRate`) | `VariableInterestRate.getFullUtilizationInterest` and `getNewRate` (V2), and the charge in `FraxlendPairCore._calculateInterest`, interest = Δt · totalBorrow · newRate / 1e18 | [FraxFinance/fraxlend](https://github.com/FraxFinance/fraxlend) `src/contracts/{VariableInterestRate,FraxlendPairCore}.sol` @ `2bed49d4dcc6` | ISC (SPDX on the files; the repo has no LICENSE file) |
| `../LadderEuler.sol` (`EulerAdaptiveCurve`) | `IRMAdaptiveCurve._newRateAtTarget`, `_calcErr`, `_curve` and the rate-at-target branch of `computeInterestRateInternal`, with `ExpLib.wExp` (copied by Euler from morpho-blue-irm `a824ce06`) | [euler-xyz/evk-periphery](https://github.com/euler-xyz/evk-periphery) `src/IRM/IRMAdaptiveCurve.sol`, `src/IRM/lib/ExpLib.sol` @ `af436991e135` | MIT, "Copyright (c) 2023 Morpho Association" |

The deployed contracts these are checked against, on a mainnet fork, by
`test/accrual/DeployedRates.t.sol` (`make rates-verify`): FraxLend's rate
contract `0x18500cB1f2fE7a40eBdA393383A0B8548a31F261` ("Variable Rate V2
[0.5 0.2@.875 5-10k] 2 days (.75-.85)", RATE_HALF_LIFE 172800) through its
`getNewRate`, and the pair `0x78bB3aEC3d855431bd9289fD98dA13F9ebB7ef15` that
uses it through `previewAddInterest`; Euler's `IRMAdaptiveCurve`
`0xC9A0109D925251E0E5380d6fB4b105408d16C23D` (from the factory
`0x3EC2d5af936bBB57DD19C292BAfb89da0E377F42`; ADJUSTMENT_SPEED
3170979198376, 100 per 365-day year) driven for fresh vault addresses
through its own `computeInterestRate` and read back with
`computeRateAtTargetView` and `computeInterestRateView`. Both verified
sources on the explorer carry the formula lines of the pinned commits.

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

For the normal CDF comparison (`test/cdf/`), Primitive's RMM-01 `getCDF` is GPL-3.0-only and is transcribed, not
vendored: `test/cdf/CdfRmm.sol` carries its licence and follows
[primitivefinance/rmm-core](https://github.com/primitivefinance/rmm-core)
`contracts/libraries/CumulativeNormalDistribution.sol` @ `8d3ef9b` line for line, on the ABDKMath64x64 already in
`lib/`. Its results equal the original's, run on rmm-core's own ABDK copy, at every point the two runs share.

