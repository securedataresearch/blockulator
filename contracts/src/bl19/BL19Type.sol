// SPDX-License-Identifier: MIT
pragma solidity ^0.8.31;

import {BL19Lib} from "./BL19Lib.sol";
import {BL127} from "../bl127/BL127Type.sol";

/// @title BL19Type
/// @notice The typed face of BL19Lib: `type BL19 is int256`, with + - * /,
///         unary -, < > <= >= == != bound to the library, and every other op
///         attached, so `x.exp()` and `a * b + c` compile to the same library
///         calls as the raw form. Opt in by importing this file; BL19Lib is
///         unchanged and the two mix freely through `BL19.wrap` /
///         `BL19.unwrap` (free at runtime).
/// @dev Every function is a pure free function, as solc requires of a bound
///      operator, and only re-types its arguments and result: the same words,
///      the same reverts (BL19Lib's errors), and the same gas
///      (test/typed/Typed19.t.sol checks both). The comparisons are
///      BL19Lib.lt and BL19Lib.eq read as bools (a < b, b < a, !(b < a),
///      ...), so a word that is not a number reverts OutOfRange in every one,
///      as in the library. The typed BL127 <-> BL19 conversions live here,
///      since this file sees both types: y.toBL127() is attached; toBL19(x)
///      is a free function (attach it in your own file with
///      `using {toBL19} for BL127;` to write x.toBL19()).
///      Names follow BL19Lib's ops. Functions that take a plain integer
///      instead of an BL19 carry the prefix (`bl19FromWad`), so this file
///      and BL127Type.sol can be imported into one scope; only ONE and PI then
///      need an alias (`import {ONE as ONE19} from ...`), as PRBMath's UNIT.

type BL19 is int256;

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
} for BL19 global;

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
    toBL127,
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
} for BL19 global;

// 1.
BL19 constant ONE = BL19.wrap(BL19Lib.ONE);
// pi, correctly rounded.
BL19 constant PI = BL19.wrap(BL19Lib.PI);

// ---- conversions -----------------------------------------------------------

/// The raw word as an BL19: BL19.wrap, PRBMath's sd().
function bl19(int256 raw) pure returns (BL19) {
    return BL19.wrap(raw);
}

/// The raw word: BL19.unwrap, attached as x.unwrap().
function unwrap(BL19 x) pure returns (int256) {
    return BL19.unwrap(x);
}

/// BL19Lib.fromUint: exact below 2^237, rounded once above.
function bl19FromUint(uint256 x) pure returns (BL19) {
    return BL19.wrap(BL19Lib.fromUint(x));
}

function bl19FromUintDown(uint256 x) pure returns (BL19) {
    return BL19.wrap(BL19Lib.fromUintDown(x));
}

function bl19FromUintUp(uint256 x) pure returns (BL19) {
    return BL19.wrap(BL19Lib.fromUintUp(x));
}

/// The integer n: BL19Lib.fromUint of |n| with the sign restored, so exact
/// below 2^237 and rounded once (half up on the magnitude) above.
function bl19FromInt(int256 n) pure returns (BL19) {
    if (n >= 0) return BL19.wrap(BL19Lib.fromUint(uint256(n)));
    unchecked {
        return BL19.wrap(BL19Lib.neg(BL19Lib.fromUint(uint256(-(n + 1)) + 1)));
    }
}

/// An 18-decimal signed word: BL19Lib.fromFixed18.
function bl19FromFixed18(int256 x) pure returns (BL19) {
    return BL19.wrap(BL19Lib.fromFixed18(x));
}

/// A WAD (unsigned, 18 decimals): BL19Lib.fromFixed18 of the same integer.
/// Reverts with Overflow above 2^255 - 1, which has no int256 word.
function bl19FromWad(uint256 x) pure returns (BL19) {
    if (x > uint256(type(int256).max)) revert BL19Lib.Overflow();
    return BL19.wrap(BL19Lib.fromFixed18(int256(x)));
}

