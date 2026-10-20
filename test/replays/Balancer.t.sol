// SPDX-License-Identifier: MIT
// Transcribes Balancer V2 arithmetic from the verified pool source; every function cites its file:lines (see BalancerV2 below).
pragma solidity ^0.8.24;

import "forge-std/Test.sol";
import {FP127Lib} from "../../contracts/src/fp127/FP127Lib.sol";
import {FP256Lib} from "../../contracts/src/fp256/FP256Lib.sol";

/// @notice Balancer V2 ComposableStablePool v5 swap arithmetic, transcribed from the source verified on
///         Etherscan for both attacked pools (0xDACf5Fa19b1f720111609043ac67A9818262850c osETH/WETH and
///         0x93d199263632a4ef4bb438f1feb99e57b4b5f0bd wstETH/WETH; the files are byte-identical, sha256 in
///         scripts/replays/balancer.json). Line numbers are in that verified standard-JSON input:
///           BaseGeneralPool.sol:68-85        _swapGivenOut (upscale, _onSwapGivenOut, downscaleUp, fee)
///           ComposableStablePool.sol:279-299 _onRegularSwap (drop BPT, invariant, _calcInGivenOut)
///           BasePool.sol:618-621             _addSwapFeeAmount  amount.divUp(fee.complement())
///           BasePool.sol:680-686             _upscale           FixedPoint.mulDown(amount, scalingFactor)
///           BasePool.sol:692-699             _upscaleArray      mulDown per balance
///           BasePool.sol:726-728             _downscaleUp       FixedPoint.divUp
///           StableMath.sol:57-120            _calculateInvariant
///           StableMath.sol:164-199           _calcInGivenOut
///           StableMath.sol:399-449           _getTokenBalanceGivenInvariantAndAllOtherBalances
///           FixedPoint.sol:48-53, 55-70, 85-102, 158-160  mulDown, mulUp, divUp, complement
///           Math.sol:88-96                   divUp
///         The original is Solidity 0.7.1, where the raw `*` and `-` in StableMath do not check; here they
///         are checked, which changes nothing unless they would have wrapped (none does on these inputs).
///         The only additions are iteration counters and the `up` switch (mulDown as deployed, mulUp as V3).
library BalancerV2 {
    uint256 internal constant ONE = 1e18;
    uint256 internal constant AMP_PRECISION = 1e3;

    function mulDown(uint256 a, uint256 b) internal pure returns (uint256) {
        return (a * b) / ONE;
    }

    function mulUp(uint256 a, uint256 b) internal pure returns (uint256) {
        uint256 product = a * b;
        return product == 0 ? 0 : ((product - 1) / ONE) + 1;
    }

    function fdivUp(uint256 a, uint256 b) internal pure returns (uint256) {
        require(b != 0, "ZERO_DIVISION");
        return a == 0 ? 0 : ((a * ONE - 1) / b) + 1;
    }

    function divUp(uint256 a, uint256 b) internal pure returns (uint256) {
        require(b != 0, "ZERO_DIVISION");
        return a == 0 ? 0 : 1 + (a - 1) / b;
    }

    function calculateInvariant(uint256 amp, uint256[] memory balances)
        internal
        pure
        returns (uint256 inv, uint256 iters)
    {
        uint256 sum = 0;
        uint256 numTokens = balances.length;
        for (uint256 i = 0; i < numTokens; i++) {
            sum += balances[i];
        }
        if (sum == 0) return (0, 0);
        uint256 prevInvariant;
        inv = sum;
        uint256 ampTimesTotal = amp * numTokens;
        for (uint256 i = 0; i < 255; i++) {
            uint256 D_P = inv;
            for (uint256 j = 0; j < numTokens; j++) {
                D_P = (D_P * inv) / (balances[j] * numTokens);
            }
            prevInvariant = inv;
            inv = (((ampTimesTotal * sum) / AMP_PRECISION + D_P * numTokens) * inv)
                / (((ampTimesTotal - AMP_PRECISION) * inv) / AMP_PRECISION + (numTokens + 1) * D_P);
            if (inv > prevInvariant) {
                if (inv - prevInvariant <= 1) return (inv, i + 1);
            } else if (prevInvariant - inv <= 1) {
                return (inv, i + 1);
            }
        }
        revert("STABLE_INVARIANT_DIDNT_CONVERGE");
    }

    function getTokenBalance(uint256 amp, uint256[] memory balances, uint256 inv, uint256 tokenIndex)
        internal
        pure
        returns (uint256 tokenBalance, uint256 iters)
    {
        uint256 ampTimesTotal = amp * balances.length;
        uint256 sum = balances[0];
        uint256 P_D = balances[0] * balances.length;
        for (uint256 j = 1; j < balances.length; j++) {
            P_D = (P_D * balances[j] * balances.length) / inv;
            sum += balances[j];
        }
        sum = sum - balances[tokenIndex];
        uint256 inv2 = inv * inv;
        uint256 c = divUp(inv2, ampTimesTotal * P_D) * AMP_PRECISION * balances[tokenIndex];
        uint256 b = sum + (inv / ampTimesTotal) * AMP_PRECISION;
        uint256 prevTokenBalance = 0;
        tokenBalance = divUp(inv2 + c, inv + b);
        for (uint256 i = 0; i < 255; i++) {
            prevTokenBalance = tokenBalance;
            tokenBalance = divUp(tokenBalance * tokenBalance + c, tokenBalance * 2 + b - inv);
            if (tokenBalance > prevTokenBalance) {
                if (tokenBalance - prevTokenBalance <= 1) return (tokenBalance, i + 1);
            } else if (prevTokenBalance - tokenBalance <= 1) {
                return (tokenBalance, i + 1);
            }
        }
        revert("STABLE_GET_BALANCE_DIDNT_CONVERGE");
    }
}

