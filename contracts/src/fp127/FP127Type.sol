// SPDX-License-Identifier: MIT
pragma solidity ^0.8.31;

import {FP127Lib} from "./FP127Lib.sol";

/// @title FP127Type
/// @notice The typed face of FP127Lib: `type FP127 is int256`, with + - * /,
///         unary -, < > <= >= == != bound to the library, and every other op
///         attached, so `x.exp()` and `a * b + c` compile to the same library
///         calls as the raw form. Opt in by importing this file; FP127Lib is
///         unchanged and the two mix freely through `FP127.wrap` /
///         `FP127.unwrap` (free at runtime).
/// @dev Every function is a pure free function, as solc requires of a bound
///      operator, and only re-types its arguments and result: the same words,
///      the same reverts (FP127Lib's errors), and the same gas
///      (test/typed/Typed127.t.sol checks both). `*` is FP127Lib.mul (floor),
///      `/` is FP127Lib.div (truncated toward zero); mulUp, divDown and the
///      other directed forms are attached by name. Comparisons are on the raw
///      words, which order as the values do in two's complement.
///      Names follow FP127Lib's ops. Functions that take a plain integer
///      instead of an FP127 carry the prefix (`fp127FromWad`), so this file
///      and FP19Type.sol can be imported into one scope; only ONE and PI then
///      need an alias (`import {ONE as ONE127} from ...`), as PRBMath's UNIT.

type FP127 is int256;

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
} for FP127 global;

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
} for FP127 global;

// 1 (raw 2^128).
FP127 constant ONE = FP127.wrap(FP127Lib.ONE);
// pi, rounded to the nearest 2^-128.
FP127 constant PI = FP127.wrap(FP127Lib.PI);

// ---- conversions -----------------------------------------------------------

/// The raw word as an FP127, value = raw / 2^128: FP127.wrap, PRBMath's sd().
function fp127(int256 raw) pure returns (FP127) {
    return FP127.wrap(raw);
}

/// The raw word, value * 2^128: FP127.unwrap, attached as x.unwrap().
function unwrap(FP127 x) pure returns (int256) {
    return FP127.unwrap(x);
}

/// The integer n, exact. Reverts with Overflow unless -2^127 <= n < 2^127.
function fp127FromInt(int256 n) pure returns (FP127) {
    if (n > type(int128).max || n < type(int128).min) revert FP127Lib.Overflow();
    unchecked {
        return FP127.wrap(n << 128);
    }
}

/// floor(x) as a plain integer, exact.
function toIntDown(FP127 x) pure returns (int256) {
    return FP127.unwrap(x) >> 128;
}

/// ceil(x) as a plain integer, exact.
function toIntUp(FP127 x) pure returns (int256 r) {
    int256 v = FP127.unwrap(x);
    r = v >> 128;
    unchecked {
        if (v & int256(uint256(type(uint128).max)) != 0) r += 1;
    }
}

/// An 18-decimal signed word: FP127Lib.fromFixed18.
function fp127FromFixed18(int256 x) pure returns (FP127) {
    return FP127.wrap(FP127Lib.fromFixed18(x));
}

/// A WAD (unsigned, 18 decimals): FP127Lib.fromFixed18 of the same integer.
/// Reverts with Overflow above 2^255 - 1, which has no int256 word (and is
/// far beyond FP127's range anyway).
function fp127FromWad(uint256 x) pure returns (FP127) {
    if (x > uint256(type(int256).max)) revert FP127Lib.Overflow();
    return FP127.wrap(FP127Lib.fromFixed18(int256(x)));
}

function toFixed18(FP127 x) pure returns (int256) {
    return FP127Lib.toFixed18(FP127.unwrap(x));
}

function toFixed18Down(FP127 x) pure returns (int256) {
    return FP127Lib.toFixed18Down(FP127.unwrap(x));
}

function toFixed18Up(FP127 x) pure returns (int256) {
    return FP127Lib.toFixed18Up(FP127.unwrap(x));
}

/// The WAD at or below x: what a protocol pays out. Reverts with OutOfRange
/// when that is negative.
function toWadDown(FP127 x) pure returns (uint256) {
    int256 r = FP127Lib.toFixed18Down(FP127.unwrap(x));
    if (r < 0) revert FP127Lib.OutOfRange();
    return uint256(r);
}

/// The WAD at or above x: what a protocol charges. Reverts with OutOfRange
/// when that is negative.
function toWadUp(FP127 x) pure returns (uint256) {
    int256 r = FP127Lib.toFixed18Up(FP127.unwrap(x));
    if (r < 0) revert FP127Lib.OutOfRange();
    return uint256(r);
}

