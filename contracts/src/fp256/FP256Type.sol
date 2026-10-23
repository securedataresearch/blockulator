// SPDX-License-Identifier: MIT
pragma solidity ^0.8.31;

import {FP256Lib} from "./FP256Lib.sol";
import {FP127} from "../fp127/FP127Type.sol";

/// @title FP256Type
/// @notice The typed face of FP256Lib: `type FP256 is int256`, with + - * /,
///         unary -, < > <= >= == != bound to the library, and every other op
///         attached, so `x.exp()` and `a * b + c` compile to the same library
///         calls as the raw form. Opt in by importing this file; FP256Lib is
///         unchanged and the two mix freely through `FP256.wrap` /
///         `FP256.unwrap` (free at runtime).
/// @dev Every function is a pure free function, as solc requires of a bound
///      operator, and only re-types its arguments and result: the same words,
///      the same reverts (FP256Lib's errors), and the same gas
///      (test/typed/Typed256.t.sol checks both). The comparisons are
///      FP256Lib.lt and FP256Lib.eq read as bools (a < b, b < a, !(b < a),
///      ...), so a word that is not a number reverts OutOfRange in every one,
///      as in the library. The typed FP127 <-> FP256 conversions live here,
///      since this file sees both types: y.toFP127() is attached; toFP256(x)
///      is a free function (attach it in your own file with
///      `using {toFP256} for FP127;` to write x.toFP256()).
///      Names follow FP256Lib's ops. Functions that take a plain integer
///      instead of an FP256 carry the prefix (`fp256FromWad`), so this file
///      and FP127Type.sol can be imported into one scope; only ONE and PI then
///      need an alias (`import {ONE as ONE256} from ...`), as PRBMath's UNIT.

type FP256 is int256;

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
} for FP256 global;

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
} for FP256 global;

// 1.
FP256 constant ONE = FP256.wrap(FP256Lib.ONE);
// pi, correctly rounded.
FP256 constant PI = FP256.wrap(FP256Lib.PI);

// ---- conversions -----------------------------------------------------------

/// The raw word as an FP256: FP256.wrap, PRBMath's sd().
function fp256(int256 raw) pure returns (FP256) {
    return FP256.wrap(raw);
}

/// The raw word: FP256.unwrap, attached as x.unwrap().
function unwrap(FP256 x) pure returns (int256) {
    return FP256.unwrap(x);
}

/// FP256Lib.fromUint: exact below 2^237, rounded once above.
function fp256FromUint(uint256 x) pure returns (FP256) {
    return FP256.wrap(FP256Lib.fromUint(x));
}

function fp256FromUintDown(uint256 x) pure returns (FP256) {
    return FP256.wrap(FP256Lib.fromUintDown(x));
}

function fp256FromUintUp(uint256 x) pure returns (FP256) {
    return FP256.wrap(FP256Lib.fromUintUp(x));
}

/// The integer n: FP256Lib.fromUint of |n| with the sign restored, so exact
/// below 2^237 and rounded once (half up on the magnitude) above.
function fp256FromInt(int256 n) pure returns (FP256) {
    if (n >= 0) return FP256.wrap(FP256Lib.fromUint(uint256(n)));
    unchecked {
        return FP256.wrap(FP256Lib.neg(FP256Lib.fromUint(uint256(-(n + 1)) + 1)));
    }
}

/// An 18-decimal signed word: FP256Lib.fromFixed18.
function fp256FromFixed18(int256 x) pure returns (FP256) {
    return FP256.wrap(FP256Lib.fromFixed18(x));
}

/// A WAD (unsigned, 18 decimals): FP256Lib.fromFixed18 of the same integer.
/// Reverts with Overflow above 2^255 - 1, which has no int256 word.
function fp256FromWad(uint256 x) pure returns (FP256) {
    if (x > uint256(type(int256).max)) revert FP256Lib.Overflow();
    return FP256.wrap(FP256Lib.fromFixed18(int256(x)));
}

