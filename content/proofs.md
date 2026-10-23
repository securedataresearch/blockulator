+++
title = "Proofs"
description = "The core arithmetic and directed rounding of FP127 and FP19, proved against independent specifications for every input."
template = "proofs.html"
path = "proofs"
+++

A test checks the inputs it was given. These checks cover every input: Halmos runs each op of the inline libraries with symbolic arguments, all 2<sup>256</sup> or 2<sup>512</sup> of them at once, and the solver shows that no input makes the op return a different word, or revert with a different error, from a reference specification written separately from the library code. The specifications are plain Solidity on exact integers, short enough to read: [`Ref127.sol`]({{ config.extra.repo }}/blob/master/test/proofs/Ref127.sol), [`Ref19.sol`]({{ config.extra.repo }}/blob/master/test/proofs/Ref19.sol). FP19's reference rounds to 237 bits from comparisons on the exact value, not from the library's normalisation.

Where the proofs found something, it is on this page: two FP127 ops leave their documented semantics on a narrow family of inputs, each pinned by a test that fails once it is fixed. The square roots are fuzzed against exact integer roots, not proved. Method, trust base and limits: [`docs/proofs.md`]({{ config.extra.repo }}/blob/master/docs/proofs.md).