// ---- operators -------------------------------------------------------------

function add(FP127 a, FP127 b) pure returns (FP127) {
    return FP127.wrap(FP127Lib.add(FP127.unwrap(a), FP127.unwrap(b)));
}

function sub(FP127 a, FP127 b) pure returns (FP127) {
    return FP127.wrap(FP127Lib.sub(FP127.unwrap(a), FP127.unwrap(b)));
}

function mul(FP127 a, FP127 b) pure returns (FP127) {
    return FP127.wrap(FP127Lib.mul(FP127.unwrap(a), FP127.unwrap(b)));
}

function div(FP127 a, FP127 b) pure returns (FP127) {
    return FP127.wrap(FP127Lib.div(FP127.unwrap(a), FP127.unwrap(b)));
}

function neg(FP127 x) pure returns (FP127) {
    return FP127.wrap(FP127Lib.neg(FP127.unwrap(x)));
}

function lt(FP127 a, FP127 b) pure returns (bool) {
    return FP127.unwrap(a) < FP127.unwrap(b);
}

function gt(FP127 a, FP127 b) pure returns (bool) {
    return FP127.unwrap(a) > FP127.unwrap(b);
}

function le(FP127 a, FP127 b) pure returns (bool) {
    return FP127.unwrap(a) <= FP127.unwrap(b);
}

function ge(FP127 a, FP127 b) pure returns (bool) {
    return FP127.unwrap(a) >= FP127.unwrap(b);
}

function eq(FP127 a, FP127 b) pure returns (bool) {
    return FP127.unwrap(a) == FP127.unwrap(b);
}

function ne(FP127 a, FP127 b) pure returns (bool) {
    return FP127.unwrap(a) != FP127.unwrap(b);
}

// ---- directed rounding -----------------------------------------------------

function mulDown(FP127 a, FP127 b) pure returns (FP127) {
    return FP127.wrap(FP127Lib.mulDown(FP127.unwrap(a), FP127.unwrap(b)));
}

function mulUp(FP127 a, FP127 b) pure returns (FP127) {
    return FP127.wrap(FP127Lib.mulUp(FP127.unwrap(a), FP127.unwrap(b)));
}

function divDown(FP127 a, FP127 b) pure returns (FP127) {
    return FP127.wrap(FP127Lib.divDown(FP127.unwrap(a), FP127.unwrap(b)));
}

function divUp(FP127 a, FP127 b) pure returns (FP127) {
    return FP127.wrap(FP127Lib.divUp(FP127.unwrap(a), FP127.unwrap(b)));
}

// ---- exponentials, logarithms, powers and roots ----------------------------

function exp2(FP127 x) pure returns (FP127) {
    return FP127.wrap(FP127Lib.exp2(FP127.unwrap(x)));
}

function exp(FP127 x) pure returns (FP127) {
    return FP127.wrap(FP127Lib.exp(FP127.unwrap(x)));
}

function exp10(FP127 x) pure returns (FP127) {
    return FP127.wrap(FP127Lib.exp10(FP127.unwrap(x)));
}

function log2(FP127 x) pure returns (FP127) {
    return FP127.wrap(FP127Lib.log2(FP127.unwrap(x)));
}

function ln(FP127 x) pure returns (FP127) {
    return FP127.wrap(FP127Lib.ln(FP127.unwrap(x)));
}

function log10(FP127 x) pure returns (FP127) {
    return FP127.wrap(FP127Lib.log10(FP127.unwrap(x)));
}

function log2Up(FP127 x) pure returns (FP127) {
    return FP127.wrap(FP127Lib.log2Up(FP127.unwrap(x)));
}

function sqrt(FP127 x) pure returns (FP127) {
    return FP127.wrap(FP127Lib.sqrt(FP127.unwrap(x)));
}

function pow(FP127 x, FP127 y) pure returns (FP127) {
    return FP127.wrap(FP127Lib.pow(FP127.unwrap(x), FP127.unwrap(y)));
}

/// x^floor(n); n is an FP127 value, as in FP127Lib.
function powu(FP127 x, FP127 n) pure returns (FP127) {
    return FP127.wrap(FP127Lib.powu(FP127.unwrap(x), FP127.unwrap(n)));
}

/// (1 + rate)^floor(n); n is an FP127 value, as in FP127Lib.
function compound(FP127 rate, FP127 n) pure returns (FP127) {
    return FP127.wrap(FP127Lib.compound(FP127.unwrap(rate), FP127.unwrap(n)));
}

function cbrt(FP127 x) pure returns (FP127) {
    return FP127.wrap(FP127Lib.cbrt(FP127.unwrap(x)));
}

