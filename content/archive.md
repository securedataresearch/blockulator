+++
title = "Archive"
description = "The games, the 21 Vyper calculators and the futures market that exercised the first FP127."
template = "archive.html"

[[extra.apps]]
kind = "calculators"
name = "21 Vyper calculators"
text = "One single-purpose contract each: π, e, τ, sin, cos, atan, √, 2^x, 10^x, e^x, ln, log₂, log₁₀, erf, Φ, φ, n!, ln n!, C(n,k), z-score, Gaussian tail, sinh, cosh, tanh, gcd and lcm. Each reads the legacy Huff FP127."
open = "vyper"
source = "contracts/src/tools"

[[extra.apps]]
kind = "market"
name = "Futures market"
text = "A small on-chain futures market with six payout distributions, priced through the legacy FP127."
open = "futures"
source = "contracts/src/market"

[[extra.apps]]
kind = "game"
name = "King of the Hill"
text = "Dethrone the king; the stakes grow every time."
address = "0x0DEEBef3228B5d0cD4158Dc367A5C4b31B6414A6"
open = "games/king-of-the-hill"
source = "contracts/src/games"

[[extra.apps]]
kind = "game"
name = "Dice Gods"
text = "Pick the least popular number."
address = "0x61d97822209D3B375c7B214597f1077F4879fD84"
open = "games/dice-gods"
source = "contracts/src/games"

[[extra.apps]]
kind = "game"
name = "Last Call"
text = "The last donor wins when the timer runs out."
address = "0xE0e1E3778d75E757fd4718FdF44bD4e0F5E73baa"
open = "games/last-call"
source = "contracts/src/games"

[[extra.apps]]
kind = "game"
name = "Time to Make the Donuts"
text = "The first donor each day at midnight."
address = "0xD222eCe3C1D844B23384F56d62E59F556e925C85"
open = "games/time-to-make-the-donuts"
source = "contracts/src/games"

[[extra.apps]]
kind = "game"
name = "Pay It Forward"
text = "Reward the previous donor."
address = "0x338C316e1FE9535e3569597D63267A8a1AD78855"
open = "games/pay-it-forward"
source = "contracts/src/games"

[[extra.apps]]
kind = "game"
name = "Pay It Backward"
text = "Get the previous player's stake."
address = "0x478A53b021639CFbAbe45d222B240ffE409FEE3f"
open = "games/pay-it-backward"
source = "contracts/src/games"

[[extra.apps]]
kind = "game"
name = "Pissing Contest"
text = "The biggest donation takes the pot."
address = "0x09CB63309F854788C76D9b6750598b2d86EADC8b"
open = "games/pissing-contest"
source = "contracts/src/games"

[[extra.apps]]
kind = "game"
name = "Satan, Moloch, Baal"
text = "Sacrifice ETH to your chosen demon."
address = "0x55Ec2808F3c2B55c02E065e1693c61a4A56967A2"
open = "games/satan-moloch-baal"
source = "contracts/src/games"

[[extra.apps]]
kind = "message board"
name = "Message Board"
text = "Permanent on-chain messages."
address = "0xE93Ac949Fe806d8b1cA93EB14e5f4d799cAc0d55"
open = "games/message-board"
source = "contracts/src/content"
+++

Built to exercise the first FP127. They still run, unmaintained, against the legacy Huff address `0xfae694D0c2c44181791F838c54Ed64C3151FfE30`. Open one and it mounts below the cards.