/// An BL127 value as an BL19: BL19Lib.fromBL127, exact below 2^237 raw.
function toBL19(BL127 x) pure returns (BL19) {
    return BL19.wrap(BL19Lib.fromBL127(BL127.unwrap(x)));
}

/// The BL127 word nearest to x: BL19Lib.toBL127.
function toBL127(BL19 x) pure returns (BL127) {
    return BL127.wrap(BL19Lib.toBL127(BL19.unwrap(x)));
}

function toFixed18(BL19 x) pure returns (int256) {
    return BL19Lib.toFixed18(BL19.unwrap(x));
}

function toFixed18Down(BL19 x) pure returns (int256) {
    return BL19Lib.toFixed18Down(BL19.unwrap(x));
}

function toFixed18Up(BL19 x) pure returns (int256) {
    return BL19Lib.toFixed18Up(BL19.unwrap(x));
}

/// The WAD at or below x: what a protocol pays out. Reverts with OutOfRange
/// when that is negative.
function toWadDown(BL19 x) pure returns (uint256) {
    int256 r = BL19Lib.toFixed18Down(BL19.unwrap(x));
    if (r < 0) revert BL19Lib.OutOfRange();
    return uint256(r);
}

/// The WAD at or above x: what a protocol charges. Reverts with OutOfRange
/// when that is negative.
function toWadUp(BL19 x) pure returns (uint256) {
    int256 r = BL19Lib.toFixed18Up(BL19.unwrap(x));
    if (r < 0) revert BL19Lib.OutOfRange();
    return uint256(r);
}

function toUintDown(BL19 x) pure returns (uint256) {
    return BL19Lib.toUintDown(BL19.unwrap(x));
}

function toUintUp(BL19 x) pure returns (uint256) {
    return BL19Lib.toUintUp(BL19.unwrap(x));
}

function toIntDown(BL19 x) pure returns (int256) {
    return BL19Lib.toIntDown(BL19.unwrap(x));
}

function toIntUp(BL19 x) pure returns (int256) {
    return BL19Lib.toIntUp(BL19.unwrap(x));
}

// ---- operators -------------------------------------------------------------

function add(BL19 a, BL19 b) pure returns (BL19) {
    return BL19.wrap(BL19Lib.add(BL19.unwrap(a), BL19.unwrap(b)));
}

function sub(BL19 a, BL19 b) pure returns (BL19) {
    return BL19.wrap(BL19Lib.sub(BL19.unwrap(a), BL19.unwrap(b)));
}

function mul(BL19 a, BL19 b) pure returns (BL19) {
    return BL19.wrap(BL19Lib.mul(BL19.unwrap(a), BL19.unwrap(b)));
}

function div(BL19 a, BL19 b) pure returns (BL19) {
    return BL19.wrap(BL19Lib.div(BL19.unwrap(a), BL19.unwrap(b)));
}

function neg(BL19 x) pure returns (BL19) {
    return BL19.wrap(BL19Lib.neg(BL19.unwrap(x)));
}

function lt(BL19 a, BL19 b) pure returns (bool) {
    return BL19Lib.lt(BL19.unwrap(a), BL19.unwrap(b)) != 0;
}

function gt(BL19 a, BL19 b) pure returns (bool) {
    return BL19Lib.lt(BL19.unwrap(b), BL19.unwrap(a)) != 0;
}

function le(BL19 a, BL19 b) pure returns (bool) {
    return BL19Lib.lt(BL19.unwrap(b), BL19.unwrap(a)) == 0;
}

function ge(BL19 a, BL19 b) pure returns (bool) {
    return BL19Lib.lt(BL19.unwrap(a), BL19.unwrap(b)) == 0;
}

function eq(BL19 a, BL19 b) pure returns (bool) {
    return BL19Lib.eq(BL19.unwrap(a), BL19.unwrap(b)) != 0;
}

