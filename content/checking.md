+++
title = "Check your math"
description = "Keep the library you have, and measure how far its answers are from the correctly rounded ones."
path = "library/checking"

[extra]
group = "library"
+++

You do not have to move to Blockulator to use it. BL19 keeps about 71 correct digits and rounds every op once, so its answer, cut to your format, is the answer your library should have returned. This page shows how to compare the two inside a Foundry test.

## One function

The example checks Solady's `expWad`. It calls your library, computes e<sup>x</sup> in BL19, rounds that down to 18 decimals, and returns the difference in wei.

```solidity
import {BL19Lib} from "@blockulator/contracts/bl19/BL19Lib.sol";
import {FixedPointMathLib} from "solady/utils/FixedPointMathLib.sol";

library CheckExample {
    function expWadGap(int256 xWad) internal pure returns (int256 yours, int256 correct, int256 gap) {
        yours = FixedPointMathLib.expWad(xWad);
        correct = BL19Lib.toFixed18Down(BL19Lib.exp(BL19Lib.fromFixed18(xWad)));
        gap = yours - correct;
    }
}
```

The file is [`test/examples/CheckExample.sol`]({{ config.extra.repo }}/blob/master/test/examples/CheckExample.sol), and [`Check.t.sol`]({{ config.extra.repo }}/blob/master/test/examples/Check.t.sol) asserts every figure below.

## What it finds

| x | Solady `expWad` | correctly rounded down | gap |
|---|---:|---:|---:|
| 1 | 2718281828459045235 | 2718281828459045235 | 0 |
| 3 | 20085536923187667741 | 20085536923187667740 | 1 wei |
| 10 | 22026465794806716516980 | 22026465794806716516957 | 23 wei |

Over the 200 inputs x = 0.05, 0.10, … 10.00, Solady's result differs from the correctly rounded one on 108, and the largest gap is 222 wei. A gap of 23 wei at e<sup>10</sup> is one part in 10<sup>21</sup>, so whether it matters depends on what you do with the result next: a single payout does not notice it, and an index multiplied ten thousand times can.

## Checking your own function

Replace `FixedPointMathLib.expWad` with your call, and `BL19Lib.exp` with the same function in BL19. Use `toFixed18Down` if your library rounds down and `toFixed18Up` if it rounds up. Then run your test over the inputs your protocol really sees.

BL19 needs the CLZ opcode (EIP-7939), so the test must compile with `evm_version = "osaka"` and solc 0.8.31 or later. Your production contract does not change.

## Checking without a test

Every op of BL19 and BL127 is also deployed on Ethereum Sepolia, so one `eth_call` returns the correctly rounded answer with no gas and no wallet. The addresses are on the [BL19](/library/bl19/) and [BL127](/library/bl127/) pages.
