// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import "forge-std/Test.sol";

import {FP127Lib} from "../../contracts/src/fp127/FP127Lib.sol";
import {FP256Lib} from "../../contracts/src/fp256/FP256Lib.sol";
import {BalancerV1Math as B} from "./BalancerV1Math.sol";

/// @title BalancerV1Replay
/// @notice The 31 Aug 2026 drain of five Balancer V1 BPools, replayed offline from the
///         integers in scripts/replays/balancer_v1.json (written by
///         scripts/replays/balancer_v1.py fetch: the pool state at the block before each
///         attack transaction and every pool call, decoded from the pool's own LOG_CALL
///         events). Every call is run through the transcribed BPool arithmetic
///         (BalancerV1Math) and every logged amount is asserted equal, swaps included.
///
///         For each single-token join (joinswapPoolAmountOut) and single-token exit
///         (exitswapPoolAmountIn) the same quantity is then computed three more ways, from
///         the same state, each converted to token units once and toward the pool (ceil for
///         an amount in, floor for an amount out):
///           bnum1  BNum's own 18-decimal ratio, the amount kept on the 1e-18 grid, one rounding
///           fp127  the formula in FP127 (127.128 fixed point), expm1(tW/wI * log1p(pAo/pS))
///           fp256  the same in FP256 (237-bit float)
///         and one line per call is printed for the 200-digit scoring
///         (scripts/replays/balancer_v1.py score):
///             BAL|<pool index, 0-based>|<call index>|<kind>|k=v;k=v;...
///         Pools are numbered 1-5 in the test names and in docs/benchmarks/replay-balancer-v1.md.
contract BalancerV1Replay is Test {
    string constant DATA = "scripts/replays/balancer_v1.json";
    uint256 constant SWAP_IN = 0;
    uint256 constant SWAP_OUT = 1;
    uint256 constant JOIN_POOL_OUT = 2;
    uint256 constant EXIT_POOL_IN = 3;
    uint256 constant EXIT_POOL = 4;
    int256 constant ONE127 = int256(1) << 128;

    string json;

    function setUp() public {
        json = vm.readFile(DATA);
    }

    struct Pool {
        uint256[] bal;
        uint256[] w;
        uint256 tW;
        uint256 fee;
        uint256 S;
    }

    struct Tape {
        uint256[] kind;
        uint256[] i;
        uint256[] j;
        uint256[] x;
        uint256[] y;
        uint256[] r;
    }

    function _key(uint256 p, string memory k) internal pure returns (string memory) {
        return string.concat(".pools[", vm.toString(p), "].", k);
    }

    function _uints(string memory key) internal view returns (uint256[] memory a) {
        string[] memory s = vm.parseJsonStringArray(json, key);
        a = new uint256[](s.length);
        for (uint256 k; k < s.length; k++) a[k] = vm.parseUint(s[k]);
    }

    function _uint(string memory key) internal view returns (uint256) {
        return vm.parseUint(vm.parseJsonString(json, key));
    }

    function _load(uint256 p) internal view returns (Pool memory pool, Tape memory t) {
        pool.bal = _uints(_key(p, "tape.balance"));
        pool.w = _uints(_key(p, "tape.denorm"));
        pool.tW = _uint(_key(p, "state.totalWeight"));
        pool.fee = _uint(_key(p, "state.swapFee"));
        pool.S = _uint(_key(p, "state.totalSupply"));
        t.kind = _uints(_key(p, "tape.kind"));
        t.i = _uints(_key(p, "tape.i"));
        t.j = _uints(_key(p, "tape.j"));
        t.x = _uints(_key(p, "tape.x"));
        t.y = _uints(_key(p, "tape.y"));
        t.r = _uints(_key(p, "tape.r"));
    }

    function test_replay_pool1_DPI_USDC_WETH_WBTC() public { _replay(0); }
    function test_replay_pool2_eight_tokens_USDC() public { _replay(1); }
    function test_replay_pool3_USDC_DAI_WETH() public { _replay(2); }
    function test_replay_pool4_renBTC() public { _replay(3); }
    function test_replay_pool5_WBTC() public { _replay(4); }

    struct Count {
        uint256 swaps;
        uint256 joins;
        uint256 exits;
        uint256 joinsBlocked;
        uint256 exitsBlocked;
    }

    /// One single-token join or exit: where it sits, its arguments and the logged result.
    struct Call {
        uint256 p;
        uint256 k;
        uint256 t; // token index
        uint256 amt; // poolAmountOut (join) / poolAmountIn (exit)
        uint256 lim; // maxAmountIn (join) / minAmountOut (exit)
        uint256 logged; // LOG_JOIN / LOG_EXIT amount
    }

    /// The same quantity computed toward the pool four ways (see the contract notice).
    struct Alt {
        uint256 bnum1;
        int256 r127;
        int256 r256;
        uint256 u127;
        uint256 u256;
    }

    function _replay(uint256 p) internal {
        (Pool memory pool, Tape memory t) = _load(p);
        Count memory c;
        for (uint256 k; k < t.kind.length; k++) {
            uint256 kind = t.kind[k];
            if (kind == SWAP_IN || kind == SWAP_OUT) {
                _swap(pool, t, k);
                c.swaps++;
            } else if (kind == JOIN_POOL_OUT) {
                if (_join(pool, Call(p, k, t.i[k], t.x[k], t.y[k], t.r[k]))) c.joinsBlocked++;
                c.joins++;
            } else if (kind == EXIT_POOL_IN) {
                if (_exit(pool, Call(p, k, t.i[k], t.x[k], t.y[k], t.r[k]))) c.exitsBlocked++;
                c.exits++;
            } else {
                _exitPool(p, pool, t.x[k]);
            }
        }
        console.log(string.concat("BALSUM|", vm.toString(p), "|swaps=", vm.toString(c.swaps), ";joins=", vm.toString(c.joins),
            ";exits=", vm.toString(c.exits), ";joinsBlockedByCeil=", vm.toString(c.joinsBlocked),
            ";exitsBlockedByFloor=", vm.toString(c.exitsBlocked), ";finalSupply=", vm.toString(pool.S)));
        // Every attack join paid one token unit for an amount whose exact price was about one and
        // a half: rounded toward the pool, each costs two and reverts on its own maxAmountIn = 1.
        assertEq(c.joinsBlocked, c.joins, "a join would still pay");
    }

    /// BPool.sol:423-484 (swapExactAmountIn), :486-546 (swapExactAmountOut)
    function _swap(Pool memory pool, Tape memory t, uint256 k) internal pure {
        uint256 i = t.i[k];
        uint256 o = t.j[k];
        uint256 before = B.calcSpotPrice(pool.bal[i], pool.w[i], pool.bal[o], pool.w[o], pool.fee);
        uint256 aI;
        uint256 aO;
        if (t.kind[k] == SWAP_IN) {
            aI = t.x[k];
            require(aI <= B.bmul(pool.bal[i], B.MAX_IN_RATIO), "ERR_MAX_IN_RATIO");
            aO = B.calcOutGivenIn(pool.bal[i], pool.w[i], pool.bal[o], pool.w[o], aI, pool.fee);
            require(aO >= t.y[k], "ERR_LIMIT_OUT");
            require(aO == t.r[k], "swapExactAmountIn: amount out differs from the chain");
        } else {
            aO = t.y[k];
            require(aO <= B.bmul(pool.bal[o], B.MAX_OUT_RATIO), "ERR_MAX_OUT_RATIO");
            aI = B.calcInGivenOut(pool.bal[i], pool.w[i], pool.bal[o], pool.w[o], aO, pool.fee);
            require(aI <= t.x[k], "ERR_LIMIT_IN");
            require(aI == t.r[k], "swapExactAmountOut: amount in differs from the chain");
        }
        pool.bal[i] = B.badd(pool.bal[i], aI);
        pool.bal[o] = B.bsub(pool.bal[o], aO);
        uint256 afterP = B.calcSpotPrice(pool.bal[i], pool.w[i], pool.bal[o], pool.w[o], pool.fee);
        require(afterP >= before, "ERR_MATH_APPROX");
        require(before <= B.bdiv(aI, aO), "ERR_MATH_APPROX");
    }

    /// BPool.sol:584-618 (joinswapPoolAmountOut). Returns true when every answer rounded toward
    /// the pool exceeds the attacker's own maxAmountIn.
    function _join(Pool memory pool, Call memory c) internal returns (bool blocked) {
        uint256 bI = pool.bal[c.t];
        B.JoinSteps memory s = B.calcSingleInGivenPoolOut(bI, pool.w[c.t], pool.S, pool.tW, c.amt, pool.fee);
        assertEq(s.tokenAmountIn, c.logged, "joinswapPoolAmountOut: tokenAmountIn differs from the chain");
        require(s.tokenAmountIn != 0, "ERR_MATH_APPROX");
        require(s.tokenAmountIn <= c.lim, "ERR_LIMIT_IN");
        require(s.tokenAmountIn <= B.bmul(bI, B.MAX_IN_RATIO), "ERR_MAX_IN_RATIO");
        // 1/w is a whole number in every attacked pool (4, 8, 10): bpow is bpowi alone, the series never runs
        assertEq(s.boo % B.BONE, 0, "bpowApprox ran in a join");

        Alt memory m;
        // BNum's 18-decimal ratio with the amount kept on the 1e-18 grid and rounded up once
        uint256 den = B.BONE - s.zar;
        m.bnum1 = (s.tokenInRatio * bI - bI * B.BONE + den - 1) / den;
        (m.r127, m.r256) = _ideal(true, bI, pool.w[c.t], pool.S, pool.tW, c.amt, pool.fee);
        m.u127 = uint256(FP127Lib.ceil(m.r127) >> 128);
        m.u256 = uint256(FP127Lib.ceil(FP256Lib.toFP127(m.r256)) >> 128);
        assertEq(m.u127, m.u256, "FP127 and FP256 disagree in token units");
        blocked = m.bnum1 > c.lim && m.u127 > c.lim && m.u256 > c.lim;

        _emit(c, JOIN_POOL_OUT, string.concat(_state(pool, c, bI), _kv("dep", s.tokenAmountIn), _kv("poolRatio", s.poolRatio),
            _kv("boo", s.boo), _kv("ratio", s.tokenInRatio), _kv("newBal", s.newTokenBalanceIn),
            _kv("afterFee", s.tokenAmountInAfterFee), _kv("zar", s.zar), _alt(m)));

        pool.bal[c.t] = B.badd(bI, s.tokenAmountIn);
        pool.S = pool.S + c.amt;
    }

    /// BPool.sol:620-656 (exitswapPoolAmountIn). Returns true when the limit was binding (minAmountOut > 0)
    /// and every answer rounded toward the pool falls below it.
    function _exit(Pool memory pool, Call memory c) internal returns (bool blocked) {
        uint256 bO = pool.bal[c.t];
        B.ExitSteps memory s = B.calcSingleOutGivenPoolIn(bO, pool.w[c.t], pool.S, pool.tW, c.amt, pool.fee);
        assertEq(s.tokenAmountOut, c.logged, "exitswapPoolAmountIn: tokenAmountOut differs from the chain");
        require(s.tokenAmountOut >= c.lim, "ERR_LIMIT_OUT");
        require(s.tokenAmountOut <= B.bmul(bO, B.MAX_OUT_RATIO), "ERR_MAX_OUT_RATIO");
        assertEq(s.boo % B.BONE, 0, "bpowApprox ran in an exit");

        Alt memory m;
        m.bnum1 = (bO * B.BONE - s.tokenOutRatio * bO) * (B.BONE - s.zaz) / (B.BONE * B.BONE);
        (m.r127, m.r256) = _ideal(false, bO, pool.w[c.t], pool.S, pool.tW, c.amt, pool.fee);
        m.u127 = uint256(FP127Lib.floor(m.r127) >> 128);
        m.u256 = uint256(FP127Lib.floor(FP256Lib.toFP127(m.r256)) >> 128);
        assertEq(m.u127, m.u256, "FP127 and FP256 disagree in token units");
        blocked = c.lim > 0 && m.bnum1 < c.lim && m.u127 < c.lim && m.u256 < c.lim;
        // the dust exits (one token unit out, minAmountOut = 1) are each worth about half a unit
        if (c.lim > 0) assertTrue(blocked, "a dust exit would still pay");

        _emit(c, EXIT_POOL_IN, string.concat(_state(pool, c, bO), _kv("dep", s.tokenAmountOut), _kv("poolRatio", s.poolRatio),
            _kv("boo", s.boo), _kv("ratio", s.tokenOutRatio), _kv("newBal", s.newTokenBalanceOut),
            _kv("beforeFee", s.tokenAmountOutBeforeSwapFee), _kv("zar", s.zaz), _alt(m)));

        pool.bal[c.t] = B.bsub(bO, s.tokenAmountOut);
        pool.S = B.bsub(pool.S, c.amt - B.bmul(c.amt, B.EXIT_FEE));
    }

    function _state(Pool memory pool, Call memory c, uint256 bal) internal pure returns (string memory) {
        return string.concat(_kv("bal", bal), _kv("P", c.amt), _kv("S", pool.S), _kv("w", pool.w[c.t]), _kv("tW", pool.tW),
            _kv("fee", pool.fee), _kv("lim", c.lim));
    }

    function _alt(Alt memory m) internal pure returns (string memory) {
        return string.concat(_kv("bnum1", m.bnum1), _kvi("fp127", m.r127), _kv("fp127u", m.u127), _kvi("fp256", m.r256),
            _kv("fp256u", m.u256));
    }

    /// BPool.sol:392-420 (exitPool): proportional exit, asserted token by token.
    function _exitPool(uint256 p, Pool memory pool, uint256 pAi) internal view {
        uint256[] memory out = _uints(_key(p, "tape.exitPoolOut"));
        uint256[] memory mins = _uints(_key(p, "tape.exitPoolMin"));
        uint256 ratio = B.bdiv(B.bsub(pAi, B.bmul(pAi, B.EXIT_FEE)), pool.S);
        require(ratio != 0, "ERR_MATH_APPROX");
        pool.S = B.bsub(pool.S, pAi);
        for (uint256 k; k < pool.bal.length; k++) {
            uint256 aO = B.bmul(ratio, pool.bal[k]);
            require(aO != 0 && aO >= mins[k], "ERR_LIMIT_OUT");
            require(aO == out[k], "exitPool: amount out differs from the chain");
            pool.bal[k] = B.bsub(pool.bal[k], aO);
        }
    }

    /// The stated formula (BMath.sol:146-155 and :184-194) in FP127 and FP256, as raw words:
    /// join: bI * ((1 + pAo/pS)^(tW/wI) - 1) / (1 - (1 - wI/tW) * sF)
    /// exit: bO * (1 - (1 - pAi/pS)^(tW/wO)) * (1 - (1 - wO/tW) * sF)     (EXIT_FEE = 0)
    /// The power is written expm1(y * log1p(x)) so nothing cancels at small pAo/pS.
    function _ideal(bool join, uint256 b, uint256 w, uint256 pS, uint256 tW, uint256 pA, uint256 fee)
        internal
        pure
        returns (int256 r127, int256 r256)
    {
        {
            int256 x = FP127Lib.div(_u(pA), _u(pS));
            int256 y = FP127Lib.div(_u(tW), _u(w));
            int256 f = FP127Lib.mul(FP127Lib.sub(ONE127, FP127Lib.div(_u(w), _u(tW))), FP127Lib.div(_u(fee), _u(1e18)));
            if (join) {
                int256 g = FP127Lib.expm1(FP127Lib.mul(y, FP127Lib.log1p(x)));
                r127 = FP127Lib.div(FP127Lib.mul(_u(b), g), FP127Lib.sub(ONE127, f));
            } else {
                int256 g = FP127Lib.neg(FP127Lib.expm1(FP127Lib.mul(y, FP127Lib.log1p(FP127Lib.neg(x)))));
                r127 = FP127Lib.mul(FP127Lib.mul(_u(b), g), FP127Lib.sub(ONE127, f));
            }
        }
        {
            int256 x = FP256Lib.div(FP256Lib.fromUint(pA), FP256Lib.fromUint(pS));
            int256 y = FP256Lib.div(FP256Lib.fromUint(tW), FP256Lib.fromUint(w));
            int256 f = FP256Lib.mul(FP256Lib.sub(FP256Lib.ONE, FP256Lib.div(FP256Lib.fromUint(w), FP256Lib.fromUint(tW))),
                FP256Lib.div(FP256Lib.fromUint(fee), FP256Lib.fromUint(1e18)));
            if (join) {
                int256 g = FP256Lib.expm1(FP256Lib.mul(y, FP256Lib.log1p(x)));
                r256 = FP256Lib.div(FP256Lib.mul(FP256Lib.fromUint(b), g), FP256Lib.sub(FP256Lib.ONE, f));
            } else {
                int256 g = FP256Lib.neg(FP256Lib.expm1(FP256Lib.mul(y, FP256Lib.log1p(FP256Lib.neg(x)))));
                r256 = FP256Lib.mul(FP256Lib.mul(FP256Lib.fromUint(b), g), FP256Lib.sub(FP256Lib.ONE, f));
            }
        }
    }

    function _u(uint256 x) internal pure returns (int256) {
        return int256(x) << 128;
    }

    function _emit(Call memory c, uint256 kind, string memory kv) internal pure {
        console.log(string.concat("BAL|", vm.toString(c.p), "|", vm.toString(c.k), "|", vm.toString(kind), "|", kv));
    }

    function _kv(string memory k, uint256 v) internal pure returns (string memory) {
        return string.concat(k, "=", vm.toString(v), ";");
    }

    function _kvi(string memory k, int256 v) internal pure returns (string memory) {
        return string.concat(k, "=", vm.toString(v), ";");
    }

    // ---- The decisive step, by hand ------------------------------------------------------------

    /// Pool 0x2257aaac...ac57 (DPI/USDC/WETH/WBTC, 25% each, swap fee 0.5%), tx 0x72510b25...,
    /// call 53 of 290 (LOG_CALL at log index 0x13a), the first join against a WBTC balance of
    /// 3 satoshi: the attacker asks for 0.6896 BPT of a 6.4645 BPT supply (10.67%) with
    /// maxAmountIn = 1. test_decisive_join_matches_the_replay checks these integers are the
    /// replay's state at that call.
    uint256 constant DECISIVE_OP = 53;
    uint256 constant DECISIVE_BAL = 3;
    uint256 constant DECISIVE_SUPPLY = 6464513554335253717;
    uint256 constant DECISIVE_POOL_OUT = 689646715905234062;

    function test_decisive_join() public pure {
        uint256 w = 12.5e18;
        uint256 tW = 50e18;
        uint256 fee = 0.005e18;
        B.JoinSteps memory s = B.calcSingleInGivenPoolOut(DECISIVE_BAL, w, DECISIVE_SUPPLY, tW, DECISIVE_POOL_OUT, fee);
        // boo = 1/0.25 = 4 exactly: bpow(poolRatio, 4e18) is bpowi; bpowApprox is never called
        assertEq(s.boo, 4e18);
        assertEq(s.poolRatio, 1106681919700321592);
        // poolRatio^4 on BNum's grid is 1.499999999999999997: three satoshi times that is
        // 4.499999999999999991, which bmul rounds half up to 4 satoshi, not 5
        assertEq(s.tokenInRatio, 1499999999999999997);
        assertEq(s.newTokenBalanceIn, 4);
        assertEq(s.tokenAmountInAfterFee, 1);
        assertEq(s.zar, 0.00375e18);
        assertEq(s.tokenAmountIn, 1); // bdiv(1, 0.99625) = 1.0038 -> 1 satoshi
        // rounded toward the pool once, BNum's own ratio already asks for 2
        uint256 num = s.tokenInRatio * DECISIVE_BAL - DECISIVE_BAL * 1e18;
        assertEq((num + (1e18 - s.zar) - 1) / (1e18 - s.zar), 2);
        (int256 r127, int256 r256) = _ideal(true, DECISIVE_BAL, w, DECISIVE_SUPPLY, tW, DECISIVE_POOL_OUT, fee);
        // exact: 1.5056461731493099... satoshi; toward the pool: 2 > maxAmountIn = 1 -> ERR_LIMIT_IN
        assertGt(r127, (int256(3) << 128) / 2);
        assertEq(FP127Lib.ceil(r127) >> 128, 2);
        assertEq(FP127Lib.ceil(FP256Lib.toFP127(r256)) >> 128, 2);
    }

    // ---- Precision or direction? -----------------------------------------------------------------

    /// The same starting state as the decisive join, with the attacker re-tuned to each rounding
    /// rule (scripts/replays/balancer_v1.py score solves for these amounts at 200 digits and checks
    /// they equal the constants below). Under "nearest, once" the pool computes the exact formula
    /// (FP127 or FP256, 37+ digits) and rounds the token amount to the nearest unit at the end; the
    /// attacker asks for just under 1.5 units' worth on the join and just over 0.5 on the exit.
    uint256 constant NEAREST_JOIN_P = 687409992083284011;
    uint256 constant NEAREST_EXIT_P = 235740524732716483;
    /// Toward the pool (ceil in, floor out): the most BPT one unit buys, the least BPT that one unit costs.
    uint256 constant TOWARD_JOIN_P = 480429659539467039;
    uint256 constant TOWARD_EXIT_P = 483973556600802202;

    function test_precision_without_direction_still_pays() public pure {
        uint256 w = 12.5e18;
        uint256 tW = 50e18;
        uint256 fee = 0.005e18;
        // join at 3 satoshi: 1.4999999999999999982 satoshi, rounded to nearest once -> 1 (pays maxAmountIn = 1)
        (int256 j127, int256 j256) = _ideal(true, DECISIVE_BAL, w, DECISIVE_SUPPLY, tW, NEAREST_JOIN_P, fee);
        assertEq(FP127Lib.round(j127) >> 128, 1);
        assertEq(FP127Lib.round(FP256Lib.toFP127(j256)) >> 128, 1);
        assertEq(FP127Lib.ceil(j127) >> 128, 2); // toward the pool it would not
        // exit at 4 satoshi from the supply after that join: just over 0.5 satoshi, to nearest -> 1 (pays minAmountOut = 1)
        uint256 s2 = DECISIVE_SUPPLY + NEAREST_JOIN_P;
        (int256 x127, int256 x256) = _ideal(false, 4, w, s2, tW, NEAREST_EXIT_P, fee);
        assertEq(FP127Lib.round(x127) >> 128, 1);
        assertEq(FP127Lib.round(FP256Lib.toFP127(x256)) >> 128, 1);
        assertEq(FP127Lib.floor(x127) >> 128, 0); // toward the pool it would not
        // one cycle: balance back to 3 satoshi, the attacker 0.4517 BPT richer (6.99% of the supply)
        assertGt(NEAREST_JOIN_P, NEAREST_EXIT_P);
        assertEq(NEAREST_JOIN_P - NEAREST_EXIT_P, 451669467350567528);
    }

    function test_direction_closes_the_loop() public pure {
        uint256 w = 12.5e18;
        uint256 tW = 50e18;
        uint256 fee = 0.005e18;
        (int256 j127,) = _ideal(true, DECISIVE_BAL, w, DECISIVE_SUPPLY, tW, TOWARD_JOIN_P, fee);
        assertEq(FP127Lib.ceil(j127) >> 128, 1); // the most one satoshi buys...
        (j127,) = _ideal(true, DECISIVE_BAL, w, DECISIVE_SUPPLY, tW, TOWARD_JOIN_P + 1, fee);
        assertEq(FP127Lib.ceil(j127) >> 128, 2); // ...one wei more costs two
        uint256 s2 = DECISIVE_SUPPLY + TOWARD_JOIN_P;
        (int256 x127,) = _ideal(false, 4, w, s2, tW, TOWARD_EXIT_P, fee);
        assertEq(FP127Lib.floor(x127) >> 128, 1); // the least BPT that pays one satoshi out...
        (x127,) = _ideal(false, 4, w, s2, tW, TOWARD_EXIT_P - 1, fee);
        assertEq(FP127Lib.floor(x127) >> 128, 0); // ...one wei less pays nothing
        // one cycle now costs the attacker BPT: the swap fee is kept, nothing is given away
        assertLt(TOWARD_JOIN_P, TOWARD_EXIT_P);
    }

    function test_decisive_join_matches_the_replay() public view {
        (Pool memory pool, Tape memory t) = _load(0);
        for (uint256 k; k < DECISIVE_OP; k++) {
            if (t.kind[k] == SWAP_IN || t.kind[k] == SWAP_OUT) {
                _swap(pool, t, k);
            } else if (t.kind[k] == JOIN_POOL_OUT) {
                pool.bal[t.i[k]] += t.r[k];
                pool.S += t.x[k];
            } else if (t.kind[k] == EXIT_POOL_IN) {
                pool.bal[t.i[k]] -= t.r[k];
                pool.S -= t.x[k];
            }
        }
        assertEq(t.kind[DECISIVE_OP], JOIN_POOL_OUT);
        assertEq(t.i[DECISIVE_OP], 3); // WBTC
        assertEq(t.y[DECISIVE_OP], 1); // maxAmountIn
        assertEq(t.r[DECISIVE_OP], 1); // LOG_JOIN tokenAmountIn
        assertEq(pool.bal[3], DECISIVE_BAL);
        assertEq(pool.S, DECISIVE_SUPPLY);
        assertEq(t.x[DECISIVE_OP], DECISIVE_POOL_OUT);
    }
}
