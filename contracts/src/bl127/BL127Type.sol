// SPDX-License-Identifier: MIT
pragma solidity ^0.8.31;

import {BL127Lib} from "./BL127Lib.sol";

/// @title BL127Type
/// @notice The typed face of BL127Lib: `type BL127 is int256`, with + - * /,
///         unary -, < > <= >= == != bound to the library, and every other op
///         attached, so `x.exp()` and `a * b + c` compile to the same library
///         calls as the raw form. Opt in by importing this file; BL127Lib is
///         unchanged and the two mix freely through `BL127.wrap` /
///         `BL127.unwrap` (free at runtime).
/// @dev Every function is a pure free function, as solc requires of a bound
///      operator, and only re-types its arguments and result: the same words,
///      the same reverts (BL127Lib's errors), and the same gas
///      (test/typed/Typed127.t.sol checks both). `*` is BL127Lib.mul (floor),
///      `/` is BL127Lib.div (truncated toward zero); mulUp, divDown and the
///      other directed forms are attached by name. Comparisons are on the raw
///      words, which order as the values do in two's complement.
///      Names follow BL127Lib's ops. Functions that take a plain integer
///      instead of an BL127 carry the prefix (`bl127FromWad`), so this file
///      and BL19Type.sol can be imported into one scope; only ONE and PI then
///      need an alias (`import {ONE as ONE127} from ...`), as PRBMath's UNIT.

type BL127 is int256;

using {
    add as +,
    sub as -,
    mul as *,
    div as /,
    neg as -,
    lt as <,
    gt as >,
    le as <=,
    ge as >=,
    eq as ==,
    ne as !=
} for BL127 global;

using {
    add,
    sub,
    mul,
    div,
    neg,
    lt,
    gt,
    le,
    ge,
    eq,
    ne,
    unwrap,
    toFixed18,
    toFixed18Down,
    toFixed18Up,
    toWadDown,
    toWadUp,
    toIntDown,
    toIntUp,
    mulDown,
    mulUp,
    divDown,
    divUp,
    exp2,
    exp,
    exp10,
    log2,
    ln,
    log10,
    log2Up,
    sqrt,
    pow,
    powu,
    compound,
    cbrt,
    gavg,
    hypot,
    inv,
    abs,
    sign,
    min,
    max,
    clamp,
    avg,
    zeroFloorSub,
    dist,
    lerp,
    floor,
    ceil,
    frac,
    round,
    factorial,
    lambertW0,
    lambertWm1,
    log1p,
    expm1,
    sinh,
    cosh,
    tanh,
    atanh,
    erf,
    erfc,
    normCdf
} for BL127 global;

// 1 (raw 2^128).
BL127 constant ONE = BL127.wrap(BL127Lib.ONE);
// pi, rounded to the nearest 2^-128.
BL127 constant PI = BL127.wrap(BL127Lib.PI);

// ---- conversions -----------------------------------------------------------

/// The raw word as an BL127, value = raw / 2^128: BL127.wrap, PRBMath's sd().
function bl127(int256 raw) pure returns (BL127) {
    return BL127.wrap(raw);
}

/// The raw word, value * 2^128: BL127.unwrap, attached as x.unwrap().
function unwrap(BL127 x) pure returns (int256) {
    return BL127.unwrap(x);
}

/// The integer n, exact. Reverts with Overflow unless -2^127 <= n < 2^127.
function bl127FromInt(int256 n) pure returns (BL127) {
    if (n > type(int128).max || n < type(int128).min) revert BL127Lib.Overflow();
    unchecked {
        return BL127.wrap(n << 128);
    }
}

/// floor(x) as a plain integer, exact.
function toIntDown(BL127 x) pure returns (int256) {
    return BL127.unwrap(x) >> 128;
}

/// ceil(x) as a plain integer, exact.
function toIntUp(BL127 x) pure returns (int256 r) {
    int256 v = BL127.unwrap(x);
    r = v >> 128;
    unchecked {
        if (v & int256(uint256(type(uint128).max)) != 0) r += 1;
    }
}

/// An 18-decimal signed word: BL127Lib.fromFixed18.
function bl127FromFixed18(int256 x) pure returns (BL127) {
    return BL127.wrap(BL127Lib.fromFixed18(x));
}

/// A WAD (unsigned, 18 decimals): BL127Lib.fromFixed18 of the same integer.
/// Reverts with Overflow above 2^255 - 1, which has no int256 word (and is
/// far beyond BL127's range anyway).
function bl127FromWad(uint256 x) pure returns (BL127) {
    if (x > uint256(type(int256).max)) revert BL127Lib.Overflow();
    return BL127.wrap(BL127Lib.fromFixed18(int256(x)));
}

function toFixed18(BL127 x) pure returns (int256) {
    return BL127Lib.toFixed18(BL127.unwrap(x));
}

function toFixed18Down(BL127 x) pure returns (int256) {
    return BL127Lib.toFixed18Down(BL127.unwrap(x));
}