function ne(BL19 a, BL19 b) pure returns (bool) {
    return BL19Lib.eq(BL19.unwrap(a), BL19.unwrap(b)) == 0;
}

/// -1, 0 or 1 as a plain integer: BL19Lib.cmp.
function cmp(BL19 a, BL19 b) pure returns (int256) {
    return BL19Lib.cmp(BL19.unwrap(a), BL19.unwrap(b));
}

// ---- directed rounding -----------------------------------------------------

function mulDown(BL19 a, BL19 b) pure returns (BL19) {
    return BL19.wrap(BL19Lib.mulDown(BL19.unwrap(a), BL19.unwrap(b)));
}

function mulUp(BL19 a, BL19 b) pure returns (BL19) {
    return BL19.wrap(BL19Lib.mulUp(BL19.unwrap(a), BL19.unwrap(b)));
}

function divDown(BL19 a, BL19 b) pure returns (BL19) {
    return BL19.wrap(BL19Lib.divDown(BL19.unwrap(a), BL19.unwrap(b)));
}

function divUp(BL19 a, BL19 b) pure returns (BL19) {
    return BL19.wrap(BL19Lib.divUp(BL19.unwrap(a), BL19.unwrap(b)));
}

// ---- exponentials, logarithms, powers and roots ----------------------------

function sqrt(BL19 x) pure returns (BL19) {
    return BL19.wrap(BL19Lib.sqrt(BL19.unwrap(x)));
}

function exp(BL19 x) pure returns (BL19) {
    return BL19.wrap(BL19Lib.exp(BL19.unwrap(x)));
}

function ln(BL19 x) pure returns (BL19) {
    return BL19.wrap(BL19Lib.ln(BL19.unwrap(x)));
}

function pow(BL19 x, BL19 y) pure returns (BL19) {
    return BL19.wrap(BL19Lib.pow(BL19.unwrap(x), BL19.unwrap(y)));
}

/// x^n; n is a plain integer, as in BL19Lib.
function powu(BL19 x, int256 n) pure returns (BL19) {
    return BL19.wrap(BL19Lib.powu(BL19.unwrap(x), n));
}

/// (1 + rate)^n; n is a plain integer, as in BL19Lib.
function compound(BL19 rate, int256 n) pure returns (BL19) {
    return BL19.wrap(BL19Lib.compound(BL19.unwrap(rate), n));
}

function exp2(BL19 x) pure returns (BL19) {
    return BL19.wrap(BL19Lib.exp2(BL19.unwrap(x)));
}

function exp10(BL19 x) pure returns (BL19) {
    return BL19.wrap(BL19Lib.exp10(BL19.unwrap(x)));
}

function log2(BL19 x) pure returns (BL19) {
    return BL19.wrap(BL19Lib.log2(BL19.unwrap(x)));
}

function log10(BL19 x) pure returns (BL19) {
    return BL19.wrap(BL19Lib.log10(BL19.unwrap(x)));
}

function log2Up(BL19 x) pure returns (BL19) {
    return BL19.wrap(BL19Lib.log2Up(BL19.unwrap(x)));
}

function cbrt(BL19 x) pure returns (BL19) {
    return BL19.wrap(BL19Lib.cbrt(BL19.unwrap(x)));
}

function gavg(BL19 a, BL19 b) pure returns (BL19) {
    return BL19.wrap(BL19Lib.gavg(BL19.unwrap(a), BL19.unwrap(b)));
}

function hypot(BL19 a, BL19 b) pure returns (BL19) {
    return BL19.wrap(BL19Lib.hypot(BL19.unwrap(a), BL19.unwrap(b)));
}

function inv(BL19 x) pure returns (BL19) {
    return BL19.wrap(BL19Lib.inv(BL19.unwrap(x)));
}

// ---- elementary ------------------------------------------------------------

function abs(BL19 x) pure returns (BL19) {
    return BL19.wrap(BL19Lib.abs(BL19.unwrap(x)));
}

function sign(BL19 x) pure returns (BL19) {
    return BL19.wrap(BL19Lib.sign(BL19.unwrap(x)));
}

