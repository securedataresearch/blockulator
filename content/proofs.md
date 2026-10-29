+++
title = "Proofs"
description = "The core arithmetic and directed rounding of BL127 and BL19, proved against independent specifications for every input."
template = "proofs.html"
path = "proofs"

[extra]
group = "results"
+++

A test checks the inputs it was given. These checks cover every input: Halmos runs each op of the inline libraries with symbolic arguments, all 2<sup>256</sup> or 2<sup>512</sup> of them at once, and the solver shows that no input makes the op return a different word, or revert with a different error, from a reference specification written separately from the library code. The specifications are plain Solidity on exact integers, short enough to read: [`Ref127.sol`]({{ config.extra.repo }}/blob/master/test/proofs/Ref127.sol), [`Ref19.sol`]({{ config.extra.repo }}/blob/master/test/proofs/Ref19.sol). BL19's reference rounds to 237 bits from comparisons on the exact value, not from the library's normalisation.

Where the proofs found something, it is on this page: two BL127 ops left their documented semantics on a narrow family of inputs (`sqrt` one above the floor at a perfect square plus one, `mulUp` reverting where its result fits); both are fixed in 3.0 and each is pinned as a regression test. BL127's square root is proved outside the solver by an exact-integer argument about its Newton iteration; BL19's, and BL127's `gavg` and `hypot`, are fuzzed against exact integer roots, not proved. Method, trust base and limits: [`docs/proofs.md`]({{ config.extra.repo }}/blob/master/docs/proofs.md).
