+++
title = "The two libraries"
description = "Blockulator is two math libraries for the EVM, BL19 and BL127. This page says what each one is and which one to use."

[extra]
group = "library"
# this address was the BL127 page: its sections are now on /library/bl127/, and the integration rules on /library/integrating/
[[extra.forwards]]
anchors = ["install", "typed-api", "the-format", "the-deployed-contracts", "integrating", "the-ops", "for-agents"]
to = "/library/bl127/"
[[extra.forwards]]
anchors = ["rule-1-bunni-v2", "rule-2-resupply", "rule-2-balancer-v2", "rule-2-balancer-v1-the-counter-example", "the-edge-ops", "divide-last", "keep-an-index-as-its-logarithm"]
to = "/library/integrating/"
+++

Blockulator is two math libraries for the EVM. Both are written in Yul and called from Solidity, and both store a number in one `int256`. Every op of both is exact or is rounded once, in the direction the op states, and an op reverts when its result is too large for the format.

## BL19

[BL19](/library/bl19/) is a 256-bit binary float. It keeps about 71 correct digits at any size, from about 10<sup>−78,913</sup> to about 10<sup>78,913</sup>. It has 65 ops, the special functions among them.

Use BL19 when your values span many sizes, or when you are checking another library's answer and want the most digits.

## BL127

[BL127](/library/bl127/) is signed fixed point with 128 bits after the point. It keeps 38 correct digits at 1, 32 at 10<sup>−6</sup> and 8 at 10<sup>−30</sup>, and its range is ±1.7 × 10<sup>38</sup>. It has 53 ops, and BL19 has every one of them.

Use BL127 when your values stay near 1 and gas matters. Called inline, BL127 costs less gas than BL19 on 48 of those 53 ops: `ln` costs 1,944 gas against 3,100, and `mul` costs 267 against 530. BL19 costs less on `abs`, `expm1`, `sinh`, `cosh` and `tanh`.

## What both need, and how we know they are right

Both libraries need the CLZ opcode (EIP-7939), so they run only on chains that have it. Both are deployed on Ethereum Sepolia and not yet on mainnet, and neither has had a third-party audit. Their assurance is the [formal proofs](/proofs/), the sweeps against correctly rounded truth, and the fact that every measurement on this site can be rerun from the repository.

## Using them

[Check your math](/library/checking/) shows how to keep the library you have and measure it against BL19. [Integrating](/library/integrating/) has the rules for using either library inside a contract. [Move to BL19 or BL127](/library/moving/) covers moving from Solady, PRBMath, ABDK or ABDKMathQuad, with what each of them does better.
