# Replay: the Balancer V2 Composable Stable Pool exploit, five rulers

Generated 2026-10-20T17:27:34Z by `uv run scripts/replays/balancer.py` from `scripts/replays/balancer.json` (fetched 2026-10-20T17:26:44Z by `balancer.py fetch`); every integer below is asserted by `forge test --match-path test/replays/Balancer.t.sol` with no network.

## What happened, in the transaction's own integers

Ethereum tx [`0x6ed07db1…`](https://etherscan.io/tx/0x6ed07db1a9fe5c0794d44cd36081d6a6df103fab868cdd75d581e3bd23bc9742) (block 23,717,397, 2025-11-03T07:46:47 UTC) deploys a contract whose constructor runs one Vault `batchSwap` against each of two ComposableStablePool v5 pools. Every swap in both is GIVEN_OUT. Each `onSwap` call from the Vault carries the pool's raw balances and the requested amount out, and returns the amount the pool charged. Those 121 + 105 calls are the data for this replay.

| pool | swaps | phase replayed | rate token, in-tx rate | amp (A·n^(n−1)·1000) | swap fee |
|---|---|---|---|---|---|
| osETH/WETH-BPT `0xdacf5fa1…` | 121 | 22–111: 90 swaps, 30 cycles of drain / micro / restore | osETH 1.058132408689971699 | 200,000 | 0.01% |
| wstETH-WETH-BPT `0x93d19926…` | 105 | 22–96: 75 swaps, 25 cycles of drain / micro / restore | wstETH 1.218116415279760760 | 5,000,000 | 0.01% |

Swaps 0–21 of each batch swap BPT in for tokens out (exits via swap) until both balances are tiny (osETH pool: 67,000 WETH-wei and 67,000 osETH-wei). The replayed phase then repeats three swaps: **drain** the rate token to 18 wei (5 in the wstETH pool), **micro**: take 17 wei (4) of it out, **restore**: swap the rate token back in for a chosen WETH amount. The last swaps buy BPT back with tokens.

The micro swap, first cycle, osETH pool (swap 23):

- balances before: 374,353 WETH-wei, 18 osETH-wei; amount out 17 osETH-wei.
- `_upscale(17, 1058132408689971699)` = mulDown(17 × 1.058132408689971699 = 17.9882509477) = **17**. mulUp gives 18. The pool's own balance of 18 wei upscales to 19, against a true 19.046. So the pool believes 2 units are left after the swap; the true figure is 1.058.
- Charged on chain: **625,492 WETH-wei**. The exact charge for the same request on the same balances (fee included, rounded up) is **957,169**, so the pool undercharged by 34.7%. The true invariant fell by 24598.5 wei-eq (17.69%) on this one call.
- wstETH pool, swap 23: 4 wei out of 5. 4 × 1.21811641527976076 = 4.87246566112 → **4**. Charged 162,427,217,924,000 WETH-wei; exact 274,224,463,642,335 (40.8% under); the invariant fell by 15.65%.

Across the phase (true invariant D*: the pool's own StableSwap invariant, solved exactly on the raw balances × the exact in-tx rates, in 18-decimal wei):

| pool | D* before swap 22 | D* after the phase | ratio | BPT `getRate()` before → after the whole batchSwap (on chain) | batchSwap net to the attacker |
|---|---|---|---|---|---|
| osETH/WETH | 137894.598 | 2446.08005 | 0.017739 | 1.027348 → 0.020189 (×0.019652) | 11873.89 ETH |
| wstETH/WETH | 2.21811425e+11 | 817973934.0 | 0.0036877 | 1.051822 → 0.003887 (×0.003696) | 7152.903 ETH |

The batchSwap net is the Vault's `assetDeltas`, valued at the in-transaction rates, with the BPT left over valued at its rate after the swaps. Both batchSwaps settle to and from the attack contract's Vault internal balance (`fromInternalBalance` and `toInternalBalance` both true), so nothing leaves the Vault in this transaction. The swaps around the phase exit at the fair BPT price and buy back after the invariant has collapsed, so the take is about (1 − ratio) × the pool's value: 11956.3 ETH projected against 11873.89 realised (osETH), and 7152.96 against 7152.903 (wstETH).

## The same calls on five rulers

Each model prices every call of the phase on that call's own on-chain balances and amount. *Below exact* counts the calls charged less than the exact charge. *ΔD* is the change in the true invariant D* if that call had been charged this model's amount. *Ratio* is the product of the per-call ratios D*after / D*before, which for the deployed row is the on-chain ratio. *Projected* is (1 − ratio) × the pool's value at block − 1, the first-order take of the exit / deflate / re-enter plan; a negative value means the pool gains.

**osETH/WETH** (90 calls, swaps 22–111; pool value 12172.24 ETH)

| model | charged in (WETH-wei / rate-token-wei) | calls below exact | calls that lower D* | ΣΔD* (wei-eq) | ratio | projected take (ETH) |
|---|---|---|---|---|---|---|
| deployed (V2, `_upscale` = mulDown) | 3,529,606 / 199,735 | 60 | 60 | -135448.5 | 0.01773877 | 11956.3 |
| mulUp on the given-out amount (V3's direction) | 5,150,267 / 199,735 | 30 | 30 | 40559.19 | 8.153544 | -87074.6 |
| FP127 inside, ceil to wei once | 4,793,847 / 207,634 | 0 | 0 | 131.117 | 1.010489 | -127.677 |
| FP256 inside, ceil to wei once | 4,793,847 / 207,634 | 0 | 0 | 131.117 | 1.010489 | -127.677 |
| exact rationals, ceil to wei once | 4,793,847 / 207,634 | 0 | 0 | 131.117 | 1.010489 | -127.677 |
| exact, but round-to-nearest at the wei boundary (sensitivity) | 4,793,810 / 207,618 | 53 | 14 | 97.06195 | 1.003503 | -42.6405 |

ΣΔD* by kind of call:

| model | drain | micro | restore |
|---|---|---|---|
| deployed | 5640.19 | -132480.0 | -8609.12 |
| mulUp | 16764.5 | 32403.8 | -8609.12 |
| fp127 | 51.6613 | 41.1886 | 38.2671 |
| fp256 | 51.6613 | 41.1886 | 38.2671 |
| exact | 51.6613 | 41.1886 | 38.2671 |
| nearest | 38.8083 | 36.8999 | 21.3538 |

**wstETH/WETH** (75 calls, swaps 22–96; pool value 7179.439 ETH)

| model | charged in (WETH-wei / rate-token-wei) | calls below exact | calls that lower D* | ΣΔD* (wei-eq) | ratio | projected take (ETH) |
|---|---|---|---|---|---|---|
| deployed (V2, `_upscale` = mulDown) | 1,312,086,551,708,809 / 624,203,250 | 51 | 51 | -2.209935e+11 | 0.0036877 | 7152.96 |
| mulUp on the given-out amount (V3's direction) | 1,929,334,036,622,810 / 624,203,250 | 25 | 25 | 9.135633e+10 | 5.227482 | -30350.9 |
| FP127 inside, ceil to wei once | 1,685,616,985,666,464 / 734,455,370 | 0 | 0 | 2.512774e+8 | 1.008329 | -59.7954 |
| FP256 inside, ceil to wei once | 1,685,616,985,666,464 / 734,455,370 | 0 | 0 | 2.512774e+8 | 1.008329 | -59.7954 |
| exact rationals, ceil to wei once | 1,685,616,985,666,464 / 734,455,370 | 0 | 0 | 2.512774e+8 | 1.008329 | -59.7954 |
| exact, but round-to-nearest at the wei boundary (sensitivity) | 1,685,616,985,666,441 / 734,455,356 | 37 | 5 | 1.643468e+8 | 1.002502 | -17.9639 |

ΣΔD* by kind of call:

| model | drain | micro | restore |
|---|---|---|---|
| deployed | 1.20743e+10 | -1.76733e+11 | -5.6335e+10 |
| mulUp | 7.6825e+10 | 7.08664e+10 | -5.6335e+10 |
| fp127 | 7.17865e+7 | 4.16169e+7 | 1.37874e+8 |
| fp256 | 7.17865e+7 | 4.16169e+7 | 1.37874e+8 |
| exact | 7.17865e+7 | 4.16169e+7 | 1.37874e+8 |
| nearest | 7.17865e+7 | 4.16169e+7 | 5.09433e+7 |

First cycle, per call (osETH/WETH): amount charged and ΔD* (wei-eq).

| swap | kind | out | deployed | mulUp | fp127 | fp256 | exact | nearest |
|---|---|---|---|---|---|---|---|---|
| osETH 22 | drain: WETH in, osETH out | 66,982 | 307,353 (1156.0) | 315,795 (3410.0) | 303,078 (8.408) | 303,078 (8.408) | 303,078 (8.408) | 303,077 (8.139) |
| osETH 23 | micro: WETH in, osETH out | 17 | 625,492 (-24600.0) | 1,041,412 (5921.0) | 957,169 (6.841) | 957,169 (6.841) | 957,169 (6.841) | 957,168 (6.77) |
| osETH 24 | restore: osETH in, WETH out | 891,000 | 5,182 (-1355.0) | 5,182 (-1355.0) | 6,257 (0.8747) | 6,257 (0.8747) | 6,257 (0.8747) | 6,257 (0.8747) |
| wstETH 22 | drain: WETH in, wstETH out | 99,999,999,995 | 221,844,531,789,055 (7.057e+9) | 233,844,076,669,826 (1.524e+10) | 211,681,214,249,624 (1.478e+7) | 211,681,214,249,624 (1.478e+7) | 211,681,214,249,624 (1.478e+7) | 211,681,214,249,624 (1.478e+7) |
| wstETH 23 | micro: WETH in, wstETH out | 4 | 162,427,217,924,000 (-3.582e+10) | 321,601,227,686,763 (1.436e+10) | 274,224,463,642,335 (8.434e+6) | 274,224,463,642,335 (8.434e+6) | 274,224,463,642,335 (8.434e+6) | 274,224,463,642,335 (8.434e+6) |
| wstETH 24 | restore: wstETH in, WETH out | 380,000,000,000,000 | 6,669 (-1.181e+10) | 6,669 (-1.181e+10) | 8,084 (1.362e+7) | 8,084 (1.362e+7) | 8,084 (1.362e+7) | 8,083 (5.784e+6) |

### Which alternative alone suffices

- **FP127 and FP256** charge exactly the exact-rational amount on all 90 + 75 calls. That is asserted call by call in the test, and no call lowers D*. Inside the format the upscaled 17 osETH-wei stays 17.988250947729518883 to within 2^-128. The only rounding to the wei grid is the final ceil, which favours the pool.
- **mulUp alone** defeats the attack as executed: every micro call now over-charges, and the per-call ratio is 8.154 (osETH) and 5.227 (wstETH) instead of 0.01774 and 0.003688. It does not make every call safe. All 30 + 25 restore calls still lower D*, by exactly the deployed amount (-8609.12 and -5.6335e+10 wei-eq). Their given-out token is WETH, whose scaling factor is exactly 1, so mulUp changes nothing there. Their loss comes from the token-in balance: 1 wei of the rate token upscales by mulDown to 1, against a true 1.058 or 1.218. mulUp also over-charges a trader heavily at these balances: 1,041,412 against the exact 957,169 on swap 23.
- **Round-to-nearest at the boundary** instead of ceil, with exact maths inside: 14 + 5 calls lower D* by under half a wei of the token in each. The 0.01% fee keeps the phase net positive, with ratios 1.0035 and 1.0025. FP127's claim therefore depends on keeping the boundary's direction.
- The attacker's plan itself cannot be executed under the alternatives. Replayed adaptively (drain to 18, take 17, restore with the recorded WETH amount) on each model's own balances, it reaches swap 25 under mulUp and swap 25 under exact pricing with less of the rate token left than it means to leave behind (13 wei against 18). In the wstETH pool it fails at swaps 28 and 31. Under deployed pricing it reproduces the on-chain sequence exactly.

### Where the deployed undercharge comes from

The difference deployed − exact, summed by kind of call and split by where the rounding happens, is in units of the token in. *amountOut*: only the given-out amount upscaled by mulDown. *balances*: only the balances upscaled by mulDown. *upscales*: both together. *solver*: what remains, which is StableMath's integer Newton (P_D floored, c rounded up, stop at ≤ 1, +1), `_downscaleUp` and the fee's divUp.

| pool | kind | amountOut | balances | upscales | solver | total |
|---|---|---|---|---|---|---|
| osETH | drain | -12041.7 | 13870.0 | 1156.35 | 11642.7 | 12799.0 |
| osETH | micro | -1.36865e+6 | 105706.0 | -1.3319e+6 | 54893.8 | -1.27701e+6 |
| osETH | restore | 0 | -10320.4 | -10320.4 | 2436.64 | -7883.77 |
| wstETH | drain | -3.98097e+13 | 5.48999e+13 | 5.53885e+12 | 9.17902e+12 | 1.47179e+13 |
| wstETH | micro | -4.07712e+14 | 5.44993e+13 | -3.88296e+14 | 4.76545e+10 | -3.88248e+14 |
| wstETH | restore | 0 | -1.10933e+8 | -1.10933e+8 | 680858.0 | -1.10252e+8 |

The micro calls' undercharge is the given-out amount's truncation. The balance truncation partly offsets it there and is the whole loss on the restore calls. The integer solvers err on the pool's side in every kind of call.

## Newton convergence: where each ruler stops

StableMath's `_calculateInvariant` and `_getTokenBalanceGivenInvariantAndAllOtherBalances` are Newton iterations that stop when two iterates differ by ≤ 1 on the wei grid. The same two maps run in FP127 and in FP256 with the same algebra, reordered only so that FP127 does not overflow. Their stop is ≤ 1 unit of the format's own grid, or a stall: the step has stopped shrinking and is already below 2^-64 (FP127) or 2^-128 (FP256) of the iterate. Residuals are measured against the exact root (200 digits) of the same inputs each solver received.

| pool | ruler | invariant: iterations (median / max) | invariant: worst residual | balance: iterations (median / max) | balance: worst residual |
|---|---|---|---|---|---|
| osETH | wei grid (deployed) | 4 / 10 | 2.255 wei (rel 0.00026, 3.59 digits) | 4 / 7 | rel 0.127 (0.9 digits), always above the root; the stop alone leaves ≤ 0.9989 wei |
| osETH | FP127 | 7 / 13 | rel 1.11e-38 (37.95 digits) | 7 / 11 | rel 2.1e-40 (39.68 digits) |
| osETH | FP256 | 8 / 13 | rel 1.15e-71 (70.94 digits) | 8 / 12 | rel 3.25e-71 (70.49 digits) |
| wstETH | wei grid (deployed) | 18 / 24 | 0.998 wei (rel 1.23e-9, 8.91 digits) | 13 / 16 | rel 0.219 (0.66 digits), always above the root; the stop alone leaves ≤ 0.9911 wei |
| wstETH | FP127 | 22 / 32 | rel 2.56e-36 (35.59 digits) | 15 / 19 | rel 3.08e-40 (39.51 digits) |
| wstETH | FP256 | 21 / 27 | rel 9.08e-72 (71.04 digits) | 15 / 19 | rel 1.84e-71 (70.74 digits) |

- The same iteration reaches whatever ruler it runs on. On the wei grid the invariant stops within 2.25 wei of its own root (worst relative 0.00026, 3.59 digits, osETH; 8.91 in the larger wstETH pool). On FP127 it reaches 35.59–37.95 digits, and on FP256 70.94–71.04. It costs a few more iterations: median 4 → 7 → 8 (osETH) and 18 → 22 → 21 (wstETH, where one balance is 1 wei against 10^14).
- The literal "≤ 1 unit" stop does not carry over to a fine grid. The map evaluated in FP127 is noisier than one unit near the root (D times a ratio carries D·2^-128), so the literal rule never stopped within 255 iterations on 11 of 90 (osETH) and 27 of 75 (wstETH) invariant solves. In FP256 the counts are 5 and 4. StableMath's cap would revert there (`STABLE_INVARIANT_DIDNT_CONVERGE`). The stall test ends them, and their residuals are in the table. The balance solver's literal rule always stopped.
- The deployed solvers are not what the attacker exploited. Their result is the root of their own rounded quadratic to within ≤ 1 wei, and is always above the exact root (90/90 and 75/75). So it charges more, by up to 0.127 and 0.219 of the solved balance, because its coefficients are rounded to whole units before it starts. b = sum + ⌊D / (amp·n)⌋·1000 loses D / (amp·n) entirely in the osETH pool, where D < amp·n = 400,000 throughout the phase. P_D = ⌊2·b0·2·b1 / D⌋ is floored and c is rounded up; each of these raises the solved balance. The invariant's ≤ 1 stop lands on either side of the root (56 below / 34 above in osETH; 75 / 0 in wstETH). The wei ruler decided these answers too, but in the pool's favour. The 1-wei quantum that hurt was the one applied to the *inputs* of the solve: the given-out amount and the token-in balance.

## Against the published write-ups

- OpenZeppelin's 17 × 1.058132408689971699 = 17.98 → 17 against a balance of 18 is exactly every micro swap of the osETH pool (the first is swap 23).
- No call in this transaction has a 9-wei balance, an 8-wei amount out or the 8.918 product. The Ethereum pools are steered to 18 wei of osETH (out 17) and 5 wei of wstETH (out 4, 4 × 1.218 = 4.87 → 4, truncated by 18%). That example may come from another chain's pool; it is not this one.
- Counts in this transaction: 121 + 105 swaps in the two batchSwaps, of which 90 + 75 are token-for-token and 30 + 25 are the micro swaps. "65 operations" does not match any of these counts.
- The truncation per micro swap is 5.5% of the amount (osETH) and 17.9% (wstETH). The damage is larger: 34.7% and 40.8% of the charge on the first micro swaps, and 17.7% and 15.6% of the whole invariant on that one call. This is because the pool also misjudges what is left, 2 against 1.058, at the steep end of the curve.

## Provenance

- Transaction 0x6ed07db1a9fe5c0794d44cd36081d6a6df103fab868cdd75d581e3bd23bc9742, block 23717397 (`0xa41291bd698366d29a718636ac12a3a46bb969f43d3955b9f7666a8293ac1fb5`), from `0x506d1f9efe24f0d47853adca907eb8d89ae03207`, contract created `0x54b53503c0e2173df29f8da735fbd45ee8aba30d`, status 1, gas 28,348,674.
- Call trace: `debug_traceTransaction` with `callTracer` from https://eth.drpc.org (keyless), sha256 of the canonical JSON `55dc57cfcbbe1ee54269bdafe25a3e0c3e0293913a0aec1ccfa4f613aa39a23f`. Every `onSwap` (selector `0x01ec954a`) to each pool is decoded into `pools.*.swaps` (kind, indices, amount, the balances the Vault passed, the return).
- Pool state at block 23717396 by `eth_call` on https://mainnet.gateway.tenderly.co: pool tokens and balances (equal to the first call's), scaling factors, rate providers, amp, swap fee, BPT rate, `version()` (`20230711-composable-stable-pool-v5`). The rate used by every swap is the one in the transaction: the attacker called `updateTokenRateCache` first. osETH's provider returned 1058132408689971699 in the transaction, against a cached 1058109553424427048 and 1058132398695929516 from the provider at block − 1. For wstETH the cache already equalled the provider (1218116415279760760). `scalingFactorsInTx` is the attacker's own `getScalingFactors()` read after the update.
- Source: verified standard-JSON input of both pools from https://api.routescan.io/v2/network/mainnet/evm/1/etherscan/api (`getsourcecode`), ComposableStablePool v0.7.1+commit.f4a555be, optimizer 800 runs; the two pools' files are byte-identical. Transcribed into `test/replays/Balancer.t.sol` (library `BalancerV2`, under its GPL-3.0-or-later license):

| function | verified file:lines | sha256 of the file |
|---|---|---|
| `onSwap` | `@balancer-labs/v2-pool-utils/contracts/BaseGeneralPool.sol:32-47` | `a48d3fe6126e1a49…` |
| `_swapGivenOut` | `@balancer-labs/v2-pool-utils/contracts/BaseGeneralPool.sol:68-85` | `a48d3fe6126e1a49…` |
| `_swapGivenOut` | `contracts/ComposableStablePool.sol:214-231` | `49222c43627d097b…` |
| `_onRegularSwap` | `contracts/ComposableStablePool.sol:279-299` | `49222c43627d097b…` |
| `_addSwapFeeAmount` | `@balancer-labs/v2-pool-utils/contracts/BasePool.sol:618-621` | `9fec78a410cccd92…` |
| `_upscale` | `@balancer-labs/v2-pool-utils/contracts/BasePool.sol:680-686` | `9fec78a410cccd92…` |
| `_upscaleArray` | `@balancer-labs/v2-pool-utils/contracts/BasePool.sol:692-699` | `9fec78a410cccd92…` |
| `_downscaleUp` | `@balancer-labs/v2-pool-utils/contracts/BasePool.sol:726-728` | `9fec78a410cccd92…` |
| `_calculateInvariant` | `contracts/StableMath.sol:57-120` | `25154c99a1317301…` |
| `_calcInGivenOut` | `contracts/StableMath.sol:164-199` | `25154c99a1317301…` |
| `_getTokenBalanceGivenInvariantAndAllOtherBalances` | `contracts/StableMath.sol:399-449` | `25154c99a1317301…` |
| `mulDown` | `@balancer-labs/v2-solidity-utils/contracts/math/FixedPoint.sol:48-53` | `9f40aa0869e0e725…` |
| `mulUp` | `@balancer-labs/v2-solidity-utils/contracts/math/FixedPoint.sol:55-70` | `9f40aa0869e0e725…` |
| `divUp` | `@balancer-labs/v2-solidity-utils/contracts/math/FixedPoint.sol:85-102` | `9f40aa0869e0e725…` |
| `complement` | `@balancer-labs/v2-solidity-utils/contracts/math/FixedPoint.sol:158-160` | `9f40aa0869e0e725…` |
| `divUp` | `@balancer-labs/v2-solidity-utils/contracts/math/Math.sol:88-96` | `396edd3bb7de1cd0…` |

Not done: recompiling the verified source and comparing bytecode with `eth_getCode`, as the accrual study does. The transcription is instead checked against all 165 on-chain returns of the phase. Each call is reproduced bit for bit from its own inputs, and the whole phase is reproduced from its first balances alone.

## What the test asserts

`test/replays/Balancer.t.sol` reads `scripts/replays/balancer.json` and needs no network:

- `test_deployed_*`: every call's return, bit for bit.
- `test_deployed_plan_*`: the plan replayed from the first balances reproduces every amount and every Vault balance.
- `test_mulUp_*`: the mulUp variant equals this script's port.
- `test_fp127_*` and `test_fp256_*`: the formats equal the exact-rational charge on every call.
- `test_upscale_headline`: the products by hand.

`balancer.py` also asserts three things: that its Python port equals the Solidity transcription in amount, D, y and iteration counts on every call; that the Vault's balances chain from call to call; and that the per-call invariant ratios telescope to the on-chain one.

## Caveat

The alternatives are priced call by call on the balances that actually occurred, not along a path an attacker would re-optimise for each ruler. They show that these calls stop paying under FP127, FP256 or exact pricing; they do not show that no other sequence could find what remains, such as the token-in balance truncation that mulUp leaves.

