// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

// @notice FP127's Yul objects (3.0, salts "FP127 v9", "FP127E v9", "FP127H v9", "FP127N v9", "FP127S v9"): the
//         number, the elementary, hyperbolic, normal and special functions, at their predicted CREATE2 addresses
//         (contracts/deployments/FP127.md has v8, the one object they replace). Tests etch the artifacts' runtimes
//         here, so the same adapter code runs in the harness and on chain; the adapters that call them are deployed
//         after them.
address constant FP127_ADDRESS = 0x0DF738d125677550a80A46BaF254386C66f96E0d;
address constant FP127E_ADDRESS = 0xc16F4C45B78D90A4D4C030cABF4f2A34c1Fb0808;
address constant FP127H_ADDRESS = 0xf2F99947aD1cC370bD5388a2997A5E4963a0B27B;
address constant FP127N_ADDRESS = 0xAA7Cd9635aE8630379636F533f23DBf2C193d296;
address constant FP127S_ADDRESS = 0xB9C2583a7Ad2251444DC7752658B6C1107C25036;
// @notice FP19's Yul objects (contracts/deployments/FP19.md; 3.0, salts "FP19 v6", "FP19E v6", "FP19H v6",
//         "FP19S v6"): the number, the elementary, hyperbolic and special functions. LadderFP19 is inline (FP19Lib) and calls none of them; LadderFP19Deployed, the form
//         the on-chain runners use, calls these, and tests etch the artifacts' runtimes here.
address constant FP19_ADDRESS = 0x94d9d43D6202827429a8058959eeCf6d232b8729;
address constant FP19E_ADDRESS = 0x8e5eE786bDD7c35a2867Fd329441d0BD0fB61092;
address constant FP19H_ADDRESS = 0xF059611C1c42543DE6EE82353Eb082Fd8999081f;
address constant FP19S_ADDRESS = 0xf74ba90535224870830e6e89D2b328d4cc09DE48;
// @notice FP19N (erf, erfc, normCdf; 3.0, salt "FP19N v6"): its predicted CREATE2 address, deployed with 3.0.
address constant FP19N_ADDRESS = 0xCe9F09D646B37a9100F05ED1FFD14E9f43180214;

/// @notice Scenario ids. Mirrors "index" in scripts/ladder/scenarios.json.
library Scenario {
    uint8 constant COMPOUND = 0;
    uint8 constant COMPOUND_POW = 1;
    uint8 constant BONDING_SQRT = 2;
    uint8 constant ROUNDTRIP = 3;
    uint8 constant AMORTISE = 4;
    uint8 constant GEO_MEAN = 5;
    uint8 constant BLACK_SCHOLES_CHAIN = 6;
    uint8 constant CUMULATIVE_PRODUCT = 7;
    uint8 constant COMPOUND_ANNUAL = 8;
    uint8 constant ACCRUAL_PER_SECOND = 9;
    uint8 constant ACCRUAL_CONTINUOUS = 10;
    uint8 constant DEEP_TAIL_OPTION = 11;
    uint8 constant DECAY = 12;
    uint8 constant ADAPTIVE_RATE = 13;
    uint8 constant COUNT = 14;
}

/// @notice Library (form) ids, in the order of LadderRunner's constructor.
///         Ids 0 to 4 are the v4 runner's and keep their numbers; 5 to 9 were
///         added with the v5 runner, 10 (FP19, the float) with v6, 11 to 15
///         (Solmate, OpenZeppelin, Uniswap FullMath, PRBMath UD60x18,
///         snekmate) with v12, and 16 and 17 (the FraxLend and Euler v2
///         adaptive rate models) in the same v12 runner, before its deploy.
library Form {
    uint8 constant FP127 = 0;
    uint8 constant FP127LIB = 1;
    uint8 constant ABDK = 2;
    uint8 constant SOLADY = 3;
    uint8 constant PRB = 4;
    uint8 constant QUAD = 5;
    uint8 constant BALANCER = 6;
    uint8 constant AAVE = 7;
    uint8 constant MORPHO = 8;
    uint8 constant MAKER = 9;
    uint8 constant FP19 = 10;
    uint8 constant SOLMATE = 11;
    uint8 constant OZ = 12;
    uint8 constant UNISWAP = 13;
    uint8 constant PRBUD = 14;
    uint8 constant SNEKMATE = 15;
    uint8 constant FRAXLEND = 16;
    uint8 constant EULER = 17;
    uint8 constant COUNT = 18;
}

/// @notice One-shot op ids for the edges dataset (scripts/ladder/edges.json).
library Op {
    uint8 constant LN = 0;
    uint8 constant EXP = 1;
    uint8 constant SQRT = 2;
    uint8 constant POW = 3;
    uint8 constant MUL = 4;
    uint8 constant DIV = 5;
    uint8 constant W0 = 6;
    uint8 constant WM1 = 7;
    uint8 constant LOG1P = 8;
    uint8 constant EXPM1 = 9;
    uint8 constant COMPOUND = 10;
    uint8 constant POWU = 11;
    uint8 constant ERF = 12;
    uint8 constant ERFC = 13;
    uint8 constant NORMCDF = 14;
    uint8 constant COUNT = 15;
}

/// @notice One adapter per library. `run` executes a scenario for n steps in
///         the library's native representation and returns the raw result in
///         that representation, plus the gas the scenario function consumed
///         (measured inside the adapter, so the external call to it is not
///         included). `p` holds the scenario's parameters already floored
///         into the adapter's representation, in the order scenarios.json
///         declares (scripts/ladder/inputs.json carries them). Reverts
///         propagate; the runner catches them.
interface ILadderAdapter {
    function run(uint8 scenario, uint32 n, int256[] calldata p) external view returns (int256 raw, uint256 gasUsed);
    /// One op once, for the edges dataset: `args` in the representation, an
    /// integer exponent unscaled. Unsupported(op) where the library has no
    /// way to compute it.
    function op(uint8 op_, int256[] calldata args) external view returns (int256 raw, uint256 gasUsed);
}

/// @notice Raised by an adapter when `p` has the wrong length for the scenario.
error BadParamCount(uint8 scenario, uint256 got);
/// @notice Raised by an adapter whose representation cannot hold p[i].
error ParamOutOfRange(uint256 i);
/// @notice Raised by an adapter whose library has no model for the scenario
///         (the accrual libraries answer only the accrual scenarios), or no
///         way to compute an edges op.
error Unsupported(uint8 scenario);
