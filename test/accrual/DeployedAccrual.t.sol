// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import "forge-std/Test.sol";

// The deployed code, from the submodules pinned to the mainnet commits
// (scripts/accrual/verify_deployed.py proves the runtime bytecode equal):
// Aave v3 Core, aave-dao/aave-v3-origin v3.7.0 (cff15de6), Pool implementation
// 0x728a138a4823392c2efa55e028d434f526fe03cf; Morpho Blue v1.0.0 (55d2d993) at
// 0xBBBBBbbBBb9cC5e90e3b3Af64bdAF62C37EEFFCb; AdaptiveCurveIrm v1.0.0 (a7d9cce3) at
// 0x870aC11D48B15DB9a138Cf899d20F13F79Ba00BC. The libraries are internal, so
// they are compiled into this harness; the IRM is a contract and runs as the
// bytecode compiled with its own deployed settings (out/accrual/AdaptiveCurveIrm.json).
import {MathUtils} from "../../lib/aave-v3-origin/src/contracts/protocol/libraries/math/MathUtils.sol";
import {WadRayMath} from "../../lib/aave-v3-origin/src/contracts/protocol/libraries/math/WadRayMath.sol";
import {TokenMath} from "../../lib/aave-v3-origin/src/contracts/protocol/libraries/helpers/TokenMath.sol";
import {MathLib} from "../../lib/morpho-blue/src/libraries/MathLib.sol";
import {MarketParams, Market, Id} from "../../lib/morpho-blue/src/interfaces/IMorpho.sol";
import {IIrm} from "../../lib/morpho-blue/src/interfaces/IIrm.sol";

import {LadderAave} from "../../contracts/src/ladder/LadderAave.sol";
import {LadderMorpho} from "../../contracts/src/ladder/LadderMorpho.sol";
import {Scenario} from "../../contracts/src/ladder/ILadder.sol";
import {IdealFP127, IdealFP256} from "./IdealAccrual.sol";

interface IAdaptiveCurveIrm is IIrm {
    function rateAtTarget(Id id) external view returns (int256);
}

