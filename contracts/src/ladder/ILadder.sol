// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

// @notice BL127's Yul objects (3.0, salts "BL127 v10", "BL127E v10", "BL127H v10", "BL127N v10", "BL127S v10"): the
//         number, the elementary, hyperbolic, normal and special functions, at their CREATE2 addresses, live on
//         Sepolia (contracts/deployments/BL127.md). Tests etch the artifacts' runtimes
//         here, so the same adapter code runs in the harness and on chain; the adapters that call them are deployed
//         after them.
address constant BL127_ADDRESS = 0x9D7f2c78EB802b83368E816E332A2aFa0997B3f2;
address constant BL127E_ADDRESS = 0xfE4627Ba196d0c9c2D068C8599837688A8BE8bD1;
address constant BL127H_ADDRESS = 0xC3B57948d3839b6B3358AC25E17fD7A055023704;
address constant BL127N_ADDRESS = 0x42f0FDe3EF14d10218126e37A672BE33012f8902;
address constant BL127S_ADDRESS = 0x315bF86feeCd5aCF3F9105f94A33ceBFa2e1Cc7E;
// @notice BL19's Yul objects (contracts/deployments/BL19.md; 3.0, salts "BL19 v7", "BL19E v7", "BL19H v7",
//         "BL19N v7", "BL19S v7"): the number, the elementary and hyperbolic functions, the normal distribution and
//         Lambert W. LadderBL19 is inline (BL19Lib) and calls none of them; LadderBL19Deployed, the form
//         the on-chain runners use, calls these, and tests etch the artifacts' runtimes here.
address constant BL19_ADDRESS = 0xbbb79a1B3c41553ee6C904D40a13f17EEFDC8230;
address constant BL19E_ADDRESS = 0x498DCcD03606E2f7B156Ec1bAE3800E8012cfD64;
address constant BL19H_ADDRESS = 0x2431fAeDd11E52EB8c104b051F2dac5DEA67dE5b;
address constant BL19N_ADDRESS = 0x0540A33443bc4b2Db8D96CBbcb8117A993227E41;
address constant BL19S_ADDRESS = 0x5a1266F89FC5b741e57077CbfEE59a6E48e32BCF;

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
///         added with the v5 runner, 10 (BL19, the float) with v6, 11 to 15
///         (Solmate, OpenZeppelin, Uniswap FullMath, PRBMath UD60x18,
///         snekmate) with v12, and 16 and 17 (the FraxLend and Euler v2
///         adaptive rate models) in the same v12 runner, before its deploy.
library Form {
    uint8 constant BL127 = 0;
    uint8 constant BL127LIB = 1;
    uint8 constant ABDK = 2;
    uint8 constant SOLADY = 3;
    uint8 constant PRB = 4;
    uint8 constant QUAD = 5;
    uint8 constant BALANCER = 6;
    uint8 constant AAVE = 7;
    uint8 constant MORPHO = 8;
    uint8 constant MAKER = 9;
    uint8 constant BL19 = 10;
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
