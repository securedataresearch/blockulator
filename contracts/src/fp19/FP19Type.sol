// SPDX-License-Identifier: MIT
pragma solidity ^0.8.31;

import {FP19Lib} from "./FP19Lib.sol";
import {FP127} from "../fp127/FP127Type.sol";

/// @title FP19Type
/// @notice The typed face of FP19Lib: `type FP19 is int256`, with + - * /,
///         unary -, < > <= >= == != bound to the library, and every other op
///         attached, so `x.exp()` and `a * b + c` compile to the same library
///         calls as the raw form. Opt in by importing this file; FP19Lib is
///         unchanged and the two mix freely through `FP19.wrap` /
///         `FP19.unwrap` (free at runtime).
/// @dev Every function is a pure free function, as solc requires of a bound
///      operator, and only re-types its arguments and result: the same words,
///      the same reverts (FP19Lib's errors), and the same gas
///      (test/typed/Typed19.t.sol checks both). The comparisons are
///      FP19Lib.lt and FP19Lib.eq read as bools (a < b, b < a, !(b < a),
///      ...), so a word that is not a number reverts OutOfRange in every one,
///      as in the library. The typed FP127 <-> FP19 conversions live here,
///      since this file sees both types: y.toFP127() is attached; toFP19(x)
///      is a free function (attach it in your own file with
///      `using {toFP19} for FP127;` to write x.toFP19()).
///      Names follow FP19Lib's ops. Functions that take a plain integer
///      instead of an FP19 carry the prefix (`fp19FromWad`), so this file
///      and FP127Type.sol can be imported into one scope; only ONE and PI then
///      need an alias (`import {ONE as ONE19} from ...`), as PRBMath's UNIT.

type FP19 is int256;

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
} for FP19 global;

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
    cmp,
    unwrap,
    toFP127,
    toFixed18,
    toFixed18Down,
    toFixed18Up,
    toWadDown,
    toWadUp,
    toUintDown,
    toUintUp,
    toIntDown,
    toIntUp,
    mulDown,
    mulUp,
    divDown,
    divUp,
    sqrt,
    exp,
    ln,
    pow,
    powu,
    compound,
    exp2,
    exp10,
    log2,
    log10,
    log2Up,
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
    dist,
    zeroFloorSub,
    lerp,
    floor,
    ceil,
    frac,
    round,
    factorial,
    log1p,
    expm1,
    erf,
    erfc,
    normCdf,
    lambertW0,
    lambertWm1,
    sinh,
    cosh,
    tanh,
    atanh
} for FP19 global;

// 1.
FP19 constant ONE = FP19.wrap(FP19Lib.ONE);
// pi, correctly rounded.
FP19 constant PI = FP19.wrap(FP19Lib.PI);

// ---- conversions -----------------------------------------------------------

/// The raw word as an FP19: FP19.wrap, PRBMath's sd().
function fp19(int256 raw) pure returns (FP19) {
    return FP19.wrap(raw);
}

/// The raw word: FP19.unwrap, attached as x.unwrap().
function unwrap(FP19 x) pure returns (int256) {
    return FP19.unwrap(x);
}

/// FP19Lib.fromUint: exact below 2^237, rounded once above.
function fp19FromUint(uint256 x) pure returns (FP19) {
    return FP19.wrap(FP19Lib.fromUint(x));
}

function fp19FromUintDown(uint256 x) pure returns (FP19) {
    return FP19.wrap(FP19Lib.fromUintDown(x));
}

function fp19FromUintUp(uint256 x) pure returns (FP19) {
    return FP19.wrap(FP19Lib.fromUintUp(x));
}

/// The integer n: FP19Lib.fromUint of |n| with the sign restored, so exact
/// below 2^237 and rounded once (half up on the magnitude) above.
function fp19FromInt(int256 n) pure returns (FP19) {
    if (n >= 0) return FP19.wrap(FP19Lib.fromUint(uint256(n)));
    unchecked {
        return FP19.wrap(FP19Lib.neg(FP19Lib.fromUint(uint256(-(n + 1)) + 1)));
    }
}