/// An FP127 value as an FP256: FP256Lib.fromFP127, exact below 2^237 raw.
function toFP256(FP127 x) pure returns (FP256) {
    return FP256.wrap(FP256Lib.fromFP127(FP127.unwrap(x)));
}

/// The FP127 word nearest to x: FP256Lib.toFP127.
function toFP127(FP256 x) pure returns (FP127) {
    return FP127.wrap(FP256Lib.toFP127(FP256.unwrap(x)));
}

function toFixed18(FP256 x) pure returns (int256) {
    return FP256Lib.toFixed18(FP256.unwrap(x));
}

function toFixed18Down(FP256 x) pure returns (int256) {
    return FP256Lib.toFixed18Down(FP256.unwrap(x));
}

function toFixed18Up(FP256 x) pure returns (int256) {
    return FP256Lib.toFixed18Up(FP256.unwrap(x));
}

/// The WAD at or below x: what a protocol pays out. Reverts with OutOfRange
/// when that is negative.
function toWadDown(FP256 x) pure returns (uint256) {
    int256 r = FP256Lib.toFixed18Down(FP256.unwrap(x));
    if (r < 0) revert FP256Lib.OutOfRange();
    return uint256(r);
}

/// The WAD at or above x: what a protocol charges. Reverts with OutOfRange
/// when that is negative.
function toWadUp(FP256 x) pure returns (uint256) {
    int256 r = FP256Lib.toFixed18Up(FP256.unwrap(x));
    if (r < 0) revert FP256Lib.OutOfRange();
    return uint256(r);
}

function toUintDown(FP256 x) pure returns (uint256) {
    return FP256Lib.toUintDown(FP256.unwrap(x));
}

function toUintUp(FP256 x) pure returns (uint256) {
    return FP256Lib.toUintUp(FP256.unwrap(x));
}

function toIntDown(FP256 x) pure returns (int256) {
    return FP256Lib.toIntDown(FP256.unwrap(x));
}

function toIntUp(FP256 x) pure returns (int256) {
    return FP256Lib.toIntUp(FP256.unwrap(x));
}

// ---- operators -------------------------------------------------------------

function add(FP256 a, FP256 b) pure returns (FP256) {
    return FP256.wrap(FP256Lib.add(FP256.unwrap(a), FP256.unwrap(b)));
}

function sub(FP256 a, FP256 b) pure returns (FP256) {
    return FP256.wrap(FP256Lib.sub(FP256.unwrap(a), FP256.unwrap(b)));
}

function mul(FP256 a, FP256 b) pure returns (FP256) {
    return FP256.wrap(FP256Lib.mul(FP256.unwrap(a), FP256.unwrap(b)));
}

function div(FP256 a, FP256 b) pure returns (FP256) {
    return FP256.wrap(FP256Lib.div(FP256.unwrap(a), FP256.unwrap(b)));
}

function neg(FP256 x) pure returns (FP256) {
    return FP256.wrap(FP256Lib.neg(FP256.unwrap(x)));
}

function lt(FP256 a, FP256 b) pure returns (bool) {
    return FP256Lib.lt(FP256.unwrap(a), FP256.unwrap(b)) != 0;
}

function gt(FP256 a, FP256 b) pure returns (bool) {
    return FP256Lib.lt(FP256.unwrap(b), FP256.unwrap(a)) != 0;
}

function le(FP256 a, FP256 b) pure returns (bool) {
    return FP256Lib.lt(FP256.unwrap(b), FP256.unwrap(a)) == 0;
}

function ge(FP256 a, FP256 b) pure returns (bool) {
    return FP256Lib.lt(FP256.unwrap(a), FP256.unwrap(b)) == 0;
}

function eq(FP256 a, FP256 b) pure returns (bool) {
    return FP256Lib.eq(FP256.unwrap(a), FP256.unwrap(b)) != 0;
}