function toFixed18Up(BL127 x) pure returns (int256) {
    return BL127Lib.toFixed18Up(BL127.unwrap(x));
}

/// The WAD at or below x: what a protocol pays out. Reverts with OutOfRange
/// when that is negative.
function toWadDown(BL127 x) pure returns (uint256) {
    int256 r = BL127Lib.toFixed18Down(BL127.unwrap(x));
    if (r < 0) revert BL127Lib.OutOfRange();
    return uint256(r);
}

/// The WAD at or above x: what a protocol charges. Reverts with OutOfRange
/// when that is negative.
function toWadUp(BL127 x) pure returns (uint256) {
    int256 r = BL127Lib.toFixed18Up(BL127.unwrap(x));
    if (r < 0) revert BL127Lib.OutOfRange();
    return uint256(r);
}

// ---- operators -------------------------------------------------------------

function add(BL127 a, BL127 b) pure returns (BL127) {
    return BL127.wrap(BL127Lib.add(BL127.unwrap(a), BL127.unwrap(b)));
}

function sub(BL127 a, BL127 b) pure returns (BL127) {
    return BL127.wrap(BL127Lib.sub(BL127.unwrap(a), BL127.unwrap(b)));
}

function mul(BL127 a, BL127 b) pure returns (BL127) {
    return BL127.wrap(BL127Lib.mul(BL127.unwrap(a), BL127.unwrap(b)));
}

function div(BL127 a, BL127 b) pure returns (BL127) {
    return BL127.wrap(BL127Lib.div(BL127.unwrap(a), BL127.unwrap(b)));
}

function neg(BL127 x) pure returns (BL127) {
    return BL127.wrap(BL127Lib.neg(BL127.unwrap(x)));
}

function lt(BL127 a, BL127 b) pure returns (bool) {
    return BL127.unwrap(a) < BL127.unwrap(b);
}

function gt(BL127 a, BL127 b) pure returns (bool) {
    return BL127.unwrap(a) > BL127.unwrap(b);
}

function le(BL127 a, BL127 b) pure returns (bool) {
    return BL127.unwrap(a) <= BL127.unwrap(b);
}

function ge(BL127 a, BL127 b) pure returns (bool) {
    return BL127.unwrap(a) >= BL127.unwrap(b);
}

function eq(BL127 a, BL127 b) pure returns (bool) {
    return BL127.unwrap(a) == BL127.unwrap(b);
}

function ne(BL127 a, BL127 b) pure returns (bool) {
    return BL127.unwrap(a) != BL127.unwrap(b);
}

// ---- directed rounding -----------------------------------------------------

function mulDown(BL127 a, BL127 b) pure returns (BL127) {
    return BL127.wrap(BL127Lib.mulDown(BL127.unwrap(a), BL127.unwrap(b)));
}

function mulUp(BL127 a, BL127 b) pure returns (BL127) {
    return BL127.wrap(BL127Lib.mulUp(BL127.unwrap(a), BL127.unwrap(b)));
}

function divDown(BL127 a, BL127 b) pure returns (BL127) {
    return BL127.wrap(BL127Lib.divDown(BL127.unwrap(a), BL127.unwrap(b)));
}

function divUp(BL127 a, BL127 b) pure returns (BL127) {
    return BL127.wrap(BL127Lib.divUp(BL127.unwrap(a), BL127.unwrap(b)));
}

// ---- exponentials, logarithms, powers and roots ----------------------------

function exp2(BL127 x) pure returns (BL127) {
    return BL127.wrap(BL127Lib.exp2(BL127.unwrap(x)));
}

function exp(BL127 x) pure returns (BL127) {
    return BL127.wrap(BL127Lib.exp(BL127.unwrap(x)));
}

function exp10(BL127 x) pure returns (BL127) {
    return BL127.wrap(BL127Lib.exp10(BL127.unwrap(x)));
}

function log2(BL127 x) pure returns (BL127) {
    return BL127.wrap(BL127Lib.log2(BL127.unwrap(x)));
}

function ln(BL127 x) pure returns (BL127) {
    return BL127.wrap(BL127Lib.ln(BL127.unwrap(x)));
}

function log10(BL127 x) pure returns (BL127) {
    return BL127.wrap(BL127Lib.log10(BL127.unwrap(x)));
}

function log2Up(BL127 x) pure returns (BL127) {
    return BL127.wrap(BL127Lib.log2Up(BL127.unwrap(x)));
}

function sqrt(BL127 x) pure returns (BL127) {
    return BL127.wrap(BL127Lib.sqrt(BL127.unwrap(x)));
}

function pow(BL127 x, BL127 y) pure returns (BL127) {
    return BL127.wrap(BL127Lib.pow(BL127.unwrap(x), BL127.unwrap(y)));
}

/// x^floor(n); n is an BL127 value, as in BL127Lib.
function powu(BL127 x, BL127 n) pure returns (BL127) {
    return BL127.wrap(BL127Lib.powu(BL127.unwrap(x), BL127.unwrap(n)));
}

