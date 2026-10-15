# Ladder deployment record

The terminal-precision ladder (docs/benchmarks/ladder.md) is reproducible on
chain: `LadderRunner.run(scenario, form, n, p)` executes any cell with one
`eth_call`, where `p` is the input's parameters floored into that library's
representation (scripts/ladder/inputs.json, served at /data/ladder-inputs.json),
and returns the raw result in that representation plus the gas the scenario
consumed inside the adapter. The harness that produced the committed dataset
called this same code, so the two cannot disagree; `scripts/ladder/livecap.py`
re-runs every cell of every input through the live runner and records the
largest N the public RPC completes.

Version 5 (ten adapters calling FP127 v4; ABDKMathQuad, Balancer, Aave,
Morpho and Maker added as forms 5 to 9; two accrual scenarios) is prepared
and not yet deployed: salt `"FP127 ladder v5"`
(`0x4650313237206c61646465722076350000000000000000000000000000000000`),
predicted by `make predict-ladder` from the artifacts:

| contract | predicted address |
|---|---|
| `LadderFP127` | `0x3d081d43718fCc84D580ADe2813049f8F797347B` |
| `LadderFP127Lib` | `0xf7e9664fe8e0A60EA5F83cf8e34Dd3A232Cd5c06` |
| `LadderABDK` | `0xbF64D2E3d934A2155db21207FC3F6Cb01F72AEdb` |
| `LadderSolady` | `0x1b71c4e4A12531dD42263631991eE5b472c2B697` |
| `LadderPRB` | `0xD78E4Fa72645BAeBef1A25E34aCc360862364c08` |
| `LadderQuad` | `0x02715fba28Ee4432d04882424cc3F3FB2d181cdE` |
| `LadderBalancer` | `0xe9e394859D6D81C3F1eB77377b72F153A921a3c6` |
| `LadderAave` | `0x9296c923De10572f04e60E4956897a285b8e2843` |
| `LadderMorpho` | `0xCB62d25bd8B69cB60316B40D7d67dbb5020Eca8d` |
| `LadderMaker` | `0xC171cf2efDf2e9d1b01d433f752BDC5B5Eab79b7` |
| `LadderRunner` | `0xE8d7FF4Dd1a962476847Cf30c04B5A97F32474c9` |

`LadderRunner` v5 is constructed with the ten adapter addresses as one
`address[10]` in form-id order; `LadderFP127` staticcalls FP127 v4 at
`0x6cFbCB928Ac068E84Ef793Dd1DFce4f8e9Cac1d1`, which is deployed first. Until
then the site's verify buttons call version 4 below, which answers the
nine original scenarios for forms 0 to 4.

Version 4 (the adapters call FP127 v3, which adds `pi`) is deployed with CREATE2
through the proxy `0x4e59b44847b379578588920cA78FbF26c0B4956C` with salt
`"FP127 ladder v4"`
(`0x4650313237206c61646465722076340000000000000000000000000000000000`).
Version 3 (salt `"FP127 ladder v3"`, runner
`0xae42E3AdEb2FAd105aF59C14714801552867D5E9`) calls FP127 v2 and still answers.
Version 2 (salt `"FP127 ladder v2"`, runner
`0x2d741eC5d66D7559857da1c398AE384A389DdE17`) has the same interface and
still answers, calling FP127 v1.
Machine-readable copy: `Ladder.json`. Deployed 2026-10-07 by `make deploy-ladder-sepolia`, all six Sourcify `exact_match`.