/// An 18-decimal signed word: FP19Lib.fromFixed18.
function fp19FromFixed18(int256 x) pure returns (FP19) {
    return FP19.wrap(FP19Lib.fromFixed18(x));
}

/// A WAD (unsigned, 18 decimals): FP19Lib.fromFixed18 of the same integer.
/// Reverts with Overflow above 2^255 - 1, which has no int256 word.
function fp19FromWad(uint256 x) pure returns (FP19) {
    if (x > uint256(type(int256).max)) revert FP19Lib.Overflow();
    return FP19.wrap(FP19Lib.fromFixed18(int256(x)));
}

/// An FP127 value as an FP19: FP19Lib.fromFP127, exact below 2^237 raw.
function toFP19(FP127 x) pure returns (FP19) {
    return FP19.wrap(FP19Lib.fromFP127(FP127.unwrap(x)));
}

/// The FP127 word nearest to x: FP19Lib.toFP127.
function toFP127(FP19 x) pure returns (FP127) {
    return FP127.wrap(FP19Lib.toFP127(FP19.unwrap(x)));
}

function toFixed18(FP19 x) pure returns (int256) {
    return FP19Lib.toFixed18(FP19.unwrap(x));
}

function toFixed18Down(FP19 x) pure returns (int256) {
    return FP19Lib.toFixed18Down(FP19.unwrap(x));
}

function toFixed18Up(FP19 x) pure returns (int256) {
    return FP19Lib.toFixed18Up(FP19.unwrap(x));
}

/// The WAD at or below x: what a protocol pays out. Reverts with OutOfRange
/// when that is negative.
function toWadDown(FP19 x) pure returns (uint256) {
    int256 r = FP19Lib.toFixed18Down(FP19.unwrap(x));
    if (r < 0) revert FP19Lib.OutOfRange();
    return uint256(r);
}

/// The WAD at or above x: what a protocol charges. Reverts with OutOfRange
/// when that is negative.
function toWadUp(FP19 x) pure returns (uint256) {
    int256 r = FP19Lib.toFixed18Up(FP19.unwrap(x));
    if (r < 0) revert FP19Lib.OutOfRange();
    return uint256(r);
}

function toUintDown(FP19 x) pure returns (uint256) {
    return FP19Lib.toUintDown(FP19.unwrap(x));
}

function toUintUp(FP19 x) pure returns (uint256) {
    return FP19Lib.toUintUp(FP19.unwrap(x));
}

function toIntDown(FP19 x) pure returns (int256) {
    return FP19Lib.toIntDown(FP19.unwrap(x));
}

function toIntUp(FP19 x) pure returns (int256) {
    return FP19Lib.toIntUp(FP19.unwrap(x));
}

// ---- operators -------------------------------------------------------------

function add(FP19 a, FP19 b) pure returns (FP19) {
    return FP19.wrap(FP19Lib.add(FP19.unwrap(a), FP19.unwrap(b)));
}

function sub(FP19 a, FP19 b) pure returns (FP19) {
    return FP19.wrap(FP19Lib.sub(FP19.unwrap(a), FP19.unwrap(b)));
}

function mul(FP19 a, FP19 b) pure returns (FP19) {
    return FP19.wrap(FP19Lib.mul(FP19.unwrap(a), FP19.unwrap(b)));
}

function div(FP19 a, FP19 b) pure returns (FP19) {
    return FP19.wrap(FP19Lib.div(FP19.unwrap(a), FP19.unwrap(b)));
}

function neg(FP19 x) pure returns (FP19) {
    return FP19.wrap(FP19Lib.neg(FP19.unwrap(x)));
}

function lt(FP19 a, FP19 b) pure returns (bool) {
    return FP19Lib.lt(FP19.unwrap(a), FP19.unwrap(b)) != 0;
}

function gt(FP19 a, FP19 b) pure returns (bool) {
    return FP19Lib.lt(FP19.unwrap(b), FP19.unwrap(a)) != 0;
}

function le(FP19 a, FP19 b) pure returns (bool) {
    return FP19Lib.lt(FP19.unwrap(b), FP19.unwrap(a)) == 0;
}

