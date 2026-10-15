+++
title = "FP127, the whole story"
description = "128-bit fixed point for the EVM: why I built it, what the Huff taught me, the port to Yul, and what it is not for."
+++

Every number here is a cell in a committed dataset, named in brackets: [`ladder.json`](/data/ladder.json), [`gas.json`](/data/gas.json) or [`precision.json`](/data/precision.json). Nothing on this page is a claim you have to take from me.

## What it is

FP127 is a signed 127.128 fixed-point library for the EVM: one `int256` per value, 128 fractional bits, 49 operations including `exp`, `ln`, `sqrt`, `pow`, an exact integer power, the error function and the normal distribution, both real branches of the Lambert W function and pi by Ramanujan's series, written as one Yul source that compiles to a deployed contract and to an inlinable Solidity library. It is validated against mpmath at 200 decimal places, and it is deployed on Sepolia at `0xe43F720861074497db2e974E5c4554E4A3b341B9`.

The one number that matters: $10,000 at 10% APR compounded daily for a year, one multiplication per day. After 365 steps ABDK is right to 17 digits, Solady and PRBMath to 16, FP127 to 36 [compound, N = 365]. The [ladder](/demo/) has eight of these scenarios, and you can re-run any cell against the chain.

## Why WAD loses digits

I wrote that up separately on the [why](/why/) page, because it is the part that matters to an auditor and it deserves its own argument. The short form: a WAD library has about 60 bits of fraction and 196 bits of overflow headroom that you cannot store a value in, every `mulWad` rounds once, and a protocol does not call it once. The slopes of every library's digit loss against N are the same, about one digit per decade. The intercepts are twenty digits apart, and the intercept is what you keep.

## The Huff era

The first FP127 was pure Huff. I wrote it that way because I wanted to count gas at the opcode level, and because at the time I thought the right shape was one contract at one address that every protocol `staticcall`s. It worked. It reached 34 operations, it was presented at EthCC[9] in Cannes, and the archived bytecode is still on Sepolia at `0xfae694D0c2c44181791F838c54Ed64C3151FfE30`, where the current test suites compare against it on every input.

It taught me three things. First, almost nobody will audit Huff. The pool of people who can read a dispatcher built from `dup1 __FUNC_SIG eq jumpi` chains is tiny, and a math library that cannot be audited is a liability no matter how good the numbers are. Second, `huffc` has an internal size limit on the expanded source. The combined macros hit it the day I added a second Lambert W branch, and `lambertWm1` never shipped. Third, a `staticcall` per op is about 700 gas, which is fine for a price calculation and rough in a hot loop. I asked two questions about this in a post I never got to publish: Huff versus Yul, and what the trust model should be. Both are answered below.

## The port

The current FP127 is one file, `FP127.yul.src`, holding Yul function bodies and nothing else. A generator reads it and emits two outputs. The deployed object wraps the bodies in a selector switch. The library, `FP127Lib.sol`, puts each body and the helpers it calls inside a `memory-safe` assembly block, one `internal pure` function per op. The suggestion to ship both forms came from Austin Griffith and Hadrien Croubois, and it dissolves the choice I was stuck on: the object gives you one address that every contract on a chain agrees with by construction, and the library gives you the same math inlined for the loops where the call overhead matters.

They agree because they are the same text. The equivalence suites then prove it: on the full `int256` domain, including which inputs revert and with what data, the object and the library return identical results, and both agree with the Huff bytecode on Sepolia on every input where the Huff computed a defined answer. The port also made arithmetic checked. Where the Huff wrapped silently on overflow, the Yul reverts with `Overflow()`, `DivisionByZero()` or `OutOfRange()`. Division, which the old documentation described as a 62-bit shortcut, turned out to have been a full 512-by-256 `mulDiv` all along; the docs were stale, and the equivalence suite is what caught it.

Precision per op is in [`precision.json`](/data/precision.json): integer, rounding and comparison ops bit-exact; `ln`, `log2` and `log10` within one ULP of the truth; `exp` and its family 146 bits at worst; `pow` 122; the Lambert W branches 126 to 128 everywhere except within 2^-20 of the branch point at −1/e, where the slope is infinite and one ULP of input moves the output by 2^-63. The transcendentals compute with 64 guard bits and round to nearest once, which the ladder forced: under the Huff's floor-everywhere policy `exp(ln(x))` came back 8 ULPs low on every call and the error marched in a straight line, and now it comes back the same word every time. The runtime is 10,401 bytes of the 24,576 allowed, and `lambertWm1`, the routine the Huff compiler could not fit, is in it.

## Trust model

The object has no storage, no owner, no proxy and no upgrade path. It was deployed with CREATE2 through the deterministic proxy at `0x4e59b44847b379578588920cA78FbF26c0B4956C` with the salt `"FP127 v1"`, so the same init code lands at the same address on every chain. It is verified on Sourcify as an exact match of the committed source. A change to the source is a new init code hash, a new salt string, a new address and a new row in the deployment record. There is nothing to freeze after an audit because there is nothing that can move. That was the answer to my second question: not a multisig, not a registry, just an address you can recompute from the repository.

## What it costs

Per op, inline, median over the gas ladder [gas.json, lib]: `mul` 472 against Solady's 347 and PRBMath's 647; `div` 939 against 361 and 715; `exp` 5,353 against 549 and 2,898; `ln` 999 against 720 and 1,052; `sqrt` 3,564 against 622 and 1,333. Multiplication and division cost about what they cost in WAD. The transcendentals cost more because they compute twice as many bits, and `sqrt` in particular pays for seven Newton steps that make it bit-exact. Through the deployed object add the `staticcall`, about 700 gas, to every op. The full table is on the [compare](/compare/) page.

## What it is not for

Range. FP127 tops out near 1.7 × 10^38. That is every balance a protocol will ever hold in whole units, but it is not every raw `uint256` in wei: a token with 18 decimals and a 10^21 supply is at 10^39 in wei. FP127 is for the maths in the middle, the rate, the price, the ratio, the exponent, and the conversion back to wei is one `toFixed18` at the edge. It is not a replacement for the integer arithmetic of a transfer, it is not for ERC20 balances, and it is not cheap enough to put in a path that does not need the digits. If your protocol multiplies once and settles, Solady is cheaper and good enough. If it accrues, iterates, chains transcendentals or subtracts two large numbers that are nearly equal, the [ladder](/demo/) is where you find out how many digits you have left.

## The talk

The Huff-era version was presented at EthCC[9]: [youtube.com/watch?v=a_tL99NY-yc](https://www.youtube.com/watch?v=a_tL99NY-yc). The numbers in it are from March 2026 against code that has since been replaced; the current ones are on this site.