function ne(FP256 a, FP256 b) pure returns (bool) {
    return FP256Lib.eq(FP256.unwrap(a), FP256.unwrap(b)) == 0;
}

/// -1, 0 or 1 as a plain integer: FP256Lib.cmp.
function cmp(FP256 a, FP256 b) pure returns (int256) {
    return FP256Lib.cmp(FP256.unwrap(a), FP256.unwrap(b));
}

// ---- directed rounding -----------------------------------------------------

function mulDown(FP256 a, FP256 b) pure returns (FP256) {
    return FP256.wrap(FP256Lib.mulDown(FP256.unwrap(a), FP256.unwrap(b)));
}

function mulUp(FP256 a, FP256 b) pure returns (FP256) {
    return FP256.wrap(FP256Lib.mulUp(FP256.unwrap(a), FP256.unwrap(b)));
}

function divDown(FP256 a, FP256 b) pure returns (FP256) {
    return FP256.wrap(FP256Lib.divDown(FP256.unwrap(a), FP256.unwrap(b)));
}

function divUp(FP256 a, FP256 b) pure returns (FP256) {
    return FP256.wrap(FP256Lib.divUp(FP256.unwrap(a), FP256.unwrap(b)));
}

// ---- exponentials, logarithms, powers and roots ----------------------------

function sqrt(FP256 x) pure returns (FP256) {
    return FP256.wrap(FP256Lib.sqrt(FP256.unwrap(x)));
}

function exp(FP256 x) pure returns (FP256) {
    return FP256.wrap(FP256Lib.exp(FP256.unwrap(x)));
}

function ln(FP256 x) pure returns (FP256) {
    return FP256.wrap(FP256Lib.ln(FP256.unwrap(x)));
}

function pow(FP256 x, FP256 y) pure returns (FP256) {
    return FP256.wrap(FP256Lib.pow(FP256.unwrap(x), FP256.unwrap(y)));
}

/// x^n; n is a plain integer, as in FP256Lib.
function powu(FP256 x, int256 n) pure returns (FP256) {
    return FP256.wrap(FP256Lib.powu(FP256.unwrap(x), n));
}

/// (1 + rate)^n; n is a plain integer, as in FP256Lib.
function compound(FP256 rate, int256 n) pure returns (FP256) {
    return FP256.wrap(FP256Lib.compound(FP256.unwrap(rate), n));
}

function exp2(FP256 x) pure returns (FP256) {
    return FP256.wrap(FP256Lib.exp2(FP256.unwrap(x)));
}

function exp10(FP256 x) pure returns (FP256) {
    return FP256.wrap(FP256Lib.exp10(FP256.unwrap(x)));
}

function log2(FP256 x) pure returns (FP256) {
    return FP256.wrap(FP256Lib.log2(FP256.unwrap(x)));
}

function log10(FP256 x) pure returns (FP256) {
    return FP256.wrap(FP256Lib.log10(FP256.unwrap(x)));
}

function log2Up(FP256 x) pure returns (FP256) {
    return FP256.wrap(FP256Lib.log2Up(FP256.unwrap(x)));
}

function cbrt(FP256 x) pure returns (FP256) {
    return FP256.wrap(FP256Lib.cbrt(FP256.unwrap(x)));
}

function gavg(FP256 a, FP256 b) pure returns (FP256) {
    return FP256.wrap(FP256Lib.gavg(FP256.unwrap(a), FP256.unwrap(b)));
}

function hypot(FP256 a, FP256 b) pure returns (FP256) {
    return FP256.wrap(FP256Lib.hypot(FP256.unwrap(a), FP256.unwrap(b)));
}

function inv(FP256 x) pure returns (FP256) {
    return FP256.wrap(FP256Lib.inv(FP256.unwrap(x)));
}

// ---- elementary ------------------------------------------------------------

function abs(FP256 x) pure returns (FP256) {
    return FP256.wrap(FP256Lib.abs(FP256.unwrap(x)));
}

function sign(FP256 x) pure returns (FP256) {
    return FP256.wrap(FP256Lib.sign(FP256.unwrap(x)));
}