function ge(FP19 a, FP19 b) pure returns (bool) {
    return FP19Lib.lt(FP19.unwrap(a), FP19.unwrap(b)) == 0;
}

function eq(FP19 a, FP19 b) pure returns (bool) {
    return FP19Lib.eq(FP19.unwrap(a), FP19.unwrap(b)) != 0;
}

function ne(FP19 a, FP19 b) pure returns (bool) {
    return FP19Lib.eq(FP19.unwrap(a), FP19.unwrap(b)) == 0;
}

/// -1, 0 or 1 as a plain integer: FP19Lib.cmp.
function cmp(FP19 a, FP19 b) pure returns (int256) {
    return FP19Lib.cmp(FP19.unwrap(a), FP19.unwrap(b));
}

// ---- directed rounding -----------------------------------------------------

function mulDown(FP19 a, FP19 b) pure returns (FP19) {
    return FP19.wrap(FP19Lib.mulDown(FP19.unwrap(a), FP19.unwrap(b)));
}

function mulUp(FP19 a, FP19 b) pure returns (FP19) {
    return FP19.wrap(FP19Lib.mulUp(FP19.unwrap(a), FP19.unwrap(b)));
}

function divDown(FP19 a, FP19 b) pure returns (FP19) {
    return FP19.wrap(FP19Lib.divDown(FP19.unwrap(a), FP19.unwrap(b)));
}

function divUp(FP19 a, FP19 b) pure returns (FP19) {
    return FP19.wrap(FP19Lib.divUp(FP19.unwrap(a), FP19.unwrap(b)));
}

// ---- exponentials, logarithms, powers and roots ----------------------------

function sqrt(FP19 x) pure returns (FP19) {
    return FP19.wrap(FP19Lib.sqrt(FP19.unwrap(x)));
}

function exp(FP19 x) pure returns (FP19) {
    return FP19.wrap(FP19Lib.exp(FP19.unwrap(x)));
}

function ln(FP19 x) pure returns (FP19) {
    return FP19.wrap(FP19Lib.ln(FP19.unwrap(x)));
}

function pow(FP19 x, FP19 y) pure returns (FP19) {
    return FP19.wrap(FP19Lib.pow(FP19.unwrap(x), FP19.unwrap(y)));
}

/// x^n; n is a plain integer, as in FP19Lib.
function powu(FP19 x, int256 n) pure returns (FP19) {
    return FP19.wrap(FP19Lib.powu(FP19.unwrap(x), n));
}

/// (1 + rate)^n; n is a plain integer, as in FP19Lib.
function compound(FP19 rate, int256 n) pure returns (FP19) {
    return FP19.wrap(FP19Lib.compound(FP19.unwrap(rate), n));
}

function exp2(FP19 x) pure returns (FP19) {
    return FP19.wrap(FP19Lib.exp2(FP19.unwrap(x)));
}

function exp10(FP19 x) pure returns (FP19) {
    return FP19.wrap(FP19Lib.exp10(FP19.unwrap(x)));
}

function log2(FP19 x) pure returns (FP19) {
    return FP19.wrap(FP19Lib.log2(FP19.unwrap(x)));
}

function log10(FP19 x) pure returns (FP19) {
    return FP19.wrap(FP19Lib.log10(FP19.unwrap(x)));
}

function log2Up(FP19 x) pure returns (FP19) {
    return FP19.wrap(FP19Lib.log2Up(FP19.unwrap(x)));
}

function cbrt(FP19 x) pure returns (FP19) {
    return FP19.wrap(FP19Lib.cbrt(FP19.unwrap(x)));
}

function gavg(FP19 a, FP19 b) pure returns (FP19) {
    return FP19.wrap(FP19Lib.gavg(FP19.unwrap(a), FP19.unwrap(b)));
}

function hypot(FP19 a, FP19 b) pure returns (FP19) {
    return FP19.wrap(FP19Lib.hypot(FP19.unwrap(a), FP19.unwrap(b)));
}

function inv(FP19 x) pure returns (FP19) {
    return FP19.wrap(FP19Lib.inv(FP19.unwrap(x)));
}

// ---- elementary ------------------------------------------------------------