function min(BL19 a, BL19 b) pure returns (BL19) {
    return BL19.wrap(BL19Lib.min(BL19.unwrap(a), BL19.unwrap(b)));
}

function max(BL19 a, BL19 b) pure returns (BL19) {
    return BL19.wrap(BL19Lib.max(BL19.unwrap(a), BL19.unwrap(b)));
}

function clamp(BL19 x, BL19 lo, BL19 hi) pure returns (BL19) {
    return BL19.wrap(BL19Lib.clamp(BL19.unwrap(x), BL19.unwrap(lo), BL19.unwrap(hi)));
}

function avg(BL19 a, BL19 b) pure returns (BL19) {
    return BL19.wrap(BL19Lib.avg(BL19.unwrap(a), BL19.unwrap(b)));
}

function dist(BL19 a, BL19 b) pure returns (BL19) {
    return BL19.wrap(BL19Lib.dist(BL19.unwrap(a), BL19.unwrap(b)));
}

function zeroFloorSub(BL19 a, BL19 b) pure returns (BL19) {
    return BL19.wrap(BL19Lib.zeroFloorSub(BL19.unwrap(a), BL19.unwrap(b)));
}

function lerp(BL19 a, BL19 b, BL19 t) pure returns (BL19) {
    return BL19.wrap(BL19Lib.lerp(BL19.unwrap(a), BL19.unwrap(b), BL19.unwrap(t)));
}

function floor(BL19 x) pure returns (BL19) {
    return BL19.wrap(BL19Lib.floor(BL19.unwrap(x)));
}

function ceil(BL19 x) pure returns (BL19) {
    return BL19.wrap(BL19Lib.ceil(BL19.unwrap(x)));
}

function frac(BL19 x) pure returns (BL19) {
    return BL19.wrap(BL19Lib.frac(BL19.unwrap(x)));
}

function round(BL19 x) pure returns (BL19) {
    return BL19.wrap(BL19Lib.round(BL19.unwrap(x)));
}

/// floor(n)!; n is an BL19 number, as in BL19Lib.
function factorial(BL19 n) pure returns (BL19) {
    return BL19.wrap(BL19Lib.factorial(BL19.unwrap(n)));
}

// ---- special functions -----------------------------------------------------

function log1p(BL19 x) pure returns (BL19) {
    return BL19.wrap(BL19Lib.log1p(BL19.unwrap(x)));
}

function expm1(BL19 x) pure returns (BL19) {
    return BL19.wrap(BL19Lib.expm1(BL19.unwrap(x)));
}

function erf(BL19 x) pure returns (BL19) {
    return BL19.wrap(BL19Lib.erf(BL19.unwrap(x)));
}

function erfc(BL19 x) pure returns (BL19) {
    return BL19.wrap(BL19Lib.erfc(BL19.unwrap(x)));
}

function normCdf(BL19 x) pure returns (BL19) {
    return BL19.wrap(BL19Lib.normCdf(BL19.unwrap(x)));
}

function lambertW0(BL19 x) pure returns (BL19) {
    return BL19.wrap(BL19Lib.lambertW0(BL19.unwrap(x)));
}

function lambertWm1(BL19 x) pure returns (BL19) {
    return BL19.wrap(BL19Lib.lambertWm1(BL19.unwrap(x)));
}

function sinh(BL19 x) pure returns (BL19) {
    return BL19.wrap(BL19Lib.sinh(BL19.unwrap(x)));
}

function cosh(BL19 x) pure returns (BL19) {
    return BL19.wrap(BL19Lib.cosh(BL19.unwrap(x)));
}

function tanh(BL19 x) pure returns (BL19) {
    return BL19.wrap(BL19Lib.tanh(BL19.unwrap(x)));
}

function atanh(BL19 x) pure returns (BL19) {
    return BL19.wrap(BL19Lib.atanh(BL19.unwrap(x)));
}