/// (1 + rate)^floor(n); n is an BL127 value, as in BL127Lib.
function compound(BL127 rate, BL127 n) pure returns (BL127) {
    return BL127.wrap(BL127Lib.compound(BL127.unwrap(rate), BL127.unwrap(n)));
}

function cbrt(BL127 x) pure returns (BL127) {
    return BL127.wrap(BL127Lib.cbrt(BL127.unwrap(x)));
}

function gavg(BL127 a, BL127 b) pure returns (BL127) {
    return BL127.wrap(BL127Lib.gavg(BL127.unwrap(a), BL127.unwrap(b)));
}

function hypot(BL127 a, BL127 b) pure returns (BL127) {
    return BL127.wrap(BL127Lib.hypot(BL127.unwrap(a), BL127.unwrap(b)));
}

function inv(BL127 x) pure returns (BL127) {
    return BL127.wrap(BL127Lib.inv(BL127.unwrap(x)));
}

// ---- elementary ------------------------------------------------------------

function abs(BL127 x) pure returns (BL127) {
    return BL127.wrap(BL127Lib.abs(BL127.unwrap(x)));
}

function sign(BL127 x) pure returns (BL127) {
    return BL127.wrap(BL127Lib.sign(BL127.unwrap(x)));
}

function min(BL127 a, BL127 b) pure returns (BL127) {
    return BL127.wrap(BL127Lib.min(BL127.unwrap(a), BL127.unwrap(b)));
}

function max(BL127 a, BL127 b) pure returns (BL127) {
    return BL127.wrap(BL127Lib.max(BL127.unwrap(a), BL127.unwrap(b)));
}

function clamp(BL127 x, BL127 lo, BL127 hi) pure returns (BL127) {
    return BL127.wrap(BL127Lib.clamp(BL127.unwrap(x), BL127.unwrap(lo), BL127.unwrap(hi)));
}

function avg(BL127 a, BL127 b) pure returns (BL127) {
    return BL127.wrap(BL127Lib.avg(BL127.unwrap(a), BL127.unwrap(b)));
}

function zeroFloorSub(BL127 a, BL127 b) pure returns (BL127) {
    return BL127.wrap(BL127Lib.zeroFloorSub(BL127.unwrap(a), BL127.unwrap(b)));
}

function dist(BL127 a, BL127 b) pure returns (BL127) {
    return BL127.wrap(BL127Lib.dist(BL127.unwrap(a), BL127.unwrap(b)));
}

function lerp(BL127 a, BL127 b, BL127 t) pure returns (BL127) {
    return BL127.wrap(BL127Lib.lerp(BL127.unwrap(a), BL127.unwrap(b), BL127.unwrap(t)));
}

function floor(BL127 x) pure returns (BL127) {
    return BL127.wrap(BL127Lib.floor(BL127.unwrap(x)));
}

function ceil(BL127 x) pure returns (BL127) {
    return BL127.wrap(BL127Lib.ceil(BL127.unwrap(x)));
}

function frac(BL127 x) pure returns (BL127) {
    return BL127.wrap(BL127Lib.frac(BL127.unwrap(x)));
}

function round(BL127 x) pure returns (BL127) {
    return BL127.wrap(BL127Lib.round(BL127.unwrap(x)));
}

/// floor(n)!; n is an BL127 value, as in BL127Lib.
function factorial(BL127 n) pure returns (BL127) {
    return BL127.wrap(BL127Lib.factorial(BL127.unwrap(n)));
}

// ---- special functions -----------------------------------------------------

function lambertW0(BL127 x) pure returns (BL127) {
    return BL127.wrap(BL127Lib.lambertW0(BL127.unwrap(x)));
}

function lambertWm1(BL127 x) pure returns (BL127) {
    return BL127.wrap(BL127Lib.lambertWm1(BL127.unwrap(x)));
}

function log1p(BL127 x) pure returns (BL127) {
    return BL127.wrap(BL127Lib.log1p(BL127.unwrap(x)));
}

function expm1(BL127 x) pure returns (BL127) {
    return BL127.wrap(BL127Lib.expm1(BL127.unwrap(x)));
}

function sinh(BL127 x) pure returns (BL127) {
    return BL127.wrap(BL127Lib.sinh(BL127.unwrap(x)));
}

function cosh(BL127 x) pure returns (BL127) {
    return BL127.wrap(BL127Lib.cosh(BL127.unwrap(x)));
}

function tanh(BL127 x) pure returns (BL127) {
    return BL127.wrap(BL127Lib.tanh(BL127.unwrap(x)));
}

function atanh(BL127 x) pure returns (BL127) {
    return BL127.wrap(BL127Lib.atanh(BL127.unwrap(x)));
}

function erf(BL127 x) pure returns (BL127) {
    return BL127.wrap(BL127Lib.erf(BL127.unwrap(x)));
}

function erfc(BL127 x) pure returns (BL127) {
    return BL127.wrap(BL127Lib.erfc(BL127.unwrap(x)));
}

function normCdf(BL127 x) pure returns (BL127) {
    return BL127.wrap(BL127Lib.normCdf(BL127.unwrap(x)));
}
