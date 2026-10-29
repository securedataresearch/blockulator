// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import "forge-std/Test.sol";
import {BL127Lib} from "../../contracts/src/bl127/BL127Lib.sol";
import {BL19Lib} from "../../contracts/src/bl19/BL19Lib.sol";

/// @notice The deployed arithmetic of the Resupply exploit, vendored line by line
///         from the Sourcify-verified sources (scripts/replays/resupply.py fetch
///         checks every cited line). Vyper 0.3.10 and Solidity 0.8.28 uint256
///         arithmetic is checked and `/` floors, as here.
library ResupplyDeployed {
    // LlamaLend Vault.vy (0xc014f34d5ba10b6799d76b0f5acdeee577805085, the
    // implementation behind the cvcrvUSD EIP-1167 proxy 0x01144442fba7adccb5c9dc9cf33dd009d50a9e1d)
    uint256 internal constant DEAD_SHARES = 1000; // Vault.vy:85

    /// Vault.vy:298-309 _convert_to_assets (304-305 numerator/denominator; 307 floor, 309 ceil).
    function convertToAssets(uint256 shares, uint256 totalAssets, uint256 totalSupply, uint256 precision, bool isFloor)
        internal
        pure
        returns (uint256)
    {
        uint256 numerator = shares * (totalAssets * precision + 1);
        uint256 denominator = (totalSupply + DEAD_SHARES) * precision;
        if (isFloor) return numerator / denominator;
        return (numerator + denominator - 1) / denominator;
    }

    // BasicVaultOracle.sol:23 (0xcb7e25fbbd8afe4ce73d7dac647dbc3d847f3c82)
    function getPrices(uint256 totalAssets, uint256 totalSupply, uint256 precision) internal pure returns (uint256) {
        return convertToAssets(1e18, totalAssets, totalSupply, precision, true);
    }

    // ResupplyPair 0x6e90c85a495d54c6d7e1f3400fef1f6e59f86bd6
    uint256 internal constant LTV_PRECISION = 1e5; // ResupplyPairConstants.sol:12
    uint256 internal constant LIQ_PRECISION = 1e5; // ResupplyPairConstants.sol:13
    uint256 internal constant EXCHANGE_PRECISION = 1e18; // ResupplyPairConstants.sol:14

    /// ResupplyPairCore.sol:573
    function exchangeRate(uint256 price) internal pure returns (uint256) {
        return 1e36 / price;
    }

    /// VaultAccount.sol:16-25 toShares
    function toShares(uint256 totalAmount, uint256 totalShares, uint256 amount, bool roundUp) internal pure returns (uint256 shares) {
        if (totalAmount == 0) {
            shares = amount;
        } else {
            shares = (amount * totalShares) / totalAmount;
            if (roundUp && (shares * totalAmount) / totalShares < amount) shares = shares + 1;
        }
    }

    /// VaultAccount.sol:29-38 toAmount
    function toAmount(uint256 totalAmount, uint256 totalShares, uint256 shares, bool roundUp) internal pure returns (uint256 amount) {
        if (totalShares == 0) {
            amount = shares;
        } else {
            amount = (shares * totalAmount) / totalShares;
            if (roundUp && totalAmount > 0 && (amount * totalShares) / totalAmount < shares) amount = amount + 1;
        }
    }

    /// ResupplyPairCore.sol:270-284 _isSolvent, with the storage reads passed in.
    function isSolvent(uint256 maxLTV, uint256 borrowerAmount, uint256 collateralAmount, uint256 rate)
        internal
        pure
        returns (bool, uint256 ltv)
    {
        if (maxLTV == 0) return (true, 0); // :272
        if (borrowerAmount == 0) return (true, 0); // :276
        if (collateralAmount == 0) return (false, 0); // :280
        ltv = ((borrowerAmount * rate * LTV_PRECISION) / EXCHANGE_PRECISION) / collateralAmount; // :282
        return (ltv <= maxLTV, ltv); // :283
    }
}