/// @title Balancer
/// @notice Replays the micro-swap phase of the Balancer V2 exploit (Ethereum tx
///         0x6ed07db1a9fe5c0794d44cd36081d6a6df103fab868cdd75d581e3bd23bc9742, block 23717397) from the integers
///         committed in scripts/replays/balancer.json (no network). Each pool's phase is every swap of the
///         attack's batchSwap that involves neither BPT: osETH/WETH swaps 22-111 (30 cycles), wstETH/WETH
///         swaps 22-96 (25 cycles), all GIVEN_OUT.
///         - deployed: every on-chain onSwap return is reproduced bit for bit from that call's own inputs, and
///           the attacker's plan replayed from the first balances reproduces the whole on-chain sequence;
///         - mulUp: the same calls (each on its own on-chain balances) with the given-out amount upscaled by
///           mulUp (Balancer V3's direction); asserted equal to scripts/replays/balancer.py's port;
///         - fp127 / fp256: the same calls with the upscaled amounts and the pool maths in FP127 / FP256, the
///           same Newton maps stopped on the format's own grid, and one ceil to token wei at the end (the pool's
///           favour); asserted equal to the exact-rational charge scripts/replays/balancer.py commits.
///         Every call prints  BAL|<pool>|<model>|<swap>|k=v;...  for balancer.py to score.
contract Balancer is Test {
    string internal constant JSON = "scripts/replays/balancer.json";
    int256 internal constant ONE127 = int256(1) << 128;

    struct Pool {
        string name;
        uint256[3] sf;
        uint256 amp;
        uint256 fee;
        uint256 bpt;
        uint256 leave;
        uint256 first;
        uint256[] i;
        uint256[] j;
        uint256[] amount;
        uint256[] plan;
        uint256[] amountIn;
        uint256[][3] bal;
    }

    struct Step {
        uint256 amountIn;
        uint256 out;
        uint256 itD;
        uint256 itY;
        int256 D;
        int256 y;
        int256 b0;
        int256 b1;
        int256 other;
        uint256 howD;
        uint256 howY;
        uint256 litD;
        uint256 litY;
    }

    // ------------------------------------------------------------------ loading

    function _u(string memory json, string memory key) internal pure returns (uint256) {
        return vm.parseUint(vm.parseJsonString(json, key));
    }

    function _ua(string memory json, string memory key) internal pure returns (uint256[] memory r) {
        string[] memory s = vm.parseJsonStringArray(json, key);
        r = new uint256[](s.length);
        for (uint256 k = 0; k < s.length; k++) {
            r[k] = vm.parseUint(s[k]);
        }
    }

    function _load(string memory name) internal view returns (Pool memory p) {
        string memory json = vm.readFile(JSON);
        string memory b = string.concat(".test.", name, ".");
        p.name = name;
        uint256[] memory sf = _ua(json, string.concat(b, "sf"));
        p.sf = [sf[0], sf[1], sf[2]];
        p.amp = _u(json, string.concat(b, "amp"));
        p.fee = _u(json, string.concat(b, "fee"));
        p.bpt = _u(json, string.concat(b, "bpt"));
        p.leave = _u(json, string.concat(b, "leave"));
        p.first = _u(json, string.concat(b, "first"));
        p.i = _ua(json, string.concat(b, "i"));
        p.j = _ua(json, string.concat(b, "j"));
        p.amount = _ua(json, string.concat(b, "amount"));
        p.plan = _ua(json, string.concat(b, "plan"));
        p.amountIn = _ua(json, string.concat(b, "amountIn"));
        p.bal[0] = _ua(json, string.concat(b, "bal0"));
        p.bal[1] = _ua(json, string.concat(b, "bal1"));
        p.bal[2] = _ua(json, string.concat(b, "bal2"));
    }

    function _expect(string memory name, string memory key) internal view returns (uint256[] memory) {
        return _ua(vm.readFile(JSON), string.concat(".test.", name, ".", key));
    }

    function _start(Pool memory p) internal pure returns (uint256[3] memory raw) {
        raw = [p.bal[0][0], p.bal[1][0], p.bal[2][0]];
    }

    // ------------------------------------------------------------------ the deployed swap (and its mulUp twin)

    /// BaseGeneralPool._swapGivenOut -> ComposableStablePool._onRegularSwap -> StableMath._calcInGivenOut.
    function _swapDeployed(Pool memory p, uint256[3] memory raw, uint256 i, uint256 j, uint256 amount, bool up)
        internal
        pure
        returns (Step memory s)
    {
        uint256[] memory bal = new uint256[](2);
        uint256 n = 0;
        for (uint256 k = 0; k < 3; k++) {
            if (k == p.bpt) continue;
            bal[n++] = BalancerV2.mulDown(raw[k], p.sf[k]); // _upscaleArray
        }
        uint256 a = up ? BalancerV2.mulUp(amount, p.sf[j]) : BalancerV2.mulDown(amount, p.sf[j]); // _upscale
        uint256 ii = i > p.bpt ? i - 1 : i;
        j = j > p.bpt ? j - 1 : j;
        uint256 D;
        uint256 y;
        (D, s.itD) = BalancerV2.calculateInvariant(p.amp, bal);
        bal[j] -= a;
        (y, s.itY) = BalancerV2.getTokenBalance(p.amp, bal, D, ii);
        bal[j] += a;
        s.amountIn = y - bal[ii] + 1; // _calcInGivenOut
        s.amountIn = BalancerV2.fdivUp(s.amountIn, p.sf[i]); // _downscaleUp
        s.amountIn = BalancerV2.fdivUp(s.amountIn, BalancerV2.ONE - p.fee); // _addSwapFeeAmount
        s.out = amount;
        s.D = int256(D);
        s.y = int256(y);
    }

    // ------------------------------------------------------------------ FP127: the same Newton maps, FP127's grid

    function _abs(int256 x) internal pure returns (int256) {
        return x < 0 ? -x : x;
    }

    // The stopping rule. StableMath stops when two iterates differ by <= 1 on its grid (1 wei of the 18-decimal
    // upscaled amount). Here the grid is the format's: <= 1 unit (2^-128 wei in FP127, one ulp in FP256). That
    // literal rule assumes the Newton map, evaluated in the format, is quiet to within one unit near the root;
    // in a format with 2^-128 resolution it is not (D times a ratio carries D * 2^-128 of noise), so the
    // iteration also stops when it has stalled: the step no longer shrinks, and is already below 2^-64 of the
    // iterate in FP127 (2^-128 in FP256). `how` records which rule fired (0 grid, 1 stall); `literal` runs the
    // literal rule alone and returns 0 iterations if it has not stopped after 255 (StableMath's cap).

    struct Solve {
        int256 x;
        uint256 it;
        uint256 how;
    }

    function _stop127(int256 x, int256 prev, int256 dPrev, uint256 it, bool literal)
        internal
        pure
        returns (bool, uint256, int256)
    {
        int256 d = _abs(x - prev);
        if (d <= 1) return (true, 0, d);
        if (!literal && it >= 3 && d >= dPrev && d <= (_abs(x) >> 64)) return (true, 1, d);
        return (false, 0, d);
    }

    /// StableMath._calculateInvariant's Newton map in FP127, values in 18-decimal wei. The algebra is the
    /// original's, D' = D (A S + n D_P) / ((A - 1) D + (n + 1) D_P), with D_P = D (D / n b0) (D / n b1); the
    /// products are reordered only so that no intermediate exceeds FP127's 2^127.
    function _inv127(int256 annP, int256 b0, int256 b1, bool literal) internal pure returns (Solve memory r) {
        int256 N = int256(2) << 128;
        int256 S = FP127Lib.add(b0, b1);
        int256 aS = FP127Lib.mul(annP, S);
        int256 aD = FP127Lib.sub(annP, ONE127);
        r.x = S;
        int256 dPrev = type(int256).max;
        for (r.it = 1; r.it <= 255; r.it++) {
            int256 DP = FP127Lib.mul(
                FP127Lib.mul(r.x, FP127Lib.div(r.x, FP127Lib.mul(b0, N))), FP127Lib.div(r.x, FP127Lib.mul(b1, N))
            );
            int256 prev = r.x;
            r.x = FP127Lib.mul(
                r.x,
                FP127Lib.div(
                    FP127Lib.add(aS, FP127Lib.mul(DP, N)),
                    FP127Lib.add(FP127Lib.mul(aD, r.x), FP127Lib.mul(int256(3) << 128, DP))
                )
            );
            bool stop;
            (stop, r.how, dPrev) = _stop127(r.x, prev, dPrev, r.it, literal);
            if (stop) return r;
        }
        if (!literal) revert("FP127 invariant did not converge");
        r.it = 0;
    }

    /// StableMath._getTokenBalanceGivenInvariantAndAllOtherBalances's map in FP127 (n = 2): y' = (y^2 + c) /
    /// (2y + b - D), c = D^2 bk / (A P_D) = D^3 / (4 A other), b = other + D / A, the first iterate (D^2 + c) / (D + b).
    function _bal127(int256 annP, int256 bk, int256 other, int256 D, bool literal)
        internal
        pure
        returns (Solve memory r)
    {
        int256 N = int256(2) << 128;
        int256 PD = FP127Lib.div(FP127Lib.mul(FP127Lib.mul(FP127Lib.mul(bk, N), other), N), D);
        int256 inv2 = FP127Lib.mul(D, D);
        int256 c = FP127Lib.mul(FP127Lib.div(inv2, FP127Lib.mul(annP, PD)), bk);
        int256 b = FP127Lib.sub(FP127Lib.add(other, FP127Lib.div(D, annP)), D);
        r.x = FP127Lib.div(FP127Lib.add(inv2, c), FP127Lib.add(FP127Lib.add(b, D), D));
        int256 dPrev = type(int256).max;
        for (r.it = 1; r.it <= 255; r.it++) {
            int256 prev = r.x;
            r.x = FP127Lib.div(FP127Lib.add(FP127Lib.mul(r.x, r.x), c), FP127Lib.add(FP127Lib.mul(r.x, N), b));
            bool stop;
            (stop, r.how, dPrev) = _stop127(r.x, prev, dPrev, r.it, literal);
            if (stop) return r;
        }
        if (!literal) revert("FP127 balance did not converge");
        r.it = 0;
    }

    function _swap127(Pool memory p, uint256[3] memory raw, uint256 i, uint256 j, uint256 amount)
        internal
        pure
        returns (Step memory s)
    {
        // the rates and the upscaled balances, exact to 2^-128 wei (no 1e-18 grid in between)
        int256[3] memory q;
        int256[2] memory b;
        uint256 n = 0;
        for (uint256 k = 0; k < 3; k++) {
            q[k] = FP127Lib.fromFixed18(int256(p.sf[k]));
            if (k == p.bpt) continue;
            b[n++] = FP127Lib.mul(int256(raw[k]) << 128, q[k]);
        }
        s.b0 = b[0];
        s.b1 = b[1];
        s.out = amount;
        int256 annP = FP127Lib.div(int256(p.amp * 2) << 128, int256(BalancerV2.AMP_PRECISION) << 128);
        Solve memory r = _inv127(annP, b[0], b[1], false);
        (s.D, s.itD, s.howD) = (r.x, r.it, r.how);
        s.litD = _inv127(annP, b[0], b[1], true).it;
        s.other = FP127Lib.sub(b[j > p.bpt ? j - 1 : j], FP127Lib.mul(int256(amount) << 128, q[j]));
        int256 bIn = b[i > p.bpt ? i - 1 : i];
        r = _bal127(annP, bIn, s.other, s.D, false);
        (s.y, s.itY, s.howY) = (r.x, r.it, r.how);
        s.litY = _bal127(annP, bIn, s.other, s.D, true).it;
        s.amountIn = _charge127(FP127Lib.div(FP127Lib.sub(s.y, bIn), q[i]), p.fee);
    }

    /// amount / (1 - fee), then one ceil to token wei: the only rounding to the wei grid, in the pool's favour.
    function _charge127(int256 tokens, uint256 fee) internal pure returns (uint256) {
        int256 gross = FP127Lib.div(tokens, FP127Lib.sub(ONE127, FP127Lib.fromFixed18(int256(fee))));
        return uint256(FP127Lib.ceil(gross) >> 128);
    }

    // ------------------------------------------------------------------ FP256: the same, FP256's grid

    /// One unit in the last place of a positive FP256 word.
    function _ulp256(int256 x) internal pure returns (int256) {
        uint256 e = (uint256(x) >> 236) & 0x7ffff;
        return int256((e - 236) << 236);
    }

    /// x * 2^-k for a positive FP256 word (exact: the exponent field only).
    function _shr256(int256 x, uint256 k) internal pure returns (int256) {
        return int256(uint256(x) - (k << 236));
    }

    function _stop256(int256 x, int256 prev, int256 dPrev, uint256 it, bool literal)
        internal
        pure
        returns (bool, uint256, int256)
    {
        int256 d = FP256Lib.abs(FP256Lib.sub(x, prev));
        if (FP256Lib.cmp(d, _ulp256(x)) <= 0) return (true, 0, d);
        if (!literal && it >= 3 && FP256Lib.cmp(d, dPrev) >= 0 && FP256Lib.cmp(d, _shr256(x, 128)) <= 0) {
            return (true, 1, d);
        }
        return (false, 0, d);
    }

    /// Smallest integer >= x for a positive FP256 word.
    function _ceil256(int256 x) internal pure returns (uint256) {
        uint256 w = uint256(x);
        uint256 e = (w >> 236) & 0x7ffff;
        uint256 m = (w & ((uint256(1) << 236) - 1)) | (uint256(1) << 236);
        if (e >= 262143 + 236) return m << (e - 262143 - 236);
        uint256 r = 262143 + 236 - e;
        if (r > 237) return 1;
        uint256 q = m >> r;
        return (m & ((uint256(1) << r) - 1)) == 0 ? q : q + 1;
    }

    /// The FP127 maps above, op for op, on FP256.
    function _inv256(int256 annP, int256 b0, int256 b1, bool literal) internal pure returns (Solve memory r) {
        int256 N = FP256Lib.fromUint(2);
        int256 S = FP256Lib.add(b0, b1);
        int256 aS = FP256Lib.mul(annP, S);
        int256 aD = FP256Lib.sub(annP, FP256Lib.ONE);
        r.x = S;
        int256 dPrev = type(int256).max;
        for (r.it = 1; r.it <= 255; r.it++) {
            int256 DP = FP256Lib.mul(
                FP256Lib.mul(r.x, FP256Lib.div(r.x, FP256Lib.mul(b0, N))), FP256Lib.div(r.x, FP256Lib.mul(b1, N))
            );
            int256 prev = r.x;
            r.x = FP256Lib.mul(
                r.x,
                FP256Lib.div(
                    FP256Lib.add(aS, FP256Lib.mul(DP, N)),
                    FP256Lib.add(FP256Lib.mul(aD, r.x), FP256Lib.mul(FP256Lib.fromUint(3), DP))
                )
            );
            bool stop;
            (stop, r.how, dPrev) = _stop256(r.x, prev, dPrev, r.it, literal);
            if (stop) return r;
        }
        if (!literal) revert("FP256 invariant did not converge");
        r.it = 0;
    }

    function _bal256(int256 annP, int256 bk, int256 other, int256 D, bool literal)
        internal
        pure
        returns (Solve memory r)
    {
        int256 N = FP256Lib.fromUint(2);
        int256 PD = FP256Lib.div(FP256Lib.mul(FP256Lib.mul(FP256Lib.mul(bk, N), other), N), D);
        int256 inv2 = FP256Lib.mul(D, D);
        int256 c = FP256Lib.mul(FP256Lib.div(inv2, FP256Lib.mul(annP, PD)), bk);
        int256 b = FP256Lib.sub(FP256Lib.add(other, FP256Lib.div(D, annP)), D);
        r.x = FP256Lib.div(FP256Lib.add(inv2, c), FP256Lib.add(FP256Lib.add(b, D), D));
        int256 dPrev = type(int256).max;
        for (r.it = 1; r.it <= 255; r.it++) {
            int256 prev = r.x;
            r.x = FP256Lib.div(FP256Lib.add(FP256Lib.mul(r.x, r.x), c), FP256Lib.add(FP256Lib.mul(r.x, N), b));
            bool stop;
            (stop, r.how, dPrev) = _stop256(r.x, prev, dPrev, r.it, literal);
            if (stop) return r;
        }
        if (!literal) revert("FP256 balance did not converge");
        r.it = 0;
    }

    function _swap256(Pool memory p, uint256[3] memory raw, uint256 i, uint256 j, uint256 amount)
        internal
        pure
        returns (Step memory s)
    {
        int256[3] memory q;
        int256[2] memory b;
        uint256 n = 0;
        for (uint256 k = 0; k < 3; k++) {
            q[k] = FP256Lib.fromFixed18(int256(p.sf[k]));
            if (k == p.bpt) continue;
            b[n++] = FP256Lib.mul(FP256Lib.fromUint(raw[k]), q[k]);
        }
        s.b0 = b[0];
        s.b1 = b[1];
        s.out = amount;
        int256 annP = FP256Lib.div(FP256Lib.fromUint(p.amp * 2), FP256Lib.fromUint(BalancerV2.AMP_PRECISION));
        Solve memory r = _inv256(annP, b[0], b[1], false);
        (s.D, s.itD, s.howD) = (r.x, r.it, r.how);
        s.litD = _inv256(annP, b[0], b[1], true).it;
        s.other = FP256Lib.sub(b[j > p.bpt ? j - 1 : j], FP256Lib.mul(FP256Lib.fromUint(amount), q[j]));
        int256 bIn = b[i > p.bpt ? i - 1 : i];
        r = _bal256(annP, bIn, s.other, s.D, false);
        (s.y, s.itY, s.howY) = (r.x, r.it, r.how);
        s.litY = _bal256(annP, bIn, s.other, s.D, true).it;
        s.amountIn = _charge256(FP256Lib.div(FP256Lib.sub(s.y, bIn), q[i]), p.fee);
    }

    function _charge256(int256 tokens, uint256 fee) internal pure returns (uint256) {
        return _ceil256(FP256Lib.div(tokens, FP256Lib.sub(FP256Lib.ONE, FP256Lib.fromFixed18(int256(fee)))));
    }

    // ------------------------------------------------------------------ one call, under a model

    enum Model {
        Deployed,
        MulUp,
        FP127,
        FP256
    }

    function _swap(Pool memory p, Model m, uint256[3] memory raw, uint256 i, uint256 j, uint256 amount)
        internal
        pure
        returns (Step memory)
    {
        if (m == Model.Deployed) return _swapDeployed(p, raw, i, j, amount, false);
        if (m == Model.MulUp) return _swapDeployed(p, raw, i, j, amount, true);
        if (m == Model.FP127) return _swap127(p, raw, i, j, amount);
        return _swap256(p, raw, i, j, amount);
    }

    function _log(Pool memory p, string memory model, uint256 t, Step memory s, bool words) internal pure {
        string memory line = string.concat(
            "BAL|",
            p.name,
            "|",
            model,
            "|",
            vm.toString(p.first + t),
            "|in=",
            vm.toString(s.amountIn),
            ";out=",
            vm.toString(s.out),
            ";itD=",
            vm.toString(s.itD),
            ";itY=",
            vm.toString(s.itY)
        );
        if (words) {
            line = string.concat(
                line,
                ";b0=",
                vm.toString(s.b0),
                ";b1=",
                vm.toString(s.b1),
                ";Dw=",
                vm.toString(s.D),
                ";yw=",
                vm.toString(s.y),
                ";ow=",
                vm.toString(s.other)
            );
            line = string.concat(
                line,
                ";howD=",
                vm.toString(s.howD),
                ";howY=",
                vm.toString(s.howY),
                ";litD=",
                vm.toString(s.litD),
                ";litY=",
                vm.toString(s.litY)
            );
        } else {
            line = string.concat(line, ";D=", vm.toString(s.D), ";y=", vm.toString(s.y));
        }
        console.log(line);
    }

    /// Every call of the phase, on that call's own on-chain balances and amount, under model `m`.
    function _calls(string memory name, Model m, string memory model, uint256[] memory expected) internal view {
        Pool memory p = _load(name);
        for (uint256 t = 0; t < p.i.length; t++) {
            uint256[3] memory raw = [p.bal[0][t], p.bal[1][t], p.bal[2][t]];
            Step memory s = _swap(p, m, raw, p.i[t], p.j[t], p.amount[t]);
            _log(p, model, t, s, m == Model.FP127 || m == Model.FP256);
            assertEq(s.amountIn, expected[t], string.concat(name, " ", model, " swap ", vm.toString(p.first + t)));
        }
    }

    // ------------------------------------------------------------------ tests

    /// Every on-chain onSwap return of the phase, bit for bit, from that call's own inputs.
    function test_deployed_osETH() public view {
        _calls("osETH", Model.Deployed, "deployed", _load("osETH").amountIn);
    }

    function test_deployed_wstETH() public view {
        _calls("wstETH", Model.Deployed, "deployed", _load("wstETH").amountIn);
    }

    /// The attacker's plan (drain the rate token to `leave` wei, take leave - 1 out, swap the recorded WETH
    /// amount back), replayed from the phase's first balances alone, is the whole on-chain sequence.
    function _plan(string memory name) internal view {
        Pool memory p = _load(name);
        uint256[3] memory raw = _start(p);
        for (uint256 t = 0; t < p.i.length; t++) {
            uint256 j = p.j[t];
            uint256 amount = p.plan[t] == 0 ? raw[j] - p.leave : p.amount[t];
            assertEq(amount, p.amount[t]);
            Step memory s = _swapDeployed(p, raw, p.i[t], j, amount, false);
            assertEq(s.amountIn, p.amountIn[t], string.concat(name, " plan swap ", vm.toString(p.first + t)));
            raw[p.i[t]] += s.amountIn;
            raw[j] -= amount;
            if (t + 1 < p.i.length) {
                for (uint256 k = 0; k < 3; k++) {
                    assertEq(raw[k], p.bal[k][t + 1]);
                }
            }
        }
    }

    function test_deployed_plan_osETH() public view {
        _plan("osETH");
    }

    function test_deployed_plan_wstETH() public view {
        _plan("wstETH");
    }

    /// The same calls with the given-out amount upscaled by mulUp; equal to scripts/replays/balancer.py's port.
    function test_mulUp_osETH() public view {
        _calls("osETH", Model.MulUp, "mulUp", _expect("osETH", "expectMulUp"));
    }

    function test_mulUp_wstETH() public view {
        _calls("wstETH", Model.MulUp, "mulUp", _expect("wstETH", "expectMulUp"));
    }

    /// The same calls in FP127 / FP256, ceil to wei once: equal to the exact-rational charge on every call.
    function test_fp127_osETH() public view {
        _calls("osETH", Model.FP127, "fp127", _expect("osETH", "expectExact"));
    }

    function test_fp127_wstETH() public view {
        _calls("wstETH", Model.FP127, "fp127", _expect("wstETH", "expectExact"));
    }

    function test_fp256_osETH() public view {
        _calls("osETH", Model.FP256, "fp256", _expect("osETH", "expectExact"));
    }

    function test_fp256_wstETH() public view {
        _calls("wstETH", Model.FP256, "fp256", _expect("wstETH", "expectExact"));
    }

    /// The headline step, by hand: 17 wei of osETH at the in-transaction rate upscales to 17.988... and
    /// _upscale's mulDown records 17; mulUp records 18. wstETH: 4 wei at 1.218... -> 4 (mulUp 5).
    function test_upscale_headline() public pure {
        assertEq(BalancerV2.mulDown(17, 1058132408689971699), 17);
        assertEq(BalancerV2.mulUp(17, 1058132408689971699), 18);
        assertEq(17 * uint256(1058132408689971699), 17988250947729518883);
        assertEq(BalancerV2.mulDown(4, 1218116415279760760), 4);
        assertEq(BalancerV2.mulUp(4, 1218116415279760760), 5);
        // the balances the pool sees at that step: 18 wei osETH -> 19 (true 19.046...), 1 wei -> 1 (true 1.058...)
        assertEq(BalancerV2.mulDown(18, 1058132408689971699), 19);
        assertEq(BalancerV2.mulDown(1, 1058132408689971699), 1);
    }
}