function gavg(FP127 a, FP127 b) pure returns (FP127) {
    return FP127.wrap(FP127Lib.gavg(FP127.unwrap(a), FP127.unwrap(b)));
}

function hypot(FP127 a, FP127 b) pure returns (FP127) {
    return FP127.wrap(FP127Lib.hypot(FP127.unwrap(a), FP127.unwrap(b)));
}

function inv(FP127 x) pure returns (FP127) {
    return FP127.wrap(FP127Lib.inv(FP127.unwrap(x)));
}

// ---- elementary ------------------------------------------------------------

function abs(FP127 x) pure returns (FP127) {
    return FP127.wrap(FP127Lib.abs(FP127.unwrap(x)));
}

function sign(FP127 x) pure returns (FP127) {
    return FP127.wrap(FP127Lib.sign(FP127.unwrap(x)));
}

function min(FP127 a, FP127 b) pure returns (FP127) {
    return FP127.wrap(FP127Lib.min(FP127.unwrap(a), FP127.unwrap(b)));
}

function max(FP127 a, FP127 b) pure returns (FP127) {
    return FP127.wrap(FP127Lib.max(FP127.unwrap(a), FP127.unwrap(b)));
}

function clamp(FP127 x, FP127 lo, FP127 hi) pure returns (FP127) {
    return FP127.wrap(FP127Lib.clamp(FP127.unwrap(x), FP127.unwrap(lo), FP127.unwrap(hi)));
}

function avg(FP127 a, FP127 b) pure returns (FP127) {
    return FP127.wrap(FP127Lib.avg(FP127.unwrap(a), FP127.unwrap(b)));
}

function zeroFloorSub(FP127 a, FP127 b) pure returns (FP127) {
    return FP127.wrap(FP127Lib.zeroFloorSub(FP127.unwrap(a), FP127.unwrap(b)));
}

function dist(FP127 a, FP127 b) pure returns (FP127) {
    return FP127.wrap(FP127Lib.dist(FP127.unwrap(a), FP127.unwrap(b)));
}

function lerp(FP127 a, FP127 b, FP127 t) pure returns (FP127) {
    return FP127.wrap(FP127Lib.lerp(FP127.unwrap(a), FP127.unwrap(b), FP127.unwrap(t)));
}

function floor(FP127 x) pure returns (FP127) {
    return FP127.wrap(FP127Lib.floor(FP127.unwrap(x)));
}

function ceil(FP127 x) pure returns (FP127) {
    return FP127.wrap(FP127Lib.ceil(FP127.unwrap(x)));
}

function frac(FP127 x) pure returns (FP127) {
    return FP127.wrap(FP127Lib.frac(FP127.unwrap(x)));
}

function round(FP127 x) pure returns (FP127) {
    return FP127.wrap(FP127Lib.round(FP127.unwrap(x)));
}

/// floor(n)!; n is an FP127 value, as in FP127Lib.
function factorial(FP127 n) pure returns (FP127) {
    return FP127.wrap(FP127Lib.factorial(FP127.unwrap(n)));
}

// ---- special functions -----------------------------------------------------

function lambertW0(FP127 x) pure returns (FP127) {
    return FP127.wrap(FP127Lib.lambertW0(FP127.unwrap(x)));
}

function lambertWm1(FP127 x) pure returns (FP127) {
    return FP127.wrap(FP127Lib.lambertWm1(FP127.unwrap(x)));
}

function log1p(FP127 x) pure returns (FP127) {
    return FP127.wrap(FP127Lib.log1p(FP127.unwrap(x)));
}

function expm1(FP127 x) pure returns (FP127) {
    return FP127.wrap(FP127Lib.expm1(FP127.unwrap(x)));
}

function sinh(FP127 x) pure returns (FP127) {
    return FP127.wrap(FP127Lib.sinh(FP127.unwrap(x)));
}

function cosh(FP127 x) pure returns (FP127) {
    return FP127.wrap(FP127Lib.cosh(FP127.unwrap(x)));
}

function tanh(FP127 x) pure returns (FP127) {
    return FP127.wrap(FP127Lib.tanh(FP127.unwrap(x)));
}

function atanh(FP127 x) pure returns (FP127) {
    return FP127.wrap(FP127Lib.atanh(FP127.unwrap(x)));
}

function erf(FP127 x) pure returns (FP127) {
    return FP127.wrap(FP127Lib.erf(FP127.unwrap(x)));
}

function erfc(FP127 x) pure returns (FP127) {
    return FP127.wrap(FP127Lib.erfc(FP127.unwrap(x)));
}

function normCdf(FP127 x) pure returns (FP127) {
    return FP127.wrap(FP127Lib.normCdf(FP127.unwrap(x)));
}