/// @title DeployedAccrual
/// @notice Runs every case in scripts/accrual/cases.json through the deployed
///         accrual code and through FP127 / FP256 computing the stated ideal,
///         and prints one line per result:
///             ACC|<case>|<form>|k=v;k=v;...
///         scripts/accrual/accrual.py scores them against mpmath at 200 digits.
///         Live cases carry the value the mainnet contract returned at the
///         survey block, and the harness asserts it reproduces it exactly.
contract DeployedAccrual is Test {
    using WadRayMath for uint256;
    using MathLib for uint256;

    string constant CASES = "scripts/accrual/cases.json";
    address constant MORPHO = 0xBBBBBbbBBb9cC5e90e3b3Af64bdAF62C37EEFFCb;

    string json;
    IAdaptiveCurveIrm irm;
    IdealFP127 fp127;
    IdealFP256 fp256;

    function setUp() public {
        json = vm.readFile(CASES);
        bytes memory init = vm.parseJsonBytes(vm.readFile("out/accrual/AdaptiveCurveIrm.json"), ".bytecode.object");
        bytes memory code = abi.encodePacked(init, abi.encode(MORPHO));
        address a;
        assembly { a := create(0, add(code, 0x20), mload(code)) }
        require(a != address(0), "irm deploy");
        irm = IAdaptiveCurveIrm(a);
        fp127 = new IdealFP127();
        fp256 = new IdealFP256();
    }

    function _s(string memory key) internal view returns (string[] memory) { return vm.parseJsonStringArray(json, key); }
    function _u(string[] memory a, uint256 i) internal pure returns (uint256) { return vm.parseUint(a[i]); }

    function _emit(string memory id, string memory form, string memory kv) internal pure {
        console.log(string.concat("ACC|", id, "|", form, "|", kv));
    }
    function _kv(string memory k, uint256 v) internal pure returns (string memory) { return string.concat(k, "=", vm.toString(v), ";"); }
    function _kvi(string memory k, int256 v) internal pure returns (string memory) { return string.concat(k, "=", vm.toString(v), ";"); }

    // ---- Aave ----------------------------------------------------------------

    struct AaveCase { string id; uint256 kind; uint256 rate; uint256 t; uint256 index0; uint256 scaled; uint256 last; uint256 expect; }

    function _aave(uint256 i) internal view returns (AaveCase memory c) {
        c.id = _s(".aave.id")[i];
        c.kind = _u(_s(".aave.kind"), i);
        c.rate = _u(_s(".aave.rate"), i);
        c.t = _u(_s(".aave.t"), i);
        c.index0 = _u(_s(".aave.index0"), i);
        c.scaled = _u(_s(".aave.scaled"), i);
        c.last = _u(_s(".aave.last"), i);
        c.expect = _u(_s(".aave.expect"), i);
    }

    /// kind 0: variable borrow (ReserveLogic._updateIndexes / getNormalizedDebt,
    /// TokenMath.getVTokenBalance); kind 1: supply (linear, getATokenBalance).
    function test_aave() public {
        uint256 n = _s(".aave.id").length;
        for (uint256 i; i < n; i++) {
            AaveCase memory c = _aave(i);
            vm.warp(c.last + c.t);
            uint256 factor;
            uint256 index1;
            uint256 bal0;
            uint256 bal1;
            if (c.kind == 0) {
                factor = MathUtils.calculateCompoundedInterest(c.rate, uint40(c.last));
                index1 = factor.rayMul(c.index0);
                bal0 = TokenMath.getVTokenBalance(c.scaled, c.index0);
                bal1 = TokenMath.getVTokenBalance(c.scaled, index1);
            } else {
                factor = MathUtils.calculateLinearInterest(c.rate, uint40(c.last));
                index1 = factor.rayMul(c.index0);
                bal0 = TokenMath.getATokenBalance(c.scaled, c.index0);
                bal1 = TokenMath.getATokenBalance(c.scaled, index1);
            }
            if (c.expect != 0) assertEq(index1, c.expect, string.concat(c.id, ": index differs from the mainnet view"));
            _emit(c.id, "deployed", string.concat(_kv("factor", factor), _kv("index1", index1), _kv("bal0", bal0), _kv("bal1", bal1)));
            (int256 b, int256 it) = fp127.aaveContinuous(c.rate, c.t, c.index0, c.scaled);
            (int256 b2, int256 it2) = fp127.aavePerSecond(c.rate, c.t, c.index0, c.scaled);
            _emit(c.id, "fp127", string.concat(_kvi("cont_bal", b), _kvi("cont_int", it), _kvi("ps_bal", b2), _kvi("ps_int", it2)));
            (b, it) = fp256.aaveContinuous(c.rate, c.t, c.index0, c.scaled);
            (b2, it2) = fp256.aavePerSecond(c.rate, c.t, c.index0, c.scaled);
            _emit(c.id, "fp256", string.concat(_kvi("cont_bal", b), _kvi("cont_int", it), _kvi("ps_bal", b2), _kvi("ps_int", it2)));
        }
    }

    // ---- Morpho --------------------------------------------------------------

    struct MorphoCase { string id; uint256 supply; uint256 borrow; uint256 r0; uint256 t; uint256 last; uint256 expect; }

    function _morpho(uint256 i) internal view returns (MorphoCase memory c) {
        c.id = _s(".morpho.id")[i];
        c.supply = _u(_s(".morpho.supply"), i);
        c.borrow = _u(_s(".morpho.borrow"), i);
        c.r0 = _u(_s(".morpho.r0"), i);
        c.t = _u(_s(".morpho.t"), i);
        c.last = _u(_s(".morpho.last"), i);
        c.expect = _u(_s(".morpho.expect"), i);
    }

    /// Morpho._accrueInterest with the AdaptiveCurveIrm:
    /// interest = totalBorrowAssets.wMulDown(borrowRate.wTaylorCompounded(elapsed)).
    function test_morpho() public {
        uint256 n = _s(".morpho.id").length;
        for (uint256 i; i < n; i++) {
            MorphoCase memory c = _morpho(i);
            MarketParams memory mp = MarketParams(address(uint160(i + 1)), address(0), address(0), address(irm), 0.86e18);
            Id id = Id.wrap(keccak256(abi.encode(mp)));
            // rateAtTarget is the IRM's only storage: mapping(Id => int256) at slot 0
            vm.store(address(irm), keccak256(abi.encode(id, uint256(0))), bytes32(c.r0));
            Market memory m = Market(uint128(c.supply), 0, uint128(c.borrow), 0, uint128(c.last), 0);
            vm.warp(c.last + c.t);
            uint256 rate = irm.borrowRateView(mp, m);
            if (c.expect != 0) assertEq(rate, c.expect, string.concat(c.id, ": borrow rate differs from the mainnet IRM"));
            vm.prank(MORPHO);
            irm.borrowRate(mp, m);
            int256 endRate = irm.rateAtTarget(id);
            uint256 taylor = rate.wTaylorCompounded(c.t);
            uint256 interest = c.borrow.wMulDown(taylor);
            _emit(c.id, "deployed", string.concat(_kv("rate", rate), _kvi("endRateAtTarget", endRate), _kv("taylor", taylor), _kv("interest", interest)));
            (int256 b, int256 it) = fp127.morphoAdaptive(c.supply, c.borrow, c.r0, c.t);
            _emit(c.id, "fp127", string.concat(_kvi("bal", b), _kvi("int", it)));
            (b, it) = fp256.morphoAdaptive(c.supply, c.borrow, c.r0, c.t);
            _emit(c.id, "fp256", string.concat(_kvi("bal", b), _kvi("int", it)));
        }
    }

    /// Morpho at a fixed per-second WAD rate (no IRM): the ladder's model.
    function test_morphoFixed() public view {
        uint256 n = _s(".morphoFixed.id").length;
        for (uint256 i; i < n; i++) {
            string memory id = _s(".morphoFixed.id")[i];
            uint256 rate = _u(_s(".morphoFixed.rate"), i);
            uint256 t = _u(_s(".morphoFixed.t"), i);
            uint256 borrow = _u(_s(".morphoFixed.borrow"), i);
            uint256 taylor = rate.wTaylorCompounded(t);
            uint256 interest = borrow.wMulDown(taylor);
            _emit(id, "deployed", string.concat(_kv("rate", rate), _kv("taylor", taylor), _kv("interest", interest)));
            (int256 b, int256 it) = fp127.morphoFixed(rate, t, borrow);
            _emit(id, "fp127", string.concat(_kvi("bal", b), _kvi("int", it)));
            (b, it) = fp256.morphoFixed(rate, t, borrow);
            _emit(id, "fp256", string.concat(_kvi("bal", b), _kvi("int", it)));
        }
    }

    // ---- the ladder's models against the deployed code -------------------------

    /// LadderAave and LadderMorpho (the transcriptions in the published ladder)
    /// against the pinned deployed libraries on the ladder's continuous-accrual
    /// inputs: the same integers in, the same integer out.
    function test_ladder_models_match_deployed() public {
        LadderAave la = new LadderAave();
        LadderMorpho lm = new LadderMorpho();
        uint32[6] memory ns = [uint32(1), 10, 100, 365, 1000, 10000];
        uint256[3] memory rates = [uint256(0.05e27), 0.5e27, 3.07e27];
        for (uint256 r; r < rates.length; r++) {
            for (uint256 k; k < ns.length; k++) {
                int256[] memory p = new int256[](3);
                p[0] = 10000e27;
                p[1] = int256(rates[r]);
                p[2] = int256(rates[r] / 1e9 / 365 days); // WAD per second, floored, as inputs.json floors it
                (int256 rawA,) = la.run(Scenario.ACCRUAL_CONTINUOUS, ns[k], p);
                vm.warp(1_700_000_000 + uint256(ns[k]) * 86400);
                uint256 f = MathUtils.calculateCompoundedInterest(rates[r], uint40(1_700_000_000));
                assertEq(uint256(rawA), uint256(10000e27).rayMul(f), "LadderAave != MathUtils v3.7.0");
                p[0] = 10000e18;
                (int256 rawM,) = lm.run(Scenario.ACCRUAL_CONTINUOUS, ns[k], p);
                uint256 want = 10000e18 + uint256(10000e18).wMulDown(uint256(p[2]).wTaylorCompounded(uint256(ns[k]) * 86400));
                assertEq(uint256(rawM), want, "LadderMorpho != MathLib v1.0.0");
                _emit(string.concat("ladder-", vm.toString(rates[r]), "-", vm.toString(ns[k])), "ladder",
                    string.concat(_kvi("aave", rawA), _kvi("morpho", rawM)));
            }
        }
    }
}