function abs(FP19 x) pure returns (FP19) {
    return FP19.wrap(FP19Lib.abs(FP19.unwrap(x)));
}

function sign(FP19 x) pure returns (FP19) {
    return FP19.wrap(FP19Lib.sign(FP19.unwrap(x)));
}

function min(FP19 a, FP19 b) pure returns (FP19) {
    return FP19.wrap(FP19Lib.min(FP19.unwrap(a), FP19.unwrap(b)));
}

function max(FP19 a, FP19 b) pure returns (FP19) {
    return FP19.wrap(FP19Lib.max(FP19.unwrap(a), FP19.unwrap(b)));
}

function clamp(FP19 x, FP19 lo, FP19 hi) pure returns (FP19) {
    return FP19.wrap(FP19Lib.clamp(FP19.unwrap(x), FP19.unwrap(lo), FP19.unwrap(hi)));
}

function avg(FP19 a, FP19 b) pure returns (FP19) {
    return FP19.wrap(FP19Lib.avg(FP19.unwrap(a), FP19.unwrap(b)));
}

function dist(FP19 a, FP19 b) pure returns (FP19) {
    return FP19.wrap(FP19Lib.dist(FP19.unwrap(a), FP19.unwrap(b)));
}

function zeroFloorSub(FP19 a, FP19 b) pure returns (FP19) {
    return FP19.wrap(FP19Lib.zeroFloorSub(FP19.unwrap(a), FP19.unwrap(b)));
}

function lerp(FP19 a, FP19 b, FP19 t) pure returns (FP19) {
    return FP19.wrap(FP19Lib.lerp(FP19.unwrap(a), FP19.unwrap(b), FP19.unwrap(t)));
}

function floor(FP19 x) pure returns (FP19) {
    return FP19.wrap(FP19Lib.floor(FP19.unwrap(x)));
}

function ceil(FP19 x) pure returns (FP19) {
    return FP19.wrap(FP19Lib.ceil(FP19.unwrap(x)));
}

function frac(FP19 x) pure returns (FP19) {
    return FP19.wrap(FP19Lib.frac(FP19.unwrap(x)));
}

function round(FP19 x) pure returns (FP19) {
    return FP19.wrap(FP19Lib.round(FP19.unwrap(x)));
}

/// floor(n)!; n is an FP19 number, as in FP19Lib.
function factorial(FP19 n) pure returns (FP19) {
    return FP19.wrap(FP19Lib.factorial(FP19.unwrap(n)));
}

// ---- special functions -----------------------------------------------------

function log1p(FP19 x) pure returns (FP19) {
    return FP19.wrap(FP19Lib.log1p(FP19.unwrap(x)));
}

function expm1(FP19 x) pure returns (FP19) {
    return FP19.wrap(FP19Lib.expm1(FP19.unwrap(x)));
}

function erf(FP19 x) pure returns (FP19) {
    return FP19.wrap(FP19Lib.erf(FP19.unwrap(x)));
}

function erfc(FP19 x) pure returns (FP19) {
    return FP19.wrap(FP19Lib.erfc(FP19.unwrap(x)));
}

function normCdf(FP19 x) pure returns (FP19) {
    return FP19.wrap(FP19Lib.normCdf(FP19.unwrap(x)));
}

function lambertW0(FP19 x) pure returns (FP19) {
    return FP19.wrap(FP19Lib.lambertW0(FP19.unwrap(x)));
}

function lambertWm1(FP19 x) pure returns (FP19) {
    return FP19.wrap(FP19Lib.lambertWm1(FP19.unwrap(x)));
}

function sinh(FP19 x) pure returns (FP19) {
    return FP19.wrap(FP19Lib.sinh(FP19.unwrap(x)));
}

function cosh(FP19 x) pure returns (FP19) {
    return FP19.wrap(FP19Lib.cosh(FP19.unwrap(x)));
}

function tanh(FP19 x) pure returns (FP19) {
    return FP19.wrap(FP19Lib.tanh(FP19.unwrap(x)));
}

function atanh(FP19 x) pure returns (FP19) {
    return FP19.wrap(FP19Lib.atanh(FP19.unwrap(x)));
}