/// @title Resupply replay
/// @notice ResupplyPair (cvcrvUSD), tx 0xffbbd492e0605a8bb6d490c3cd879e87ff60862b0684160d08fd5711e7a872d3,
///         block 22785461, index 0. Replays the decisive step from the integers
///         pinned in scripts/replays/resupply.json (no network), asserts it equals
///         what happened on chain, then runs the same step with divUp, with the
///         division by the price moved to the end, in BL127 and in BL19. Prints
///             RSP|<form>|k=v;k=v;...
///         for scripts/replays/resupply.py, which scores each against exact rationals.
contract ResupplyReplay is Test {
    string constant PINS = "scripts/replays/resupply.json";

    // ---- pinned integers (provenance for each in resupply.json and docs/benchmarks/replay-resupply.md)
    uint256 constant VAULT_TOTAL_ASSETS = 2002000000000000000001; // crvUSD.balanceOf(controller) + total_debt, traced
    uint256 constant VAULT_TOTAL_SUPPLY = 1; // 0 before the tx + the attacker's 1-wei mint
    uint256 constant VAULT_PRECISION = 1; // 10**(18 - crvUSD.decimals())
    uint256 constant PRICE_ON_CHAIN = 2000000000000000000001998001998001998; // oracle.getPrices(vault), traced
    uint256 constant EXCHANGE_RATE_ON_CHAIN = 0; // UpdateExchangeRate(0) log
    uint256 constant COLLATERAL = 1; // AddCollateral(borrower, 1) log
    uint256 constant BORROW_AMOUNT = 10_000_000e18; // borrow() input, Borrow log
    uint256 constant BORROW_SHARES = 10_000_000e18; // borrow() return, Borrow log
    uint256 constant MINT_FEE = 0; // pair.mintFee(), traced
    uint256 constant TOTAL_BORROW_AMOUNT_BEFORE = 0; // eth_call pair.totalBorrow() at block-1
    uint256 constant TOTAL_BORROW_SHARES_BEFORE = 0;
    uint256 constant MAX_LTV = 95000; // eth_call pair.maxLTV(): 95%
    uint256 constant DONATION = 2000e18; // crvUSD.transfer(controller, ...), traced
    uint256 constant MINT_SHARES = 1;
    uint256 constant MINT_ASSETS = 2000000000000000001; // vault.mint(1) return, traced

    function _pin(string memory json, string memory key) internal pure returns (uint256) {
        return vm.parseUint(vm.parseJsonString(json, string.concat(".pins.", key)));
    }

    function test_pins_match_json() public view {
        string memory j = vm.readFile(PINS);
        assertEq(_pin(j, "vaultTotalAssets"), VAULT_TOTAL_ASSETS);
        assertEq(_pin(j, "vaultTotalSupply"), VAULT_TOTAL_SUPPLY);
        assertEq(_pin(j, "vaultPrecision"), VAULT_PRECISION);
        assertEq(_pin(j, "deadShares"), ResupplyDeployed.DEAD_SHARES);
        assertEq(_pin(j, "price"), PRICE_ON_CHAIN);
        assertEq(_pin(j, "exchangeRateOnChain"), EXCHANGE_RATE_ON_CHAIN);
        assertEq(_pin(j, "collateral"), COLLATERAL);
        assertEq(_pin(j, "borrowAmount"), BORROW_AMOUNT);
        assertEq(_pin(j, "borrowShares"), BORROW_SHARES);
        assertEq(_pin(j, "mintFee"), MINT_FEE);
        assertEq(_pin(j, "totalBorrowAmountBefore"), TOTAL_BORROW_AMOUNT_BEFORE);
        assertEq(_pin(j, "totalBorrowSharesBefore"), TOTAL_BORROW_SHARES_BEFORE);
        assertEq(_pin(j, "maxLTV"), MAX_LTV);
        assertEq(_pin(j, "ltvPrecision"), ResupplyDeployed.LTV_PRECISION);
        assertEq(_pin(j, "exchangePrecision"), ResupplyDeployed.EXCHANGE_PRECISION);
        assertEq(_pin(j, "donation"), DONATION);
        assertEq(_pin(j, "mintShares"), MINT_SHARES);
        assertEq(_pin(j, "mintAssets"), MINT_ASSETS);
    }

    /// The borrower amount the solvency check reads after borrow()'s bookkeeping
    /// (ResupplyPairCore.sol:640-656, then :275).
    function _borrowerAmount() internal pure returns (uint256 amount, uint256 shares) {
        uint256 debtForMint = BORROW_AMOUNT * (ResupplyDeployed.LIQ_PRECISION + MINT_FEE) / ResupplyDeployed.LIQ_PRECISION;
        shares = ResupplyDeployed.toShares(TOTAL_BORROW_AMOUNT_BEFORE, TOTAL_BORROW_SHARES_BEFORE, debtForMint, true);
        uint256 tbAmount = TOTAL_BORROW_AMOUNT_BEFORE + debtForMint;
        uint256 tbShares = TOTAL_BORROW_SHARES_BEFORE + shares;
        amount = ResupplyDeployed.toAmount(tbAmount, tbShares, shares, true);
    }

    /// Bit-exact: the vault price, the floored rate, the LTV and the verdict
    /// are what the chain computed.
    function test_deployed_replay() public pure {
        // the attacker's mint(1) cost, from the pre-mint vault (0 shares, donation only); Vault.vy:422 rounds up
        assertEq(ResupplyDeployed.convertToAssets(MINT_SHARES, DONATION, 0, VAULT_PRECISION, false), MINT_ASSETS);
        // the oracle price the pair read inside borrow()
        uint256 price = ResupplyDeployed.getPrices(VAULT_TOTAL_ASSETS, VAULT_TOTAL_SUPPLY, VAULT_PRECISION);
        assertEq(price, PRICE_ON_CHAIN);
        assertGt(price, 1e36);
        // the exchange rate: 1e36 / 2.000000000000000000001998e36 floors to 0
        uint256 rate = ResupplyDeployed.exchangeRate(price);
        assertEq(rate, EXCHANGE_RATE_ON_CHAIN);
        assertEq(rate, 0);
        // the borrow's bookkeeping gives the shares the Borrow event logged
        (uint256 amount, uint256 shares) = _borrowerAmount();
        assertEq(shares, BORROW_SHARES);
        assertEq(amount, BORROW_AMOUNT);
        // the solvency check passes with LTV 0
        (bool ok, uint256 ltv) = ResupplyDeployed.isSolvent(MAX_LTV, amount, COLLATERAL, rate);
        assertEq(ltv, 0);
        assertTrue(ok);
    }

    function test_report() public pure {
        (uint256 B,) = _borrowerAmount();
        uint256 P = ResupplyDeployed.getPrices(VAULT_TOTAL_ASSETS, VAULT_TOTAL_SUPPLY, VAULT_PRECISION);
        uint256 LP = ResupplyDeployed.LTV_PRECISION;
        uint256 EP = ResupplyDeployed.EXCHANGE_PRECISION;

        // as deployed
        {
            uint256 rate = ResupplyDeployed.exchangeRate(P);
            (bool ok, uint256 ltv) = ResupplyDeployed.isSolvent(MAX_LTV, B, COLLATERAL, rate);
            _line("deployed", string.concat("rate=", vm.toString(rate), ";ltv=", vm.toString(ltv), ";solvent=", _b(ok),
                ";borrowerAmount=", vm.toString(B), ";price=", vm.toString(P)));
        }
        // divUp on the rate, everything else as deployed
        {
            uint256 rate = (1e36 + P - 1) / P;
            (bool ok, uint256 ltv) = ResupplyDeployed.isSolvent(MAX_LTV, B, COLLATERAL, rate);
            assertEq(rate, 1);
            assertFalse(ok);
            uint256 maxBorrow = COLLATERAL * MAX_LTV * EP / (rate * LP);
            _line("divup", string.concat("rate=", vm.toString(rate), ";ltv=", vm.toString(ltv), ";solvent=", _b(ok),
                ";maxBorrow=", vm.toString(maxBorrow)));
        }
        // no reciprocal: divide by the price at the end; LTV rounded up (the protocol's favour)
        {
            uint256 num = B * 1e36 * LP;
            uint256 den = P * EP * COLLATERAL;
            uint256 ltvUp = (num + den - 1) / den;
            uint256 ltvFloor = num / den;
            bool ok = ltvUp <= MAX_LTV;
            assertFalse(ok);
            assertFalse(ltvFloor <= MAX_LTV);
            uint256 maxBorrow = COLLATERAL * MAX_LTV * EP * P / (1e36 * LP);
            _line("divlast", string.concat("ltv=", vm.toString(ltvUp), ";ltvFloor=", vm.toString(ltvFloor), ";solvent=", _b(ok),
                ";maxBorrow=", vm.toString(maxBorrow)));
        }
        // BL127: same integers, same formula, the inline library
        {
            int256 rate = BL127Lib.div(_q(1e36), _q(P));
            int256 ltv = BL127Lib.div(BL127Lib.div(BL127Lib.mul(BL127Lib.mul(_q(B), rate), _q(LP)), _q(EP)), _q(COLLATERAL));
            bool ok = ltv <= _q(MAX_LTV);
            assertGt(rate, 0);
            assertFalse(ok);
            int256 ltvCeil = BL127Lib.ceil(ltv) >> 128;
            int256 mb = BL127Lib.div(BL127Lib.mul(BL127Lib.mul(_q(COLLATERAL), _q(MAX_LTV)), _q(EP)), BL127Lib.mul(rate, _q(LP)));
            int256 maxBorrow = BL127Lib.floor(mb) >> 128;
            _line("bl127", string.concat("rate=", vm.toString(rate), ";ltv=", vm.toString(ltv), ";solvent=", _b(ok),
                ";ltvCeil=", vm.toString(ltvCeil), ";maxBorrow=", vm.toString(maxBorrow)));
        }
        // BL19: same
        {
            int256 rate = BL19Lib.div(BL19Lib.fromUint(1e36), BL19Lib.fromUint(P));
            int256 ltv = BL19Lib.div(
                BL19Lib.div(BL19Lib.mul(BL19Lib.mul(BL19Lib.fromUint(B), rate), BL19Lib.fromUint(LP)), BL19Lib.fromUint(EP)),
                BL19Lib.fromUint(COLLATERAL)
            );
            bool ok = BL19Lib.cmp(ltv, BL19Lib.fromUint(MAX_LTV)) <= 0;
            assertGt(BL19Lib.cmp(rate, 0), 0);
            assertFalse(ok);
            int256 ltvCeil = BL127Lib.ceil(BL19Lib.toBL127(ltv)) >> 128;
            int256 mb = BL19Lib.div(
                BL19Lib.mul(BL19Lib.mul(BL19Lib.fromUint(COLLATERAL), BL19Lib.fromUint(MAX_LTV)), BL19Lib.fromUint(EP)),
                BL19Lib.mul(rate, BL19Lib.fromUint(LP))
            );
            int256 maxBorrow = BL127Lib.floor(BL19Lib.toBL127(mb)) >> 128;
            _line("bl19", string.concat("rate=", vm.toString(rate), ";ltv=", vm.toString(ltv), ";solvent=", _b(ok),
                ";ltvCeil=", vm.toString(ltvCeil), ";maxBorrow=", vm.toString(maxBorrow)));
        }
    }

    /// BL127 holds integers below 2^127 (about 1.7e38) exactly; the price here is 2.0e36.
    function _q(uint256 x) internal pure returns (int256) {
        require(x < 1 << 127, "BL127 range");
        return int256(x) << 128;
    }

    function _b(bool x) internal pure returns (string memory) {
        return x ? "1" : "0";
    }

    function _line(string memory form, string memory kv) internal pure {
        console.log(string.concat("RSP|", form, "|", kv));
    }
}