function min(FP256 a, FP256 b) pure returns (FP256) {
    return FP256.wrap(FP256Lib.min(FP256.unwrap(a), FP256.unwrap(b)));
}

function max(FP256 a, FP256 b) pure returns (FP256) {
    return FP256.wrap(FP256Lib.max(FP256.unwrap(a), FP256.unwrap(b)));
}

function clamp(FP256 x, FP256 lo, FP256 hi) pure returns (FP256) {
    return FP256.wrap(FP256Lib.clamp(FP256.unwrap(x), FP256.unwrap(lo), FP256.unwrap(hi)));
}

function avg(FP256 a, FP256 b) pure returns (FP256) {
    return FP256.wrap(FP256Lib.avg(FP256.unwrap(a), FP256.unwrap(b)));
}

function dist(FP256 a, FP256 b) pure returns (FP256) {
    return FP256.wrap(FP256Lib.dist(FP256.unwrap(a), FP256.unwrap(b)));
}

function zeroFloorSub(FP256 a, FP256 b) pure returns (FP256) {
    return FP256.wrap(FP256Lib.zeroFloorSub(FP256.unwrap(a), FP256.unwrap(b)));
}

function lerp(FP256 a, FP256 b, FP256 t) pure returns (FP256) {
    return FP256.wrap(FP256Lib.lerp(FP256.unwrap(a), FP256.unwrap(b), FP256.unwrap(t)));
}

function floor(FP256 x) pure returns (FP256) {
    return FP256.wrap(FP256Lib.floor(FP256.unwrap(x)));
}

function ceil(FP256 x) pure returns (FP256) {
    return FP256.wrap(FP256Lib.ceil(FP256.unwrap(x)));
}

function frac(FP256 x) pure returns (FP256) {
    return FP256.wrap(FP256Lib.frac(FP256.unwrap(x)));
}

function round(FP256 x) pure returns (FP256) {
    return FP256.wrap(FP256Lib.round(FP256.unwrap(x)));
}

/// floor(n)!; n is an FP256 number, as in FP256Lib.
function factorial(FP256 n) pure returns (FP256) {
    return FP256.wrap(FP256Lib.factorial(FP256.unwrap(n)));
}

// ---- special functions -----------------------------------------------------

function log1p(FP256 x) pure returns (FP256) {
    return FP256.wrap(FP256Lib.log1p(FP256.unwrap(x)));
}

function expm1(FP256 x) pure returns (FP256) {
    return FP256.wrap(FP256Lib.expm1(FP256.unwrap(x)));
}

function erf(FP256 x) pure returns (FP256) {
    return FP256.wrap(FP256Lib.erf(FP256.unwrap(x)));
}

function erfc(FP256 x) pure returns (FP256) {
    return FP256.wrap(FP256Lib.erfc(FP256.unwrap(x)));
}

function normCdf(FP256 x) pure returns (FP256) {
    return FP256.wrap(FP256Lib.normCdf(FP256.unwrap(x)));
}

function lambertW0(FP256 x) pure returns (FP256) {
    return FP256.wrap(FP256Lib.lambertW0(FP256.unwrap(x)));
}

function lambertWm1(FP256 x) pure returns (FP256) {
    return FP256.wrap(FP256Lib.lambertWm1(FP256.unwrap(x)));
}

function sinh(FP256 x) pure returns (FP256) {
    return FP256.wrap(FP256Lib.sinh(FP256.unwrap(x)));
}

function cosh(FP256 x) pure returns (FP256) {
    return FP256.wrap(FP256Lib.cosh(FP256.unwrap(x)));
}

function tanh(FP256 x) pure returns (FP256) {
    return FP256.wrap(FP256Lib.tanh(FP256.unwrap(x)));
}

function atanh(FP256 x) pure returns (FP256) {
    return FP256.wrap(FP256Lib.atanh(FP256.unwrap(x)));
}
