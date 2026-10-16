+++
title = "FP127, the whole story"
description = "128-bit fixed point for the EVM: why I built it, what the Huff taught me, the port to Yul, and what it is not for."
+++

Bracketed references are cells in [`ladder.json`](/data/ladder.json), [`gas.json`](/data/gas.json) or [`precision.json`](/data/precision.json).

## What it is

FP127 is a signed 127.128 fixed-point library for the EVM: one `int256` per value, 128 fractional bits, 49 operations including `exp`, `ln`, `sqrt`, `pow`, an exact integer power, the error function and the normal distribution, both real branches of the Lambert W function and pi by Ramanujan's series, written as one Yul source that compiles to a deployed contract and to an inlinable Solidity library. It is validated against mpmath at 200 decimal places, and it is deployed on Sepolia at `0x6cFbCB928Ac068E84Ef793Dd1DFce4f8e9Cac1d1`.

The one number that matters: $10,000 at 10% APR compounded daily for a year, one multiplication per day. After 365 steps ABDK is right to 17 digits, Solady, PRBMath and Balancer to 16, ABDKMathQuad to 31, Maker's rpow to 24, FP127 to 36 [compound, N = 365]. The [ladder](/results/ladder/) has thirteen of these scenarios, and every cell is re-run against the chain.

## Why WAD loses digits

The full argument is on the [why](/why/) page. The short form: a WAD library has about 60 bits of fraction and 196 bits of overflow headroom that you cannot store a value in, every `mulWad` rounds once, and a protocol does not call it once. The slopes of every library's digit loss against N are the same, about one digit per decade. The intercepts are twenty digits apart, and the intercept is what you keep.

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

Per op, inline, median over the gas ladder [gas.json, lib]: `mul` 531 against Solady's 321, PRBMath's 641 and Quad's 1,036; `div` 981 against 329, 705 and 1,209; `exp` 5,366 against 547, 2,951 and 6,072; `ln` 1,035 against 731, 1,099 and 1,927; `sqrt` 3,632 against 622, 1,402 and 1,205; `normCdf` 23,487, the honest expensive one. Multiplication and division cost about what they cost in WAD. The transcendentals cost more because they compute twice as many bits, and `sqrt` in particular pays for seven Newton steps that make it bit-exact. Through the deployed object add the `staticcall`, about 700 gas, to every op. The full table is on the [per-op](/results/ops/) page.

## The edges

The ladder measures a slope. The [edges](/results/edges/) measure the cliffs: 139 probes, one call each at the end of a domain, through nine libraries, every cell either with its digits or with how the library had no answer: zero below its floor, a revert, an argument outside its word, or no way to compute the op [edges.json]. ln(1 + 10^-9), a per-second rate inside a logarithm, has 8 digits on an 18-decimal grid and 30 on FP127; exp(−42), a probability of one in 10^18, is zero on the grid and 21 digits here; 10^-10 × 10^-10 is zero on every grid but this one and Quad's; N(−9), the normal tail an option lives in, is zero on WAD and 21 digits here. And FP127's own walls are on the page: exp(−89) is zero, exp(89) reverts, 1.0001^887272 is one bit past the word, a root of 10^-30 keeps eight digits. ABDKMathQuad, the one float, keeps 29 to 34 at every probe, because its point moves; it also keeps four fewer digits than FP127 in the middle and rounds at every op, so it loses on every ladder.

The accrual maths of the protocols most of the money sits in are in the same tables, judged against the model each one states: Aave's and Morpho's three-term expansion of e^(rt) keeps 6 digits after one idle year and 1 after twenty-seven [accrual-continuous, N = 365 and 10,000]; Maker's rpow keeps 23 after ten thousand days [compound, N = 10,000]; Morpho's per-second rate in eighteen decimals has ten digits before any arithmetic. None of these are mistakes; each is right for the interval it was built for.

## What it is not for

Range, and the floor. FP127 tops out near 1.7 × 10^38 and its grid stops at 2^-128. That is every balance a protocol will ever hold in whole units, but it is not every raw `uint256` in wei: a token with 18 decimals and a 10^21 supply is at 10^39 in wei. FP127 is for the maths in the middle, the rate, the price, the ratio, the exponent, and the conversion back to wei is one `toFixed18` at the edge. It is not a replacement for the integer arithmetic of a transfer, it is not for ERC20 balances, and it is not cheap enough to put in a path that does not need the digits. If your protocol multiplies once and settles, Solady is cheaper and good enough. If it accrues, iterates, chains transcendentals or subtracts two large numbers that are nearly equal, the [ladder](/results/ladder/) is where you find out how many digits you have left.

## The second ruler

A fixed point spends 127 bits on a range nobody uses and still has walls; a float with half the word has no walls and four fewer digits. The other half of that word was idle, so I filled it. FP256 is a 256-bit binary float: one sign bit, a 19-bit exponent, a 236-bit fraction with an implicit one, about 71 digits at any magnitude from 10^−78,900 to 10^78,900, no NaN, no infinity, no subnormals. Every kernel in FP127 was already a significand engine (the integer power routine computes exactly that pair, a 256-bit mantissa and an exponent, before it rounds back to the grid), so release one took the kernels as they were: the arithmetic, the root, the comparisons and the conversions were exact to the 237-bit grid at every vector, and `exp`, `ln` and `pow` held about 145 bits. Release two refits the kernels for the wide word, at 2^−254 with 512-bit products, and every one of the nineteen ops is now rounded once, correctly, at every committed vector. Release one is live on Sepolia at `0x628b8dfC82954983a9E8E22056ffc767B4a26077`; release two is in the repository and deploys next. Both are documented on the [FP256](/library/fp256/) page.

On the ladder it holds 67 to 70 digits where the arithmetic is exact (daily compounding, the bonding curve, the cumulative product), 62 to 72 where exp or ln carry the step (per-second accrual, continuous accrual, the geometric mean, daily compounding by pow), the exact cap on the round trip (exp(ln x) returns the same word at every N), and 64 to 66 on the option walk at d₁ = −12, where FP127 keeps 3 and WAD zero [deep-tail-option, reference, N = 10,000]. On the edges it has no zero, no revert and no range anywhere: 71 digits of 10^−10 × 10^−10, of √10^−30 and of 1/10^−30, 71 to 72 of e^x from −100 to 136, 71 of ln(10^−30) and ln(10^38), 62 of ln(1 + 10^−9) and 62 to 65 of a per-second rate raised to a year of seconds, which is what a 71-digit input leaves after the cancellation [edges]. Pi through its own primitives reaches 47 digits at six terms where Quad stops at 33 [pi.md]. The price is the moving point: `add` 1,440 gas inline against FP127's 357, `mul` 1,366 against 524, `div` 2,115 against 938, `exp` 7,145, `ln` 6,882, `pow` 10,916; `sqrt` is cheaper, 2,794 against 3,441 [gas256.json]. FP127 stays the ruler for the middle of the number line, where it has 38 digits to the float's 71 at a third of the gas; FP256 is the ruler for everything the edges showed a fixed point cannot hold.

## The talk

The Huff-era version was presented at EthCC[9]: [youtube.com/watch?v=a_tL99NY-yc](https://www.youtube.com/watch?v=a_tL99NY-yc). The numbers in it are from March 2026 against code that has since been replaced; the current ones are on this site.