| contract | address | tx | block | gas |
|---|---|---|---:|---:|
| `LadderFP127` | `0x3b3b7300B22e621a2350353f2D6BCD5B3Cf79cB6` | [`0x23aa191f…`](https://sepolia.etherscan.io/tx/0x23aa191fd3b0a2f563d7e2e6fb0836e309e85b5b0963bb747f2050198d5b69ae) | 11,861,165 | 4,103,006 |
| `LadderFP127Lib` | `0x5Fe3420fc2C330553061bc39d9fb178E7d854Fe1` | [`0x953f7b7b…`](https://sepolia.etherscan.io/tx/0x953f7b7be6a55c5b046e17779e6f0bebcdee75c59f7680cef8c4097c93216cb2) | 11,861,166 | 9,476,398 |
| `LadderABDK` | `0x8974369439217370d5D486FB12EF71C0A1F38897` | [`0x0f38a2be…`](https://sepolia.etherscan.io/tx/0x0f38a2becfe648083df4b167d2ee2dca3fc40034bf91fb30146474dba6477ef7) | 11,861,167 | 9,120,028 |
| `LadderSolady` | `0x9F7766CF9f807799CBB92068257891dAD0372de7` | [`0xe7910122…`](https://sepolia.etherscan.io/tx/0xe79101221ff0ad2d6cc758a5fd00be9a80b7446692fa537d273690780a67555f) | 11,861,168 | 5,935,658 |
| `LadderPRB` | `0xa014CCDd2F71B7D253Ba8A9bC0Fd72eba4d8E038` | [`0x363db9cf…`](https://sepolia.etherscan.io/tx/0x363db9cfd2d198e2f2ff00515d11b98ef4528b7952ad6ffc4b81950ec104c1d1) | 11,861,170 | 9,844,327 |
| `LadderRunner` | `0x798C37A3E5B421D480AC850258466b5598A1A555` | [`0x36e7ee33…`](https://sepolia.etherscan.io/tx/0x36e7ee330e95d3170111756691a4aa9bb7ef9f6916f97c7896ecd1caaa95473e) | 11,861,171 | 2,644,644 |

`LadderRunner` is constructed with the five adapter addresses in that
order; `LadderFP127` staticcalls the FP127 object at
`0xe43F720861074497db2e974E5c4554E4A3b341B9` (version 3).

The version 1 contracts (salt `"FP127 ladder v1"`, runner
`0x3FD3461EE53F9C6f2322CbB3fF97A3EdA522d4a4`, `run(uint8,uint8,uint32)` with
the parameters compiled in) remain on Sepolia and still answer for the v1
dataset, which is in the repository history up to the ladder-inputs merge.

## Calling it

```
cast call 0x798C37A3E5B421D480AC850258466b5598A1A555 \
  "run(uint8,uint8,uint32,int256[])(bool,int256,bytes4,uint256,uint256)" \
  <scenario> <form> <n> "[<p0>,<p1>,...]" \
  --rpc-url https://ethereum-sepolia-rpc.publicnode.com
```

Scenario ids are the `index` field in `scripts/ladder/scenarios.json`
(0 compound, 1 compound-pow, 2 bonding-sqrt, 3 roundtrip, 4 amortise,
5 geo-mean, 6 black-scholes-chain, 7 cumulative-product, 8 compound-annual,
9 accrual-per-second, 10 accrual-continuous; the last two from v5);
forms are 0 fp127, 1 fp127lib, 2 abdk, 3 solady, 4 prb, and from v5
5 quad, 6 balancer, 7 aave, 8 morpho, 9 maker. `p` is the input's `fp127`,
`abdk`, `wad`, `quad` or `ray` array from `scripts/ladder/inputs.json` (forms
0 and 1 take `fp127`, 2 `abdk`, 3, 4, 6 and 8 `wad`, 5 `quad`, 7 and 9 `ray`),
in the scenario's `order`. The returned `bool` is false when the library
reverted, with the selector in the `bytes4`; `BadParamCount`,
`ParamOutOfRange` and `Unsupported` are the adapter's own errors for a
wrong-length or out-of-range `p` or a scenario outside the library's model.
Decode `int256` by the form's scale (2^128, 2^128, 2^64, 1e18, 1e18; the
`quad` form returns the bit pattern of an IEEE binary128; `ray` is 1e27). The last two values
are gas per step and total gas, measured inside the adapter around the
scenario function.

Example, the headline cell (compound, reference input, FP127, N = 365):

```
cast call 0x798C37A3E5B421D480AC850258466b5598A1A555 \
  "run(uint8,uint8,uint32,int256[])(bool,int256,bytes4,uint256,uint256)" 0 0 365 \
  "[3402823669209384634633746074317682114560000,93228045731763962592705371899114578]" \
  --rpc-url https://ethereum-sepolia-rpc.publicnode.com
```

## Live cap

Public RPCs limit `eth_call`. Cells needing more than roughly 40M gas (the
transcendental scenarios at N = 10,000) fail with a bare revert from the
runner's try/catch, because the adapter ran out of gas inside it. The
largest N that completes for every input of a form is recorded as
`liveMaxN` in `ladder.json`; the page greys out verify above it. Anyone with
their own node can raise the cap and run every cell.

## Trust model

No storage, no owner, no upgrade path. The adapters are immutable in the
runner. A change to any scenario is a new source, new init code hashes,
new addresses and a new salt string, recorded here.

## Reproduce

```
make predict-ladder            # the addresses above, from the current source
make deploy-ladder-sepolia     # DEPLOYER_KEY in the environment; skips what is deployed
make verify-ladder-sepolia     # Sourcify (and Etherscan with ETHERSCAN_API_KEY)
uv run scripts/ladder/livecap.py   # every cell of every input against the live runner
```
